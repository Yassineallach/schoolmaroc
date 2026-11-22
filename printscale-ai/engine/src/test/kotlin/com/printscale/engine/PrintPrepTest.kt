package com.printscale.engine

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.awt.Color
import java.awt.RenderingHints
import java.awt.image.BufferedImage
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import javax.imageio.ImageIO
import kotlin.math.abs
import kotlin.random.Random

class PrintPrepTest {
    private class Collect(val w: Int, val h: Int) : RowSink {
        val px = IntArray(w * h)
        var rows = 0
        var finished = false
        override fun writeRow(y: Int, argb: IntArray) { assertEquals(rows, y); System.arraycopy(argb, 0, px, y * w, w); rows++ }
        override fun finish() { finished = true }
    }

    @Test fun calculatorExamplesFromTheBrief() {
        assertEquals(2400, PrintMath.pixels(8.0, 300))
        assertEquals(3000, PrintMath.pixels(10.0, 300))
        assertEquals(3600, PrintMath.pixels(12.0, 300))
        assertEquals(4800, PrintMath.pixels(16.0, 300))
        assertEquals(1800, PrintMath.pixels(12.0, 150))
        assertEquals(PrintMath.pixels(LengthUnit.CM.toInches(30.48), 300), 3600) // 30.48 cm = 12 in
    }

    @Test fun placementMath() {
        val p = PrintLayout.fit(12.0, 16.0, 2000, 1000)          // wide art on a tall canvas
        assertEquals(12.0, p.wIn, 1e-9); assertEquals(6.0, p.hIn, 1e-9)
        assertEquals(0.0, p.xIn, 1e-9); assertEquals(5.0, p.yIn, 1e-9)
        val top = PrintLayout.fit(12.0, 16.0, 2000, 1000, alignTop = true)
        assertEquals(0.0, top.yIn, 1e-9)
        val moved = p.copy(xIn = 3.0, yIn = 1.0)
        assertEquals(0.0, PrintLayout.centerHorizontally(moved, 12.0).xIn, 1e-9)
        assertEquals(5.0, PrintLayout.centerVertically(moved, 16.0).yIn, 1e-9)
        val px = PrintLayout.toPixels(12.0, 16.0, p, 300)
        assertEquals(PixelPlacement(3600, 4800, 0, 1500, 3600, 1800), px)
        assertEquals(0.0, PrintLayout.clippedFraction(p, 12.0, 16.0), 1e-9)
        assertEquals(0.5, PrintLayout.clippedFraction(p.copy(xIn = 6.0), 12.0, 16.0), 1e-9)
        val r = PrintLayout.resize(p, 6.0, 3.0)
        assertEquals(p.centerXIn, r.centerXIn, 1e-9); assertEquals(p.centerYIn, r.centerYIn, 1e-9)
    }

    @Test fun canvasCompositionMatchesDirectReference() {
        val rnd = Random(5)
        val art = PixelBuffer(10, 6, IntArray(60) { (rnd.nextInt(256) shl 24) or rnd.nextInt(1 shl 24) })
        for ((x, y) in listOf(5 to 3, -3 to 2, 14 to -2, 0 to 0, 25 to 3, 4 to 15)) {
            val px = PixelPlacement(20, 12, x, y, 10, 6) // same size: an exact copy is expected
            val out = Collect(20, 12)
            PrintRenderer.render(art, px, out)
            assertTrue(out.finished); assertEquals(12, out.rows)
            for (cy in 0 until 12) for (cx in 0 until 20) {
                val ax = cx - x; val ay = cy - y
                val expect = if (ax in 0 until 10 && ay in 0 until 6) art.argb[ay * 10 + ax] else 0
                assertEquals("offset $x,$y at $cx,$cy", expect, out.px[cy * 20 + cx])
            }
        }
    }

    @Test fun printFileHasExactPixelsTransparencyAndDpi() {
        // opaque disc on transparent ground, placed at 300 x 225 inside a 400 x 400 canvas
        val art = PixelBuffer(40, 30, IntArray(1200) { i -> val x = i % 40 - 20; val y = i / 40 - 15; if (x * x + y * y < 140) 0xFF2060C0.toInt() else 0 })
        val px = PixelPlacement(400, 400, 50, 80, 300, 225)
        val bos = ByteArrayOutputStream()
        PrintRenderer.render(art, px, PngStreamWriter(bos, 400, 400, true, 300, null))
        val bytes = bos.toByteArray()
        val img = ImageIO.read(ByteArrayInputStream(bytes))
        assertEquals(400, img.width); assertEquals(400, img.height)
        assertEquals(0, img.getRGB(0, 0) ushr 24)               // canvas corner clear
        assertEquals(0, img.getRGB(60, 90) ushr 24)             // artwork corner clear (it was transparent)
        assertEquals(255, img.getRGB(200, 192) ushr 24)         // centre of the disc solid
        assertTrue(String(bytes, 0, 100, Charsets.ISO_8859_1).contains("pHYs"))
    }

