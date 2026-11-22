package com.printscale.ai.ui.prep

import android.graphics.Bitmap
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.FilterQuality
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.ImageShader
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.ShaderBrush
import androidx.compose.ui.graphics.TileMode
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.graphics.drawscope.clipPath
import androidx.compose.ui.graphics.drawscope.clipRect
import androidx.compose.ui.graphics.Matrix
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.withTransform
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import com.printscale.engine.Placement
import kotlin.math.min
import kotlin.math.roundToInt
import kotlin.random.Random

/**
 * Visualisation only: draws the prepared artwork on a garment at true scale. Nothing here
 * touches the exported print file.
 */
@Composable
fun GarmentPreview(
    art: Bitmap,
    garment: Garment,
    color: GarmentColor,
    canvasWIn: Double,
    canvasHIn: Double,
    placement: Placement,
    collarIn: Double,
    showPrintArea: Boolean,
    height: Dp = 420.dp,
) {
    val image = remember(art) { art.asImageBitmap() }
    val noise = remember { fabricNoise() }
    val outline = remember(garment) { garment.outline() }
    val hood = remember(garment) { garment.hood() }
    val details = remember(garment) { garment.details() }

    Canvas(Modifier.fillMaxWidth().height(height).semantics {
        contentDescription = "${color.name} ${garment.label.lowercase()} with the print placed ${collarIn} inches below the collar. Preview only."
    }) {
        val k = min(size.width / garment.widthIn, size.height / garment.heightIn) * 0.94f
        val ox = (size.width - garment.widthIn * k) / 2
        val oy = (size.height - garment.heightIn * k) / 2
        val shade = if (color.dark) Color.White else Color.Black
        withTransform({ translate(ox, oy); scale(k, k, Offset.Zero) }) {
            hood?.let { h ->
                drawPath(h, color.color)
                drawPath(h, Brush.verticalGradient(listOf(shade.copy(alpha = 0.10f), Color.Transparent), 0f, 8f))
            }
            drawPath(outline, color.color)
            clipPath(outline) {
                // fabric: soft side shading, two fold shadows and a fine knit texture
                drawRect(Brush.horizontalGradient(
                    0f to Color.Black.copy(alpha = 0.16f), 0.18f to Color.Transparent, 0.82f to Color.Transparent, 1f to Color.Black.copy(alpha = 0.16f),
                    startX = garment.bodyLeft, endX = garment.bodyRight), Offset.Zero, Size(garment.widthIn, garment.heightIn))

                // the print: canvas centred on the chest, its top `collarIn` below the collar seam
                val canvasLeft = (garment.widthIn - canvasWIn.toFloat()) / 2
                val canvasTop = garment.collarCenterY + collarIn.toFloat()
                if (showPrintArea) {
                    val (mw, mh) = garment.maxPrintIn
                    drawRect(shade.copy(alpha = 0.35f), Offset((garment.widthIn - mw.toFloat()) / 2, canvasTop), Size(mw.toFloat(), mh.toFloat()),
                        style = Stroke(0.06f, pathEffect = PathEffect.dashPathEffect(floatArrayOf(0.4f, 0.25f))))
                }
                val ax = canvasLeft + placement.xIn.toFloat()
                val ay = canvasTop + placement.yIn.toFloat()
                // only what is inside the print area prints
                clipRect(canvasLeft, canvasTop, canvasLeft + canvasWIn.toFloat(), canvasTop + canvasHIn.toFloat()) {
                    drawArtInches(image, ax, ay, placement.wIn.toFloat(), placement.hIn.toFloat(), k)
                }
                // folds drawn over the print so it sits in the fabric
                drawRect(Brush.radialGradient(listOf(Color.Black.copy(alpha = 0.10f), Color.Transparent),
                    Offset(garment.widthIn * 0.33f, garment.heightIn * 0.62f), garment.widthIn * 0.22f), Offset.Zero, Size(garment.widthIn, garment.heightIn))
                drawRect(Brush.radialGradient(listOf(Color.White.copy(alpha = if (color.dark) 0.05f else 0.12f), Color.Transparent),
                    Offset(garment.widthIn * 0.6f, garment.heightIn * 0.35f), garment.widthIn * 0.25f), Offset.Zero, Size(garment.widthIn, garment.heightIn))
                details.forEach { (p, a) -> drawPath(p, shade.copy(alpha = a)) }
            }
            drawPath(outline, Color.Black.copy(alpha = 0.25f), style = Stroke(0.05f))
        }
        // knit texture in screen pixels, so it stays fine at any size
        val screenOutline = Path().apply {
            addPath(outline)
            transform(Matrix().apply { scale(k, k); })
            translate(Offset(ox, oy))
        }
        clipPath(screenOutline) {
            drawRect(ShaderBrush(ImageShader(noise, TileMode.Repeated, TileMode.Repeated)), alpha = 0.6f)
        }
    }
}

/** Draws in inch units; the image is sampled at the on-screen size for a clean result. */
private fun androidx.compose.ui.graphics.drawscope.DrawScope.drawArtInches(img: ImageBitmap, x: Float, y: Float, w: Float, h: Float, k: Float) {
    if (w <= 0 || h <= 0) return
    withTransform({ scale(1 / k, 1 / k, Offset.Zero) }) {
        drawImage(img, IntOffset.Zero, IntSize(img.width, img.height), IntOffset((x * k).roundToInt(), (y * k).roundToInt()),
            IntSize((w * k).roundToInt().coerceAtLeast(1), (h * k).roundToInt().coerceAtLeast(1)), filterQuality = FilterQuality.Medium)
    }
}

/** Small tileable knit-like noise, drawn once. */
private fun fabricNoise(): ImageBitmap {
    val n = 48
    val b = Bitmap.createBitmap(n, n, Bitmap.Config.ARGB_8888)
    val r = Random(11)
    for (y in 0 until n) for (x in 0 until n) {
        val v = if ((x + y) % 2 == 0) 0 else 255
        b.setPixel(x, y, ((6 + r.nextInt(10)) shl 24) or (v shl 16) or (v shl 8) or v)
    }
    return b.asImageBitmap()
}
