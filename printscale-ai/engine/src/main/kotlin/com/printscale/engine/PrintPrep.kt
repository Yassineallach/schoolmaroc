package com.printscale.engine

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

/** Garment print methods. They share the same print file format (transparent PNG at print size). */
enum class PrintMethod(val title: String) {
    DTF("DTF"),
    DTG("DTG"),
}

/**
 * Where the artwork sits on the print canvas, in inches from the canvas's top-left corner.
 * The canvas is the print file: its size is the requested print size.
 */
data class Placement(val xIn: Double, val yIn: Double, val wIn: Double, val hIn: Double) {
    val centerXIn get() = xIn + wIn / 2
    val centerYIn get() = yIn + hIn / 2
}

/** The same placement converted to whole pixels at a DPI. */
data class PixelPlacement(val canvasW: Int, val canvasH: Int, val x: Int, val y: Int, val w: Int, val h: Int)

object PrintLayout {
    /** Largest size that fits inside the canvas with the artwork's own proportions. */
    fun fit(canvasWIn: Double, canvasHIn: Double, artW: Int, artH: Int, alignTop: Boolean = false): Placement {
        val ratio = artW.toDouble() / artH
        var w = canvasWIn
        var h = w / ratio
        if (h > canvasHIn) { h = canvasHIn; w = h * ratio }
        val x = (canvasWIn - w) / 2
        val y = if (alignTop) 0.0 else (canvasHIn - h) / 2
        return Placement(x, y, w, h)
    }

    fun centerHorizontally(p: Placement, canvasWIn: Double) = p.copy(xIn = (canvasWIn - p.wIn) / 2)
    fun centerVertically(p: Placement, canvasHIn: Double) = p.copy(yIn = (canvasHIn - p.hIn) / 2)

    /** Resize around the artwork's centre. */
    fun resize(p: Placement, wIn: Double, hIn: Double) =
        Placement(p.centerXIn - wIn / 2, p.centerYIn - hIn / 2, max(0.05, wIn), max(0.05, hIn))

    fun toPixels(canvasWIn: Double, canvasHIn: Double, p: Placement, dpi: Int) = PixelPlacement(
        canvasW = PrintMath.pixels(canvasWIn, dpi),
        canvasH = PrintMath.pixels(canvasHIn, dpi),
        x = (p.xIn * dpi).roundToInt(),
        y = (p.yIn * dpi).roundToInt(),
        w = max(1, (p.wIn * dpi).roundToInt()),
        h = max(1, (p.hIn * dpi).roundToInt()),
    )

    /** Share of the artwork's area that falls outside the canvas (it would be cut off). */
    fun clippedFraction(p: Placement, canvasWIn: Double, canvasHIn: Double): Double {
        val iw = max(0.0, min(p.xIn + p.wIn, canvasWIn) - max(p.xIn, 0.0))
        val ih = max(0.0, min(p.yIn + p.hIn, canvasHIn) - max(p.yIn, 0.0))
        return 1 - (iw * ih) / (p.wIn * p.hIn)
    }
}

/**
 * Receives the resized artwork rows and writes full canvas rows: transparent everywhere except
 * where the artwork lands, clipped at the canvas edges. Streams, so the canvas never exists in memory.
 */
class CanvasPlacer(
    private val px: PixelPlacement,
    private val out: RowSink,
    /** When set, alpha >= cutoff becomes fully opaque and below becomes transparent (solid edges for DTF). */
    private val solidAlphaCutoff: Int? = null,
) : RowSink {
    private val row = IntArray(px.canvasW)
    private var emitted = 0

    private fun blank() {
        row.fill(0)
        out.writeRow(emitted++, row)
    }

    override fun writeRow(y: Int, argb: IntArray) {
        val cy = px.y + y
        if (cy < 0 || cy >= px.canvasH) return
        while (emitted < cy) blank()
        row.fill(0)
        val from = max(0, px.x)
        val to = min(px.canvasW, px.x + px.w)
        for (cx in from until to) {
            var p = argb[cx - px.x]
            if (solidAlphaCutoff != null) {
                p = if ((p ushr 24) >= solidAlphaCutoff) p or (0xFF shl 24) else 0
            }
            row[cx] = p
        }
        out.writeRow(emitted++, row)
    }

    override fun finish() {
        while (emitted < px.canvasH) blank()
        out.finish()
    }
}

object PrintRenderer {
    /**
     * Resamples the artwork to its placed pixel size (Lanczos, separate horizontal and vertical
     * scale, so a deliberate stretch is honoured) and composes it onto a transparent canvas.
     */
    fun render(art: PixelBuffer, px: PixelPlacement, sink: RowSink, solidAlphaCutoff: Int? = null, checkCancel: () -> Unit = {}) {
        val placer = CanvasPlacer(px, sink, solidAlphaCutoff)
        var y = 0
        StreamingResizer(art.width, art.height, px.w, px.h).run({ dst ->
            System.arraycopy(art.argb, y * art.width, dst, 0, art.width); y++
        }, placer, checkCancel)
        placer.finish()
    }
}

