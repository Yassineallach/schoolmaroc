package com.printscale.engine

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.awt.image.BufferedImage
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import javax.imageio.ImageIO
import kotlin.math.abs
import kotlin.random.Random

class CoreTest {
    private val roomy = DeviceBudget(heapBytesAvailable = 2L shl 30, freeDiskBytes = 50L shl 30)

    @Test fun printPixels() {
        val p = PrintMath.preset("24x36")!!.oriented(landscape = false)
        assertEquals(7200 to 10800, p.pixels(300))
        assertEquals(3600 to 5400, p.pixels(150))
        assertEquals(1500 to 2100, PrintMath.preset("5x7")!!.oriented(false).pixels(300))
        assertEquals(14, PrintMath.PRESETS.size)
        assertEquals(2.0 / 3.0, p.aspect, 1e-9)
        assertEquals(2400 to 3000, PrintSize(LengthUnit.CM.toInches(20.32), LengthUnit.CM.toInches(25.4)).pixels(300))
    }

    @Test fun ratioLabels() {
        assertEquals("1:1", PrintMath.ratioLabel(1024, 1024))
        assertEquals("2:3", PrintMath.ratioLabel(1024, 1536))
        assertEquals("16:9", PrintMath.ratioLabel(1920, 1080))
        assertEquals("≈4:5", PrintMath.ratioLabel(1001, 1252))
    }

    @Test fun plannerTypicalEtsyJob() {
        // 1024 x 1536 AI art -> 24 x 36 in at 300 DPI
        val plan = Planner.plan(1024, 1536, 7200, 10800, false, roomy, PrintTarget(PrintSize(24.0, 36.0), 300))
        assertTrue(plan.feasible)
        assertTrue(plan.useAi)
        assertEquals(4096, plan.aiW)
        assertEquals(7200.0 / 4096, plan.interpolationBeyondAi, 1e-9)
        assertEquals(4096 / 24.0, plan.aiDetailDpi!!, 1e-9)
        assertTrue(plan.warnings.any { it.contains("Lanczos interpolation") })
    }

    @Test fun plannerBlocksImpractical() {
        val tooBig = Planner.plan(4096, 4096, 32768, 32768, false, roomy)
        assertFalse(tooBig.feasible)
        val lowMem = Planner.plan(1024, 1024, 4096, 4096, false, DeviceBudget(32L shl 20, 50L shl 30))
        assertFalse(lowMem.feasible)
        val lowDisk = Planner.plan(1024, 1024, 8192, 8192, false, DeviceBudget(2L shl 30, 100L shl 20))
        assertFalse(lowDisk.feasible)
        val noAi = Planner.plan(3000, 3000, 2400, 2400, false, roomy)
        assertTrue(noAi.feasible)
        assertFalse(noAi.useAi)
    }

    @Test fun cropFillAndFit() {
        val fill = CropGeometry(1024, 1024, 2.0 / 3.0, FitMode.FILL, CropState())
        assertEquals(683, fill.outW)
        assertEquals(1024, fill.outH)
        assertTrue(fill.isPixelExact)
        val m = fill.matrix()
        // source centre lands on canvas centre, scale 1
        val cx = m[0] * 512 + m[1] * 512 + m[2]
        assertEquals(fill.outW / 2.0, cx, 1.0)
        assertEquals(1.0, m[0], 1e-9)

        val fit = CropGeometry(1024, 1024, 2.0 / 3.0, FitMode.FIT, CropState())
        assertEquals(1024, fit.outW)
        assertEquals(1536, fit.outH)

        // Pan beyond the edge is clamped to the image.
        val panned = CropGeometry(1024, 1024, 2.0 / 3.0, FitMode.FILL, CropState(panX = 5f))
        assertEquals((1024 - 683) / 2.0, panned.panPx, 1.0)

        // Quarter turn swaps dimensions; (0,0) maps to the top-right corner.
        val q = CropGeometry(400, 200, null, FitMode.FILL, CropState(quarterTurns = 1))
        assertEquals(200, q.outW)
        assertEquals(400, q.outH)
        val qm = q.matrix()
        assertEquals(200.0, qm[0] * 0 + qm[1] * 0 + qm[2], 1e-6)
        assertEquals(0.0, qm[3] * 0 + qm[4] * 0 + qm[5], 1e-6)

        // Straightened fill must stay inside the image: all canvas corners map inside the source.
        val st = CropGeometry(1000, 800, 1.0, FitMode.FILL, CropState(straightenDeg = 10f))
        val mm = st.matrix()
        val det = mm[0] * mm[4] - mm[1] * mm[3]
        for ((x, y) in listOf(0.0 to 0.0, st.outW.toDouble() to 0.0, 0.0 to st.outH.toDouble(), st.outW.toDouble() to st.outH.toDouble())) {
            val sx = (mm[4] * (x - mm[2]) - mm[1] * (y - mm[5])) / det
            val sy = (-mm[3] * (x - mm[2]) + mm[0] * (y - mm[5])) / det
            assertTrue("corner $x,$y -> $sx,$sy", sx >= -1 && sx <= 1001 && sy >= -1 && sy <= 801)
        }
    }

