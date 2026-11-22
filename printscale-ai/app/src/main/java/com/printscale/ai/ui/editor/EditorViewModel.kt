package com.printscale.ai.ui.editor

import android.graphics.Bitmap
import android.os.StatFs
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.printscale.ai.AppGraph
import com.printscale.ai.data.ImportedImage
import com.printscale.ai.data.JobSpec
import com.printscale.ai.imaging.Imaging
import com.printscale.ai.imaging.orientedTo
import com.printscale.engine.CropGeometry
import com.printscale.engine.CropState
import com.printscale.engine.DeviceBudget
import com.printscale.engine.EnhanceSettings
import com.printscale.engine.FitMode
import com.printscale.engine.Planner
import com.printscale.engine.PrintMath
import com.printscale.engine.PrintSize
import com.printscale.engine.PrintTarget
import com.printscale.engine.UpscalePlan
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.math.abs

enum class OutputMode { PRINT, SCALE }

enum class Strength(val label: String, val detail: Float, val sharpen: Float, val denoise: Float) {
    LOW("Low", 0.6f, 0f, 0.3f),
    BALANCED("Balanced", 1f, 0.15f, 0.5f),
    HIGH("High", 1f, 0.35f, 0.8f),
}

enum class Background(val label: String) { TRANSPARENT("Transparent"), WHITE("White"), BLACK("Black"), EDGE("Edge colour") }

/** Ratio stored short:long; orientation is applied with the landscape flag. */
data class AspectChoice(val short: Double, val long: Double) {
    fun ratio(landscape: Boolean) = if (landscape) long / short else short / long
    fun label(landscape: Boolean): String {
        val a = PrintMath.formatInches(short)
        val b = PrintMath.formatInches(long)
        return if (short == long) "1:1" else if (landscape) "$b:$a" else "$a:$b"
    }
}

val ASPECTS = listOf(
    AspectChoice(1.0, 1.0), AspectChoice(2.0, 3.0), AspectChoice(3.0, 4.0), AspectChoice(4.0, 5.0),
    AspectChoice(5.0, 7.0), AspectChoice(11.0, 14.0), AspectChoice(9.0, 16.0),
)

data class EditorUi(
    val loading: Boolean = true,
    val error: String? = null,
    val info: ImportedImage? = null,
    val preview: Bitmap? = null,
    val edgeColor: Int = 0xFFFFFFFF.toInt(),
    val crop: CropState = CropState(),
    /** null = the artwork's own ratio. */
    val aspect: AspectChoice? = null,
    val landscape: Boolean = false,
    val fitMode: FitMode = FitMode.FILL,
    val background: Background = Background.WHITE,
    val outputMode: OutputMode = OutputMode.PRINT,
    val presetId: String? = null,
    val customPrint: PrintSize? = null,
    val dpi: Int = PrintMath.DEFAULT_DPI,
    val factor: Int = 4,
    val strength: Strength = Strength.BALANCED,
    val detail: Float = Strength.BALANCED.detail,
    val sharpen: Float = Strength.BALANCED.sharpen,
    val denoise: Float = Strength.BALANCED.denoise,
    val starting: Boolean = false,
    /** JobSpec.ENGINE_DEVICE or JobSpec.ENGINE_CLOUD. */
    val engine: String = JobSpec.ENGINE_DEVICE,
) {
    val cloud: Boolean get() = engine == JobSpec.ENGINE_CLOUD

    /** The print size in the current orientation, if the output is a print. */
    val printSize: PrintSize?
        get() {
            if (outputMode != OutputMode.PRINT) return null
            val base = customPrint ?: PrintMath.preset(presetId)?.oriented(false) ?: return null
            val portrait = if (base.widthIn > base.heightIn) base.swapped() else base
            return if (landscape) portrait.swapped() else portrait
        }

    /** Canvas ratio actually used for the crop. */
    val effectiveAspect: Double?
        get() = printSize?.aspect ?: aspect?.ratio(landscape)

    val backgroundArgb: Int?
        get() = when (background) {
            Background.TRANSPARENT -> null
            Background.WHITE -> 0xFFFFFFFF.toInt()
            Background.BLACK -> 0xFF000000.toInt()
            Background.EDGE -> edgeColor
        }

    fun geometry(): CropGeometry? = info?.let { CropGeometry(it.workW, it.workH, effectiveAspect, fitMode, crop) }

    val outputHasAlpha: Boolean
        get() = (info?.hasAlpha == true) || (fitMode == FitMode.FIT && background == Background.TRANSPARENT)
}