object AlphaStats {
    data class Stats(val hasTransparency: Boolean, val semiTransparentFraction: Double, val visibleFraction: Double)

    fun of(p: PixelBuffer): Stats {
        var visible = 0L
        var semi = 0L
        for (px in p.argb) {
            val a = px ushr 24
            if (a > 0) visible++
            if (a in 1..254) semi++
        }
        val n = p.argb.size.toDouble()
        return Stats(visible < p.argb.size, if (visible == 0L) 0.0 else semi / visible.toDouble(), visible / n)
    }

    /** Bounding box of pixels with alpha above [minAlpha], or null when fully transparent. */
    fun visibleBounds(p: PixelBuffer, minAlpha: Int = 8): IntArray? {
        var l = p.width; var t = p.height; var r = -1; var b = -1
        for (y in 0 until p.height) {
            val o = y * p.width
            for (x in 0 until p.width) {
                if ((p.argb[o + x] ushr 24) > minAlpha) {
                    if (x < l) l = x; if (x > r) r = x; if (y < t) t = y; if (y > b) b = y
                }
            }
        }
        return if (r < 0) null else intArrayOf(l, t, r + 1, b + 1)
    }

    fun crop(p: PixelBuffer, box: IntArray): PixelBuffer {
        val w = box[2] - box[0]
        val h = box[3] - box[1]
        val out = IntArray(w * h)
        for (y in 0 until h) System.arraycopy(p.argb, (box[1] + y) * p.width + box[0], out, y * w, w)
        return PixelBuffer(w, h, out)
    }
}

/** Where an artwork file came from, so the analyzer can tell real detail from interpolated pixels. */
data class Provenance(
    /** Width of the image before it was upscaled. */
    val originalW: Int,
    val originalH: Int,
    /** Width of the upscaled file this artwork was taken from. */
    val upscaledW: Int,
    val upscaledH: Int,
    val aiUpscaled: Boolean,
)

enum class Level { OK, WARN, BAD }

data class QualityCheck(val level: Level, val title: String, val detail: String)

enum class ResolutionStatus(val label: String) { EXCELLENT("Excellent"), GOOD("Good"), LOW("Low resolution") }

data class QualityReport(
    val overall: Level,
    val headline: String,
    val resolution: ResolutionStatus,
    /** Pixels per inch the file actually delivers at the placed size. */
    val pixelDpi: Double,
    /** Pixels per inch of real detail when the artwork was upscaled, else null. */
    val detailDpi: Double?,
    val checks: List<QualityCheck>,
)

data class QualityInput(
    val method: PrintMethod,
    val artW: Int,
    val artH: Int,
    val placement: Placement,
    val canvasWIn: Double,
    val canvasHIn: Double,
    val dpi: Int,
    val alpha: AlphaStats.Stats,
    val solidEdges: Boolean,
    val provenance: Provenance? = null,
    /** Largest printable area of the chosen garment/platen, for DTG boundary checks. */
    val maxPrintAreaIn: Pair<Double, Double>? = null,
)

/**
 * Checks a prepared print before export. Resolution is judged on real detail: Lanczos-enlarged
 * pixels count for nothing, AI-upscaled pixels count but are flagged as reconstructed.
 */
object QualityAnalyzer {
    fun status(effectiveDpi: Double, dpi: Int): ResolutionStatus = when {
        effectiveDpi >= dpi * 0.9 -> ResolutionStatus.EXCELLENT
        effectiveDpi >= max(dpi * 0.6, 120.0) -> ResolutionStatus.GOOD
        else -> ResolutionStatus.LOW
    }

