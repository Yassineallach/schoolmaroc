package com.printscale.ai.imaging

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.BitmapRegionDecoder
import android.graphics.Canvas
import android.graphics.ColorSpace
import android.graphics.ImageDecoder
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.Rect
import com.printscale.engine.CropGeometry
import com.printscale.engine.PixelBuffer
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.nio.ByteBuffer
import kotlin.math.max
import kotlin.math.roundToInt
import kotlin.math.sqrt

object Imaging {
    /** Decoding limit for processing. Larger images are reduced on import (AI art is far below this). */
    const val MAX_WORK_PIXELS = 24_000_000L

    fun workSize(w: Int, h: Int): Pair<Int, Int> {
        val px = w.toLong() * h
        if (px <= MAX_WORK_PIXELS) return w to h
        val s = sqrt(MAX_WORK_PIXELS.toDouble() / px)
        return max(1, (w * s).toInt()) to max(1, (h * s).toInt())
    }

    /**
     * Decodes with EXIF orientation applied (ImageDecoder does this) into a software ARGB_8888
     * bitmap, keeping the file's colour space.
     */
    fun decode(file: File, targetW: Int? = null, targetH: Int? = null): Bitmap {
        val bmp = ImageDecoder.decodeBitmap(ImageDecoder.createSource(file)) { decoder, _, _ ->
            decoder.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
            decoder.memorySizePolicy = ImageDecoder.MEMORY_POLICY_DEFAULT
            if (targetW != null && targetH != null) decoder.setTargetSize(targetW, targetH)
        }
        return to8888(bmp)
    }

    /** Fast reduced decode for on-screen previews. */
    fun decodePreview(file: File, maxSide: Int): Bitmap {
        val bmp = ImageDecoder.decodeBitmap(ImageDecoder.createSource(file)) { decoder, info, _ ->
            decoder.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
            val w = info.size.width
            val h = info.size.height
            val s = maxSide.toDouble() / max(w, h)
            if (s < 1) decoder.setTargetSize(max(1, (w * s).roundToInt()), max(1, (h * s).roundToInt()))
        }
        return to8888(bmp)
    }

    private fun to8888(bmp: Bitmap): Bitmap {
        if (bmp.config == Bitmap.Config.ARGB_8888) return bmp
        // 16-bit and F16 images: draw into 8-bit sRGB. Print output here is 8 bits per channel.
        val out = Bitmap.createBitmap(bmp.width, bmp.height, Bitmap.Config.ARGB_8888, true, ColorSpace.get(ColorSpace.Named.SRGB))
        Canvas(out).drawBitmap(bmp, 0f, 0f, Paint(Paint.FILTER_BITMAP_FLAG))
        bmp.recycle()
        return out
    }

    fun isSrgb(cs: ColorSpace?): Boolean = cs == null || cs == ColorSpace.get(ColorSpace.Named.SRGB)

    /**
     * Renders the crop/fit canvas. Pure crops are pixel copies; only straightening resamples.
     * The result keeps [colorSpace], so pixel values stay in the source's profile.
     */
    fun renderPrepared(src: Bitmap, geom: CropGeometry, background: Int?, colorSpace: ColorSpace): Bitmap {
        val out = Bitmap.createBitmap(geom.outW, geom.outH, Bitmap.Config.ARGB_8888, true, colorSpace)
        val canvas = Canvas(out)
        if (background != null) canvas.drawColor(background)
        val m = geom.matrix()
        val matrix = Matrix().apply {
            setValues(floatArrayOf(m[0].toFloat(), m[1].toFloat(), m[2].toFloat(), m[3].toFloat(), m[4].toFloat(), m[5].toFloat(), 0f, 0f, 1f))
        }
        val paint = Paint().apply { isFilterBitmap = !geom.isPixelExact; isAntiAlias = !geom.isPixelExact }
        canvas.drawBitmap(src, matrix, paint)
        return out
    }

