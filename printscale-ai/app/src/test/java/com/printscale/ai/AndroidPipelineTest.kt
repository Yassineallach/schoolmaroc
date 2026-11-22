package com.printscale.ai

import android.graphics.BitmapFactory
import android.graphics.ColorSpace
import androidx.exifinterface.media.ExifInterface
import androidx.work.ListenableWorker
import androidx.work.testing.WorkManagerTestInitHelper
import com.printscale.ai.data.Paths
import com.printscale.ai.export.ExportFormat
import com.printscale.ai.export.ExportOptions
import com.printscale.ai.imaging.Imaging
import com.printscale.ai.imaging.orientedTo
import com.printscale.engine.CropGeometry
import com.printscale.engine.CropState
import com.printscale.engine.FitMode
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35])
class AndroidPipelineTest {
    @Before fun setup() {
        WorkManagerTestInitHelper.initializeTestWorkManager(Fixtures.app)
        Fixtures.realisticDevice()
    }

    @Test fun importsTransparentPng() = runBlocking {
        val f = Fixtures.writePng(Fixtures.artwork(320, 240, transparent = true), "alpha.png")
        val info = Fixtures.import(f)
        assertEquals(320, info.width); assertEquals(240, info.height)
        assertTrue(info.hasAlpha)
        assertEquals("PNG", info.formatLabel)
        assertTrue(Fixtures.app.graph.imports.thumb(info.id).exists())
    }

    @Test fun importsOpaquePngAsOpaque() = runBlocking {
        val info = Fixtures.import(Fixtures.writePng(Fixtures.artwork(200, 200), "opaque.png"))
        assertFalse(info.hasAlpha)
    }

    @Test fun exifRotationIsApplied() = runBlocking {
        // stored landscape 300x200, EXIF says rotate 90: the artwork is really portrait 200x300
        val f = Fixtures.writeJpeg(Fixtures.artwork(300, 200), "rot.jpg", ExifInterface.ORIENTATION_ROTATE_90)
        val info = Fixtures.import(f)
        assertEquals(200, info.width); assertEquals(300, info.height)
        assertTrue(info.exifRotated)
        val bmp = Imaging.decode(f, info.workW, info.workH).orientedTo(info.workW, info.workH, f)
        assertEquals(200, bmp.width); assertEquals(300, bmp.height)
    }

    @Test fun rejectsNonImage() = runBlocking {
        val f = java.io.File(Fixtures.app.cacheDir, "notes.png").apply { writeText("not an image") }
        val e = runCatching { Fixtures.import(f) }.exceptionOrNull()
        assertNotNull(e)
        assertTrue(e!!.message!!.contains("not an image"))
    }

    @Test fun preparedCropAndPixelRoundTrip() {
        val src = Fixtures.artwork(400, 300, transparent = true)
        val geom = CropGeometry(400, 300, 1.0, FitMode.FILL, CropState())
        val prepared = Imaging.renderPrepared(src, geom, null, ColorSpace.get(ColorSpace.Named.SRGB))
        assertEquals(300, prepared.width); assertEquals(300, prepared.height)
        // pure crop must be a pixel copy: canvas (0,0) is source (50,0)
        assertEquals(src.getPixel(50 + 150, 150), prepared.getPixel(150, 150))
        val buf = Imaging.toPixelBuffer(prepared)
        val back = Imaging.toBitmap(buf, ColorSpace.get(ColorSpace.Named.SRGB))
        assertEquals(prepared.getPixel(150, 120), back.getPixel(150, 120))
        assertEquals(0, buf.argb[0] ushr 24) // corner of transparent artwork stays transparent
    }

    @Test fun workerProducesPrintFileAndHistory() = runBlocking {
        val info = Fixtures.import(Fixtures.writePng(Fixtures.artwork(1000, 1250), "big.png"))
        // 8 x 10 in at 300 DPI is 2400 x 3000: larger than the source, so normally AI. Here we
        // ask for a smaller file to stay on the Lanczos path that runs on the JVM.
        val (id, result) = Fixtures.runJob(Fixtures.app, Fixtures.spec(info.id, 800, 1000, aspect = 0.8, print = Fixtures.print8x10))
        assertTrue("worker result $result", result is ListenableWorker.Result.Success)
        val paths = Paths(Fixtures.app)
        val opts = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(paths.jobMaster(id).path, opts)
        assertEquals(800, opts.outWidth); assertEquals(1000, opts.outHeight)
        val bytes = paths.jobMaster(id).readBytes()
        assertTrue(String(bytes, 0, 200, Charsets.ISO_8859_1).contains("pHYs"))
        assertTrue(paths.jobPreview(id).exists() && paths.jobBefore(id).exists() && paths.jobSource(id).exists())
        val item = Fixtures.app.graph.history.get(id)!!
        assertEquals(1000, item.preparedW); assertEquals(1250, item.preparedH)
        assertEquals(300, item.dpi)
    }

    @Test fun failedJobCleansUp() = runBlocking {
        val (id, result) = Fixtures.runJob(Fixtures.app, Fixtures.spec("missing-import", 100, 100))
        assertTrue(result is ListenableWorker.Result.Failure)
        assertFalse(Paths(Fixtures.app).jobMaster(id).exists())
    }

    @Test fun exportsJpegWithDpiAndPngCopy() = runBlocking {
        val info = Fixtures.import(Fixtures.writePng(Fixtures.artwork(600, 600, transparent = true), "t.png"))
        val (id, _) = Fixtures.runJob(Fixtures.app, Fixtures.spec(info.id, 500, 500, print = Fixtures.print8x10))
        val item = Fixtures.app.graph.history.get(id)!!
        assertTrue(item.hasAlpha)
        val jpg = Fixtures.app.graph.exporter.render(item, ExportOptions(ExportFormat.JPEG, 95, fileName = "a.jpg"))
        val b = jpg.readBytes()
        assertEquals(0xFF.toByte(), b[0]); assertEquals(0xD8.toByte(), b[1])
        if (String(b, 6, 4, Charsets.ISO_8859_1) == "JFIF") {
            assertEquals(1, b[13].toInt())
            assertEquals(300, ((b[14].toInt() and 0xFF) shl 8) or (b[15].toInt() and 0xFF))
        }
        val decoded = BitmapFactory.decodeFile(jpg.path)
        assertEquals(500, decoded.width)
        // transparent corner flattened onto white
        val corner = decoded.getPixel(2, 2)
        assertTrue((corner and 0xFF) > 240)
        val png = Fixtures.app.graph.exporter.render(item, ExportOptions(ExportFormat.PNG, fileName = "a.png"))
        assertTrue(png.readBytes().contentEquals(Paths(Fixtures.app).jobMaster(id).readBytes()))
        val webp = Fixtures.app.graph.exporter.render(item, ExportOptions(ExportFormat.WEBP, webpLossless = true, fileName = "a.webp"))
        assertEquals(500, BitmapFactory.decodeFile(webp.path).width)
    }
}
