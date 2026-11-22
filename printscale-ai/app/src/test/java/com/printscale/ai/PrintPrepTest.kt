package com.printscale.ai

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.hasClickAction
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextReplacement
import androidx.work.testing.WorkManagerTestInitHelper
import com.printscale.ai.data.ThemeChoice
import com.printscale.ai.processing.BackgroundMode
import com.printscale.ai.processing.PrintPrepEngine
import com.printscale.ai.ui.prep.PrepTab
import com.printscale.ai.ui.prep.PrintPrepScreen
import com.printscale.ai.ui.result.ResultScreen
import com.printscale.ai.ui.theme.PrintScaleTheme
import com.printscale.engine.PrintLayout
import com.printscale.engine.PrintMethod
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.io.File

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w400dp-h860dp-xhdpi")
class PrintPrepTest {
    @get:Rule val rule = createAndroidComposeRule<androidx.activity.ComponentActivity>()
    private val graph get() = Fixtures.app.graph

    @Before fun setup() {
        WorkManagerTestInitHelper.initializeTestWorkManager(Fixtures.app)
        Fixtures.realisticDevice()
        graph.settings.setTheme(ThemeChoice.DARK)
    }

    /** A typical POD design: illustration on a plain white background, 1200 x 1500 px. */
    private fun whiteBackgroundDesign(): File {
        val b = Bitmap.createBitmap(1200, 1500, Bitmap.Config.ARGB_8888)
        val c = Canvas(b)
        c.drawColor(Color.WHITE)
        val p = Paint(Paint.ANTI_ALIAS_FLAG)
        p.color = Color.rgb(234, 110, 60); c.drawCircle(600f, 600f, 380f, p)
        p.color = Color.rgb(30, 40, 90); c.drawRect(250f, 1050f, 950f, 1350f, p)
        return Fixtures.writePng(b, "design.png")
    }

    private fun waitText(t: String, timeout: Long = 20_000) =
        rule.waitUntil(timeout) { rule.onAllNodes(hasText(t, substring = true)).fetchSemanticsNodes().isNotEmpty() }

    @Test fun engineExportHasExactPixelsTransparencyAndDpi() = runBlocking {
        val info = Fixtures.import(whiteBackgroundDesign())
        val engine = PrintPrepEngine(Fixtures.app)
        val src = engine.loadSource(info, graph.imports.original(info.id))
        val art = engine.prepare(info.id, src, BackgroundMode.PLAIN, 0.12f, false, true) {}
        assertTrue(art.alpha.hasTransparency)
        assertTrue("trimmed to the visible design", art.width < 1200 && art.height < 1500)
        assertEquals(0xFFFFFFFF.toInt(), src.argb[0]) // the source pixels were not modified
        // 10 x 12 in at 300 DPI, artwork fitted and centred
        val placement = PrintLayout.fit(10.0, 12.0, art.width, art.height)
        val px = PrintLayout.toPixels(10.0, 12.0, placement, 300)
        val out = File(Fixtures.app.cacheDir, "print.png")
        engine.export(art, px, 300, solidEdges = false, compressionLevel = 6, out = out) {}
        val o = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(out.path, o)
        assertEquals(3000, o.outWidth); assertEquals(3600, o.outHeight)
        val bmp = BitmapFactory.decodeFile(out.path)
        assertEquals(0, Color.alpha(bmp.getPixel(5, 5)))                 // canvas corner clear
        assertEquals(255, Color.alpha(bmp.getPixel(1500, px.y + px.h / 3))) // inside the disc solid
        val head = out.readBytes().copyOfRange(0, 200)
        assertTrue(String(head, Charsets.ISO_8859_1).contains("pHYs"))
        // original import untouched on disk
        assertTrue(graph.imports.original(info.id).length() > 0)
    }

    @Test fun dtfWorkflowFromSizeToExport() {
        val info = runBlocking { Fixtures.import(whiteBackgroundDesign()) }
        var upscaleFor: String? = null
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { PrintPrepScreen(graph, info.id, PrintMethod.DTF, PrepTab.PRINT, {}, { upscaleFor = it }) } }
        waitText("Export print file (3600 × 4800 px)")
        Fixtures.screenshot(rule, "13_dtf_canvas")

        // sizes and DPI drive the calculator
        rule.onNodeWithText("8 × 10 in").performScrollTo().performClick()
        waitText("Export print file (2400 × 3000 px)")
        rule.onNodeWithText("150 DPI").performScrollTo().performClick()
        waitText("Export print file (1200 × 1500 px)")
        rule.onNodeWithText("300 DPI (recommended)").performScrollTo().performClick()
        rule.onNodeWithText("2400 × 3000 px for the full print area").performScrollTo().assertIsDisplayed()
        // 1200 px across 8 in is 150 DPI: flagged, not called print-ready
        rule.onNodeWithText("Low resolution").performScrollTo().assertIsDisplayed()
        Fixtures.screenshot(rule, "14_dtf_calculator")

