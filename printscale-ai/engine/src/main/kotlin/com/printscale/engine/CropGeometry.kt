package com.printscale.engine

import kotlin.math.abs
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.math.sin

enum class FitMode {
    /** Cover the canvas; whatever falls outside is cropped. */
    FILL,
    /** Keep the whole artwork; empty canvas is filled with the background. */
    FIT,
}

/**
 * User adjustments on top of the base framing.
 * pan is the offset of the canvas centre from the image centre, as a fraction of the
 * rotated image width and height.
 */
data class CropState(
    val quarterTurns: Int = 0,
    val straightenDeg: Float = 0f,
    val zoom: Float = 1f,
    val panX: Float = 0f,
    val panY: Float = 0f,
)

/**
 * Maps the decoded (orientation-corrected) source onto the prepared canvas.
 * The canvas keeps the source's pixel density: one canvas pixel is one source pixel,
 * so cropping never resamples unless the user straightens the image.
 */
class CropGeometry(
    val srcW: Int,
    val srcH: Int,
    /** Width / height of the canvas, or null for the source's own ratio. */
    aspect: Double?,
    val mode: FitMode,
    state: CropState,
) {
    val quarter = ((state.quarterTurns % 4) + 4) % 4
    val rotW: Double = if (quarter % 2 == 0) srcW.toDouble() else srcH.toDouble()
    val rotH: Double = if (quarter % 2 == 0) srcH.toDouble() else srcW.toDouble()
    val ratio: Double = aspect ?: (rotW / rotH)
    val theta: Double = Math.toRadians(state.straightenDeg.toDouble())
    private val c = abs(cos(theta))
    private val s = abs(sin(theta))

    val zoom: Float = state.zoom.coerceIn(if (mode == FitMode.FILL) 1f else MIN_FIT_ZOOM, MAX_ZOOM)

    private val baseH: Double = when (mode) {
        FitMode.FILL -> min(rotW / (ratio * c + s), rotH / (ratio * s + c))
        FitMode.FIT -> max(rotW * s + rotH * c, (rotW * c + rotH * s) / ratio)
    }

    val canvasH: Double = baseH / zoom
    val canvasW: Double = ratio * canvasH
    val outW: Int = max(MIN_SIDE, canvasW.roundToInt())
    val outH: Int = max(MIN_SIDE, canvasH.roundToInt())

    /** Pan in rotated-image pixels after clamping. */
    val panPx: Double
    val panPy: Double

    init {
        val maxX: Double
        val maxY: Double
        if (mode == FitMode.FILL) {
            val bw = canvasW * c + canvasH * s
            val bh = canvasW * s + canvasH * c
            maxX = max(0.0, (rotW - bw) / 2)
            maxY = max(0.0, (rotH - bh) / 2)
        } else {
            maxX = rotW / 2
            maxY = rotH / 2
        }
        panPx = (state.panX * rotW).coerceIn(-maxX, maxX)
        panPy = (state.panY * rotH).coerceIn(-maxY, maxY)
    }

    /** The clamped state, so the UI can store exactly what is rendered. */
    val clampedState: CropState = state.copy(
        quarterTurns = quarter,
        zoom = zoom,
        panX = (panPx / rotW).toFloat(),
        panY = (panPy / rotH).toFloat(),
    )

    /** True when the mapping is a pure pixel copy (no straighten), so no resampling happens. */
    val isPixelExact: Boolean get() = theta == 0.0

    /**
     * Affine matrix [a, b, tx, c, d, ty] mapping source pixel coordinates to canvas coordinates:
     * x' = a*x + b*y + tx, y' = c*x + d*y + ty.
     */
    fun matrix(): DoubleArray {
        // 1. quarter turn (clockwise) into rotated-image space
        val q = when (quarter) {
            0 -> doubleArrayOf(1.0, 0.0, 0.0, 0.0, 1.0, 0.0)
            1 -> doubleArrayOf(0.0, -1.0, srcH.toDouble(), 1.0, 0.0, 0.0)
            2 -> doubleArrayOf(-1.0, 0.0, srcW.toDouble(), 0.0, -1.0, srcH.toDouble())
            else -> doubleArrayOf(0.0, 1.0, 0.0, -1.0, 0.0, srcW.toDouble())
        }
        // 2. move the chosen centre to the origin
        val cx = rotW / 2 + panPx
        val cy = rotH / 2 + panPy
        val t1 = doubleArrayOf(1.0, 0.0, -cx, 0.0, 1.0, -cy)
        // 3. straighten (clockwise on screen, y down)
        val ct = cos(theta)
        val st = sin(theta)
        val r = doubleArrayOf(ct, -st, 0.0, st, ct, 0.0)
        // 4. canvas centre
        var tx = outW / 2.0
        var ty = outH / 2.0
        val m = mul(doubleArrayOf(1.0, 0.0, tx, 0.0, 1.0, ty), mul(r, mul(t1, q)))
        if (isPixelExact) {
            // Snap so the copy lands on whole pixels.
            m[2] = Math.round(m[2]).toDouble()
            m[5] = Math.round(m[5]).toDouble()
        }
        return m
    }

    companion object {
        const val MIN_FIT_ZOOM = 0.5f
        const val MAX_ZOOM = 8f
        const val MIN_SIDE = 16

        fun mul(a: DoubleArray, b: DoubleArray): DoubleArray = doubleArrayOf(
            a[0] * b[0] + a[1] * b[3], a[0] * b[1] + a[1] * b[4], a[0] * b[2] + a[1] * b[5] + a[2],
            a[3] * b[0] + a[4] * b[3], a[3] * b[1] + a[4] * b[4], a[3] * b[2] + a[4] * b[5] + a[5],
        )
    }
}
