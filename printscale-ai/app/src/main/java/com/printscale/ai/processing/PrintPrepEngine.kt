package com.printscale.ai.processing

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.ColorSpace
import android.graphics.Paint
import com.printscale.ai.data.ImportedImage
import com.printscale.ai.imaging.Imaging
import com.printscale.ai.imaging.orientedTo
import com.printscale.engine.AiCutout
import com.printscale.engine.OrtMaskModel
import com.printscale.engine.PixelBuffer
import com.printscale.engine.PixelPlacement
import com.printscale.engine.PlainBackground
import com.printscale.engine.PngStreamReader
import com.printscale.engine.PngStreamWriter
import com.printscale.engine.PreviewSink
import com.printscale.engine.PrintRenderer
import com.printscale.engine.AlphaStats
import java.io.BufferedOutputStream
import java.io.File
import java.io.FileOutputStream
import kotlin.math.max
import kotlin.math.min
import kotlin.math.roundToInt

enum class BackgroundMode(val label: String) {
    KEEP("Keep"),
    PLAIN("Plain colour"),
    AI("AI cutout"),
}

/** Artwork ready for placement: the full-resolution file plus what the UI needs to show it. */
data class PreparedArtwork(val file: File, val width: Int, val height: Int, val alpha: AlphaStats.Stats, val preview: Bitmap)

/**
 * Print preparation on the device. Works on copies: the imported original is never changed, and
 * each background/trim result is written to its own file in the job folder.
 */
class PrintPrepEngine(private val context: Context) {
    private val srgb = ColorSpace.get(ColorSpace.Named.SRGB)

    fun dir(importId: String) = File(context.filesDir, "prep/$importId").apply { mkdirs() }

    /**
     * Decodes the original (camera orientation applied) into sRGB, the colour space DTF and DTG
     * RIP software expects.
     */
    fun loadSource(info: ImportedImage, original: File): PixelBuffer {
        var bmp = Imaging.decode(original, info.workW, info.workH).orientedTo(info.workW, info.workH, original)
        if (!Imaging.isSrgb(bmp.colorSpace)) {
            val conv = Bitmap.createBitmap(bmp.width, bmp.height, Bitmap.Config.ARGB_8888, true, srgb)
            Canvas(conv).drawBitmap(bmp, 0f, 0f, Paint(Paint.FILTER_BITMAP_FLAG))
            bmp.recycle()
            bmp = conv
        }
        val p = Imaging.toPixelBuffer(bmp)
        bmp.recycle()
        return p
    }

    fun previewBitmap(p: PixelBuffer, maxSide: Int = 1600): Bitmap {
        val sink = PreviewSink(p.width, p.height, maxSide)
        val row = IntArray(p.width)
        for (y in 0 until p.height) { System.arraycopy(p.argb, y * p.width, row, 0, p.width); sink.writeRow(y, row) }
        return Imaging.toBitmap(sink.result, srgb)
    }

    /**
     * Applies the background choice and trimming, writes the result next to the job and returns it.
     * @param checkCancel throws if the user changed settings meanwhile.
     */
    fun prepare(
        importId: String, source: PixelBuffer, mode: BackgroundMode, tolerance: Float, enclosed: Boolean, trim: Boolean,
        checkCancel: () -> Unit,
    ): PreparedArtwork {
        var art = when (mode) {
            BackgroundMode.KEEP -> source
            BackgroundMode.PLAIN -> PlainBackground.remove(source, tolerance, enclosed).pixels
            BackgroundMode.AI -> {
                val bytes = context.assets.open("models/u2netp.onnx").use { it.readBytes() }
                OrtMaskModel(bytes, Runtime.getRuntime().availableProcessors().coerceIn(1, 4)).use { AiCutout.apply(source, it) }
            }
        }
        checkCancel()
        if (trim) {
            AlphaStats.visibleBounds(art)?.let { b ->
                // keep a hairline of padding so anti-aliased edges are not shaved
                val pad = max(2, (min(art.width, art.height) * 0.003).roundToInt())
                val box = intArrayOf(max(0, b[0] - pad), max(0, b[1] - pad), min(art.width, b[2] + pad), min(art.height, b[3] + pad))
                if (box[0] > 0 || box[1] > 0 || box[2] < art.width || box[3] < art.height) art = AlphaStats.crop(art, box)
            }
        }
        checkCancel()
        val stats = AlphaStats.of(art)
        val file = File(dir(importId), "artwork_${mode.name.lowercase()}.png")
        BufferedOutputStream(FileOutputStream(file), 1 shl 20).use { out ->
            val png = PngStreamWriter(out, art.width, art.height, stats.hasTransparency, null, null, compressionLevel = 1)
            val row = IntArray(art.width)
            for (y in 0 until art.height) { System.arraycopy(art.argb, y * art.width, row, 0, art.width); png.writeRow(y, row) }
            png.finish()
        }
        return PreparedArtwork(file, art.width, art.height, stats, previewBitmap(art))
    }

    fun loadArtwork(file: File): PixelBuffer = PngStreamReader(file.inputStream()).use { r ->
        val p = PixelBuffer(r.width, r.height)
        val row = IntArray(r.width)
        for (y in 0 until r.height) { r.readRow(row); System.arraycopy(row, 0, p.argb, y * r.width, r.width) }
        p
    }

    /** Writes the print file: a transparent PNG at exact print pixels with the DPI embedded. */
    fun export(art: PreparedArtwork, px: PixelPlacement, dpi: Int, solidEdges: Boolean, compressionLevel: Int, out: File, checkCancel: () -> Unit) {
        val pixels = loadArtwork(art.file)
        BufferedOutputStream(FileOutputStream(out), 1 shl 20).use { os ->
            val png = PngStreamWriter(os, px.canvasW, px.canvasH, true, dpi, null, compressionLevel)
            PrintRenderer.render(pixels, px, png, if (solidEdges) 128 else null, checkCancel)
        }
    }
}