class EditorViewModel(
    val graph: AppGraph,
    private val importId: String,
    initialPreset: String?,
    initialFactor: Int?,
) : ViewModel() {
    private val _ui = MutableStateFlow(EditorUi())
    val ui: StateFlow<EditorUi> = _ui

    init {
        viewModelScope.launch {
            val info = graph.imports.get(importId)
            if (info == null) {
                _ui.update { it.copy(loading = false, error = "This image is no longer available. Import it again.") }
                return@launch
            }
            try {
                val preview = withContext(Dispatchers.Default) {
                    val file = graph.imports.original(importId)
                    val b = Imaging.decodePreview(file, 2048)
                    // Keep the preview's orientation consistent with the processing decode.
                    val s = 2048.0 / maxOf(info.workW, info.workH)
                    val ew = if (s < 1) (info.workW * s).toInt().coerceAtLeast(1) else info.workW
                    val eh = if (s < 1) (info.workH * s).toInt().coerceAtLeast(1) else info.workH
                    if ((b.width > b.height) != (ew > eh) && b.width != b.height) b.orientedTo(ew, eh, file) else b
                }
                val landscape = info.workW > info.workH
                var state = EditorUi(
                    loading = false, info = info, preview = preview, edgeColor = averageEdge(preview), landscape = landscape,
                    background = if (info.hasAlpha) Background.TRANSPARENT else Background.WHITE,
                    // a connected cloud GPU is the user's stated preference for quality
                    engine = if (graph.settings.cloudLink.value != null) JobSpec.ENGINE_CLOUD else JobSpec.ENGINE_DEVICE,
                )
                state = when {
                    initialPreset != null -> state.copy(outputMode = OutputMode.PRINT, presetId = initialPreset)
                    initialFactor != null -> state.copy(outputMode = OutputMode.SCALE, factor = initialFactor)
                    else -> {
                        // Default: the largest common print (up to 24 × 36 in) that matches the artwork's ratio.
                        val r = minOf(info.workW, info.workH).toDouble() / maxOf(info.workW, info.workH)
                        val match = PrintMath.PRESETS.filter { abs(it.shortIn / it.longIn - r) < 0.02 && it.longIn <= 36 }
                            .maxByOrNull { it.longIn }
                        if (match != null) state.copy(outputMode = OutputMode.PRINT, presetId = match.id)
                        else state.copy(outputMode = OutputMode.SCALE, factor = 4)
                    }
                }
                _ui.value = state
            } catch (e: Throwable) {
                _ui.update { it.copy(loading = false, error = "The image could not be opened for editing (${e.message}).") }
            }
        }
    }

    private fun averageEdge(b: Bitmap): Int {
        var r = 0L; var g = 0L; var bl = 0L; var n = 0L
        val w = b.width; val h = b.height
        val step = maxOf(1, (w + h) / 400)
        fun add(p: Int) { r += (p shr 16) and 0xFF; g += (p shr 8) and 0xFF; bl += p and 0xFF; n++ }
        for (x in 0 until w step step) { add(b.getPixel(x, 0)); add(b.getPixel(x, h - 1)) }
        for (y in 0 until h step step) { add(b.getPixel(0, y)); add(b.getPixel(w - 1, y)) }
        if (n == 0L) return 0xFFFFFFFF.toInt()
        return (0xFF shl 24) or ((r / n).toInt() shl 16) or ((g / n).toInt() shl 8) or (bl / n).toInt()
    }

    private fun clampCrop(s: EditorUi): EditorUi = s.geometry()?.let { s.copy(crop = it.clampedState) } ?: s

    fun setCrop(c: CropState) = _ui.update { clampCrop(it.copy(crop = c)) }
    fun rotate90() = _ui.update {
        // Rotating the artwork also flips the canvas, so a portrait print stays matched to the image.
        clampCrop(it.copy(crop = it.crop.copy(quarterTurns = (it.crop.quarterTurns + 1) % 4, panX = 0f, panY = 0f), landscape = !it.landscape))
    }
    fun setStraighten(deg: Float) = _ui.update { clampCrop(it.copy(crop = it.crop.copy(straightenDeg = deg))) }
    fun zoomBy(f: Float) = _ui.update { clampCrop(it.copy(crop = it.crop.copy(zoom = it.crop.zoom * f))) }
    fun resetCrop() = _ui.update { clampCrop(it.copy(crop = CropState(quarterTurns = it.crop.quarterTurns))) }
    fun setAspect(a: AspectChoice?) = _ui.update { clampCrop(it.copy(aspect = a)) }
    fun toggleOrientation() = _ui.update { clampCrop(it.copy(landscape = !it.landscape)) }
    fun setFitMode(m: FitMode) = _ui.update { clampCrop(it.copy(fitMode = m, crop = it.crop.copy(zoom = 1f, panX = 0f, panY = 0f))) }
    fun setBackground(b: Background) = _ui.update { it.copy(background = b) }
    fun setOutputMode(m: OutputMode) = _ui.update {
        val withPreset = if (m == OutputMode.PRINT && it.presetId == null && it.customPrint == null) it.copy(presetId = "16x20") else it
        clampCrop(withPreset.copy(outputMode = m))
    }
    fun setPreset(id: String) = _ui.update { clampCrop(it.copy(presetId = id, customPrint = null)) }
    fun setCustomPrint(p: PrintSize) = _ui.update {
        clampCrop(it.copy(customPrint = p, presetId = null, landscape = p.widthIn > p.heightIn))
    }
    fun setEngine(e: String) = _ui.update { it.copy(engine = e) }
    fun setDpi(d: Int) = _ui.update { it.copy(dpi = d) }
    fun setFactor(f: Int) = _ui.update { it.copy(factor = f) }
    fun setStrength(s: Strength) = _ui.update { it.copy(strength = s, detail = s.detail, sharpen = s.sharpen, denoise = s.denoise) }
    fun setDetail(v: Float) = _ui.update { it.copy(detail = v) }
    fun setSharpen(v: Float) = _ui.update { it.copy(sharpen = v) }
    fun setDenoise(v: Float) = _ui.update { it.copy(denoise = v) }

    fun budget(): DeviceBudget {
        val rt = Runtime.getRuntime()
        val heap = rt.maxMemory() - (rt.totalMemory() - rt.freeMemory())
        val disk = runCatching { StatFs(graph.app.filesDir.path).availableBytes }.getOrDefault(0L)
        return DeviceBudget(heap, disk)
    }

    fun targetFor(s: EditorUi, geom: CropGeometry, factor: Int = s.factor): Pair<Int, Int> =
        s.printSize?.pixels(s.dpi) ?: (geom.outW * factor to geom.outH * factor)

    fun plan(s: EditorUi, factor: Int = s.factor): UpscalePlan? {
        val geom = s.geometry() ?: return null
        val (tw, th) = targetFor(s, geom, factor)
        return Planner.plan(geom.outW, geom.outH, tw, th, s.outputHasAlpha, budget(), s.printSize?.let { PrintTarget(it, s.dpi) })
    }

    fun start(onStarted: (String) -> Unit) {
        val s = _ui.value
        val geom = s.geometry() ?: return
        val plan = plan(s) ?: return
        if (!plan.feasible || s.starting) return
        _ui.update { it.copy(starting = true) }
        viewModelScope.launch {
            try {
                val spec = JobSpec(
                    importId = importId, crop = geom.clampedState, aspect = s.effectiveAspect, fitMode = s.fitMode,
                    background = if (s.fitMode == FitMode.FIT) s.backgroundArgb else null,
                    targetW = plan.targetW, targetH = plan.targetH, useAi = plan.useAi,
                    print = s.printSize?.let { PrintTarget(it, s.dpi) },
                    settings = EnhanceSettings(s.detail, s.sharpen, s.denoise),
                    engine = if (s.cloud && graph.settings.cloudLink.value != null) JobSpec.ENGINE_CLOUD else JobSpec.ENGINE_DEVICE,
                )
                val id = graph.processing.enqueue(spec)
                onStarted(id)
            } catch (e: Exception) {
                _ui.update { it.copy(error = "Could not start processing: ${e.message}") }
            } finally {
                _ui.update { it.copy(starting = false) }
            }
        }
    }

    fun clearError() = _ui.update { it.copy(error = null) }
}