    @Test fun solidEdgesRemovePartialAlpha() {
        val art = PixelBuffer(4, 1, intArrayOf(0x10FF0000, 0x80FF0000.toInt(), 0x7FFF0000, 0xFFFF0000.toInt()))
        val out = Collect(4, 1)
        PrintRenderer.render(art, PixelPlacement(4, 1, 0, 0, 4, 1), out, solidAlphaCutoff = 128)
        assertEquals(listOf(0, 0xFFFF0000.toInt(), 0, 0xFFFF0000.toInt()), out.px.toList())
    }

    private fun design(bg: Color): PixelBuffer {
        val img = BufferedImage(200, 200, BufferedImage.TYPE_INT_ARGB)
        val g = img.createGraphics()
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
        g.color = bg; g.fillRect(0, 0, 200, 200)
        g.color = Color(30, 40, 90); g.fillOval(40, 40, 120, 120)   // ring...
        g.color = bg; g.fillOval(80, 80, 40, 40)                    // ...with a background-coloured hole
        g.dispose()
        val px = IntArray(200 * 200); img.getRGB(0, 0, 200, 200, px, 0, 200)
        return PixelBuffer(200, 200, px)
    }

    @Test fun plainBackgroundRemoval() {
        val src = design(Color.WHITE)
        val r = PlainBackground.remove(src)
        assertEquals(0xFFFFFFFF.toInt(), r.background)
        val a = { x: Int, y: Int -> r.pixels.argb[y * 200 + x] ushr 24 }
        assertEquals(0, a(5, 5))          // background gone
        assertEquals(255, a(60, 100))      // ring kept
        assertEquals(255, a(100, 100))     // hole not connected to the border: kept by default
        val enclosed = PlainBackground.remove(src, enclosed = true)
        assertEquals(0, enclosed.pixels.argb[100 * 200 + 100] ushr 24)
        // anti-aliased edge: partial alpha, and the white is un-mixed so no light fringe remains
        var partial = 0
        for (p in r.pixels.argb) {
            val al = p ushr 24
            if (al in 1..254) {
                partial++
                val bright = ((p shr 16) and 0xFF) + ((p shr 8) and 0xFF) + (p and 0xFF)
                assertTrue("edge pixel should be ring-coloured, not white-ish: ${Integer.toHexString(p)}", bright < 3 * 170)
            }
        }
        assertTrue(partial > 0)
        // the original is never modified
        assertEquals(0xFFFFFFFF.toInt(), src.argb[0])
        // visual check: the cut-out on a black garment, edge enlarged 6x
        val out = File(System.getProperty("outDir") ?: "build/test-output").apply { mkdirs() }
        val crop = BufferedImage(60, 60, BufferedImage.TYPE_INT_RGB)
        for (y in 0 until 60) for (x in 0 until 60) {
            val p = r.pixels.argb[(30 + y) * 200 + (30 + x)]
            val a = (p ushr 24) / 255.0
            fun ch(sh: Int) = (((p shr sh) and 0xFF) * a).toInt()
            crop.setRGB(x, y, (ch(16) shl 16) or (ch(8) shl 8) or ch(0))
        }
        val big = BufferedImage(360, 360, BufferedImage.TYPE_INT_RGB)
        big.createGraphics().apply { drawImage(crop.getScaledInstance(360, 360, java.awt.Image.SCALE_FAST), 0, 0, null); dispose() }
        ImageIO.write(big, "png", File(out, "cutout_edge_on_black.png"))
    }

    @Test fun aiCutoutWithRealModel() {
        val dir = File(System.getProperty("modelDir"))
        OrtMaskModel(File(dir, "u2netp.onnx").readBytes(), 4).use { m ->
            // subject on a busy background, where a colour key cannot work
            val rnd = Random(2)
            val img = BufferedImage(400, 400, BufferedImage.TYPE_INT_RGB)
            for (y in 0 until 400) for (x in 0 until 400) img.setRGB(x, y, Color(120 + rnd.nextInt(80), 120 + rnd.nextInt(80), 110 + rnd.nextInt(80)).rgb)
            val g = img.createGraphics()
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            g.color = Color(234, 110, 60); g.fillOval(100, 60, 200, 200)
            g.color = Color(40, 90, 70); g.fillPolygon(intArrayOf(80, 200, 320), intArrayOf(330, 220, 330), 3)
            g.dispose()
            val truth = BufferedImage(400, 400, BufferedImage.TYPE_BYTE_GRAY).also { t ->
                val tg = t.createGraphics(); tg.color = Color.WHITE
                tg.fillOval(100, 60, 200, 200); tg.fillPolygon(intArrayOf(80, 200, 320), intArrayOf(330, 220, 330), 3); tg.dispose()
            }
            val px = IntArray(400 * 400); img.getRGB(0, 0, 400, 400, px, 0, 400)
            val cut = AiCutout.apply(PixelBuffer(400, 400, px), m)
            var inter = 0; var union = 0
            for (y in 0 until 400) for (x in 0 until 400) {
                val a = (cut.argb[y * 400 + x] ushr 24) > 127
                val t = (truth.raster.getSample(x, y, 0)) > 127
                if (a && t) inter++
                if (a || t) union++
            }
            val iou = inter.toDouble() / union
            println("AI cutout IoU on busy background: ${"%.3f".format(iou)}")
            assertTrue("IoU $iou", iou > 0.9)
        }
    }

