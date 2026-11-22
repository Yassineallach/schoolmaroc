package com.printscale.ai

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithContentDescription
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.setValue
import androidx.work.testing.WorkManagerTestInitHelper
import com.printscale.ai.data.ExportRecord
import com.printscale.ai.data.ThemeChoice
import com.printscale.ai.processing.JobStage
import com.printscale.ai.processing.JobStatus
import com.printscale.ai.ui.editor.EditorScreen
import com.printscale.ai.ui.history.HistoryScreen
import com.printscale.ai.ui.home.HomeScreen
import com.printscale.ai.ui.processing.ProcessingBody
import com.printscale.ai.ui.result.ExportDoneScreen
import com.printscale.ai.ui.result.ResultScreen
import com.printscale.ai.ui.settings.SettingsScreen
import com.printscale.ai.ui.theme.PrintScaleTheme
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

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w400dp-h860dp-xhdpi")
class UiFlowTest {
    @get:Rule val rule = createAndroidComposeRule<androidx.activity.ComponentActivity>()
    private val graph get() = Fixtures.app.graph

    @Before fun setup() {
        WorkManagerTestInitHelper.initializeTestWorkManager(Fixtures.app)
        Fixtures.realisticDevice()
        org.robolectric.Shadows.shadowOf(Fixtures.app).grantPermissions(android.Manifest.permission.POST_NOTIFICATIONS)
        graph.settings.setTheme(ThemeChoice.DARK)
    }

    private fun waitForText(text: String, timeout: Long = 15_000) =
        rule.waitUntil(timeout) { rule.onAllNodesWithText(text, substring = true).fetchSemanticsNodes().isNotEmpty() }

    @Test fun homeEmptyStateAndNavigation() {
        var history = false; var settings = false
        rule.setContent {
            PrintScaleTheme(ThemeChoice.DARK) {
                HomeScreen(graph, { _, _, _ -> }, {}, {}, { history = true }, { settings = true })
            }
        }
        waitForText("Nothing here yet")
        rule.onNodeWithText("Upscale artwork").assertIsDisplayed().assertIsEnabled()
        rule.onNodeWithText("Open from Files").assertIsDisplayed()
        Fixtures.screenshot(rule, "01_home_dark")
        rule.onNodeWithContentDescription("History").performClick()
        rule.onNodeWithContentDescription("Settings").performClick()
        assertTrue(history && settings)
        rule.onNodeWithText("Print size presets").performScrollTo()
        rule.onNodeWithText("24 × 36 in").performScrollTo().assertIsDisplayed()
    }

    @Test fun homeLightTheme() {
        rule.setContent {
            PrintScaleTheme(ThemeChoice.LIGHT) { HomeScreen(graph, { _, _, _ -> }, {}, {}, {}, {}) }
        }
        waitForText("Nothing here yet")
        Fixtures.screenshot(rule, "02_home_light")
    }

