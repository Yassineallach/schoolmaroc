package com.printscale.ai.ui.result

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.Orientation
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.gestures.draggable
import androidx.compose.foundation.gestures.rememberDraggableState
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.semantics.ProgressBarRangeInfo
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.progressBarRangeInfo
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.semantics.setProgress
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import com.printscale.ai.ui.theme.LocalExtras
import kotlin.math.floor
import kotlin.math.min
import kotlin.math.roundToInt

enum class CompareMode(val label: String) { SPLIT("Compare"), ORIGINAL("Original"), ENHANCED("Enhanced") }

/**
 * Both images are drawn into the same rectangle with the same bilinear filter, so the only
 * difference you see is the processing. The "original" is the prepared crop, enlarged on screen.
 */
@Composable
fun CompareViewer(
    before: ImageBitmap,
    after: ImageBitmap,
    mode: CompareMode,
    transparent: Boolean,
    modifier: Modifier = Modifier,
    onTapImage: ((Float, Float) -> Unit)? = null,
) {
    var split by remember { mutableFloatStateOf(0.5f) }
    var scale by remember(before, after) { mutableFloatStateOf(1f) }
    var pan by remember(before, after) { mutableStateOf(Offset.Zero) }
    val scheme = MaterialTheme.colorScheme
    val checker = LocalExtras.current.checker
    val density = LocalDensity.current

    BoxWithConstraints(modifier.clipToBounds().background(scheme.surfaceContainerLowest)) {
        val wPx = constraints.maxWidth.toFloat()
        val hPx = constraints.maxHeight.toFloat()
        val fit = min(wPx / after.width, hPx / after.height)
        fun imageRect(): Pair<Offset, Float> {
            val s = fit * scale
            val iw = after.width * s
            val ih = after.height * s
            return Offset((wPx - iw) / 2 + pan.x, (hPx - ih) / 2 + pan.y) to s
        }

        Canvas(
            Modifier.fillMaxSize()
                .semantics { contentDescription = "Before and after comparison. Pinch to zoom, drag to pan." }
                .pointerInput(before, after) {
                    detectTransformGestures { _, p, z, _ ->
                        val ns = (scale * z).coerceIn(1f, 12f)
                        scale = ns
                        val maxX = (after.width * fit * ns - wPx).coerceAtLeast(0f) / 2
                        val maxY = (after.height * fit * ns - hPx).coerceAtLeast(0f) / 2
                        pan = Offset((pan.x + p.x).coerceIn(-maxX, maxX), (pan.y + p.y).coerceIn(-maxY, maxY))
                    }
                }
                .pointerInput(onTapImage, before, after) {
                    detectTapGestures(
                        onDoubleTap = { scale = 1f; pan = Offset.Zero },
                        onTap = { pos ->
                            val (o, s) = imageRect()
                            val nx = (pos.x - o.x) / (after.width * s)
                            val ny = (pos.y - o.y) / (after.height * s)
                            if (nx in 0f..1f && ny in 0f..1f) onTapImage?.invoke(nx, ny)
                        },
                    )
                },
        ) {
            val (o, s) = imageRect()
            val dstW = (after.width * s).roundToInt()
            val dstH = (after.height * s).roundToInt()
            val dstOff = IntOffset(o.x.roundToInt(), o.y.roundToInt())
            val dstSize = IntSize(dstW, dstH)
            if (transparent) {
                // checkerboard under transparent artwork, visible cells only
                val cell = 12.dp.toPx()
                val x1 = min(o.x + dstW, size.width)
                val y1 = min(o.y + dstH, size.height)
                var r = floor((maxOf(o.y, 0f) - o.y) / cell).toInt()
                while (o.y + r * cell < y1) {
                    var c = floor((maxOf(o.x, 0f) - o.x) / cell).toInt()
                    while (o.x + c * cell < x1) {
                        if ((r + c) % 2 == 0) drawRect(checker, Offset(o.x + c * cell, o.y + r * cell), androidx.compose.ui.geometry.Size(cell, cell))
                        c++
                    }
                    r++
                }
            }
            val divider = size.width * split
            if (mode != CompareMode.ORIGINAL) {
                drawImage(after, IntOffset.Zero, IntSize(after.width, after.height), dstOff, dstSize, filterQuality = FilterQuality.Low)
            }
            if (mode == CompareMode.ORIGINAL) {
                drawImage(before, IntOffset.Zero, IntSize(before.width, before.height), dstOff, dstSize, filterQuality = FilterQuality.Low)
            } else if (mode == CompareMode.SPLIT) {
                clipRect(0f, 0f, divider, size.height) {
                    drawImage(before, IntOffset.Zero, IntSize(before.width, before.height), dstOff, dstSize, filterQuality = FilterQuality.Low)
                }
                drawLine(Color.White, Offset(divider, 0f), Offset(divider, size.height), 2.dp.toPx())
                drawLine(Color.Black.copy(alpha = 0.35f), Offset(divider + 2.dp.toPx(), 0f), Offset(divider + 2.dp.toPx(), size.height), 1.dp.toPx())
            }
        }

        if (mode == CompareMode.SPLIT) {
            val handleX = with(density) { (wPx * split).toDp() }
            Box(
                Modifier.offset(x = handleX - 22.dp).width(44.dp).fillMaxHeight()
                    .semantics {
                        contentDescription = "Comparison divider"
                        progressBarRangeInfo = ProgressBarRangeInfo(split, 0f..1f)
                        setProgress { v -> split = v.coerceIn(0f, 1f); true }
                    }
                    .draggable(rememberDraggableState { d -> split = (split + d / wPx).coerceIn(0f, 1f) }, Orientation.Horizontal),
                contentAlignment = Alignment.Center,
            ) {
                Box(Modifier.size(28.dp).background(Color.White, RoundedCornerShape(6.dp)), contentAlignment = Alignment.Center) {
                    Text("⇆", color = Color.Black, style = MaterialTheme.typography.labelLarge)
                }
            }
        }
        // ORIGINAL | ENHANCED indicator
        val labelMod = Modifier.padding(10.dp).background(Color.Black.copy(alpha = 0.6f), RoundedCornerShape(4.dp))
            .padding(horizontal = 7.dp, vertical = 3.dp)
        if (mode != CompareMode.ENHANCED) {
            Text("ORIGINAL", color = Color.White, style = MaterialTheme.typography.labelSmall, modifier = labelMod.align(Alignment.TopStart))
        }
        if (mode != CompareMode.ORIGINAL) {
            Text("ENHANCED", color = Color.White, style = MaterialTheme.typography.labelSmall, modifier = labelMod.align(Alignment.TopEnd))
        }
    }
}
