package com.printscale.engine

import kotlin.math.max
import kotlin.math.min

/** A super-resolution network. Input and output are CHW RGB planes in 0..1. */
interface SrModel : AutoCloseable {
    val scale: Int
    fun run(chw: FloatArray, h: Int, w: Int): FloatArray
    /** Ask a running inference to stop as soon as possible. */
    fun interrupt() {}
}

class UpscaleCancelled : RuntimeException("Processing cancelled")

data class EnhanceSettings(
    /** 1 = full AI detail, lower values blend towards a smooth bicubic enlargement. */
    val detail: Float = 1f,
    /** Unsharp-mask amount applied to the AI output. 0 = none. */
    val sharpen: Float = 0.15f,
    /** Real-ESRGAN denoise strength. Used when the model is built (see ModelBlender). */
    val denoise: Float = 0.5f,
)

data class TileConfig(
    val tile: Int = 256,
    /** Context around each tile. 24 px keeps seams below 1/255 for this model (see tests). */
    val pad: Int = 24,
    /** Upper bound for the buffer holding one strip of AI output rows. */
    val maxStripBytes: Long = 48L * 1024 * 1024,
)

enum class Stage { ANALYZING, UPSCALING, FINALIZING }

interface ProgressListener {
    fun onStage(stage: Stage) {}
    /** done/total measure source pixels already run through the model. */
    fun onAiProgress(done: Long, total: Long, etaMillis: Long?) {}
}

/**
 * Produces the 4× AI image one row at a time. Internally it fills one horizontal strip of tiles,
 * hands out its rows, then computes the next strip, so the full 4× image never exists in memory.
 */
class AiRowProducer(
    private val src: PixelBuffer,
    private val model: SrModel,
    private val settings: EnhanceSettings,
    private val cfg: TileConfig,
    private val hasAlpha: Boolean,
    private val onTileDone: (Long) -> Unit,
    private val checkCancel: () -> Unit,
) {
    private val s = model.scale
    val outW = src.width * s
    val outH = src.height * s
    private val stripH: Int = (cfg.maxStripBytes / (4L * s * s * src.width)).toInt().coerceIn(8, cfg.tile)
    private val strip = IntArray(s * stripH * outW)
    private var stripY0 = 0
    private var stripRows = 0
    private var nextSrcY = 0
    private var nextRow = 0

    fun readRow(dst: IntArray) {
        if (nextRow >= stripY0 + stripRows) computeStrip()
        System.arraycopy(strip, (nextRow - stripY0) * outW, dst, 0, outW)
        nextRow++
    }

    private fun computeStrip() {
        val sy = nextSrcY
        check(sy < src.height) { "Read past the end of the image" }
        val sh = min(stripH, src.height - sy)
        var sx = 0
        while (sx < src.width) {
            checkCancel()
            val tw = min(cfg.tile, src.width - sx)
            processTile(sx, sy, tw, sh)
            onTileDone(tw.toLong() * sh)
            sx += tw
        }
        stripY0 = sy * s
        stripRows = sh * s
        nextSrcY += sh
    }

    private fun processTile(sx: Int, sy: Int, tw: Int, th: Int) {
        val pad = cfg.pad
        val x0 = max(0, sx - pad)
        val y0 = max(0, sy - pad)
        val x1 = min(src.width, sx + tw + pad)
        val y1 = min(src.height, sy + th + pad)
        val pw = x1 - x0
        val ph = y1 - y0
        val n = pw * ph
        val input = FloatArray(3 * n)
        val alpha = if (hasAlpha) FloatArray(n) else null
        for (y in 0 until ph) {
            val row = (y0 + y) * src.width + x0
            for (x in 0 until pw) {
                val p = src.argb[row + x]
                val i = y * pw + x
                input[i] = ((p shr 16) and 0xFF) / 255f
                input[n + i] = ((p shr 8) and 0xFF) / 255f
                input[2 * n + i] = (p and 0xFF) / 255f
                if (alpha != null) alpha[i] = (p ushr 24) / 255f
            }
        }
        val ai = model.run(input, ph, pw)
        val ow = pw * s
        val oh = ph * s
        val on = ow * oh
        check(ai.size == 3 * on) { "Model returned ${ai.size} values, expected ${3 * on}" }

        val planes = Array(3) { c -> ai.copyOfRange(c * on, (c + 1) * on) }
        if (settings.detail < 0.999f && s == 4) {
            val d = settings.detail.coerceIn(0f, 1f)
            for (c in 0 until 3) {
                val bic = Filters.bicubic4x(input.copyOfRange(c * n, (c + 1) * n), pw, ph)
                val p = planes[c]
                for (i in 0 until on) p[i] = bic[i] + d * (p[i] - bic[i])
            }
        }
        if (settings.sharpen > 0.001f) {
            for (c in 0 until 3) Filters.unsharp(planes[c], ow, oh, settings.sharpen * 1.2f)
        }
        val alphaUp = alpha?.let { if (s == 4) Filters.bicubic4x(it, pw, ph) else upNearest(it, pw, ph) }

        val ix = (sx - x0) * s
        val iy = (sy - y0) * s
        val iw = tw * s
        val ih = th * s
        for (y in 0 until ih) {
            val srcRow = (iy + y) * ow + ix
            val dstRow = y * outW + sx * s // tiles start at the strip's first row
            for (x in 0 until iw) {
                val i = srcRow + x
                val r = q(planes[0][i])
                val g = q(planes[1][i])
                val b = q(planes[2][i])
                val a = if (alphaUp != null) q(alphaUp[i]) else 255
                strip[dstRow + x] = (a shl 24) or (r shl 16) or (g shl 8) or b
            }
        }
    }

    private fun upNearest(p: FloatArray, w: Int, h: Int): FloatArray {
        val ow = w * s
        val out = FloatArray(ow * h * s)
        for (y in 0 until h * s) for (x in 0 until ow) out[y * ow + x] = p[(y / s) * w + x / s]
        return out
    }

    private fun q(v: Float): Int = when {
        v <= 0f -> 0
        v >= 1f -> 255
        else -> (v * 255f + 0.5f).toInt()
    }
}

