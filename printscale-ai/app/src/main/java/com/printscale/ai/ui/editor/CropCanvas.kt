package com.printscale.ai.ui.editor

import android.graphics.Bitmap
import android.graphics.Matrix
import android.graphics.Paint
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.awaitEachGesture
import androidx.compose.foundation.gestures.awaitFirstDown
import androidx.compose.foundation.gestures.calculatePan
import androidx.compose.foundation.gestures.calculateZoom
import androidx.compose.ui.input.pointer.positionChanged
import androidx.compose.foundation.layout.BoxWithConstraints
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
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.graphics.drawscope.drawIntoCanvas
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.printscale.ai.ui.components.drawCropMarks
import com.printscale.ai.ui.theme.LocalExtras
import com.printscale.engine.CropGeometry
import com.printscale.engine.CropState
import com.printscale.engine.FitMode
import kotlin.math.cos
import kotlin.math.min
import kotlin.math.sin

/**
 * Shows exactly what the worker will render: the same CropGeometry drives both.
 * Areas outside the frame stay visible but dimmed, so nothing is cropped unseen.
 */
@Composable
fun CropCanvas(
    preview: Bitmap,
    geom: CropGeometry,
    background: Int?,
    onChange: (CropState) -> Unit,
    onDoubleTap: () -> Unit,
    height: Dp = 360.dp,
) {
    val current by rememberUpdatedState(geom)
    val change by rememberUpdatedState(onChange)
    var interacting by remember { mutableStateOf(false) }
    val scheme = MaterialTheme.colorScheme
    val checker = LocalExtras.current.checker
    val paint = remember { Paint(Paint.FILTER_BITMAP_FLAG or Paint.ANTI_ALIAS_FLAG) }
    val matrix = remember { Matrix() }

    BoxWithConstraints(Modifier.fillMaxWidth().height(height)) {
        Canvas(
            Modifier.fillMaxWidth().height(height)
                .semantics { contentDescription = "Crop preview. Drag to move the artwork, pinch to zoom, double tap to reset." }
                .pointerInput(Unit) {
                    awaitEachGesture {
                        awaitFirstDown(requireUnconsumed = false)
                        interacting = true
                        do {
                            val event = awaitPointerEvent()
                            val zoom = event.calculateZoom()
                            val pan = event.calculatePan()
                            if (zoom != 1f || pan != Offset.Zero) {
                                val g = current
                                val k = displayScale(size.width.toFloat(), size.height.toFloat(), g, margin = 28.dp.toPx())
                                val dx = pan.x / k
                                val dy = pan.y / k
                                // Express the finger movement in the image's own (straightened) axes.
                                val c = cos(g.theta); val s = sin(g.theta)
                                val ix = c * dx + s * dy
                                val iy = -s * dx + c * dy
                                val st = g.clampedState
                                change(
                                    st.copy(
                                        zoom = st.zoom * zoom,
                                        panX = (st.panX - ix / g.rotW).toFloat(),
                                        panY = (st.panY - iy / g.rotH).toFloat(),
                                    ),
                                )
                                event.changes.forEach { if (it.positionChanged()) it.consume() }
                            }
                        } while (event.changes.any { it.pressed })
                        interacting = false
                    }
                }
                .pointerInput(Unit) { detectTapGestures(onDoubleTap = { onDoubleTap() }) },
        ) {
            val margin = 28.dp.toPx()
            val k = displayScale(size.width, size.height, geom, margin)
            val fw = (geom.canvasW * k).toFloat()
            val fh = (geom.canvasH * k).toFloat()
            val fl = (size.width - fw) / 2
            val ft = (size.height - fh) / 2

            // Fit background (or a checkerboard for transparent)
            if (geom.mode == FitMode.FIT || background == null) {
                if (background != null) {
                    drawRect(Color(background), Offset(fl, ft), Size(fw, fh))
                } else {
                    clipRect(fl, ft, fl + fw, ft + fh) {
                        val cell = 10.dp.toPx()
                        var y = ft; var row = 0
                        while (y < ft + fh) {
                            var x = fl + if (row % 2 == 0) 0f else cell
                            while (x < fl + fw) { drawRect(checker, Offset(x, y), Size(cell, cell)); x += 2 * cell }
                            y += cell; row++
                        }
                    }
                }
            }

            // Artwork: preview pixels -> source pixels -> canvas pixels -> screen.
            val m = geom.matrix()
            val toSource = geom.srcW.toFloat() / preview.width
            matrix.setValues(floatArrayOf(m[0].toFloat(), m[1].toFloat(), m[2].toFloat(), m[3].toFloat(), m[4].toFloat(), m[5].toFloat(), 0f, 0f, 1f))
            matrix.preScale(toSource, toSource)
            matrix.postScale(k.toFloat(), k.toFloat())
            matrix.postTranslate(fl, ft)
            drawIntoCanvas { it.nativeCanvas.drawBitmap(preview, matrix, paint) }

            // Dim everything outside the frame.
            val scrim = scheme.background.copy(alpha = 0.78f)
            drawRect(scrim, Offset.Zero, Size(size.width, ft))
            drawRect(scrim, Offset(0f, ft + fh), Size(size.width, size.height - ft - fh))
            drawRect(scrim, Offset(0f, ft), Size(fl, fh))
            drawRect(scrim, Offset(fl + fw, ft), Size(size.width - fl - fw, fh))

            if (interacting) {
                val grid = scheme.onBackground.copy(alpha = 0.35f)
                for (i in 1..2) {
                    drawLine(grid, Offset(fl + fw * i / 3, ft), Offset(fl + fw * i / 3, ft + fh), 1f)
                    drawLine(grid, Offset(fl, ft + fh * i / 3), Offset(fl + fw, ft + fh * i / 3), 1f)
                }
            }
            drawRect(scheme.onBackground.copy(alpha = 0.55f), Offset(fl, ft), Size(fw, fh), style = Stroke(1.dp.toPx()))
            drawCropMarks(scheme.onBackground, 12.dp.toPx(), 5.dp.toPx(), 1.5.dp.toPx(), fl, ft, fl + fw, ft + fh)
        }
    }
}

private fun displayScale(w: Float, h: Float, g: CropGeometry, margin: Float): Double =
    min((w - 2 * margin) / g.canvasW, (h - 2 * margin) / g.canvasH)
