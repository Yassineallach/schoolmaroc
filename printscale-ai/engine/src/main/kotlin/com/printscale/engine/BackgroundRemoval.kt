package com.printscale.engine

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.nio.FloatBuffer
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

/**
 * Removes a plain or near-plain background, the usual case for AI-generated t-shirt designs
 * ("on a white background"). Flood fill from the image border through pixels close to the
 * background colour; pixels at the boundary get partial alpha and have the background colour
 * un-mixed from them so no light fringe is left on dark garments.
 */
object PlainBackground {
    data class Result(val pixels: PixelBuffer, val background: Int, val removedFraction: Double)

    private const val EDGE_RADIUS = 2   // anti-aliasing is at most a couple of pixels wide
    private const val REF_RADIUS = 3    // where to look for solid artwork colour next to an edge

    /**
     * @param tolerance 0..1, how far from the background colour still counts as background.
     * @param enclosed also remove background-coloured areas not connected to the border (inside letters).
     */
    fun remove(src: PixelBuffer, tolerance: Float = 0.12f, enclosed: Boolean = false): Result {
        val w = src.width
        val h = src.height
        val n = w * h
        val bg = borderColor(src)
        val br = (bg shr 16) and 0xFF; val bgG = (bg shr 8) and 0xFF; val bb = bg and 0xFF
        val dist = FloatArray(n)
        for (i in 0 until n) {
            val p = src.argb[i]
            val dr = ((p shr 16) and 0xFF) - br
            val dg = ((p shr 8) and 0xFF) - bgG
            val db = (p and 0xFF) - bb
            dist[i] = sqrt((dr * dr + dg * dg + db * db).toFloat()) / 441.673f
        }
        // 1. background region
        val isBg = BooleanArray(n)
        if (enclosed) {
            for (i in 0 until n) isBg[i] = dist[i] <= tolerance || (src.argb[i] ushr 24) == 0
        } else {
            val queue = IntArray(n)
            var head = 0
            var tail = 0
            fun seed(i: Int) {
                if (!isBg[i] && (dist[i] <= tolerance || (src.argb[i] ushr 24) == 0)) { isBg[i] = true; queue[tail++] = i }
            }
            for (x in 0 until w) { seed(x); seed((h - 1) * w + x) }
            for (y in 0 until h) { seed(y * w); seed(y * w + w - 1) }
            while (head < tail) {
                val i = queue[head++]
                val x = i % w
                if (x > 0) seed(i - 1)
                if (x < w - 1) seed(i + 1)
                if (i >= w) seed(i - w)
                if (i < n - w) seed(i + w)
            }
        }
        // 2. edge band: artwork pixels within EDGE_RADIUS of removed background
        val edge = BooleanArray(n)
        for (i in 0 until n) {
            if (!isBg[i]) continue
            val x = i % w; val y = i / w
            for (dy in -EDGE_RADIUS..EDGE_RADIUS) for (dx in -EDGE_RADIUS..EDGE_RADIUS) {
                val xx = x + dx; val yy = y + dy
                if (xx in 0 until w && yy in 0 until h) {
                    val j = yy * w + xx
                    if (!isBg[j]) edge[j] = true
                }
            }
        }
        // 3. un-mix edge pixels: observed = a * artwork + (1 - a) * background
        val out = src.argb.copyOf()
        var removed = 0L
        for (i in 0 until n) {
            if (isBg[i]) { out[i] = 0; removed++; continue }
            if (!edge[i]) continue
            val x = i % w; val y = i / w
            var ref = dist[i]
            for (dy in -REF_RADIUS..REF_RADIUS) for (dx in -REF_RADIUS..REF_RADIUS) {
                val xx = x + dx; val yy = y + dy
                if (xx in 0 until w && yy in 0 until h) {
                    val j = yy * w + xx
                    if (!isBg[j] && !edge[j] && dist[j] > ref) ref = dist[j]
                }
            }
            val a = if (ref <= 1e-4f) 1f else (dist[i] / ref).coerceIn(0f, 1f)
            val p = out[i]
            if (a < 0.03f) { out[i] = 0; removed++; continue }
            fun un(c: Int, b: Int) = ((c - (1 - a) * b) / a).toInt().coerceIn(0, 255)
            val na = ((p ushr 24) * a).toInt().coerceIn(1, 255)
            out[i] = (na shl 24) or (un((p shr 16) and 0xFF, br) shl 16) or (un((p shr 8) and 0xFF, bgG) shl 8) or un(p and 0xFF, bb)
        }
        return Result(PixelBuffer(w, h, out), bg, removed / n.toDouble())
    }

