package com.printscale.ai.ui.prep

import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path

/**
 * Flat front views drawn in inches (adult medium), so a print shown on them is at true scale
 * relative to the garment. These are generic shapes drawn for this app.
 */
enum class Garment(val label: String, val widthIn: Float, val heightIn: Float, val collarCenterY: Float,
                   val maxPrintIn: Pair<Double, Double>, val bodyLeft: Float, val bodyRight: Float) {
    TEE("T-shirt", 31f, 30f, 2.6f, 12.0 to 16.0, 5.5f, 25.5f),
    HOODIE("Hoodie", 31f, 34f, 7.6f, 12.0 to 12.0, 5f, 26f);

    fun outline(): Path = Path().apply {
        when (this@Garment) {
            TEE -> {
                moveTo(12.2f, 0.7f)
                cubicTo(13.5f, 3.3f, 17.5f, 3.3f, 18.8f, 0.7f)
                lineTo(25.5f, 2.2f); lineTo(31f, 8.6f); lineTo(27.9f, 10.9f); lineTo(25.5f, 9.3f)
                lineTo(25.6f, 29.2f)
                quadraticTo(15.5f, 29.8f, 5.4f, 29.2f)
                lineTo(5.5f, 9.3f); lineTo(3.1f, 10.9f); lineTo(0f, 8.6f); lineTo(5.5f, 2.2f)
                close()
            }
            HOODIE -> {
                moveTo(11.2f, 6.6f)
                cubicTo(12.6f, 8.6f, 18.4f, 8.6f, 19.8f, 6.6f)
                lineTo(26f, 8f); lineTo(30.6f, 15f); lineTo(31f, 28.8f); lineTo(27.8f, 29.2f); lineTo(26.2f, 15.8f)
                lineTo(26.1f, 33.6f)
                quadraticTo(15.5f, 34f, 4.9f, 33.6f)
                lineTo(4.8f, 15.8f); lineTo(3.2f, 29.2f); lineTo(0f, 28.8f); lineTo(0.4f, 15f); lineTo(5f, 8f)
                close()
            }
        }
    }

    /** Hood (behind the body), hood opening, collar band and similar details. */
    fun details(): List<Pair<Path, Float>> = when (this) {
        TEE -> listOf(
            Path().apply { // collar band
                moveTo(12.2f, 0.7f); cubicTo(13.5f, 3.3f, 17.5f, 3.3f, 18.8f, 0.7f)
                lineTo(18.3f, 0.6f); cubicTo(17.2f, 2.5f, 13.8f, 2.5f, 12.7f, 0.6f); close()
            } to 0.10f,
        )
        HOODIE -> listOf(
            Path().apply { // hood opening
                moveTo(12.6f, 7.2f); cubicTo(12f, 2.4f, 19f, 2.4f, 18.4f, 7.2f); cubicTo(16.6f, 8.1f, 14.4f, 8.1f, 12.6f, 7.2f); close()
            } to 0.22f,
            Path().apply { // pocket
                moveTo(9.6f, 24f); lineTo(21.4f, 24f); lineTo(22.6f, 31.2f); lineTo(8.4f, 31.2f); close()
            } to 0.06f,
            Path().apply { moveTo(4.9f, 32.2f); lineTo(26.1f, 32.2f); lineTo(26.1f, 33.6f); quadraticTo(15.5f, 34f, 4.9f, 33.6f); close() } to 0.07f,
        )
    }

    fun hood(): Path? = if (this == HOODIE) Path().apply {
        moveTo(10.8f, 7.4f); cubicTo(9.6f, 1f, 12.4f, 0f, 15.5f, 0f); cubicTo(18.6f, 0f, 21.4f, 1f, 20.2f, 7.4f); close()
    } else null
}

data class GarmentColor(val name: String, val color: Color, val dark: Boolean)

val GARMENT_COLORS = listOf(
    GarmentColor("White", Color(0xFFF3F2EE), false),
    GarmentColor("Black", Color(0xFF1C1C1E), true),
    GarmentColor("Sport grey", Color(0xFF9C9CA0), false),
    GarmentColor("Sand", Color(0xFFD8C6A5), false),
    GarmentColor("Navy", Color(0xFF1F2A44), true),
    GarmentColor("Red", Color(0xFFA3262D), true),
    GarmentColor("Forest", Color(0xFF2E4A39), true),
    GarmentColor("Royal", Color(0xFF2C4D9A), true),
    GarmentColor("Light pink", Color(0xFFE9BAC4), false),
)