/**
 * The full job: optional AI 4× pass, then an exact Lanczos resample to the target size,
 * streamed into the sink (normally a PNG encoder plus a preview).
 */
class UpscalePipeline(
    private val source: PixelBuffer,
    private val targetW: Int,
    private val targetH: Int,
    private val settings: EnhanceSettings,
    private val useAi: Boolean,
    private val tileConfig: TileConfig = TileConfig(),
    private val clock: () -> Long = System::currentTimeMillis,
) {
    val hasAlpha: Boolean = source.hasTransparency()

    fun run(model: SrModel?, sink: RowSink, listener: ProgressListener, isCancelled: () -> Boolean) {
        val checkCancel = {
            if (isCancelled()) {
                model?.interrupt()
                throw UpscaleCancelled()
            }
        }
        listener.onStage(Stage.ANALYZING)
        if (hasAlpha) AlphaBleed.apply(source)
        checkCancel()

        val readRow: (IntArray) -> Unit
        val inW: Int
        val inH: Int
        if (useAi) {
            requireNotNull(model) { "AI step requested without a model" }
            val total = source.width.toLong() * source.height
            var done = 0L
            var firstTileAt = -1L
            var doneAtFirst = 0L
            listener.onStage(Stage.UPSCALING)
            listener.onAiProgress(0, total, null)
            val producer = AiRowProducer(source, model, settings, tileConfig, hasAlpha, { units ->
                done += units
                val now = clock()
                if (firstTileAt < 0) { firstTileAt = now; doneAtFirst = done }
                // ETA only once the rate is measured on work after the first (warm-up) tile.
                val measured = done - doneAtFirst
                val elapsed = now - firstTileAt
                val eta = if (measured > 0 && elapsed > 3000 && measured >= total / 20) {
                    (elapsed.toDouble() / measured * (total - done)).toLong()
                } else null
                listener.onAiProgress(done, total, eta)
                if (done >= total) listener.onStage(Stage.FINALIZING)
            }, checkCancel)
            readRow = producer::readRow
            inW = producer.outW
            inH = producer.outH
        } else {
            listener.onStage(Stage.FINALIZING)
            var y = 0
            readRow = { dst ->
                System.arraycopy(source.argb, y * source.width, dst, 0, source.width)
                y++
            }
            inW = source.width
            inH = source.height
        }
        StreamingResizer(inW, inH, targetW, targetH).run(readRow, sink, checkCancel)
        sink.finish()
    }
}
