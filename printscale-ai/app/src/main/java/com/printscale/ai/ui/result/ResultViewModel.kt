package com.printscale.ai.ui.result

import android.content.Intent
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Rect
import android.net.Uri
import android.provider.OpenableColumns
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.printscale.ai.AppGraph
import com.printscale.ai.data.ExportRecord
import com.printscale.ai.data.HistoryItem
import com.printscale.ai.data.Paths
import com.printscale.ai.export.ExportFormat
import com.printscale.ai.export.ExportOptions
import com.printscale.ai.imaging.Imaging
import com.printscale.engine.FileNaming
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class Inspect(val before: ImageBitmap, val after: ImageBitmap, val rect: Rect)

data class ResultUi(
    val loading: Boolean = true,
    val error: String? = null,
    val item: HistoryItem? = null,
    val before: ImageBitmap? = null,
    val after: ImageBitmap? = null,
    val masterAvailable: Boolean = false,
    val inspectPicking: Boolean = false,
    val inspectLoading: Boolean = false,
    val inspect: Inspect? = null,
    val busy: String? = null,
    val message: String? = null,
)

class ResultViewModel(private val graph: AppGraph, private val jobId: String) : ViewModel() {
    private val paths = Paths(graph.app)
    private val _ui = MutableStateFlow(ResultUi())
    val ui: StateFlow<ResultUi> = _ui

    init {
        viewModelScope.launch {
            val item = graph.history.get(jobId)
            if (item == null) {
                _ui.value = ResultUi(loading = false, error = "This result is no longer available.")
                return@launch
            }
            val (before, after) = withContext(Dispatchers.IO) {
                runCatching { BitmapFactory.decodeFile(paths.jobBefore(jobId).path)?.asImageBitmap() }.getOrNull() to
                    runCatching { BitmapFactory.decodeFile(paths.jobPreview(jobId).path)?.asImageBitmap() }.getOrNull()
            }
            _ui.value = ResultUi(
                loading = false, item = item, before = before, after = after,
                masterAvailable = paths.jobMaster(jobId).exists(),
                error = if (before == null || after == null) "Preview images are missing for this result." else null,
            )
        }
    }

    fun suggestedName(format: ExportFormat): String {
        val it = _ui.value.item ?: return "Artwork.${format.ext}"
        return FileNaming.suggest(it.displayName, it.effectiveScale, it.finalW, it.finalH, it.dpi, format.ext)
    }

    fun unavailable(format: ExportFormat): String? = _ui.value.item?.let { graph.exporter.unavailableReason(it, format) }

    fun startInspect() = _ui.update { it.copy(inspectPicking = true, inspect = null) }
    fun endInspect() = _ui.update { it.copy(inspectPicking = false, inspect = null) }

    /** Decodes a 1:1 crop of the full-resolution file around a tapped point, plus the same area of the original. */
    fun inspectAt(nx: Float, ny: Float) {
        val item = _ui.value.item ?: return
        _ui.update { it.copy(inspectLoading = true) }
        viewModelScope.launch {
            val result = withContext(Dispatchers.IO) {
                val side = minOf(900, item.finalW, item.finalH)
                val cx = (nx * item.finalW).toInt()
                val cy = (ny * item.finalH).toInt()
                val l = (cx - side / 2).coerceIn(0, item.finalW - side)
                val t = (cy - side / 2).coerceIn(0, item.finalH - side)
                val rect = Rect(l, t, l + side, t + side)
                val after = Imaging.decodeRegion(paths.jobMaster(jobId), rect) ?: return@withContext null
                val sx = item.preparedW.toDouble() / item.finalW
                val sy = item.preparedH.toDouble() / item.finalH
                val srcRect = Rect(
                    (rect.left * sx).toInt(), (rect.top * sy).toInt(),
                    maxOf((rect.left * sx).toInt() + 1, (rect.right * sx).toInt()).coerceAtMost(item.preparedW),
                    maxOf((rect.top * sy).toInt() + 1, (rect.bottom * sy).toInt()).coerceAtMost(item.preparedH),
                )
                val src = Imaging.decodeRegion(paths.jobSource(jobId), srcRect) ?: return@withContext null
                // Plain bilinear enlargement of the original pixels, the honest "before".
                val before = Bitmap.createScaledBitmap(src, after.width, after.height, true)
                if (before != src) src.recycle()
                Inspect(before.asImageBitmap(), after.asImageBitmap(), rect)
            }
            _ui.update {
                if (result == null) it.copy(inspectLoading = false, message = "Could not read that area of the file.")
                else it.copy(inspectLoading = false, inspectPicking = false, inspect = result)
            }
        }
    }

    /** Renders the file, then saves it to the gallery folder or to a document the user picked. */
    fun export(options: ExportOptions, target: Uri?, onDone: () -> Unit) {
        val item = _ui.value.item ?: return
        _ui.update { it.copy(busy = "Exporting ${options.format.label}") }
        viewModelScope.launch {
            try {
                val file = graph.exporter.render(item, options)
                val (uri, location) = if (target == null) {
                    graph.exporter.saveToGallery(file, options.format) to "Gallery · Pictures/PrintScale"
                } else {
                    graph.exporter.saveToUri(file, target)
                    target to "Files · ${displayName(target) ?: file.name}"
                }
                graph.history.addExport(item.id, ExportRecord(file.name, options.format.label, file.length(), location, uri.toString(), System.currentTimeMillis()))
                _ui.update { it.copy(busy = null) }
                onDone()
            } catch (e: Exception) {
                _ui.update { it.copy(busy = null, message = e.message ?: "Export failed.") }
            }
        }
    }

    fun share(launch: (Intent) -> Unit) {
        val item = _ui.value.item ?: return
        _ui.update { it.copy(busy = "Preparing file") }
        viewModelScope.launch {
            try {
                val opts = ExportOptions(ExportFormat.PNG, fileName = suggestedName(ExportFormat.PNG))
                val file = graph.exporter.render(item, opts)
                _ui.update { it.copy(busy = null) }
                launch(graph.exporter.shareIntent(file, ExportFormat.PNG))
            } catch (e: Exception) {
                _ui.update { it.copy(busy = null, message = e.message ?: "Sharing failed.") }
            }
        }
    }

    private suspend fun displayName(uri: Uri): String? = withContext(Dispatchers.IO) {
        runCatching {
            graph.app.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { c ->
                if (c.moveToFirst()) c.getString(0) else null
            }
        }.getOrNull()
    }

    fun clearMessage() = _ui.update { it.copy(message = null) }

}