    /** Most common colour along the border (5-bit buckets), averaged within its bucket. */
    fun borderColor(src: PixelBuffer): Int {
        val w = src.width
        val h = src.height
        val counts = HashMap<Int, IntArray>()
        fun add(p: Int) {
            if ((p ushr 24) < 128) return
            val key = (((p shr 19) and 31) shl 10) or (((p shr 11) and 31) shl 5) or ((p shr 3) and 31)
            val c = counts.getOrPut(key) { IntArray(4) }
            c[0]++; c[1] += (p shr 16) and 0xFF; c[2] += (p shr 8) and 0xFF; c[3] += p and 0xFF
        }
        for (x in 0 until w) { add(src.argb[x]); add(src.argb[(h - 1) * w + x]) }
        for (y in 0 until h) { add(src.argb[y * w]); add(src.argb[y * w + w - 1]) }
        val best = counts.values.maxByOrNull { it[0] } ?: return 0xFFFFFFFF.toInt()
        val n = best[0]
        return (0xFF shl 24) or ((best[1] / n) shl 16) or ((best[2] / n) shl 8) or (best[3] / n)
    }
}

/** A salient-object segmentation network: 320 × 320 RGB in, 320 × 320 mask out. */
interface MaskModel : AutoCloseable {
    val size: Int
    fun predict(chw: FloatArray): FloatArray
}

/** U²-Net-p (Apache-2.0, 4.5 MB) through ONNX Runtime. */
class OrtMaskModel(bytes: ByteArray, threads: Int) : MaskModel {
    private val env = OrtEnvironment.getEnvironment()
    private val session: OrtSession
    override val size = 320

    init {
        val opts = OrtSession.SessionOptions().apply {
            setOptimizationLevel(OrtSession.SessionOptions.OptLevel.ALL_OPT)
            setIntraOpNumThreads(threads.coerceAtLeast(1))
        }
        session = env.createSession(bytes, opts)
        opts.close()
    }

    override fun predict(chw: FloatArray): FloatArray {
        val name = session.inputNames.first()
        OnnxTensor.createTensor(env, FloatBuffer.wrap(chw), longArrayOf(1, 3, size.toLong(), size.toLong())).use { t ->
            session.run(mapOf(name to t)).use { r ->
                val fb = (r.get(0) as OnnxTensor).floatBuffer
                return FloatArray(fb.remaining()).also { fb.get(it) }
            }
        }
    }

    override fun close() = session.close()
}

/**
 * Cuts the main subject out with a segmentation model. The model sees a 320 px version; its mask
 * is scaled up and its edge sharpened. Good for subjects on busy backgrounds; edges are softer
 * than the plain-background method, so check them before printing.
 */
object AiCutout {
    private val MEAN = floatArrayOf(0.485f, 0.456f, 0.406f)
    private val STD = floatArrayOf(0.229f, 0.224f, 0.225f)

    fun apply(src: PixelBuffer, model: MaskModel): PixelBuffer {
        val s = model.size
        val input = FloatArray(3 * s * s)
        // area-average downsample to s x s
        val sx = src.width.toDouble() / s
        val sy = src.height.toDouble() / s
        for (y in 0 until s) {
            val y0 = (y * sy).toInt(); val y1 = max(y0 + 1, min(src.height, ((y + 1) * sy).toInt()))
            for (x in 0 until s) {
                val x0 = (x * sx).toInt(); val x1 = max(x0 + 1, min(src.width, ((x + 1) * sx).toInt()))
                var r = 0L; var g = 0L; var b = 0L; var c = 0
                for (yy in y0 until y1) for (xx in x0 until x1) {
                    val p = src.argb[yy * src.width + xx]
                    r += (p shr 16) and 0xFF; g += (p shr 8) and 0xFF; b += p and 0xFF; c++
                }
                val i = y * s + x
                input[i] = (r / c / 255f - MEAN[0]) / STD[0]
                input[s * s + i] = (g / c / 255f - MEAN[1]) / STD[1]
                input[2 * s * s + i] = (b / c / 255f - MEAN[2]) / STD[2]
            }
        }
        val m = model.predict(input)
        var lo = Float.MAX_VALUE; var hi = -Float.MAX_VALUE
        for (v in m) { if (v < lo) lo = v; if (v > hi) hi = v }
        val range = max(1e-6f, hi - lo)
        val out = src.argb.copyOf()
        for (y in 0 until src.height) {
            val fy = ((y + 0.5) / src.height * s - 0.5).coerceIn(0.0, s - 1.0)
            val y0 = fy.toInt(); val y1 = min(s - 1, y0 + 1); val ty = (fy - y0).toFloat()
            for (x in 0 until src.width) {
                val fx = ((x + 0.5) / src.width * s - 0.5).coerceIn(0.0, s - 1.0)
                val x0 = fx.toInt(); val x1 = min(s - 1, x0 + 1); val tx = (fx - x0).toFloat()
                val v = (m[y0 * s + x0] * (1 - tx) + m[y0 * s + x1] * tx) * (1 - ty) +
                    (m[y1 * s + x0] * (1 - tx) + m[y1 * s + x1] * tx) * ty
                val mv = (v - lo) / range
                // sharpen the upscaled mask edge: smoothstep between 0.3 and 0.7
                val t = ((mv - 0.3f) / 0.4f).coerceIn(0f, 1f)
                val a = t * t * (3 - 2 * t)
                val i = y * src.width + x
                val p = out[i]
                val na = ((p ushr 24) * a).toInt()
                out[i] = if (na == 0) 0 else (na shl 24) or (p and 0xFFFFFF)
            }
        }
        return PixelBuffer(src.width, src.height, out)
    }
}