    @Test fun editorControlsWorkAndStartJob() {
        val info = runBlocking { Fixtures.import(Fixtures.writePng(Fixtures.artwork(1024, 1536), "art.png")) }
        var started: String? = null
        rule.setContent {
            PrintScaleTheme(ThemeChoice.DARK) {
                EditorScreen(graph, info.id, null, null, onBack = {}, onStarted = { started = it })
            }
        }
        waitForText("Output size")
        // 2:3 artwork defaults to the 24 x 36 in print at 300 DPI
        rule.onNodeWithText("Upscale to 7200 × 10800 px").assertIsDisplayed().assertIsEnabled()
        Fixtures.screenshot(rule, "03_editor_top")

        rule.onNodeWithText("150 DPI").performScrollTo().performClick()
        rule.onNodeWithText("Upscale to 3600 × 5400 px").assertIsDisplayed()
        rule.onNodeWithText("300 DPI").performScrollTo().performClick()

        rule.onNodeWithText("Custom size").performScrollTo().performClick()
        rule.onNodeWithText("Custom print size").performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("Cancel").performScrollTo().performClick()
        rule.onAllNodesWithText("Custom print size").fetchSemanticsNodes().let { assertEquals(0, it.size) }

        rule.onNodeWithText("Scale factor").performScrollTo().performClick()
        rule.onNodeWithText("Upscale to 4096 × 6144 px").assertIsDisplayed()
        rule.onNodeWithText("2×").performClick()
        rule.onNodeWithText("Upscale to 2048 × 3072 px").assertIsDisplayed()
        rule.onNodeWithText("1:1").performScrollTo().performClick()
        rule.onNodeWithText("Upscale to 2048 × 2048 px").assertIsDisplayed()

        rule.onNodeWithText("Fit (add margin)").performScrollTo().performClick()
        // Fit keeps the whole 1024 x 1536 artwork on a square canvas: 1536 x 1536, so 2x is 3072
        rule.onNodeWithText("Upscale to 3072 × 3072 px").assertExists()
        rule.onNodeWithText("Edge colour").performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("Advanced").performScrollTo().performClick()
        rule.onNodeWithText("Noise reduction").performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("High").performScrollTo().performClick()
        rule.onNodeWithContentDescription("Rotate 90 degrees").performScrollTo().performClick()
        rule.onNodeWithContentDescription("Reset crop").performClick()
        rule.onNodeWithText("Method").performScrollTo()
        Fixtures.screenshot(rule, "04_editor_plan")

        rule.onNodeWithText("Upscale to 3072 × 3072 px").assertIsEnabled().performClick()
        repeat(20) { if (started == null) { rule.waitForIdle(); Thread.sleep(250) } }
        rule.waitUntil(10_000) { started != null }
        assertNotNull(started)
    }

