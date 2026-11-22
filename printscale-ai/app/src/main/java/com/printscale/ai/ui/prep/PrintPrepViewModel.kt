package com.printscale.ai.ui.prep

import android.graphics.Bitmap
import android.net.Uri
import android.provider.OpenableColumns
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.printscale.ai.AppGraph
import com.printscale.ai.data.ImportedImage
import com.printscale.ai.data.Paths
import com.printscale.ai.export.ExportFormat
import com.printscale.ai.processing.BackgroundMode
import com.printscale.ai.processing.PreparedArtwork
import com.printscale.ai.processing.PrintPrepEngine
import com.printscale.engine.FileNaming
import com.printscale.engine.LengthUnit
import com.printscale.engine.Placement
import com.printscale.engine.PixelBuffer
import com.printscale.engine.PrintLayout
import com.printscale.engine.PrintMath
import com.printscale.engine.PrintMethod
import com.printscale.engine.QualityAnalyzer
import com.printscale.engine.QualityInput
import com.printscale.engine.QualityReport
import com.printscale.engine.UpscaleCancelled
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import kotlin.coroutines.coroutineContext

enum class PrepTab(val label: String) { ORIGINAL("Original"), PRINT("Print file"), GARMENT("Garment"), QUALITY("Quality") }

enum class CanvasBackground(val label: String) { CHECKER("Checks"), WHITE("White"), BLACK("Black"), GARMENT("Garment") }

/** Common transfer/print sizes, short side first. Orientation follows the artwork. */
val PREP_SIZES = listOf("8x10" to (8.0 to 10.0), "10x12" to (10.0 to 12.0), "12x16" to (12.0 to 16.0), "12x18" to (12.0 to 18.0))

data class PrepExport(val fileName: String, val bytes: Long, val widthPx: Int, val heightPx: Int, val widthIn: Double, val heightIn: Double,
                      val dpi: Int, val location: String, val uri: String, val cacheFile: File)

data class PrepUi(
    val loading: Boolean = true,
    val error: String? = null,
    val info: ImportedImage? = null,
    val method: PrintMethod = PrintMethod.DTF,
    val original: Bitmap? = null,
    val art: PreparedArtwork? = null,
    val working: String? = null,
    val bgMode: BackgroundMode = BackgroundMode.KEEP,
    val tolerance: Float = 0.12f,
    val enclosed: Boolean = false,
    val trim: Boolean = true,
    val solidEdges: Boolean = false,
    val unit: LengthUnit = LengthUnit.INCH,
    val dpi: Int = 300,
    val sizeId: String? = "12x16",
    val printW: Double = 12.0,
    val printH: Double = 16.0,
    val placement: Placement? = null,
    val lockRatio: Boolean = true,
    val tab: PrepTab = PrepTab.PRINT,
    val canvasBg: CanvasBackground = CanvasBackground.CHECKER,
    val garment: Garment = Garment.TEE,
    val garmentColor: Int = 0,
    val collarIn: Double = 3.0,
    val showPrintArea: Boolean = true,
    val exporting: Boolean = false,
    val exported: PrepExport? = null,
    val message: String? = null,
) {
    val canvasPx get() = PrintMath.pixels(printW, dpi) to PrintMath.pixels(printH, dpi)

    fun report(): QualityReport? {
        val a = art ?: return null
        val p = placement ?: return null
        return QualityAnalyzer.analyze(
            QualityInput(method, a.width, a.height, p, printW, printH, dpi, a.alpha, solidEdges, info?.provenance,
                if (method == PrintMethod.DTG) garment.maxPrintIn else null),
        )
    }
}

