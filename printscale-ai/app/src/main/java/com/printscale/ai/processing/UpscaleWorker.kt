package com.printscale.ai.processing

import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.content.pm.ServiceInfo
import android.graphics.ColorSpace
import androidx.core.app.NotificationCompat
import androidx.work.CoroutineWorker
import androidx.work.ForegroundInfo
import androidx.work.WorkerParameters
import androidx.work.workDataOf
import com.printscale.ai.PrintScaleApp
import com.printscale.ai.R
import com.printscale.ai.data.HistoryItem
import com.printscale.ai.data.JobSpec
import com.printscale.ai.data.Paths
import com.printscale.ai.imaging.Imaging
import com.printscale.ai.imaging.orientedTo
import com.printscale.engine.AlphaBleed
import com.printscale.engine.CloudClient
import com.printscale.engine.CloudException
import com.printscale.engine.CloudLink
import com.printscale.engine.CropGeometry
import com.printscale.engine.PixelBuffer
import com.printscale.engine.PngStreamReader
import com.printscale.engine.StreamingResizer
import com.printscale.engine.PngStreamWriter
import com.printscale.engine.PreviewSink
import com.printscale.engine.ProgressListener
import com.printscale.engine.Stage
import com.printscale.engine.TeeSink
import com.printscale.engine.UpscaleCancelled
import com.printscale.engine.UpscalePipeline
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileOutputStream

class UpscaleWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    private val paths = Paths(context)
    private val graph get() = (applicationContext as PrintScaleApp).graph
    private val startedAt = System.currentTimeMillis()
    private var lastProgressAt = 0L

    override suspend fun doWork(): Result {
        val jobId = inputData.getString(KEY_JOB) ?: return Result.failure(workDataOf(KEY_ERROR to "Missing job."))
        val master = paths.jobMaster(jobId)
        return try {
            runCatching { setForeground(foregroundInfo(0, 0, "Preparing image")) }
            report(JobStage.PREPARING, 0, 0, null, force = true)
            val spec = JobSpec.fromJson(JSONObject(paths.jobSpec(jobId).readText()))
            val info = graph.imports.get(spec.importId) ?: throw IllegalStateException("The imported image is no longer available.")
            val originalFile = graph.imports.original(spec.importId)
            val icc = graph.imports.icc(spec.importId)

            val result = withContext(Dispatchers.Default) {
                // 1. Prepare the crop/fit canvas at source resolution.
                val decoded = Imaging.decode(originalFile, info.workW, info.workH).orientedTo(info.workW, info.workH, originalFile)
                val keepProfile = icc != null && !Imaging.isSrgb(decoded.colorSpace)
                val cs = if (keepProfile) decoded.colorSpace!! else ColorSpace.get(ColorSpace.Named.SRGB)
                val geom = CropGeometry(decoded.width, decoded.height, spec.aspect, spec.fitMode, spec.crop)
                val prepared = Imaging.renderPrepared(decoded, geom, spec.background, cs)
                decoded.recycle()
                Imaging.savePng(prepared, paths.jobSource(jobId))
                Imaging.scaleToFit(prepared, PREVIEW_SIDE).let { b ->
                    Imaging.savePng(b, paths.jobBefore(jobId)); if (b != prepared) b.recycle()
                }
                val pixels = Imaging.toPixelBuffer(prepared)
                prepared.recycle()
                if (isStopped) throw UpscaleCancelled()

                val preview = PreviewSink(spec.targetW, spec.targetH, PREVIEW_SIDE)
                val hasAlpha: Boolean
                if (spec.useAi && spec.engine == JobSpec.ENGINE_CLOUD) {
                    // 2a. AI on the user's notebook GPU; everything after it happens here.
                    hasAlpha = pixels.hasTransparency()
                    runCloud(jobId, pixels, geom.outW, geom.outH, spec, hasAlpha, if (keepProfile) icc else null, preview)
                } else {
                    // 2b. On-device model, pipeline, streaming PNG.
                    report(JobStage.ANALYZING, 0, 0, null, force = true)
                    val pipeline = UpscalePipeline(pixels, spec.targetW, spec.targetH, spec.settings, spec.useAi)
                    hasAlpha = pipeline.hasAlpha
                    val model = if (spec.useAi) ModelProvider.create(applicationContext, spec.settings.denoise) else null
                    try {
                        BufferedOutputStream(FileOutputStream(master), 1 shl 20).use { out ->
                            val png = PngStreamWriter(out, spec.targetW, spec.targetH, pipeline.hasAlpha, spec.print?.dpi ?: 300,
                                if (keepProfile) icc else null)
                            pipeline.run(model, TeeSink(png, preview), object : ProgressListener {
                                override fun onStage(stage: Stage) {
                                    when (stage) {
                                        Stage.ANALYZING -> report(JobStage.ANALYZING, 0, 0, null, force = true)
                                        Stage.UPSCALING -> report(JobStage.UPSCALING, 0, 1, null, force = true)
                                        Stage.FINALIZING -> report(JobStage.FINALIZING, 0, 0, null, force = true)
                                    }
                                }

                                override fun onAiProgress(done: Long, total: Long, etaMillis: Long?) {
                                    report(JobStage.UPSCALING, done, total, etaMillis)
                                }
                            }, { isStopped })
                        }
                    } finally {
                        model?.close()
                    }
                }
                val pv = Imaging.toBitmap(preview.result, cs)
                Imaging.savePng(pv, paths.jobPreview(jobId))
                pv.recycle()
                Triple(geom.outW, geom.outH, hasAlpha)
            }
            graph.history.add(
                HistoryItem(
                    id = jobId, createdAt = System.currentTimeMillis(), displayName = info.displayName,
                    importId = spec.importId, originalW = info.width, originalH = info.height,
                    preparedW = result.first, preparedH = result.second, finalW = spec.targetW, finalH = spec.targetH,
                    aiUsed = spec.useAi, printWIn = spec.print?.size?.widthIn, printHIn = spec.print?.size?.heightIn,
                    dpi = spec.print?.dpi, hasAlpha = result.third, masterBytes = master.length(),
                    durationMs = System.currentTimeMillis() - startedAt, exports = emptyList(),
                    engine = if (spec.useAi) spec.engine else JobSpec.ENGINE_DEVICE,
                ),
            )
            Result.success()
        } catch (e: UpscaleCancelled) {
            cleanup(jobId); Result.failure(workDataOf(KEY_ERROR to "Cancelled."))
        } catch (e: OutOfMemoryError) {
            cleanup(jobId)
            Result.failure(workDataOf(KEY_ERROR to "The phone ran out of memory. Try a smaller crop or output size."))
        } catch (e: Exception) {
            cleanup(jobId)
            if (isStopped) Result.failure(workDataOf(KEY_ERROR to "Cancelled."))
            else Result.failure(workDataOf(KEY_ERROR to (e.message ?: "Processing failed (${e.javaClass.simpleName}).")))
        } catch (e: LinkageError) {
            // The ONNX Runtime native library could not load (unsupported CPU or damaged install).
            cleanup(jobId)
            Result.failure(workDataOf(KEY_ERROR to "The AI engine could not start on this device (${e.javaClass.simpleName})."))
        }
    }

    /**
     * Uploads the prepared crop, waits for AuraSR on the notebook GPU, downloads the 4x result and
     * streams it through the same Lanczos resize and PNG writer the on-device path uses.
     */
    private suspend fun runCloud(
        jobId: String, pixels: PixelBuffer, w: Int, h: Int, spec: JobSpec, hasAlpha: Boolean, icc: ByteArray?, preview: PreviewSink,
    ) {
        val link = graph.settings.cloudLink.value?.let(CloudLink::parse)
            ?: throw CloudException("No cloud GPU is connected. Open Cloud GPU on the Home screen and paste the notebook link.")
        val client = CloudClient(link)
        val dir = paths.jobDir(jobId)
        val upload = File(dir, "upload.png")
        val result = File(dir, "cloud_result.png")
        if (hasAlpha) AlphaBleed.apply(pixels) // the model only sees colour; keep cut-out edges clean
        BufferedOutputStream(FileOutputStream(upload), 1 shl 20).use { out ->
            val png = PngStreamWriter(out, w, h, hasAlpha, null, null, compressionLevel = 6)
            val row = IntArray(w)
            for (y in 0 until h) { System.arraycopy(pixels.argb, y * w, row, 0, w); png.writeRow(y, row) }
            png.finish()
        }
        report(JobStage.UPLOADING, 0, upload.length(), null, force = true)
        val remoteId = client.submit(upload, { s, t -> report(JobStage.UPLOADING, s, t, null) }, { isStopped })
        upload.delete()
        try {
            var failures = 0
            var firstAt = -1L
            var firstDone = 0L
            while (true) {
                if (isStopped) throw UpscaleCancelled()
                delay(1500)
                val job = try {
                    client.status(remoteId).also { failures = 0 }
                } catch (e: CloudException) {
                    // tunnels drop the odd request; give up only after about 45 s of silence
                    if (!e.retryable || ++failures > 30) throw e
                    continue
                }
                if (job.failed) throw CloudException(job.error?.let { "The cloud GPU failed: $it" } ?: "The job was stopped on the server.")
                if (job.total > 0) {
                    val now = System.currentTimeMillis()
                    if (firstAt < 0 && job.done > 0) { firstAt = now; firstDone = job.done }
                    val measured = job.done - firstDone
                    val eta = if (firstAt > 0 && measured > 0 && now - firstAt > 3000) (now - firstAt) * (job.total - job.done) / measured else null
                    report(JobStage.CLOUD, job.done, job.total, eta)
                } else {
                    report(JobStage.CLOUD, 0, 0, null)
                }
                if (job.finished) break
            }
            report(JobStage.DOWNLOADING, 0, 1, null, force = true)
            client.download(remoteId, result, { s, t -> report(JobStage.DOWNLOADING, s, t, null) }, { isStopped })
        } catch (e: Exception) {
            client.cancel(remoteId)
            throw e
        }
        client.cancel(remoteId) // done: free the server's copy right away
        report(JobStage.FINALIZING, 0, 0, null, force = true)
        PngStreamReader(result.inputStream()).use { r ->
            if (r.width != w * 4 || r.height != h * 4) {
                throw CloudException("The server returned ${r.width} x ${r.height} px, expected ${w * 4} x ${h * 4}.")
            }
            BufferedOutputStream(FileOutputStream(paths.jobMaster(jobId)), 1 shl 20).use { out ->
                val png = PngStreamWriter(out, spec.targetW, spec.targetH, hasAlpha, spec.print?.dpi ?: 300, icc)
                val sink = TeeSink(png, preview)
                StreamingResizer(r.width, r.height, spec.targetW, spec.targetH).run(r::readRow, sink) {
                    if (isStopped) throw UpscaleCancelled()
                }
                sink.finish()
            }
        }
        result.delete()
    }

    /** Temporary files of a job that did not finish are removed straight away. */
    private fun cleanup(jobId: String) {
        paths.jobDir(jobId).deleteRecursively()
    }

    private fun report(stage: JobStage, done: Long, total: Long, eta: Long?, force: Boolean = false) {
        val now = System.currentTimeMillis()
        if (!force && now - lastProgressAt < 400) return
        lastProgressAt = now
        setProgressAsync(
            workDataOf(
                KEY_STAGE to stage.name, KEY_DONE to done, KEY_TOTAL to total,
                KEY_ETA to (eta ?: -1L), KEY_STARTED to startedAt,
            ),
        )
        runCatching { setForegroundAsync(foregroundInfo(done, total, stage.label)) }
    }

    override suspend fun getForegroundInfo(): ForegroundInfo = foregroundInfo(0, 0, "Preparing image")

    private fun foregroundInfo(done: Long, total: Long, text: String): ForegroundInfo {
        val nm = applicationContext.getSystemService(NotificationManager::class.java)
        if (nm.getNotificationChannel(CHANNEL) == null) {
            nm.createNotificationChannel(NotificationChannel(CHANNEL, "Upscaling progress", NotificationManager.IMPORTANCE_LOW))
        }
        val pct = if (total > 0) (done * 100 / total).toInt() else 0
        val n = NotificationCompat.Builder(applicationContext, CHANNEL)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle("Upscaling artwork")
            .setContentText(text)
            .setOngoing(true)
            .setOnlyAlertOnce(true)
            .setProgress(100, pct, total <= 0)
            .build()
        return ForegroundInfo(NOTIFICATION_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC)
    }

    companion object {
        const val KEY_JOB = "job"
        const val KEY_ERROR = "error"
        const val KEY_STAGE = "stage"
        const val KEY_DONE = "done"
        const val KEY_TOTAL = "total"
        const val KEY_ETA = "eta"
        const val KEY_STARTED = "started"
        const val PREVIEW_SIDE = 2048
        private const val CHANNEL = "upscale"
        private const val NOTIFICATION_ID = 41
    }
}
