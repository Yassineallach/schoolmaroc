package com.printscale.ai.export

import android.app.ActivityManager
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import androidx.core.content.FileProvider
import com.printscale.ai.data.HistoryItem
import com.printscale.ai.data.Paths
import com.printscale.engine.JfifDpiOutputStream
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileOutputStream

enum class ExportFormat(val label: String, val ext: String, val mime: String) {
    PNG("PNG", "png", "image/png"),
    JPEG("JPEG", "jpg", "image/jpeg"),
    WEBP("WebP", "webp", "image/webp"),
}

data class ExportOptions(
    val format: ExportFormat = ExportFormat.PNG,
    val jpegQuality: Int = 95,
    val webpLossless: Boolean = true,
    val fileName: String,
)

class ExportException(message: String) : Exception(message)

class Exporter(private val context: Context) {
    private val paths = Paths(context)

    /** Why a format cannot be written for this job on this phone, or null if it can. */
    fun unavailableReason(item: HistoryItem, format: ExportFormat): String? {
        val px = item.finalW.toLong() * item.finalH
        return when (format) {
            ExportFormat.PNG -> null
            ExportFormat.WEBP -> when {
                item.finalW > 16383 || item.finalH > 16383 -> "WebP is limited to 16383 px per side."
                !fitsInMemory(px) -> "Too large to convert in this phone's free memory. PNG works at any size."
                else -> null
            }
            ExportFormat.JPEG -> if (!fitsInMemory(px)) "Too large to convert in this phone's free memory. PNG works at any size." else null
        }
    }

    /** JPEG and WebP encoders need the whole image as one bitmap (4 bytes per pixel, plus headroom). */
    private fun fitsInMemory(px: Long): Boolean {
        val am = context.getSystemService(ActivityManager::class.java)
        val mi = ActivityManager.MemoryInfo().also { am.getMemoryInfo(it) }
        return px * 4 * 2 < mi.availMem
    }

    /** Writes the export into the app cache. Saving and sharing copy from there. */
    suspend fun render(item: HistoryItem, opts: ExportOptions): File = withContext(Dispatchers.IO) {
        val master = paths.jobMaster(item.id)
        if (!master.exists()) throw ExportException("The processed file is no longer on this phone.")
        unavailableReason(item, opts.format)?.let { throw ExportException(it) }
        paths.exports.listFiles()?.forEach { it.delete() } // keep only the latest temporary export
        val out = File(paths.exports, opts.fileName)
        try {
            when (opts.format) {
                // The master already is a lossless PNG with DPI and colour profile embedded.
                ExportFormat.PNG -> master.copyTo(out, overwrite = true)
                ExportFormat.JPEG, ExportFormat.WEBP -> {
                    val decoded = BitmapFactory.decodeFile(master.path, BitmapFactory.Options().apply {
                        inPreferredConfig = Bitmap.Config.ARGB_8888
                    }) ?: throw ExportException("The processed file could not be read.")
                    val bmp = if (opts.format == ExportFormat.JPEG && item.hasAlpha) flattenOnWhite(decoded) else decoded
                    BufferedOutputStream(FileOutputStream(out), 1 shl 20).use { fos ->
                        if (opts.format == ExportFormat.JPEG) {
                            JfifDpiOutputStream(fos, item.dpi ?: 300).use { s ->
                                bmp.compress(Bitmap.CompressFormat.JPEG, opts.jpegQuality, s)
                            }
                        } else {
                            val fmt = if (opts.webpLossless) Bitmap.CompressFormat.WEBP_LOSSLESS else Bitmap.CompressFormat.WEBP_LOSSY
                            bmp.compress(fmt, if (opts.webpLossless) 100 else opts.jpegQuality, fos)
                        }
                    }
                    bmp.recycle()
                }
            }
        } catch (e: OutOfMemoryError) {
            out.delete()
            throw ExportException("Not enough memory to convert. Export as PNG instead.")
        }
        out
    }

    private fun flattenOnWhite(src: Bitmap): Bitmap {
        val out = Bitmap.createBitmap(src.width, src.height, Bitmap.Config.ARGB_8888, false, src.colorSpace!!)
        Canvas(out).apply { drawColor(Color.WHITE); drawBitmap(src, 0f, 0f, null) }
        src.recycle()
        return out
    }

    /** Pictures/PrintScale: shows up in the gallery and as its own folder. */
    suspend fun saveToGallery(file: File, format: ExportFormat): Uri = withContext(Dispatchers.IO) {
        val values = ContentValues().apply {
            put(MediaStore.Images.Media.DISPLAY_NAME, file.name)
            put(MediaStore.Images.Media.MIME_TYPE, format.mime)
            put(MediaStore.Images.Media.RELATIVE_PATH, Environment.DIRECTORY_PICTURES + "/PrintScale")
            put(MediaStore.Images.Media.IS_PENDING, 1)
        }
        val collection = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY)
        } else MediaStore.Images.Media.EXTERNAL_CONTENT_URI
        val resolver = context.contentResolver
        val uri = resolver.insert(collection, values) ?: throw ExportException("The gallery refused the file.")
        try {
            resolver.openOutputStream(uri)?.use { os -> file.inputStream().use { it.copyTo(os, 1 shl 20) } }
                ?: throw ExportException("Could not write to the gallery.")
            values.clear()
            values.put(MediaStore.Images.Media.IS_PENDING, 0)
            resolver.update(uri, values, null, null)
        } catch (e: Exception) {
            resolver.delete(uri, null, null)
            throw if (e is ExportException) e else ExportException("Saving failed: ${e.message}")
        }
        uri
    }

    /** A location the user picked in the system file chooser. */
    suspend fun saveToUri(file: File, target: Uri) = withContext(Dispatchers.IO) {
        context.contentResolver.openOutputStream(target, "w")?.use { os -> file.inputStream().use { it.copyTo(os, 1 shl 20) } }
            ?: throw ExportException("Could not write to the chosen location.")
    }

    fun contentUri(file: File): Uri = FileProvider.getUriForFile(context, context.packageName + ".files", file)

    fun shareIntent(file: File, format: ExportFormat): Intent {
        val send = Intent(Intent.ACTION_SEND).apply {
            type = format.mime
            putExtra(Intent.EXTRA_STREAM, contentUri(file))
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        return Intent.createChooser(send, "Share artwork")
    }

    fun viewIntent(uri: Uri, format: ExportFormat): Intent {
        val view = Intent(Intent.ACTION_VIEW).apply {
            setDataAndType(uri, format.mime)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        return Intent.createChooser(view, "Open with")
    }
}
