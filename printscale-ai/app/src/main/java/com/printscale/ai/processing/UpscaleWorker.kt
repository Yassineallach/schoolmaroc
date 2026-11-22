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
import com.printscale.engine.CropGeometry
import com.printscale.engine.PngStreamWriter
import com.printscale.engine.PreviewSink
import com.printscale.engine.ProgressListener
import com.printscale.engine.Stage
import com.printscale.engine.TeeSink
import com.printscale.engine.UpscaleCancelled
import com.printscale.engine.UpscalePipeline
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.BufferedOutputStream
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

                // 2. Model, pipeline, streaming PNG.
                report(JobStage.ANALYZING, 0, 0, null, force = true)
                val pipeline = UpscalePipeline(pixels, spec.targetW, spec.targetH, spec.settings, spec.useAi)
                val model = if (spec.useAi) ModelProvider.create(applicationContext, spec.settings.denoise) else null
                val preview = PreviewSink(spec.targetW, spec.targetH, PREVIEW_SIDE)
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
                val pv = Imaging.toBitmap(preview.result, cs)
                Imaging.savePng(pv, paths.jobPreview(jobId))
                pv.recycle()
                Triple(geom.outW, geom.outH, pipeline.hasAlpha)
            }
            graph.history.add(
                HistoryItem(
                    id = jobId, createdAt = System.currentTimeMillis(), displayName = info.displayName,
                    importId = spec.importId, originalW = info.width, originalH = info.height,
                    preparedW = result.first, preparedH = result.second, finalW = spec.targetW, finalH = spec.targetH,
                    aiUsed = spec.useAi, printWIn = spec.print?.size?.widthIn, printHIn = spec.print?.size?.heightIn,
                    dpi = spec.print?.dpi, hasAlpha = result.third, masterBytes = master.length(),
                    durationMs = System.currentTimeMillis() - startedAt, exports = emptyList(),
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