    /**
     * Copies raw pixels without colour conversion (getPixels would convert to sRGB),
     * then un-premultiplies.
     */
    fun toPixelBuffer(bmp: Bitmap): PixelBuffer {
        val w = bmp.width
        val h = bmp.height
        val buf = ByteBuffer.allocateDirect(w * h * 4)
        bmp.copyPixelsToBuffer(buf)
        buf.rewind()
        val out = IntArray(w * h)
        for (i in 0 until w * h) {
            val r = buf.get().toInt() and 0xFF
            val g = buf.get().toInt() and 0xFF
            val b = buf.get().toInt() and 0xFF
            val a = buf.get().toInt() and 0xFF
            out[i] = when (a) {
                255 -> (0xFF shl 24) or (r shl 16) or (g shl 8) or b
                0 -> 0
                else -> (a shl 24) or (minOf(255, (r * 255 + a / 2) / a) shl 16) or
                    (minOf(255, (g * 255 + a / 2) / a) shl 8) or minOf(255, (b * 255 + a / 2) / a)
            }
        }
        return PixelBuffer(w, h, out)
    }

    fun toBitmap(p: PixelBuffer, colorSpace: ColorSpace): Bitmap {
        val buf = ByteBuffer.allocateDirect(p.width * p.height * 4)
        for (px in p.argb) {
            val a = px ushr 24
            val r = (px shr 16) and 0xFF
            val g = (px shr 8) and 0xFF
            val b = px and 0xFF
            buf.put((r * a / 255).toByte()); buf.put((g * a / 255).toByte()); buf.put((b * a / 255).toByte()); buf.put(a.toByte())
        }
        buf.rewind()
        val bmp = Bitmap.createBitmap(p.width, p.height, Bitmap.Config.ARGB_8888, true, colorSpace)
        bmp.copyPixelsFromBuffer(buf)
        return bmp
    }

    fun savePng(bmp: Bitmap, file: File) {
        FileOutputStream(file).use { bmp.compress(Bitmap.CompressFormat.PNG, 100, it) }
    }

    fun scaleToFit(bmp: Bitmap, maxSide: Int): Bitmap {
        val s = maxSide.toDouble() / max(bmp.width, bmp.height)
        if (s >= 1) return bmp
        return Bitmap.createScaledBitmap(bmp, max(1, (bmp.width * s).roundToInt()), max(1, (bmp.height * s).roundToInt()), true)
    }

    /** Decodes a rectangle of a (possibly huge) PNG without loading the rest. */
    @Suppress("DEPRECATION")
    fun decodeRegion(file: File, rect: Rect): Bitmap? = runCatching {
        FileInputStream(file).use { stream ->
            val dec = BitmapRegionDecoder.newInstance(stream, false) ?: return null
            try {
                dec.decodeRegion(rect, BitmapFactory.Options().apply { inPreferredConfig = Bitmap.Config.ARGB_8888 })
            } finally {
                dec.recycle()
            }
        }
    }.getOrNull()
}

/**
 * Guard for decoders that skip EXIF orientation: if the decoded size is the expected size
 * transposed, rotate by the EXIF tag; if it is off for any other reason, scale to expected.
 */
fun Bitmap.orientedTo(expectedW: Int, expectedH: Int, file: File): Bitmap {
    if (width == expectedW && height == expectedH) return this
    if (width == expectedH && height == expectedW) {
        val o = runCatching {
            androidx.exifinterface.media.ExifInterface(file.path).rotationDegrees
        }.getOrDefault(90)
        val m = Matrix().apply { postRotate(if (o == 0) 90f else o.toFloat()) }
        val r = Bitmap.createBitmap(this, 0, 0, width, height, m, true)
        if (r != this) recycle()
        return r
    }
    val s = Bitmap.createScaledBitmap(this, expectedW, expectedH, true)
    if (s != this) recycle()
    return s
}
