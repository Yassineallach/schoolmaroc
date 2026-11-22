package com.printscale.engine

import kotlin.math.PI
import kotlin.math.abs
import kotlin.math.ceil
import kotlin.math.floor
import kotlin.math.max
import kotlin.math.sin

/** Plane operations used inside one tile. Planes are row-major float arrays. */
object Filters {

    private fun cubic(x: Double): Double {
        val a = -0.5
        val t = abs(x)
        return when {
            t <= 1 -> (a + 2) * t * t * t - (a + 3) * t * t + 1
            t < 2 -> a * t * t * t - 5 * a * t * t + 8 * a * t - 4 * a
            else -> 0.0
        }
    }

    // For an exact 4x upscale the sample phases repeat every 4 output pixels.
    // Output X maps to source X/4 - 0.375: offsets (floor) and fractions below.
    private val PHASE_BASE = intArrayOf(-1, -1, 0, 0)
    private val PHASE_W: Array<FloatArray> = Array(4) { m ->
        val f = doubleArrayOf(0.625, 0.875, 0.125, 0.375)[m]
        floatArrayOf(cubic(1 + f).toFloat(), cubic(f).toFloat(), cubic(1 - f).toFloat(), cubic(2 - f).toFloat())
    }

    /** Catmull-Rom 4x upscale of a w×h plane into a (4w)×(4h) plane. */
    fun bicubic4x(src: FloatArray, w: Int, h: Int, dst: FloatArray = FloatArray(16 * w * h)): FloatArray {
        val ow = 4 * w
        val tmp = FloatArray(ow * h)
        for (y in 0 until h) {
            val row = y * w
            for (X in 0 until ow) {
                val m = X and 3
                val base = (X shr 2) + PHASE_BASE[m] - 1
                val wt = PHASE_W[m]
                var s = 0f
                for (k in 0 until 4) {
                    val xi = (base + k).coerceIn(0, w - 1)
                    s += wt[k] * src[row + xi]
                }
                tmp[y * ow + X] = s
            }
        }
        for (Y in 0 until 4 * h) {
            val m = Y and 3
            val base = (Y shr 2) + PHASE_BASE[m] - 1
            val wt = PHASE_W[m]
            val r0 = (base).coerceIn(0, h - 1) * ow
            val r1 = (base + 1).coerceIn(0, h - 1) * ow
            val r2 = (base + 2).coerceIn(0, h - 1) * ow
            val r3 = (base + 3).coerceIn(0, h - 1) * ow
            val o = Y * ow
            for (X in 0 until ow) {
                dst[o + X] = wt[0] * tmp[r0 + X] + wt[1] * tmp[r1 + X] + wt[2] * tmp[r2 + X] + wt[3] * tmp[r3 + X]
            }
        }
        return dst
    }

    /** Unsharp mask with a 5-tap binomial blur (radius about 1 px at output scale). In place. */
    fun unsharp(plane: FloatArray, w: Int, h: Int, amount: Float) {
        if (amount <= 0f) return
        val k = floatArrayOf(1f / 16, 4f / 16, 6f / 16, 4f / 16, 1f / 16)
        val tmp = FloatArray(w * h)
        for (y in 0 until h) {
            val r = y * w
            for (x in 0 until w) {
                var s = 0f
                for (i in -2..2) s += k[i + 2] * plane[r + (x + i).coerceIn(0, w - 1)]
                tmp[r + x] = s
            }
        }
        val blur = FloatArray(w * h)
        for (y in 0 until h) {
            for (x in 0 until w) {
                var s = 0f
                for (i in -2..2) s += k[i + 2] * tmp[(y + i).coerceIn(0, h - 1) * w + x]
                blur[y * w + x] = s
            }
        }
        for (i in plane.indices) plane[i] = plane[i] + amount * (plane[i] - blur[i])
    }
}

/** Separable Lanczos-3 weights with edge taps folded into the image. */
class LanczosWeights(inSize: Int, outSize: Int) {
    val lo = IntArray(outSize)
    val count = IntArray(outSize)
    val offset = IntArray(outSize)
    val weights: FloatArray
    val maxTaps: Int

