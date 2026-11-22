package com.printscale.engine

import java.io.ByteArrayOutputStream
import java.io.OutputStream
import java.util.zip.CRC32
import java.util.zip.Deflater
import java.util.zip.DeflaterOutputStream
import kotlin.math.abs
import kotlin.math.roundToLong

/**
 * Writes a PNG row by row, so outputs far larger than any Bitmap Android could allocate
 * can be produced. Embeds print resolution (pHYs) and the colour profile (iCCP or sRGB).
 */
class PngStreamWriter(
    private val out: OutputStream,
    private val width: Int,
    private val height: Int,
    private val hasAlpha: Boolean,
    dpi: Int?,
    icc: ByteArray?,
    compressionLevel: Int = 5,
) : RowSink {
    private val bpp = if (hasAlpha) 4 else 3
    private val rowLen = width * bpp
    private var prev = ByteArray(rowLen)
    private var cur = ByteArray(rowLen)
    private val candidates = Array(5) { ByteArray(rowLen) }
    private val idat = IdatStream(out)
    private val deflater = Deflater(compressionLevel)
    private val zout = DeflaterOutputStream(idat, deflater, 1 shl 16)
    private var rowsWritten = 0

    init {
        out.write(byteArrayOf(0x89.toByte(), 'P'.code.toByte(), 'N'.code.toByte(), 'G'.code.toByte(), 13, 10, 26, 10))
        val ihdr = ByteArrayOutputStream()
        ihdr.int32(width); ihdr.int32(height)
        ihdr.write(8) // bit depth
        ihdr.write(if (hasAlpha) 6 else 2) // RGBA or RGB
        ihdr.write(0); ihdr.write(0); ihdr.write(0)
        chunk(out, "IHDR", ihdr.toByteArray())
        if (icc != null) {
            val b = ByteArrayOutputStream()
            b.write("ICC profile".toByteArray(Charsets.ISO_8859_1)); b.write(0); b.write(0)
            val d = Deflater(9)
            DeflaterOutputStream(b, d).use { it.write(icc) }
            d.end()
            chunk(out, "iCCP", b.toByteArray())
        } else {
            chunk(out, "sRGB", byteArrayOf(0))
        }
        if (dpi != null && dpi > 0) {
            val ppm = (dpi / 0.0254).roundToLong().toInt()
            val b = ByteArrayOutputStream()
            b.int32(ppm); b.int32(ppm); b.write(1)
            chunk(out, "pHYs", b.toByteArray())
        }
    }

    override fun writeRow(y: Int, argb: IntArray) {
        check(y == rowsWritten) { "Rows must arrive in order" }
        var j = 0
        for (x in 0 until width) {
            val p = argb[x]
            cur[j++] = (p shr 16).toByte()
            cur[j++] = (p shr 8).toByte()
            cur[j++] = p.toByte()
            if (hasAlpha) cur[j++] = (p ushr 24).toByte()
        }
        val type = chooseFilter()
        zout.write(type)
        zout.write(candidates[type], 0, rowLen)
        val t = prev; prev = cur; cur = t
        rowsWritten++
    }

    override fun finish() {
        check(rowsWritten == height) { "Wrote $rowsWritten of $height rows" }
        zout.finish()
        deflater.end()
        idat.flushChunk()
        chunk(out, "IEND", ByteArray(0))
        out.flush()
    }

    /** Standard adaptive heuristic: pick the filter with the smallest sum of absolute signed bytes. */
    private fun chooseFilter(): Int {
        val none = candidates[0]; val sub = candidates[1]; val up = candidates[2]
        val avg = candidates[3]; val paeth = candidates[4]
        val sums = LongArray(5)
        for (i in 0 until rowLen) {
            val x = cur[i].toInt() and 0xFF
            val a = if (i >= bpp) cur[i - bpp].toInt() and 0xFF else 0
            val b = prev[i].toInt() and 0xFF
            val c = if (i >= bpp) prev[i - bpp].toInt() and 0xFF else 0
            none[i] = x.toByte()
            sub[i] = (x - a).toByte()
            up[i] = (x - b).toByte()
            avg[i] = (x - ((a + b) ushr 1)).toByte()
            val p = a + b - c
            val pa = abs(p - a); val pb = abs(p - b); val pc = abs(p - c)
            val pr = if (pa <= pb && pa <= pc) a else if (pb <= pc) b else c
            paeth[i] = (x - pr).toByte()
            sums[0] += abs(none[i].toInt()); sums[1] += abs(sub[i].toInt()); sums[2] += abs(up[i].toInt())
            sums[3] += abs(avg[i].toInt()); sums[4] += abs(paeth[i].toInt())
        }
        var best = 0
        for (k in 1 until 5) if (sums[k] < sums[best]) best = k
        return best
    }

    private class IdatStream(private val out: OutputStream) : OutputStream() {
        private val buf = ByteArrayOutputStream(1 shl 18)
        override fun write(b: Int) { buf.write(b); if (buf.size() >= 1 shl 18) flushChunk() }
        override fun write(b: ByteArray, off: Int, len: Int) {
            buf.write(b, off, len)
            if (buf.size() >= 1 shl 18) flushChunk()
        }
        fun flushChunk() {
            if (buf.size() == 0) return
            chunk(out, "IDAT", buf.toByteArray())
            buf.reset()
        }
    }

    companion object {
        fun chunk(out: OutputStream, type: String, data: ByteArray) {
            val t = type.toByteArray(Charsets.ISO_8859_1)
            out.write(int32Bytes(data.size))
            out.write(t)
            out.write(data)
            val crc = CRC32()
            crc.update(t); crc.update(data)
            out.write(int32Bytes(crc.value.toInt()))
        }

        private fun int32Bytes(v: Int) = byteArrayOf((v ushr 24).toByte(), (v ushr 16).toByte(), (v ushr 8).toByte(), v.toByte())
        private fun ByteArrayOutputStream.int32(v: Int) = write(int32Bytes(v))
    }
}