    private class Collect(val w: Int, val h: Int) : RowSink {
        val px = IntArray(w * h)
        override fun writeRow(y: Int, argb: IntArray) = System.arraycopy(argb, 0, px, y * w, w)
    }

    @Test fun resizerKeepsFlatColourAndAlpha() {
        val w = 37; val h = 23
        val src = IntArray(w * h) { 0xFF336699.toInt() }
        for (tw in listOf(37, 100, 11)) {
            val th = h * tw / w + 1
            val out = Collect(tw, th)
            var y = 0
            StreamingResizer(w, h, tw, th).run({ System.arraycopy(src, (y++) * w, it, 0, w) }, out, {})
            out.px.forEach { assertEquals(0xFF336699.toInt(), it) }
        }
        // a transparent pixel's black RGB must not leak into neighbours (premultiplied resampling)
        val a = IntArray(16 * 16) { if (it % 16 < 8) 0xFFFF0000.toInt() else 0x00000000 }
        val out = Collect(64, 64)
        var y = 0
        StreamingResizer(16, 16, 64, 64).run({ System.arraycopy(a, (y++) * 16, it, 0, 16) }, out, {})
        for (p in out.px) if ((p ushr 24) > 10) assertTrue("red stays red: ${Integer.toHexString(p)}", (p shr 16 and 0xFF) > 240)
    }

    @Test fun pngRoundTripWithDpiAndIcc() {
        val rnd = Random(1)
        for (alpha in listOf(false, true)) {
            val w = 53; val h = 31
            val px = IntArray(w * h) { i ->
                val a = if (alpha) rnd.nextInt(256) else 255
                (a shl 24) or (((i * 7) and 0xFF) shl 16) or (rnd.nextInt(256) shl 8) or ((i / w * 9) and 0xFF)
            }
            val fakeIcc = ByteArray(600) { (it % 251).toByte() }
            val bos = ByteArrayOutputStream()
            val wr = PngStreamWriter(bos, w, h, alpha, 300, if (alpha) fakeIcc else null)
            for (y in 0 until h) wr.writeRow(y, px.copyOfRange(y * w, (y + 1) * w))
            wr.finish()
            val bytes = bos.toByteArray()
            val img = ImageIO.read(ByteArrayInputStream(bytes))
            assertEquals(w, img.width); assertEquals(h, img.height)
            for (y in 0 until h) for (x in 0 until w) {
                val exp = if (alpha) px[y * w + x] else px[y * w + x] or (0xFF shl 24)
                if (alpha && (exp ushr 24) == 0) continue // Java2D drops colour of fully transparent pixels
                assertEquals("pixel $x,$y", exp, img.getRGB(x, y))
            }
            val s = String(bytes, Charsets.ISO_8859_1)
            assertTrue(s.contains("pHYs"))
            if (alpha) assertArrayEquals(fakeIcc, IccExtractor.extract(bytes)) else assertTrue(s.contains("sRGB"))
        }
    }

    @Test fun jpegDpiPatch() {
        val img = BufferedImage(20, 10, BufferedImage.TYPE_INT_RGB)
        val raw = ByteArrayOutputStream().also { ImageIO.write(img, "jpg", it) }.toByteArray()
        val patched = ByteArrayOutputStream()
        JfifDpiOutputStream(patched, 300).use { it.write(raw) }
        val p = patched.toByteArray()
        assertEquals(raw.size, p.size)
        assertEquals(1, p[13].toInt())
        assertEquals(300, ((p[14].toInt() and 0xFF) shl 8) or (p[15].toInt() and 0xFF))
        assertNotNull(ImageIO.read(ByteArrayInputStream(p)))
    }

    @Test fun naming() {
        assertEquals("Artwork_4x_7200x10800_300DPI.png", FileNaming.suggest(null, 4.0, 7200, 10800, 300, "png"))
        assertEquals("sunset_v2_7x_7200x10800.jpg", FileNaming.suggest("sunset v2!.jpeg", 7.03, 7200, 10800, null, "jpg"))
        assertEquals("My print.png", FileNaming.finalize("My print.png", "png"))
    }

    @Test fun alphaBleedFillsTransparentRgb() {
        val b = PixelBuffer(4, 1, intArrayOf(0xFF00FF00.toInt(), 0, 0, 0))
        AlphaBleed.apply(b)
        assertEquals(0x0000FF00, b.argb[3])
        assertEquals(0xFF00FF00.toInt(), b.argb[0])
    }

    @Test fun bicubicPreservesFlat() {
        val p = FloatArray(6 * 5) { 0.4f }
        val o = Filters.bicubic4x(p, 6, 5)
        o.forEach { assertTrue(abs(it - 0.4f) < 1e-5) }
    }
}