    init {
        val scale = inSize.toDouble() / outSize
        val fs = max(1.0, scale)
        val support = 3.0 * fs
        val all = ArrayList<Float>(outSize * 8)
        var mt = 1
        for (o in 0 until outSize) {
            val center = (o + 0.5) * scale - 0.5
            val left = ceil(center - support).toInt()
            val right = floor(center + support).toInt()
            val l = left.coerceIn(0, inSize - 1)
            val r = right.coerceIn(0, inSize - 1)
            val tmp = DoubleArray(r - l + 1)
            for (i in left..right) {
                tmp[i.coerceIn(0, inSize - 1) - l] += lanczos3((i - center) / fs)
            }
            var sum = 0.0
            for (v in tmp) sum += v
            if (sum == 0.0) { tmp.fill(0.0); tmp[(center.toInt() - l).coerceIn(0, tmp.size - 1)] = 1.0; sum = 1.0 }
            lo[o] = l
            count[o] = tmp.size
            offset[o] = all.size
            for (v in tmp) all.add((v / sum).toFloat())
            mt = max(mt, tmp.size)
        }
        weights = all.toFloatArray()
        maxTaps = mt
    }

    private fun lanczos3(x: Double): Double {
        if (x == 0.0) return 1.0
        if (x <= -3.0 || x >= 3.0) return 0.0
        val px = PI * x
        return 3.0 * sin(px) * sin(px / 3.0) / (px * px)
    }
}

/**
 * Resizes a stream of rows to an exact output size without holding either image in memory.
 * Only a window of horizontally resampled rows (as tall as the vertical filter) is kept.
 * Works in premultiplied alpha so transparent edges do not darken.
 */
class StreamingResizer(
    private val inW: Int,
    private val inH: Int,
    private val outW: Int,
    private val outH: Int,
) {
    val identity = inW == outW && inH == outH

    fun run(readRow: (IntArray) -> Unit, sink: RowSink, checkCancel: () -> Unit) {
        val inRow = IntArray(inW)
        if (identity) {
            for (y in 0 until outH) {
                if (y and 15 == 0) checkCancel()
                readRow(inRow)
                sink.writeRow(y, inRow)
            }
            return
        }
        val hw = LanczosWeights(inW, outW)
        val vw = LanczosWeights(inH, outH)
        val cap = vw.maxTaps + 1
        val ring = Array(cap) { FloatArray(outW * 4) }
        val inF = FloatArray(inW * 4)
        val out = IntArray(outW)
        val acc = FloatArray(outW * 4)
        var loaded = 0
        for (y in 0 until outH) {
            if (y and 15 == 0) checkCancel()
            val lo = vw.lo[y]
            val n = vw.count[y]
            val hi = lo + n - 1
            while (loaded <= hi) {
                readRow(inRow)
                toPremulFloat(inRow, inF)
                horizontal(inF, ring[loaded % cap], hw)
                loaded++
            }
            acc.fill(0f)
            val off = vw.offset[y]
            for (k in 0 until n) {
                val wk = vw.weights[off + k]
                val row = ring[(lo + k) % cap]
                for (i in acc.indices) acc[i] += wk * row[i]
            }
            for (x in 0 until outW) {
                val i = x * 4
                val a = acc[i].coerceIn(0f, 1f)
                out[x] = if (a < 0.5f / 255f) 0 else {
                    val inv = 1f / a
                    val r = (acc[i + 1] * inv).coerceIn(0f, 1f)
                    val g = (acc[i + 2] * inv).coerceIn(0f, 1f)
                    val b = (acc[i + 3] * inv).coerceIn(0f, 1f)
                    (q(a) shl 24) or (q(r) shl 16) or (q(g) shl 8) or q(b)
                }
            }
            sink.writeRow(y, out)
        }
    }

    private fun q(v: Float): Int = (v * 255f + 0.5f).toInt()

    private fun toPremulFloat(src: IntArray, dst: FloatArray) {
        for (x in src.indices) {
            val p = src[x]
            val a = (p ushr 24) / 255f
            val i = x * 4
            dst[i] = a
            dst[i + 1] = ((p shr 16) and 0xFF) / 255f * a
            dst[i + 2] = ((p shr 8) and 0xFF) / 255f * a
            dst[i + 3] = (p and 0xFF) / 255f * a
        }
    }

    private fun horizontal(src: FloatArray, dst: FloatArray, w: LanczosWeights) {
        for (x in 0 until outW) {
            val lo = w.lo[x]
            val n = w.count[x]
            val off = w.offset[x]
            var a = 0f; var r = 0f; var g = 0f; var b = 0f
            for (k in 0 until n) {
                val wk = w.weights[off + k]
                val i = (lo + k) * 4
                a += wk * src[i]; r += wk * src[i + 1]; g += wk * src[i + 2]; b += wk * src[i + 3]
            }
            val o = x * 4
            dst[o] = a; dst[o + 1] = r; dst[o + 2] = g; dst[o + 3] = b
        }
    }
}
