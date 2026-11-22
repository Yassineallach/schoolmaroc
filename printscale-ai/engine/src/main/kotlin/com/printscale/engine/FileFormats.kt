package com.printscale.engine

import java.io.ByteArrayOutputStream
import java.io.FilterOutputStream
import java.io.OutputStream
import java.util.zip.Inflater

/** Pulls the embedded ICC colour profile out of PNG, JPEG or WebP bytes. */
object IccExtractor {
    fun extract(head: ByteArray): ByteArray? = runCatching {
        when {
            isPng(head) -> png(head)
            head.size > 3 && head[0] == 0xFF.toByte() && head[1] == 0xD8.toByte() -> jpeg(head)
            head.size > 12 && String(head, 0, 4, Charsets.ISO_8859_1) == "RIFF" &&
                String(head, 8, 4, Charsets.ISO_8859_1) == "WEBP" -> webp(head)
            else -> null
        }
    }.getOrNull()

    private fun isPng(b: ByteArray) = b.size > 8 && b[0] == 0x89.toByte() && b[1] == 'P'.code.toByte()

    private fun be32(b: ByteArray, o: Int) =
        ((b[o].toInt() and 0xFF) shl 24) or ((b[o + 1].toInt() and 0xFF) shl 16) or
            ((b[o + 2].toInt() and 0xFF) shl 8) or (b[o + 3].toInt() and 0xFF)

    private fun le32(b: ByteArray, o: Int) =
        (b[o].toInt() and 0xFF) or ((b[o + 1].toInt() and 0xFF) shl 8) or
            ((b[o + 2].toInt() and 0xFF) shl 16) or ((b[o + 3].toInt() and 0xFF) shl 24)

    private fun png(b: ByteArray): ByteArray? {
        var p = 8
        while (p + 8 <= b.size) {
            val len = be32(b, p)
            val type = String(b, p + 4, 4, Charsets.ISO_8859_1)
            val data = p + 8
            if (len < 0 || data + len > b.size) return null
            when (type) {
                "iCCP" -> {
                    var z = data
                    while (z < data + len && b[z] != 0.toByte()) z++
                    val start = z + 2 // null separator + compression method
                    val inf = Inflater()
                    inf.setInput(b, start, data + len - start)
                    val out = ByteArrayOutputStream()
                    val buf = ByteArray(8192)
                    while (!inf.finished()) {
                        val n = inf.inflate(buf)
                        if (n == 0 && (inf.needsInput() || inf.needsDictionary())) break
                        out.write(buf, 0, n)
                    }
                    inf.end()
                    return out.toByteArray().takeIf { it.isNotEmpty() }
                }
                "IDAT", "IEND" -> return null
            }
            p = data + len + 4
        }
        return null
    }

    private fun jpeg(b: ByteArray): ByteArray? {
        val parts = sortedMapOf<Int, ByteArray>()
        var p = 2
        while (p + 4 <= b.size) {
            if (b[p] != 0xFF.toByte()) return null
            val marker = b[p + 1].toInt() and 0xFF
            if (marker == 0xDA || marker == 0xD9) break
            val len = ((b[p + 2].toInt() and 0xFF) shl 8) or (b[p + 3].toInt() and 0xFF)
            val seg = p + 4
            if (marker == 0xE2 && len > 16 && seg + 14 <= b.size &&
                String(b, seg, 11, Charsets.ISO_8859_1) == "ICC_PROFILE"
            ) {
                val seq = b[seg + 12].toInt() and 0xFF
                val end = minOf(b.size, p + 2 + len)
                parts[seq] = b.copyOfRange(seg + 14, end)
            }
            p += 2 + len
        }
        if (parts.isEmpty()) return null
        val out = ByteArrayOutputStream()
        parts.values.forEach { out.write(it) }
        return out.toByteArray()
    }

    private fun webp(b: ByteArray): ByteArray? {
        var p = 12
        while (p + 8 <= b.size) {
            val type = String(b, p, 4, Charsets.ISO_8859_1)
            val len = le32(b, p + 4)
            if (len < 0 || p + 8 + len > b.size) return null
            if (type == "ICCP") return b.copyOfRange(p + 8, p + 8 + len)
            p += 8 + len + (len and 1)
        }
        return null
    }
}

/**
 * Android's JPEG encoder writes a JFIF header with no physical density. This stream rewrites
 * the density fields of that header so print software reads the intended DPI.
 */
class JfifDpiOutputStream(out: OutputStream, private val dpi: Int) : FilterOutputStream(out) {
    private val head = ByteArray(18)
    private var filled = 0
    private var passthrough = false

    override fun write(b: Int) {
        if (passthrough) { out.write(b); return }
        head[filled++] = b.toByte()
        if (filled == head.size) release()
    }

    override fun write(b: ByteArray, off: Int, len: Int) {
        var i = 0
        while (!passthrough && i < len) { write(b[off + i].toInt()); i++ }
        if (i < len) out.write(b, off + i, len - i)
    }

    private fun release() {
        val isJfif = head[0] == 0xFF.toByte() && head[1] == 0xD8.toByte() &&
            head[2] == 0xFF.toByte() && head[3] == 0xE0.toByte() &&
            String(head, 6, 5, Charsets.ISO_8859_1) == "JFIF\u0000"
        if (isJfif) {
            head[13] = 1 // dots per inch
            head[14] = (dpi shr 8).toByte(); head[15] = dpi.toByte()
            head[16] = (dpi shr 8).toByte(); head[17] = dpi.toByte()
        }
        out.write(head, 0, filled)
        passthrough = true
    }

    override fun flush() {
        if (!passthrough && filled > 0) release()
        super.flush()
    }

    override fun close() {
        flush()
        super.close()
    }
}

object FileNaming {
    /** e.g. Artwork_4x_7200x10800_300DPI.png */
    fun suggest(baseName: String?, effectiveScale: Double, w: Int, h: Int, dpi: Int?, ext: String): String {
        val base = sanitize(baseName).ifEmpty { "Artwork" }
        val factor = PrintMath.formatFactor(effectiveScale).replace("×", "x")
        val dpiPart = dpi?.let { "_${it}DPI" } ?: ""
        return "${base}_${factor}_${w}x${h}$dpiPart.$ext"
    }

    fun sanitize(name: String?): String {
        if (name == null) return ""
        val noExt = name.substringBeforeLast('.')
        return noExt.replace(Regex("[^A-Za-z0-9_-]+"), "_").trim('_').take(48)
    }

    /** Ensures a user-typed name is a valid file name with the right extension. */
    fun finalize(userName: String, ext: String): String {
        val cleaned = userName.trim().removeSuffix(".$ext").replace(Regex("[\\\\/:*?\"<>|]+"), "_").trim()
        return (cleaned.ifEmpty { "Artwork" }) + ".$ext"
    }
}
