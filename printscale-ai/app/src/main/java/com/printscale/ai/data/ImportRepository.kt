package com.printscale.ai.data

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.provider.OpenableColumns
import androidx.exifinterface.media.ExifInterface
import com.printscale.ai.imaging.Imaging
import com.printscale.engine.IccExtractor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.FileInputStream
import java.io.FileOutputStream
import java.util.UUID

class ImportException(message: String) : Exception(message)

class ImportRepository(private val context: Context) {
    private val paths = Paths(context)

    /**
     * Copies the picked image into app storage (picker grants are temporary) and records
     * what the editor needs to know about it.
     */
    suspend fun import(uri: Uri): ImportedImage = withContext(Dispatchers.IO) {
        val resolver = context.contentResolver
        var name = "Artwork"
        resolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { c ->
            if (c.moveToFirst()) c.getString(0)?.let { name = it }
        }
        val id = UUID.randomUUID().toString()
        val dir = paths.importDir(id).apply { mkdirs() }
        val original = paths.importOriginal(id)
        try {
            val stream = resolver.openInputStream(uri) ?: throw ImportException("The image could not be opened.")
            stream.use { input -> FileOutputStream(original).use { input.copyTo(it, 1 shl 16) } }
            val size = original.length()
            if (size == 0L) throw ImportException("The file is empty.")

            val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeFile(original.path, bounds)
            if (bounds.outWidth <= 0 || bounds.outHeight <= 0) {
                throw ImportException("This file is not an image Android can read.")
            }
            val mime = bounds.outMimeType ?: resolver.getType(uri) ?: "image/*"
            val orientation = runCatching {
                ExifInterface(original.path).getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL)
            }.getOrDefault(ExifInterface.ORIENTATION_NORMAL)
            val swaps = orientation in setOf(
                ExifInterface.ORIENTATION_ROTATE_90, ExifInterface.ORIENTATION_ROTATE_270,
                ExifInterface.ORIENTATION_TRANSPOSE, ExifInterface.ORIENTATION_TRANSVERSE,
            )
            val w = if (swaps) bounds.outHeight else bounds.outWidth
            val h = if (swaps) bounds.outWidth else bounds.outHeight
            val (workW, workH) = Imaging.workSize(w, h)

            val head = FileInputStream(original).use { it.readNBytesCompat(4 shl 20) }
            val icc = IccExtractor.extract(head)

            // Thumbnail doubles as a decode check and tells us if any pixel is actually transparent.
            val thumb = Imaging.decodePreview(original, 512)
            val hasAlpha = thumb.hasAlpha() && hasTransparentPixel(thumb)
            val colorSpaceName = thumb.colorSpace?.name ?: "sRGB"
            FileOutputStream(paths.importThumb(id)).use { thumb.compress(Bitmap.CompressFormat.JPEG, 88, it) }
            thumb.recycle()
            if (icc != null && !Imaging.isSrgb(bounds.outColorSpace)) paths.importIcc(id).writeBytes(icc)

            val info = ImportedImage(
                id = id, displayName = name, mime = mime, formatLabel = formatLabel(mime), fileSize = size,
                width = w, height = h, workW = workW, workH = workH,
                exifRotated = orientation != ExifInterface.ORIENTATION_NORMAL && orientation != ExifInterface.ORIENTATION_UNDEFINED,
                hasAlpha = hasAlpha, colorSpaceName = colorSpaceName, hasIcc = paths.importIcc(id).exists(),
            )
            paths.importMeta(id).writeText(info.toJson().toString())
            info
        } catch (e: ImportException) {
            dir.deleteRecursively(); throw e
        } catch (e: OutOfMemoryError) {
            dir.deleteRecursively(); throw ImportException("The image is too large to open on this device.")
        } catch (e: Exception) {
            dir.deleteRecursively(); throw ImportException("The image could not be read: ${e.message ?: e.javaClass.simpleName}")
        }
    }

    suspend fun get(id: String): ImportedImage? = withContext(Dispatchers.IO) {
        runCatching { ImportedImage.fromJson(JSONObject(paths.importMeta(id).readText())) }.getOrNull()
    }

    fun original(id: String) = paths.importOriginal(id)
    fun thumb(id: String) = paths.importThumb(id)
    fun icc(id: String): ByteArray? = paths.importIcc(id).takeIf { it.exists() }?.readBytes()

    private fun hasTransparentPixel(b: Bitmap): Boolean {
        val row = IntArray(b.width)
        for (y in 0 until b.height) {
            b.getPixels(row, 0, b.width, 0, y, b.width, 1)
            for (p in row) if ((p ushr 24) != 0xFF) return true
        }
        return false
    }

    private fun formatLabel(mime: String) = when (mime.lowercase()) {
        "image/png" -> "PNG"
        "image/jpeg", "image/jpg" -> "JPEG"
        "image/webp" -> "WebP"
        "image/heif", "image/heic" -> "HEIF"
        "image/avif" -> "AVIF"
        "image/gif" -> "GIF"
        "image/bmp", "image/x-ms-bmp" -> "BMP"
        else -> mime.substringAfter('/').uppercase()
    }
}

private fun java.io.InputStream.readNBytesCompat(max: Int): ByteArray {
    val out = java.io.ByteArrayOutputStream()
    val buf = ByteArray(1 shl 16)
    var total = 0
    while (total < max) {
        val n = read(buf, 0, minOf(buf.size, max - total))
        if (n < 0) break
        out.write(buf, 0, n); total += n
    }
    return out.toByteArray()
}