    @Test fun editorBlocksImpracticalSize() {
        val info = runBlocking { Fixtures.import(Fixtures.writePng(Fixtures.artwork(4000, 4000), "huge.png")) }
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { EditorScreen(graph, info.id, null, 8, {}, {}) } }
        waitForText("Output size")
        // 8x of a 16 MP crop is 32000 px: the button is disabled and the reason is shown
        rule.onNodeWithText("Upscale to 32000 × 32000 px").assertIsNotEnabled()
        rule.onNodeWithText("beyond this app's limit", substring = true).performScrollTo().assertIsDisplayed()
    }

    @Test fun processingStates() {
        var cancel = false
        var status: JobStatus by androidx.compose.runtime.mutableStateOf(
            JobStatus.Running(JobStage.UPSCALING, 42, 100, 95_000, System.currentTimeMillis() - 63_000),
        )
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { ProcessingBody(status, null, System.currentTimeMillis(), { cancel = true }, {}) } }
        rule.onAllNodesWithText("Enhancing details and upscaling")[0].assertIsDisplayed()
        rule.onNodeWithText("42% of the artwork through the model").assertIsDisplayed()
        rule.onNodeWithText("about 1 min 35s left").assertIsDisplayed()
        Fixtures.screenshot(rule, "05_processing")
        rule.onNodeWithText("Cancel").performScrollTo().performClick()
        assertTrue(cancel)
        status = JobStatus.Running(JobStage.FINALIZING, 0, 0, null, 0)
        rule.onAllNodesWithText("Preparing print output")[0].assertIsDisplayed()
        status = JobStatus.Failed("The phone ran out of memory. Try a smaller crop or output size.")
        rule.onNodeWithText("Processing stopped").assertIsDisplayed()
        rule.onNodeWithText("Back to editor").assertIsDisplayed()
    }

    private fun finishedJob(transparent: Boolean = false): String = runBlocking {
        val info = Fixtures.import(Fixtures.writePng(Fixtures.artwork(900, 1125, transparent), "job.png"))
        val (id, _) = Fixtures.runJob(Fixtures.app, Fixtures.spec(info.id, 720, 900, aspect = 0.8, print = Fixtures.print8x10))
        id
    }

    @Test fun resultCompareInspectAndExportSheet() {
        val id = finishedJob()
        var exported = false
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { ResultScreen(graph, id, {}, {}, { exported = true }) } }
        waitForText("720 × 900 px")
        rule.onNodeWithText("ORIGINAL").assertIsDisplayed()
        rule.onNodeWithText("ENHANCED").assertIsDisplayed()
        Fixtures.screenshot(rule, "06_result")
        rule.onNodeWithText("Original").performClick()
        rule.onAllNodesWithText("ENHANCED").fetchSemanticsNodes().let { assertEquals(0, it.size) }
        rule.onNodeWithText("Enhanced").performClick()
        rule.onNodeWithText("Compare").performClick()
        rule.onNodeWithText("Inspect detail at 100%", substring = true).performClick()
        rule.onNodeWithText("Tap the area you want to inspect at 100%.").assertIsDisplayed()
        rule.onNodeWithText("Cancel").performClick()
        rule.onNodeWithText("Largest print at each resolution").performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("Export as").performScrollTo().performClick()
        rule.onNodeWithText("Save to Files").assertIsDisplayed()
        rule.onNodeWithText("JPEG").performClick()
        rule.onNodeWithText("95%").assertIsDisplayed()
        Fixtures.screenshot(rule, "07_export_sheet")
        assertTrue(!exported)
    }

    @Test fun exportDoneShowsDetails() {
        val id = finishedJob()
        runBlocking {
            graph.history.addExport(id, ExportRecord("Artwork_1x_720x900_300DPI.png", "PNG", 123_456, "Gallery · Pictures/PrintScale", "content://media/1", 0))
        }
        var done = false
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { ExportDoneScreen(graph, id, { done = true }, {}) } }
        waitForText("Saved")
        rule.onNodeWithText("Gallery · Pictures/PrintScale").assertIsDisplayed()
        rule.onNodeWithText("8 × 10 in").assertIsDisplayed()
        Fixtures.screenshot(rule, "08_export_done")
        rule.onNodeWithText("Done").performScrollTo().performClick()
        assertTrue(done)
    }

    @Test fun historyListAndDelete() {
        val id = finishedJob()
        var opened: String? = null
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { HistoryScreen(graph, {}, { opened = it }) } }
        waitForText("→ 720 × 900 px")
        Fixtures.screenshot(rule, "09_history")
        rule.onNode(hasText("→ 720 × 900 px", substring = true)).performClick()
        assertEquals(id, opened)
        rule.onNode(androidx.compose.ui.test.hasContentDescription("Delete ", substring = true)).performClick()
        rule.onNodeWithText("Delete this project?").assertIsDisplayed()
        rule.onNodeWithText("Delete").performClick()
        waitForText("No projects yet")
    }

    @Test fun settingsThemeAndLicences() {
        rule.setContent {
            val theme by graph.settings.theme.collectAsState()
            PrintScaleTheme(theme) { SettingsScreen(graph, {}) }
        }
        rule.onNodeWithText("Light").performClick()
        assertEquals(ThemeChoice.LIGHT, graph.settings.theme.value)
        rule.onNodeWithText("Real-ESRGAN licence").performScrollTo().performClick()
        rule.onNodeWithText("BSD 3-Clause License", substring = true).assertIsDisplayed()
        rule.onNodeWithText("Close").performClick()
        Fixtures.screenshot(rule, "10_settings_light")
    }

    @Test fun customSizeInCentimetres() {
        val info = runBlocking { Fixtures.import(Fixtures.writePng(Fixtures.artwork(800, 1000), "cm.png")) }
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { EditorScreen(graph, info.id, "8x10", null, {}, {}) } }
        waitForText("Output size")
        rule.onNodeWithText("Custom size").performScrollTo().performClick()
        rule.onNodeWithText("Centimetres").performScrollTo().performClick()
        rule.onNodeWithText("Width").performScrollTo().performTextInput("20.32")
        rule.onNodeWithText("Height").performTextInput("25.4")
        rule.onNodeWithText("Use size").performScrollTo().performClick()
        // 20.32 x 25.4 cm is 8 x 10 in: 2400 x 3000 px at 300 DPI
        rule.onNodeWithText("Upscale to 2400 × 3000 px").assertExists()
        rule.onNodeWithText("8 × 10 in at 300 DPI").assertExists()
    }
}