    fun analyze(q: QualityInput): QualityReport {
        val checks = mutableListOf<QualityCheck>()
        val p = q.placement
        val pixelDpi = min(q.artW / p.wIn, q.artH / p.hIn)
        val prov = q.provenance
        val detailDpi = prov?.let { pixelDpi * it.originalW.toDouble() / it.upscaledW }

        // 1. resolution, judged on the measure that reflects real detail
        val judged = when {
            prov == null -> pixelDpi
            prov.aiUpscaled -> pixelDpi
            else -> detailDpi!! // plain interpolation adds no detail
        }
        var res = status(judged, q.dpi)
        if (prov != null && prov.aiUpscaled && res == ResolutionStatus.EXCELLENT && detailDpi!! < q.dpi * 0.5) {
            res = ResolutionStatus.GOOD // reconstructed, not recovered: never call it excellent
        }
        val size = "${fmt(p.wIn)} × ${fmt(p.hIn)} in"
        checks += when (res) {
            ResolutionStatus.EXCELLENT -> QualityCheck(Level.OK, "Resolution: excellent",
                "About ${pixelDpi.roundToInt()} pixels per inch at $size (target ${q.dpi}).")
            ResolutionStatus.GOOD -> QualityCheck(Level.WARN, "Resolution: good",
                "About ${judged.roundToInt()} DPI at $size. Fine at arm's length; fine detail may look soft up close.")
            ResolutionStatus.LOW -> QualityCheck(Level.BAD, "Resolution: too low for this size",
                "Only about ${judged.roundToInt()} DPI at $size. Print smaller, or upscale the artwork first.")
        }

        // 2. enlargement and pixelation
        val enlarge = q.dpi / pixelDpi
        if (enlarge > 1.05) {
            val lvl = when { enlarge <= 1.6 -> Level.WARN; else -> Level.BAD }
            checks += QualityCheck(lvl, "Will be enlarged ${fmt(enlarge)}×",
                "The artwork has fewer pixels than ${q.dpi} DPI needs, so it is enlarged on export. " +
                    if (lvl == Level.BAD) "At this much enlargement edges turn soft and blocky." else "Edges will be a little softer.")
        }
        prov?.let {
            val f = it.upscaledW.toDouble() / it.originalW
            checks += if (it.aiUpscaled) QualityCheck(Level.WARN, "Upscaled ${fmt(f)}× with AI",
                "Pixel count supports ${pixelDpi.roundToInt()} DPI, but the original only had about ${detailDpi!!.roundToInt()} DPI of real detail. " +
                    "AI fills in plausible detail; check it at 100% before printing.")
            else QualityCheck(Level.WARN, "Enlarged ${fmt(f)}× without AI",
                "Interpolation adds pixels, not detail. Judged on the original: about ${detailDpi!!.roundToInt()} DPI.")
        }

        // 3. transparency
        checks += if (q.alpha.hasTransparency) QualityCheck(Level.OK, "Transparent background",
            "Only the artwork prints; the rest of the canvas stays clear.")
        else QualityCheck(Level.WARN, "No transparency",
            "The whole rectangle prints, background included. Remove the background if it should not be printed.")

        // 4. semi-transparent pixels (shadows, glows, soft edges)
        if (q.alpha.semiTransparentFraction > 0.005) {
            val pct = (q.alpha.semiTransparentFraction * 100).let { if (it < 1) "under 1" else it.roundToInt().toString() }
            checks += if (q.solidEdges) QualityCheck(Level.OK, "Soft edges made solid",
                "$pct% of visible pixels were partly transparent; the export turns them fully solid or clear.")
            else if (q.method == PrintMethod.DTF) QualityCheck(Level.WARN, "Partly transparent pixels ($pct%)",
                "DTF prints a white underbase under anything visible, so glows, shadows and soft edges can print solid or speckled. Turn on Solid edges or remove those effects.")
            else QualityCheck(Level.WARN, "Partly transparent pixels ($pct%)",
                "On dark garments the white underbase can make soft shadows and glows look patchy. Check them on the dark-shirt preview.")
        }

        // 5. stretching
        val stretch = (q.artW.toDouble() / q.artH) / (p.wIn / p.hIn)
        val dev = abs(stretch - 1)
        if (dev > 0.01) {
            checks += QualityCheck(if (dev > 0.1) Level.BAD else Level.WARN, "Artwork is stretched",
                "Width and height are scaled differently (${(dev * 100).roundToInt()}%). Lock the proportions unless this is intended.")
        }

        // 6. clipping
        val clipped = PrintLayout.clippedFraction(p, q.canvasWIn, q.canvasHIn)
        if (clipped > 0.001) {
            checks += QualityCheck(if (clipped > 0.05) Level.BAD else Level.WARN, "Part of the artwork is cut off",
                "${(clipped * 100).let { if (it < 1) "Under 1" else it.roundToInt().toString() }}% of it lies outside the print area and will not print.")
        }

        // 7. garment boundaries (DTG platen / printable area)
        q.maxPrintAreaIn?.let { (mw, mh) ->
            if (q.canvasWIn > mw + 0.01 || q.canvasHIn > mh + 0.01) {
                checks += QualityCheck(Level.WARN, "Larger than the garment's print area",
                    "${fmt(q.canvasWIn)} × ${fmt(q.canvasHIn)} in exceeds the usual ${fmt(mw)} × ${fmt(mh)} in for this garment. Check your printer's maximum.")
            }
        }

        val overall = when {
            checks.any { it.level == Level.BAD } -> Level.BAD
            checks.any { it.level == Level.WARN } -> Level.WARN
            else -> Level.OK
        }
        val headline = when (overall) {
            Level.OK -> "Excellent print quality"
            Level.WARN -> "Acceptable, quality may be reduced"
            Level.BAD -> if (res == ResolutionStatus.LOW) "Resolution is too low for this print size" else "Fix the issues below before printing"
        }
        return QualityReport(overall, headline, res, pixelDpi, detailDpi, checks)
    }

    private fun fmt(v: Double): String {
        val r = (v * 10).roundToInt() / 10.0
        return if (abs(r - r.roundToInt()) < 1e-9) r.roundToInt().toString() else r.toString()
    }
}
