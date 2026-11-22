package com.printscale.engine

import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

enum class LengthUnit(val label: String) {
    INCH("in"),
    CM("cm");

    fun toInches(value: Double): Double = if (this == INCH) value else value / 2.54
    fun fromInches(inches: Double): Double = if (this == INCH) inches else inches * 2.54
}

enum class PresetGroup(val title: String) {
    SMALL("Small prints"),
    MEDIUM("Medium prints"),
    LARGE("Large prints"),
    EXTRA_LARGE("Extra large prints"),
    ISO("International (A sizes)"),
}

/** A physical print size stored short side first. Orientation is applied separately. */
data class PrintPreset(
    val id: String,
    val shortIn: Double,
    val longIn: Double,
    val group: PresetGroup,
    /** Paper name for ISO sizes, e.g. "A4". */
    val name: String? = null,
) {
    val label: String get() = name ?: "${fmt(shortIn)} × ${fmt(longIn)} in"

    fun oriented(landscape: Boolean): PrintSize =
        if (landscape) PrintSize(longIn, shortIn) else PrintSize(shortIn, longIn)

    private fun fmt(v: Double) = if (v % 1.0 == 0.0) v.toInt().toString() else v.toString()
}

data class PrintSize(val widthIn: Double, val heightIn: Double) {
    fun pixels(dpi: Int): Pair<Int, Int> = PrintMath.pixels(widthIn, dpi) to PrintMath.pixels(heightIn, dpi)
    val aspect: Double get() = widthIn / heightIn
    val isLandscape: Boolean get() = widthIn > heightIn
    fun swapped() = PrintSize(heightIn, widthIn)
}

data class DpiOption(val dpi: Int, val label: String)

object PrintMath {
    val DPI_OPTIONS = listOf(
        DpiOption(300, "Premium print quality"),
        DpiOption(240, "High-quality printing"),
        DpiOption(200, "Standard large prints"),
        DpiOption(150, "Large-format printing"),
    )
    const val DEFAULT_DPI = 300

    val PRESETS: List<PrintPreset> = listOf(
        PrintPreset("5x7", 5.0, 7.0, PresetGroup.SMALL),
        PrintPreset("8x10", 8.0, 10.0, PresetGroup.SMALL),
        PrintPreset("8x12", 8.0, 12.0, PresetGroup.SMALL),
        PrintPreset("10x12", 10.0, 12.0, PresetGroup.SMALL),
        PrintPreset("11x14", 11.0, 14.0, PresetGroup.MEDIUM),
        PrintPreset("12x16", 12.0, 16.0, PresetGroup.MEDIUM),
        PrintPreset("12x18", 12.0, 18.0, PresetGroup.MEDIUM),
        PrintPreset("16x20", 16.0, 20.0, PresetGroup.MEDIUM),
        PrintPreset("18x24", 18.0, 24.0, PresetGroup.LARGE),
        PrintPreset("20x24", 20.0, 24.0, PresetGroup.LARGE),
        PrintPreset("20x30", 20.0, 30.0, PresetGroup.LARGE),
        PrintPreset("24x36", 24.0, 36.0, PresetGroup.LARGE),
        PrintPreset("30x40", 30.0, 40.0, PresetGroup.EXTRA_LARGE),
        PrintPreset("36x48", 36.0, 48.0, PresetGroup.EXTRA_LARGE),
        iso("a5", "A5", 148, 210),
        iso("a4", "A4", 210, 297),
        iso("a3", "A3", 297, 420),
        iso("a2", "A2", 420, 594),
        iso("a1", "A1", 594, 841),
    )

    /** ISO 216 sizes from their exact millimetres. */
    private fun iso(id: String, name: String, shortMm: Int, longMm: Int) =
        PrintPreset(id, shortMm / 25.4, longMm / 25.4, PresetGroup.ISO, name)

    /** "A4" when a stored print size is an ISO preset (either orientation), otherwise null. */
    fun nameFor(wIn: Double, hIn: Double): String? = PRESETS.firstOrNull {
        it.name != null && abs(minOf(wIn, hIn) - it.shortIn) < 0.01 && abs(maxOf(wIn, hIn) - it.longIn) < 0.01
    }?.name

    /** Human label for a stored print size: "A4" or "8 × 10 in". */
    fun describe(wIn: Double, hIn: Double): String =
        nameFor(wIn, hIn)?.let { "$it (${formatInches(wIn)} × ${formatInches(hIn)} in)" } ?: "${formatInches(wIn)} × ${formatInches(hIn)} in"

    /**
     * Etsy's limit for each digital-download file. Written as 20 000 000 bytes so the file fits
     * whether "20 MB" means 10^6 or 2^20 bytes.
     */
    const val ETSY_FILE_LIMIT_BYTES = 20_000_000L

    fun preset(id: String?): PrintPreset? = PRESETS.firstOrNull { it.id == id }

    /** Pixels = Inches × DPI. */
    fun pixels(inches: Double, dpi: Int): Int = max(1, (inches * dpi).roundToInt())

    /** Largest print (in inches) a pixel size supports at a DPI. */
    fun maxInches(px: Int, dpi: Int): Double = px.toDouble() / dpi

    /** Reduce a ratio to a readable form, e.g. 1024x1536 -> "2:3". Falls back to a decimal. */
    fun ratioLabel(w: Int, h: Int): String {
        val g = gcd(w, h)
        val a = w / g
        val b = h / g
        if (a <= 32 && b <= 32) return "$a:$b"
        val known = listOf(1 to 1, 2 to 3, 3 to 2, 3 to 4, 4 to 3, 4 to 5, 5 to 4, 5 to 7, 7 to 5,
            11 to 14, 14 to 11, 16 to 9, 9 to 16)
        val r = w.toDouble() / h
        known.forEach { (x, y) -> if (abs(r - x.toDouble() / y) < 0.006) return "≈$x:$y" }
        return String.format("%.2f:1", r)
    }

    fun gcd(a: Int, b: Int): Int {
        var x = abs(a)
        var y = abs(b)
        while (y != 0) {
            val t = x % y; x = y; y = t
        }
        return max(1, x)
    }

    fun formatInches(v: Double): String =
        if (abs(v - v.roundToInt()) < 0.05) v.roundToInt().toString() else String.format("%.1f", v)

    fun formatFactor(f: Double): String {
        val r1 = (f * 10).roundToInt() / 10.0
        return if (abs(r1 - r1.roundToInt()) < 0.001) "${r1.roundToInt()}×" else "${r1}×"
    }

    /** Preset sizes (in the given orientation) that a pixel size fully covers at a DPI. */
    fun coveredPresets(px: Int, py: Int, dpi: Int): List<PrintPreset> {
        val landscape = px > py
        return PRESETS.filter {
            val s = it.oriented(landscape)
            pixels(s.widthIn, dpi) <= px && pixels(s.heightIn, dpi) <= py
        }
    }

    fun minOf(a: Double, b: Double) = min(a, b)
}