class PrintPrepViewModel(
    val graph: AppGraph,
    private val importId: String,
    method: PrintMethod,
    tab: PrepTab,
) : ViewModel() {
    private val engine = PrintPrepEngine(graph.app)
    private val _ui = MutableStateFlow(PrepUi(method = method, tab = tab))
    val ui: StateFlow<PrepUi> = _ui
    private var source: PixelBuffer? = null
    private var prepJob: Job? = null

    init {
        viewModelScope.launch {
            val info = graph.imports.get(importId)
            if (info == null) {
                _ui.update { it.copy(loading = false, error = "This image is no longer available. Import it again.") }
                return@launch
            }
            try {
                val src = withContext(Dispatchers.Default) { engine.loadSource(info, graph.imports.original(importId)) }
                source = src
                val original = withContext(Dispatchers.Default) { engine.previewBitmap(src) }
                // Landscape artwork gets a landscape canvas; portrait (the usual front print) stays upright.
                val landscape = info.workW > info.workH * 1.15
                _ui.update {
                    it.copy(loading = false, info = info, original = original, bgMode = BackgroundMode.KEEP,
                        printW = if (landscape) 16.0 else 12.0, printH = if (landscape) 12.0 else 16.0)
                }
                rebuild()
            } catch (e: OutOfMemoryError) {
                _ui.update { it.copy(loading = false, error = "This image is too large to prepare on this phone.") }
            } catch (e: Exception) {
                _ui.update { it.copy(loading = false, error = "The image could not be opened (${e.message}).") }
            }
        }
    }

    /** Re-runs background removal and trimming off the main thread; newer settings cancel older runs. */
    private fun rebuild(refit: Boolean = true) {
        val src = source ?: return
        val s = _ui.value
        prepJob?.cancel()
        _ui.update { it.copy(working = when (s.bgMode) { BackgroundMode.AI -> "Cutting out the subject"; BackgroundMode.PLAIN -> "Removing the background"; else -> "Preparing artwork" }) }
        prepJob = viewModelScope.launch {
            try {
                val ctx = coroutineContext
                val art = withContext(Dispatchers.Default) {
                    engine.prepare(importId, src, s.bgMode, s.tolerance, s.enclosed, s.trim) {
                        ctx.ensureActive()
                    }
                }
                _ui.update { u ->
                    val placement = if (refit || u.placement == null) fitPlacement(u, art.width, art.height) else u.placement
                    u.copy(art = art, working = null, placement = placement)
                }
            } catch (e: kotlinx.coroutines.CancellationException) {
                throw e
            } catch (e: LinkageError) {
                _ui.update { it.copy(working = null, bgMode = BackgroundMode.KEEP, message = "AI cutout is not available on this device.") }
            } catch (e: OutOfMemoryError) {
                _ui.update { it.copy(working = null, message = "Not enough memory for this step. Try the plain-colour method.") }
            } catch (e: Exception) {
                _ui.update { it.copy(working = null, message = "Background step failed: ${e.message}") }
            }
        }
    }

    private fun fitPlacement(u: PrepUi, w: Int, h: Int) =
        PrintLayout.fit(u.printW, u.printH, w, h, alignTop = u.method == PrintMethod.DTG)

    // ---------------------------------------------------------------- settings
    fun setMethod(m: PrintMethod) = _ui.update { u -> u.copy(method = m, placement = u.art?.let { fitPlacement(u.copy(method = m), it.width, it.height) }) }
    fun setTab(t: PrepTab) = _ui.update { it.copy(tab = t) }
    fun setBackground(m: BackgroundMode) { if (_ui.value.bgMode != m) { _ui.update { it.copy(bgMode = m) }; rebuild() } }
    fun setTolerance(t: Float) = _ui.update { it.copy(tolerance = t) }
    fun applyTolerance() = rebuild()
    fun setEnclosed(v: Boolean) { _ui.update { it.copy(enclosed = v) }; rebuild() }
    fun setTrim(v: Boolean) { _ui.update { it.copy(trim = v) }; rebuild() }
    fun setSolidEdges(v: Boolean) = _ui.update { it.copy(solidEdges = v) }
    fun setUnit(u: LengthUnit) = _ui.update { it.copy(unit = u) }
    fun setDpi(d: Int) = _ui.update { it.copy(dpi = d) }

    fun setSize(id: String) {
        val (a, b) = PREP_SIZES.first { it.first == id }.second
        _ui.update { u ->
            val landscape = u.printW > u.printH
            val n = u.copy(sizeId = id, printW = if (landscape) b else a, printH = if (landscape) a else b)
            n.copy(placement = n.art?.let { fitPlacement(n, it.width, it.height) })
        }
    }

    /** Custom size in the current unit. */
    fun setCustomSize(w: Double, h: Double) = _ui.update { u ->
        val n = u.copy(sizeId = null, printW = u.unit.toInches(w), printH = u.unit.toInches(h))
        n.copy(placement = n.art?.let { fitPlacement(n, it.width, it.height) })
    }

    fun rotateCanvas() = _ui.update { u ->
        val n = u.copy(printW = u.printH, printH = u.printW)
        n.copy(placement = n.art?.let { fitPlacement(n, it.width, it.height) })
    }

    // ---------------------------------------------------------------- placement
    fun setPlacement(p: Placement) = _ui.update { it.copy(placement = p) }
    fun centerH() = _ui.update { u -> u.copy(placement = u.placement?.let { PrintLayout.centerHorizontally(it, u.printW) }) }
    fun centerV() = _ui.update { u -> u.copy(placement = u.placement?.let { PrintLayout.centerVertically(it, u.printH) }) }
    fun fit() = _ui.update { u -> u.copy(placement = u.art?.let { PrintLayout.fit(u.printW, u.printH, it.width, it.height) }) }
    fun reset() = _ui.update { u -> u.copy(lockRatio = true, placement = u.art?.let { fitPlacement(u, it.width, it.height) }) }
    fun setLockRatio(v: Boolean) = _ui.update { u ->
        // Re-locking restores the artwork's own proportions at the current width.
        val p = u.placement
        val a = u.art
        if (v && p != null && a != null) u.copy(lockRatio = true, placement = PrintLayout.resize(p, p.wIn, p.wIn * a.height / a.width))
        else u.copy(lockRatio = v)
    }

    /** Artwork size typed in the current unit; the other side follows when proportions are locked. */
    fun setArtworkSize(w: Double?, h: Double?) = _ui.update { u ->
        val p = u.placement ?: return@update u
        val a = u.art ?: return@update u
        val ratio = a.width.toDouble() / a.height
        val wIn = w?.let { u.unit.toInches(it) }
        val hIn = h?.let { u.unit.toInches(it) }
        val (nw, nh) = when {
            u.lockRatio && wIn != null -> wIn to wIn / ratio
            u.lockRatio && hIn != null -> hIn * ratio to hIn
            else -> (wIn ?: p.wIn) to (hIn ?: p.hIn)
        }
        u.copy(placement = PrintLayout.resize(p, nw, nh))
    }

    // ---------------------------------------------------------------- preview
    fun setCanvasBg(b: CanvasBackground) = _ui.update { it.copy(canvasBg = b) }
    fun setGarment(g: Garment) = _ui.update { it.copy(garment = g) }
    fun setGarmentColor(i: Int) = _ui.update { it.copy(garmentColor = i) }
    fun setCollar(v: Double) = _ui.update { it.copy(collarIn = v) }
    fun setShowPrintArea(v: Boolean) = _ui.update { it.copy(showPrintArea = v) }

    // ---------------------------------------------------------------- export
    fun suggestedName(): String {
        val u = _ui.value
        val base = FileNaming.sanitize(u.info?.displayName).ifEmpty { "Artwork" }
        val size = "${PrintMath.formatInches(u.printW)}x${PrintMath.formatInches(u.printH)}in"
        return "${base}_${u.method.title}_${size}_${u.dpi}DPI"
    }

    fun export(fileName: String, compressionLevel: Int, target: Uri?) {
        val u = _ui.value
        val art = u.art ?: return
        val p = u.placement ?: return
        if (u.exporting) return
        _ui.update { it.copy(exporting = true) }
        viewModelScope.launch {
            try {
                val name = FileNaming.finalize(fileName, "png")
                val px = PrintLayout.toPixels(u.printW, u.printH, p, u.dpi)
                val dir = Paths(graph.app).exports.apply { listFiles()?.forEach { it.delete() } }
                val out = File(dir, name)
                val ctx = coroutineContext
                withContext(Dispatchers.Default) {
                    engine.export(art, px, u.dpi, u.solidEdges, compressionLevel, out) { if (!ctx.isActive) throw UpscaleCancelled() }
                }
                val (uri, location) = if (target == null) {
                    graph.exporter.saveToGallery(out, ExportFormat.PNG) to "Gallery · Pictures/PrintScale"
                } else {
                    graph.exporter.saveToUri(out, target)
                    target to "Files · ${displayName(target) ?: name}"
                }
                _ui.update {
                    it.copy(exporting = false, exported = PrepExport(name, out.length(), px.canvasW, px.canvasH, u.printW, u.printH, u.dpi, location, uri.toString(), out))
                }
            } catch (e: OutOfMemoryError) {
                _ui.update { it.copy(exporting = false, message = "Not enough memory to write this print file. Try a lower DPI.") }
            } catch (e: kotlinx.coroutines.CancellationException) {
                throw e
            } catch (e: Exception) {
                _ui.update { it.copy(exporting = false, message = e.message ?: "Export failed.") }
            }
        }
    }

    private val kotlin.coroutines.CoroutineContext.isActive get() = this[Job]?.isActive != false

    private suspend fun displayName(uri: Uri): String? = withContext(Dispatchers.IO) {
        runCatching {
            graph.app.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { c ->
                if (c.moveToFirst()) c.getString(0) else null
            }
        }.getOrNull()
    }

    fun clearExported() = _ui.update { it.copy(exported = null) }
    fun clearMessage() = _ui.update { it.copy(message = null) }
}