        // background removal (off the main thread) gives transparency
        rule.onNodeWithText("Plain colour").performScrollTo().performClick()
        rule.waitUntil(20_000) { rule.onAllNodesWithText("Removing the background").fetchSemanticsNodes().isEmpty() }

        // placement controls
        rule.onNodeWithText("Print file").performScrollTo().performClick()
        rule.onNodeWithContentDescription("Center horizontally").performClick()
        rule.onNodeWithContentDescription("Center vertically").performClick()
        rule.onNodeWithContentDescription("Fit to canvas").performClick()
        rule.onNodeWithContentDescription("Reset placement").performClick()
        rule.onNodeWithContentDescription("Change backdrop, now checks").performClick()
        rule.onNodeWithContentDescription("Change backdrop, now white").assertExists()
        rule.onNodeWithText("Backdrop (white) is for viewing only", substring = true).assertExists()

        // garment preview is separate from the file
        rule.onNodeWithText("Garment").performScrollTo().performClick()
        rule.onNodeWithText("C. Preview only", substring = true).assertExists()
        rule.onNodeWithContentDescription("Black").performClick()
        rule.onNodeWithContentDescription("Black, selected").assertExists()
        rule.onNodeWithText("Hoodie").performClick()
        Fixtures.screenshot(rule, "15_garment_hoodie_black")
        rule.onNodeWithText("T-shirt").performClick()
        rule.onNodeWithContentDescription("Sand").performClick()
        Fixtures.screenshot(rule, "16_garment_tee_sand")

        // quality report
        rule.onNodeWithText("Quality").performScrollTo().performClick()
        rule.onNodeWithText("Transparent background").assertExists()
        rule.onNodeWithText("Resolution is too low for this print size").assertExists()
        Fixtures.screenshot(rule, "17_quality")
        rule.onNodeWithText("Upscale this artwork first").performScrollTo().performClick()
        assertEquals(info.id, upscaleFor)

        // export: the real file, not the mockup
        rule.onNode(hasText("Export print file", substring = true) and hasClickAction()).performClick()
        rule.onNodeWithText("PNG with transparent background").assertExists()
        rule.onNodeWithText("Save to gallery").performClick()
        rule.waitUntil(30_000) { rule.onAllNodesWithText("Print file saved").fetchSemanticsNodes().isNotEmpty() }
        assertTrue(rule.onAllNodesWithText("2400 × 3000 px").fetchSemanticsNodes().isNotEmpty())
        val saved = File(Fixtures.app.cacheDir, "exports").listFiles()!!.single { it.name.endsWith(".png") }
        assertTrue(saved.name, saved.name.endsWith("_DTF_8x10in_300DPI.png"))
        val o = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(saved.path, o)
        assertEquals(2400, o.outWidth); assertEquals(3000, o.outHeight)
        assertEquals(0, Color.alpha(BitmapFactory.decodeFile(saved.path).getPixel(2, 2)))
    }

    @Test fun customCentimetreSizeAndDtgBoundaries() {
        val info = runBlocking { Fixtures.import(whiteBackgroundDesign()) }
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { PrintPrepScreen(graph, info.id, PrintMethod.DTG, PrepTab.QUALITY, {}, {}) } }
        waitText("Export print file")
        rule.onNodeWithText("Centimetres").performScrollTo().performClick()
        rule.onNodeWithText("Print width").performTextReplacement("30.48")
        rule.onNodeWithText("Print height").performTextReplacement("40.64")
        waitText("Export print file (3600 × 4800 px)")
        // a 14 x 18 in DTG print exceeds the usual 12 x 16 in platen
        rule.onNodeWithText("Inches").performScrollTo().performClick()
        rule.onNodeWithText("Print width").performTextReplacement("14")
        rule.onNodeWithText("Print height").performTextReplacement("18")
        waitText("Export print file (4200 × 5400 px)")
        rule.onNodeWithText("Larger than the garment's print area").assertExists()
    }

    @Test fun upscaledResultCarriesProvenanceIntoPrintPrep() {
        val id = runBlocking {
            val info = Fixtures.import(Fixtures.writePng(Fixtures.artwork(900, 1125), "job.png"))
            Fixtures.runJob(Fixtures.app, Fixtures.spec(info.id, 720, 900, aspect = 0.8, print = Fixtures.print8x10)).first
        }
        var prepId: String? = null
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { ResultScreen(graph, id, {}, {}, {}, onPrep = { prepId = it }) } }
        waitText("720 × 900 px")
        rule.onNodeWithText("Prepare for DTF / DTG").performScrollTo().performClick()
        repeat(60) { if (prepId == null) { rule.waitForIdle(); Thread.sleep(250) } } // import runs on a real IO thread
        rule.waitUntil(5_000) { prepId != null }
        val imported = runBlocking { graph.imports.get(prepId!!) }
        assertNotNull(imported)
        assertTrue(imported!!.displayName.endsWith("_upscaled.png"))
        // this fixture job only resized (no AI step was needed), so no upscale provenance is recorded
        assertEquals(null, imported.provenance)
    }
}
