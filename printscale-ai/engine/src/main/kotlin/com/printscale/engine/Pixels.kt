package com.printscale.engine

/** Unpremultiplied 0xAARRGGBB pixels, row-major. */
class PixelBuffer(val width: Int, val height: Int, val argb: IntArray = IntArray(width * height)) {
    init {
        require(width > 0 && height > 0) { "Empty image" }
        require(argb.size == width * height) { "Pixel array size mismatch" }
    }

    fun hasTransparency(): Boolean {
        for (p in argb) if ((p ushr 24) != 0xFF) return true
        return false
    }
}

/** Receives output rows strictly in order, y = 0 until height. */
interface RowSink {
    fun writeRow(y: Int, argb: IntArray)
    fun finish() {}
}

class TeeSink(private vararg val sinks: RowSink) : RowSink {
    override fun writeRow(y: Int, argb: IntArray) = sinks.forEach { it.writeRow(y, argb) }
    override fun finish() = sinks.forEach { it.finish() }
}

/** Builds a small box-filtered preview while the full image streams past. */
class PreviewSink(private val width: Int, private val height: Int, maxSide: Int) : RowSink {
    val factor: Int = maxOf(1, (maxOf(width, height) + maxSide - 1) / maxSide)
    val previewW = (width + factor - 1) / factor
    val previewH = (height + factor - 1) / factor
    val result = PixelBuffer(previewW, previewH)
    private val acc = LongArray(previewW * 4)
    private val cnt = IntArray(previewW)
    private var rowsInBand = 0

    override fun writeRow(y: Int, argb: IntArray) {
        for (x in 0 until width) {
            val p = argb[x]
            val a = p ushr 24
            val px = x / factor
            val i = px * 4
            // premultiplied average keeps transparent edges clean
            acc[i] += a.toLong()
            acc[i + 1] += ((p shr 16) and 0xFF).toLong() * a
            acc[i + 2] += ((p shr 8) and 0xFF).toLong() * a
            acc[i + 3] += (p and 0xFF).toLong() * a
            cnt[px]++
        }
        rowsInBand++
        if (rowsInBand == factor || y == height - 1) flush(y / factor)
    }

    private fun flush(py: Int) {
        for (px in 0 until previewW) {
            val i = px * 4
            val n = cnt[px]
            val aSum = acc[i]
            val pixel = if (n == 0 || aSum == 0L) 0 else {
                val a = (aSum / n).toInt()
                val r = (acc[i + 1] / aSum).toInt()
                val g = (acc[i + 2] / aSum).toInt()
                val b = (acc[i + 3] / aSum).toInt()
                (a shl 24) or (r shl 16) or (g shl 8) or b
            }
            result.argb[py * previewW + px] = pixel
        }
        acc.fill(0)
        cnt.fill(0)
        rowsInBand = 0
    }
}

object AlphaBleed {
    /**
     * Copies the colour of the nearest visible pixel into fully transparent pixels.
     * Transparent pixels usually store black, and an RGB model would smear that black into
     * the edges of a cut-out. Alpha is left untouched.
     */
    fun apply(buf: PixelBuffer) {
        val w = buf.width
        val h = buf.height
        val px = buf.argb
        val n = w * h
        val done = BooleanArray(n)
        var any = false
        for (i in 0 until n) if ((px[i] ushr 24) != 0) { done[i] = true; any = true }
        if (!any) return
        val queue = IntArray(n)
        var head = 0
        var tail = 0
        for (i in 0 until n) {
            if (!done[i]) continue
            val x = i % w
            val y = i / w
            if ((x > 0 && !done[i - 1]) || (x < w - 1 && !done[i + 1]) ||
                (y > 0 && !done[i - w]) || (y < h - 1 && !done[i + w])
            ) queue[tail++] = i
        }
        while (head < tail) {
            val i = queue[head++]
            val rgb = px[i] and 0xFFFFFF
            val x = i % w
            val y = i / w
            if (x > 0 && !done[i - 1]) { done[i - 1] = true; px[i - 1] = rgb; queue[tail++] = i - 1 }
            if (x < w - 1 && !done[i + 1]) { done[i + 1] = true; px[i + 1] = rgb; queue[tail++] = i + 1 }
            if (y > 0 && !done[i - w]) { done[i - w] = true; px[i - w] = rgb; queue[tail++] = i - w }
            if (y < h - 1 && !done[i + w]) { done[i + w] = true; px[i + w] = rgb; queue[tail++] = i + w }
        }
    }
}
