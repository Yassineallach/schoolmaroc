package com.printscale.engine

import java.io.DataInputStream
import java.io.EOFException
import java.io.IOException
import java.io.InputStream
import java.util.zip.InflaterInputStream
import kotlin.math.abs

/**
 * Reads an 8-bit, non-interlaced PNG one row at a time, so the 4× result from the cloud server
 * can be resized and re-encoded without ever holding the whole image in memory.
 */
class PngStreamReader(input: InputStream) : AutoCloseable {
    private val din = DataInputStream(input.buffered(1 shl 16))
    val width: Int
    val height: Int
    val hasAlpha: Boolean
    private val channels: Int
    private val rowLen: Int
    private var prev: ByteArray
    private var cur: ByteArray
    private val pixels: DataInputStream
    private var rowsRead = 0
    private var idatRemaining = 0 // declared before init, which sets it

    init {
        val sig = ByteArray(8)
        din.readFully(sig)
        if (sig[0] != 0x89.toByte() || String(sig, 1, 3, Charsets.ISO_8859_1) != "PNG") throw IOException("Not a PNG file")
        var w = 0; var h = 0; var ct = -1
        while (true) {
            val len = din.readInt()
            val type = ByteArray(4).also { din.readFully(it) }.toString(Charsets.ISO_8859_1)
            if (type == "IHDR") {
                w = din.readInt(); h = din.readInt()
                val depth = din.readUnsignedByte(); ct = din.readUnsignedByte()
                din.readUnsignedByte(); din.readUnsignedByte()
                val interlace = din.readUnsignedByte()
                din.skipNBytesCompat(4L) // crc
                if (depth != 8 || interlace != 0 || ct !in setOf(0, 2, 4, 6)) {
                    throw IOException("Unsupported PNG (bit depth $depth, colour type $ct, interlace $interlace)")
                }
            } else if (type == "IDAT") {
                if (w <= 0) throw IOException("PNG has no header")
                idatRemaining = len
                break
            } else {
                din.skipNBytesCompat(len + 4L)
            }
        }
        width = w; height = h
        channels = when (ct) { 0 -> 1; 4 -> 2; 2 -> 3; else -> 4 }
        hasAlpha = ct == 4 || ct == 6
        rowLen = width * channels
        prev = ByteArray(rowLen)
        cur = ByteArray(rowLen)
        pixels = DataInputStream(InflaterInputStream(IdatStream(), java.util.zip.Inflater(), 1 shl 16))
    }

    /** Concatenated IDAT payloads. */
    private inner class IdatStream : InputStream() {
        private var done = false
        private fun advance(): Boolean {
            while (idatRemaining == 0) {
                if (done) return false
                din.skipNBytesCompat(4L) // crc of the finished chunk
                val len = din.readInt()
                val type = ByteArray(4).also { din.readFully(it) }.toString(Charsets.ISO_8859_1)
                if (type != "IDAT") { done = true; return false }
                idatRemaining = len
            }
            return true
        }

        override fun read(): Int {
            if (!advance()) return -1
            idatRemaining--
            return din.read()
        }

        override fun read(b: ByteArray, off: Int, len: Int): Int {
            if (len == 0) return 0
            if (!advance()) return -1
            val n = din.read(b, off, minOf(len, idatRemaining))
            if (n < 0) throw EOFException("PNG ended inside image data")
            idatRemaining -= n
            return n
        }
    }

    /** Next row as unpremultiplied 0xAARRGGBB. */
    fun readRow(dst: IntArray) {
        if (rowsRead >= height) throw IOException("Read past the last row")
        val filter = pixels.readUnsignedByte()
        pixels.readFully(cur)
        unfilter(filter)
        var j = 0
        for (x in 0 until width) {
            dst[x] = when (channels) {
                3 -> { val r = u(j); val g = u(j + 1); val b = u(j + 2); j += 3; (0xFF shl 24) or (r shl 16) or (g shl 8) or b }
                4 -> { val r = u(j); val g = u(j + 1); val b = u(j + 2); val a = u(j + 3); j += 4; (a shl 24) or (r shl 16) or (g shl 8) or b }
                1 -> { val v = u(j); j += 1; (0xFF shl 24) or (v shl 16) or (v shl 8) or v }
                else -> { val v = u(j); val a = u(j + 1); j += 2; (a shl 24) or (v shl 16) or (v shl 8) or v }
            }
        }
        val t = prev; prev = cur; cur = t
        rowsRead++
    }

    private fun u(i: Int) = cur[i].toInt() and 0xFF

    private fun unfilter(type: Int) {
        val bpp = channels
        when (type) {
            0 -> {}
            1 -> for (i in bpp until rowLen) cur[i] = (cur[i] + cur[i - bpp]).toByte()
            2 -> for (i in 0 until rowLen) cur[i] = (cur[i] + prev[i]).toByte()
            3 -> for (i in 0 until rowLen) {
                val a = if (i >= bpp) cur[i - bpp].toInt() and 0xFF else 0
                cur[i] = (cur[i] + ((a + (prev[i].toInt() and 0xFF)) ushr 1)).toByte()
            }
            4 -> for (i in 0 until rowLen) {
                val a = if (i >= bpp) cur[i - bpp].toInt() and 0xFF else 0
                val b = prev[i].toInt() and 0xFF
                val c = if (i >= bpp) prev[i - bpp].toInt() and 0xFF else 0
                val p = a + b - c
                val pa = abs(p - a); val pb = abs(p - b); val pc = abs(p - c)
                cur[i] = (cur[i] + if (pa <= pb && pa <= pc) a else if (pb <= pc) b else c).toByte()
            }
            else -> throw IOException("Corrupt PNG (filter $type)")
        }
    }

    override fun close() = din.close()
}

private fun DataInputStream.skipNBytesCompat(n: Long) {
    var left = n
    while (left > 0) {
        val s = skip(left)
        if (s <= 0) { if (read() < 0) throw EOFException(); left-- } else left -= s
    }
}
