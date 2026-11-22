package com.printscale.ai.ui.prep

import android.graphics.Bitmap
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.calculatePan
import androidx.compose.foundation.gestures.calculateZoom
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.positionChanged
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import com.printscale.ai.ui.components.drawCropMarks
import com.printscale.ai.ui.theme.LocalExtras
import com.printscale.engine.Placement
import kotlin.math.abs
import kotlin.math.min
import kotlin.math.roundToInt

/**
 * The print file: the canvas is the exported area, the artwork can be dragged and pinched.
 * Anything outside the dashed boundary is shown faded because it will not print.
 */
@Composable
fun PrintCanvas(
    art: Bitmap,
    canvasWIn: Double,
    canvasHIn: Double,
    placement: Placement,
    background: CanvasBackground,
    garmentColor: Color,
    viewZoom: Float,
    onPlacement: (Placement) -> Unit,
    height: Dp = 380.dp,
) {
    val image = remember(art) { art.asImageBitmap() }
    val current by rememberUpdatedState(placement)
    val change by rememberUpdatedState(onPlacement)
    var dragging by remember { mutableStateOf(false) }
    val scheme = MaterialTheme.colorScheme
    val checker = LocalExtras.current.checker
    val accent = scheme.primary

    Canvas(
        Modifier.fillMaxWidth().height(height)
            .semantics { contentDescription = "Print canvas. Drag the artwork to move it, pinch to resize it." }
            .pointerInput(canvasWIn, canvasHIn, viewZoom) {
                awaitEachGesture {
                    awaitFirstDown(requireUnconsumed = false)
                    dragging = true
                    do {
                        val e = awaitPointerEvent()
                        val zoom = e.calculateZoom()
                        val pan = e.calculatePan()
                        if (zoom != 1f || pan != Offset.Zero) {
                            val k = pxPerInch(size.width.toFloat(), size.height.toFloat(), canvasWIn, canvasHIn, viewZoom)
                            var p = current
                            if (zoom != 1f) {
                                val nw = (p.wIn * zoom).coerceIn(0.25, canvasWIn * 4)
                                val nh = p.hIn * nw / p.wIn
                                p = Placement(p.centerXIn - nw / 2, p.centerYIn - nh / 2, nw, nh)
                            }
                            p = p.copy(xIn = p.xIn + pan.x / k, yIn = p.yIn + pan.y / k)
                            change(snap(p, canvasWIn, canvasHIn))
                            e.changes.forEach { if (it.positionChanged()) it.consume() }
                        }
                    } while (e.changes.any { it.pressed })
                    dragging = false
                }
            },
    ) {
        val k = pxPerInch(size.width, size.height, canvasWIn, canvasHIn, viewZoom)
        val cw = (canvasWIn * k).toFloat()
        val ch = (canvasHIn * k).toFloat()
        val cl = (size.width - cw) / 2
        val ct = (size.height - ch) / 2
        val ax = cl + (placement.xIn * k).toFloat()
        val ay = ct + (placement.yIn * k).toFloat()
        val aw = (placement.wIn * k).toFloat()
        val ah = (placement.hIn * k).toFloat()

        // Outside the print area: faded, so cut-off parts are visible but clearly excluded.
        drawArt(image, ax, ay, aw, ah, 0.25f)
        clipRect(cl, ct, cl + cw, ct + ch) {
            when (background) {
                CanvasBackground.CHECKER -> checkerboard(checker, cl, ct, cw, ch)
                CanvasBackground.WHITE -> drawRect(Color.White, Offset(cl, ct), Size(cw, ch))
                CanvasBackground.BLACK -> drawRect(Color.Black, Offset(cl, ct), Size(cw, ch))
                CanvasBackground.GARMENT -> drawRect(garmentColor, Offset(cl, ct), Size(cw, ch))
            }
            drawArt(image, ax, ay, aw, ah, 1f)
            // centre guides appear while dragging, when the artwork snaps to the middle
            if (dragging && abs(placement.centerXIn - canvasWIn / 2) < 0.01) drawLine(accent, Offset(cl + cw / 2, ct), Offset(cl + cw / 2, ct + ch), 1.dp.toPx())
            if (dragging && abs(placement.centerYIn - canvasHIn / 2) < 0.01) drawLine(accent, Offset(cl, ct + ch / 2), Offset(cl + cw, ct + ch / 2), 1.dp.toPx())
        }
        if (dragging) drawRect(accent.copy(alpha = 0.8f), Offset(ax, ay), Size(aw, ah), style = Stroke(1.dp.toPx()))
        // print-area boundary
        drawRect(scheme.onBackground.copy(alpha = 0.7f), Offset(cl, ct), Size(cw, ch),
            style = Stroke(1.dp.toPx(), pathEffect = PathEffect.dashPathEffect(floatArrayOf(8.dp.toPx(), 5.dp.toPx()))))
        drawCropMarks(scheme.onBackground, 10.dp.toPx(), 4.dp.toPx(), 1.5.dp.toPx(), cl, ct, cl + cw, ct + ch)
    }
}

private fun DrawScope.drawArt(img: ImageBitmap, x: Float, y: Float, w: Float, h: Float, alpha: Float) {
    if (w < 1 || h < 1) return
    drawImage(img, IntOffset.Zero, IntSize(img.width, img.height), IntOffset(x.roundToInt(), y.roundToInt()),
        IntSize(w.roundToInt(), h.roundToInt()), alpha = alpha, filterQuality = FilterQuality.Medium)
}

private fun DrawScope.checkerboard(c: Color, l: Float, t: Float, w: Float, h: Float) {
    drawRect(Color.White, Offset(l, t), Size(w, h))
    val cell = 10.dp.toPx()
    var r = 0
    var y = t
    while (y < t + h) {
        var x = l + if (r % 2 == 0) 0f else cell
        while (x < l + w) { drawRect(c.copy(alpha = 0.45f), Offset(x, y), Size(cell, cell)); x += 2 * cell }
        y += cell; r++
    }
}

private fun pxPerInch(w: Float, h: Float, cwIn: Double, chIn: Double, zoom: Float): Double {
    val m = 28.0 * (w / 400.0).coerceIn(0.6, 2.0)
    return min((w - 2 * m) / cwIn, (h - 2 * m) / chIn) * zoom
}

/** Pulls the artwork onto the centre lines when it is within a fraction of an inch of them. */
private fun snap(p: Placement, cw: Double, ch: Double): Placement {
    var q = p
    if (abs(q.centerXIn - cw / 2) < 0.12) q = q.copy(xIn = (cw - q.wIn) / 2)
    if (abs(q.centerYIn - ch / 2) < 0.12) q = q.copy(yIn = (ch - q.hIn) / 2)
    return q
}
