package com.printscale.engine

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.fail
import org.junit.BeforeClass
import org.junit.Test
import java.awt.BasicStroke
import java.awt.Color
import java.awt.Font
import java.awt.GradientPaint
import java.awt.RenderingHints
import java.awt.image.BufferedImage
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.File
import javax.imageio.IIOImage
import javax.imageio.ImageIO
import javax.imageio.ImageWriteParam
import kotlin.math.abs
import kotlin.math.max

/** Runs the real Real-ESRGAN ONNX model through ONNX Runtime on the JVM. */
class ModelPipelineTest {
    companion object {
        private lateinit var strong: ByteArray
        private lateinit var weak: ByteArray
        private lateinit var ranges: List<IntArray>
        private val outDir = File(System.getProperty("outDir") ?: "build/test-output").apply { mkdirs() }

        @BeforeClass @JvmStatic fun load() {
            val dir = File(System.getProperty("modelDir"))
            strong = File(dir, "realesr-general-x4v3.onnx").readBytes()
            weak = File(dir, "realesr-general-wdn-x4v3.onnx").readBytes()
            ranges = ModelBlender.parseRanges(File(dir, "blend_map.json").readText())
        }

        fun model(strength: Float = 0.5f) = OrtSrModel(ModelBlender.blend(strong, weak, ranges, strength), 4)

        /** Synthetic "AI artwork": gradients, shapes, thin lines and lettering, made small and JPEG-compressed. */
        fun artwork(w: Int, h: Int, alpha: Boolean = false): PixelBuffer {
            val big = BufferedImage(w * 4, h * 4, if (alpha) BufferedImage.TYPE_INT_ARGB else BufferedImage.TYPE_INT_RGB)
            val g = big.createGraphics()
            g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)
            g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING, RenderingHints.VALUE_TEXT_ANTIALIAS_ON)
            if (!alpha) {
                g.paint = GradientPaint(0f, 0f, Color(232, 196, 150), 0f, h * 4f, Color(60, 52, 90))
                g.fillRect(0, 0, w * 4, h * 4)
            }
            g.color = Color(240, 120, 60); g.fillOval(w, h / 2, w * 2, w * 2)
            g.color = Color(30, 40, 60)
            g.stroke = BasicStroke(6f)
            for (i in 0 until 12) g.drawLine(0, h * 3 + i * 18, w * 4, h * 2 + i * 30)
            g.color = Color(250, 245, 235)
            g.font = Font(Font.SERIF, Font.BOLD, w / 2)
            g.drawString("Golden Hour", w / 4, h * 4 - h / 3)
            g.dispose()
            val small = BufferedImage(w, h, big.type)
            val g2 = small.createGraphics()
            g2.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR)
            g2.drawImage(big.getScaledInstance(w, h, java.awt.Image.SCALE_AREA_AVERAGING), 0, 0, null)
            g2.dispose()
            val img = if (alpha) small else {
                // JPEG round trip at quality 0.7 to mimic downloaded generator output
                val bos = ByteArrayOutputStream()
                val wr = ImageIO.getImageWritersByFormatName("jpg").next()
                wr.output = ImageIO.createImageOutputStream(bos)
                val p = wr.defaultWriteParam.apply { compressionMode = ImageWriteParam.MODE_EXPLICIT; compressionQuality = 0.7f }
                wr.write(null, IIOImage(small, null, null), p)
                (wr.output as javax.imageio.stream.ImageOutputStream).close()
                ImageIO.read(ByteArrayInputStream(bos.toByteArray()))
            }
            val px = IntArray(w * h)
            img.getRGB(0, 0, w, h, px, 0, w)
            return PixelBuffer(w, h, px)
        }

        fun toImage(p: PixelBuffer, alpha: Boolean): BufferedImage {
            val img = BufferedImage(p.width, p.height, if (alpha) BufferedImage.TYPE_INT_ARGB else BufferedImage.TYPE_INT_RGB)
            img.setRGB(0, 0, p.width, p.height, p.argb, 0, p.width)
            return img
        }
    }

    private class Collect(val w: Int, val h: Int) : RowSink {
        val px = IntArray(w * h)
        override fun writeRow(y: Int, argb: IntArray) = System.arraycopy(argb, 0, px, y * w, w)
    }

    @Test fun onnxBlendMatchesEndpoints() {
        val x = FloatArray(3 * 20 * 20) { (it % 97) / 97f }
        val a = model(1f).use { it.run(x, 20, 20) }
        val b = model(0f).use { it.run(x, 20, 20) }
        val m = model(0.5f).use { it.run(x, 20, 20) }
        assertEquals(3 * 80 * 80, a.size)
        // the blended network is a different network, not a pixel average, but it should land between
        var diffAB = 0.0
        for (i in a.indices) diffAB += abs(a[i] - b[i])
        assertTrue("checkpoints differ", diffAB / a.size > 1e-4)
        assertTrue(m.all { it in 0f..1f })
    }

    @Test fun tiledOutputMatchesWholeImageInference() {
        val src = artwork(150, 110)
        model().use { m ->
            // whole image in one run, no tiling
            val n = src.width * src.height
            val chw = FloatArray(3 * n)
            for (i in 0 until n) {
                val p = src.argb[i]
                chw[i] = (p shr 16 and 0xFF) / 255f; chw[n + i] = (p shr 8 and 0xFF) / 255f; chw[2 * n + i] = (p and 0xFF) / 255f
            }
            val whole = m.run(chw, src.height, src.width)
            val ow = src.width * 4; val oh = src.height * 4; val on = ow * oh

            val prod = AiRowProducer(src, m, EnhanceSettings(detail = 1f, sharpen = 0f), TileConfig(tile = 48, pad = 24),
                false, {}, {})
            val row = IntArray(ow)
            var maxErr = 0
            var sumErr = 0L
            for (y in 0 until oh) {
                prod.readRow(row)
                for (x in 0 until ow) {
                    val i = y * ow + x
                    val p = row[x]
                    for ((c, sh) in listOf(0 to 16, 1 to 8, 2 to 0)) {
                        val ref = (whole[c * on + i].coerceIn(0f, 1f) * 255f + 0.5f).toInt()
                        val e = abs(((p shr sh) and 0xFF) - ref)
                        maxErr = max(maxErr, e); sumErr += e
                    }
                }
            }
            println("tile seam check: max error $maxErr/255, mean ${sumErr.toDouble() / (3L * on)}")
            assertTrue("max error $maxErr", maxErr <= 3)
        }
    }

    @Test fun fullPipelineToPrintSizeWithPng() {
        val src = artwork(160, 240)
        val sink = ByteArrayOutputStream()
        val tw = 1200; val th = 1800 // 4 x 6 in at 300 DPI: 7.5x, beyond the AI's 4x
        val preview = PreviewSink(tw, th, 512)
        val stages = mutableListOf<Stage>()
        var lastDone = 0L; var totalUnits = 0L
        val t0 = System.currentTimeMillis()
        model().use { m ->
            UpscalePipeline(src, tw, th, EnhanceSettings(), useAi = true, TileConfig(tile = 96, pad = 24))
                .run(m, TeeSink(PngStreamWriter(sink, tw, th, false, 300, null), preview), object : ProgressListener {
                    override fun onStage(stage: Stage) { stages += stage }
                    override fun onAiProgress(done: Long, total: Long, etaMillis: Long?) {
                        lastDone = done
                        totalUnits = total
                    }
                }, { false })
        }
        println("pipeline 160x240 -> 1200x1800 took ${System.currentTimeMillis() - t0} ms")
        assertEquals(listOf(Stage.ANALYZING, Stage.UPSCALING, Stage.FINALIZING), stages)
        assertEquals(totalUnits, lastDone)
        val img = ImageIO.read(ByteArrayInputStream(sink.toByteArray()))
        assertEquals(tw, img.width); assertEquals(th, img.height)
        assertTrue(preview.previewW <= 512 && preview.previewH <= 512)
        File(outDir, "pipeline_1200x1800.png").writeBytes(sink.toByteArray())
    }

    @Test fun transparentArtworkKeepsAlpha() {
        val src = artwork(96, 96, alpha = true)
        assertTrue(src.hasTransparency())
        val out = Collect(384, 384)
        model().use { m -> UpscalePipeline(src, 384, 384, EnhanceSettings(), true).run(m, out, object : ProgressListener {}, { false }) }
        val corner = out.px[0] ushr 24
        val centre = out.px[192 * 384 + 192] ushr 24
        assertEquals(0, corner)
        assertEquals(255, centre)
        ImageIO.write(toImage(PixelBuffer(384, 384, out.px), true), "png", File(outDir, "alpha_384.png"))
    }

    @Test fun cancellationStopsBetweenTiles() {
        val src = artwork(200, 200)
        var tiles = 0
        try {
            model().use { m ->
                UpscalePipeline(src, 800, 800, EnhanceSettings(), true, TileConfig(tile = 64, pad = 24))
                    .run(m, Collect(800, 800), object : ProgressListener {
                        override fun onAiProgress(done: Long, total: Long, etaMillis: Long?) { tiles++ }
                    }, { tiles >= 3 })
            }
            fail("expected cancellation")
        } catch (e: UpscaleCancelled) {
            assertTrue(tiles in 3..4)
        }
    }

    /** Writes side-by-side crops (bicubic vs AI) for visual review. Not an assertion of quality. */
    @Test fun writeVisualComparison() {
        val src = artwork(200, 150)
        val ai = Collect(800, 600)
        model().use { m -> UpscalePipeline(src, 800, 600, EnhanceSettings(), true).run(m, ai, object : ProgressListener {}, { false }) }
        val bic = Collect(800, 600)
        var y = 0
        StreamingResizer(200, 150, 800, 600).run({ System.arraycopy(src.argb, (y++) * 200, it, 0, 200) }, bic, {})
        val sheet = BufferedImage(800, 300, BufferedImage.TYPE_INT_RGB)
        val a = toImage(PixelBuffer(800, 600, bic.px), false).getSubimage(150, 300, 400, 300)
        val b = toImage(PixelBuffer(800, 600, ai.px), false).getSubimage(150, 300, 400, 300)
        val g = sheet.createGraphics(); g.drawImage(a, 0, 0, null); g.drawImage(b, 400, 0, null); g.dispose()
        ImageIO.write(sheet, "png", File(outDir, "compare_lanczos_vs_ai.png"))
        ImageIO.write(toImage(src, false), "png", File(outDir, "source_200x150.png"))
    }
}