    private fun input(artW: Int, artH: Int, wIn: Double, hIn: Double, dpi: Int = 300, alpha: AlphaStats.Stats = AlphaStats.Stats(true, 0.0, 0.5),
                      solid: Boolean = false, prov: Provenance? = null, method: PrintMethod = PrintMethod.DTF, canvas: Pair<Double, Double> = wIn to hIn,
                      max: Pair<Double, Double>? = null, placement: Placement = Placement(0.0, 0.0, wIn, hIn)) =
        QualityInput(method, artW, artH, placement, canvas.first, canvas.second, dpi, alpha, solid, prov, max)

    @Test fun qualityAnalyzer() {
        val excellent = QualityAnalyzer.analyze(input(2400, 3000, 8.0, 10.0))
        assertEquals(Level.OK, excellent.overall)
        assertEquals("Excellent print quality", excellent.headline)
        assertEquals(ResolutionStatus.EXCELLENT, excellent.resolution)

        val good = QualityAnalyzer.analyze(input(1800, 2250, 8.0, 10.0))   // 225 DPI
        assertEquals(ResolutionStatus.GOOD, good.resolution); assertEquals(Level.WARN, good.overall)

        val low = QualityAnalyzer.analyze(input(1024, 1280, 16.0, 20.0))   // 64 DPI
        assertEquals(ResolutionStatus.LOW, low.resolution); assertEquals(Level.BAD, low.overall)
        assertTrue(low.checks.any { it.title.startsWith("Will be enlarged") && it.level == Level.BAD })

        // AI upscale from 600 px: enough pixels, but never called excellent on reconstructed detail
        val ai = QualityAnalyzer.analyze(input(2400, 3000, 8.0, 10.0, prov = Provenance(600, 750, 2400, 3000, true)))
        assertEquals(ResolutionStatus.GOOD, ai.resolution)
        assertEquals(75.0, ai.detailDpi!!, 0.5)
        assertTrue(ai.checks.any { it.title.contains("with AI") })
        // plain interpolation counts as the original's resolution
        val lanczos = QualityAnalyzer.analyze(input(2400, 3000, 8.0, 10.0, prov = Provenance(600, 750, 2400, 3000, false)))
        assertEquals(ResolutionStatus.LOW, lanczos.resolution)

        val opaque = QualityAnalyzer.analyze(input(2400, 3000, 8.0, 10.0, alpha = AlphaStats.Stats(false, 0.0, 1.0)))
        assertTrue(opaque.checks.any { it.title == "No transparency" && it.level == Level.WARN })

        val soft = AlphaStats.Stats(true, 0.08, 0.5)
        assertTrue(QualityAnalyzer.analyze(input(2400, 3000, 8.0, 10.0, alpha = soft)).checks.any { it.title.startsWith("Partly transparent") })
        assertTrue(QualityAnalyzer.analyze(input(2400, 3000, 8.0, 10.0, alpha = soft, solid = true)).checks.any { it.title == "Soft edges made solid" && it.level == Level.OK })

        val stretched = QualityAnalyzer.analyze(input(2400, 2400, 8.0, 10.0))
        assertTrue(stretched.checks.any { it.title == "Artwork is stretched" && it.level == Level.BAD })

        val clipped = QualityAnalyzer.analyze(input(2400, 3000, 8.0, 10.0, placement = Placement(4.0, 0.0, 8.0, 10.0)))
        assertTrue(clipped.checks.any { it.title.contains("cut off") && it.level == Level.BAD })

        val dtg = QualityAnalyzer.analyze(input(4200, 5400, 14.0, 18.0, method = PrintMethod.DTG, max = 12.0 to 16.0))
        assertTrue(dtg.checks.any { it.title.contains("garment's print area") })
    }

    @Test fun alphaStatsAndTrim() {
        val p = PixelBuffer(5, 4, IntArray(20).also { it[6] = 0xFF000000.toInt(); it[13] = 0x80000000.toInt() })
        val s = AlphaStats.of(p)
        assertTrue(s.hasTransparency); assertEquals(0.5, s.semiTransparentFraction, 1e-9)
        val b = AlphaStats.visibleBounds(p)!!
        assertEquals(listOf(1, 1, 4, 3), b.toList())
        assertEquals(3, AlphaStats.crop(p, b).width)
        assertNull(AlphaStats.visibleBounds(PixelBuffer(2, 2)))
    }
}
