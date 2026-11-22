package com.printscale.ai

import android.content.Intent
import android.graphics.BitmapFactory
import android.net.Uri
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.test.performTextReplacement
import androidx.compose.ui.test.hasSetTextAction
import androidx.work.ListenableWorker
import androidx.work.testing.WorkManagerTestInitHelper
import com.printscale.ai.data.JobSpec
import com.printscale.ai.data.Paths
import com.printscale.ai.data.ThemeChoice
import com.printscale.ai.ui.editor.EditorScreen
import com.printscale.ai.ui.home.HomeScreen
import com.printscale.ai.ui.theme.PrintScaleTheme
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], qualifiers = "w400dp-h860dp-xhdpi")
class CloudFlowTest {
    @get:Rule val rule = createAndroidComposeRule<androidx.activity.ComponentActivity>()
    private val graph get() = Fixtures.app.graph
    private var fake: FakeCloudServer? = null

    @Before fun setup() {
        WorkManagerTestInitHelper.initializeTestWorkManager(Fixtures.app)
        Fixtures.realisticDevice()
        graph.settings.setCloudLink(null)
        graph.settings.setTheme(ThemeChoice.DARK)
    }

    @After fun teardown() { fake?.close() }

    private fun cloudSpec(importId: String, tw: Int, th: Int) =
        Fixtures.spec(importId, tw, th, aspect = 0.8, print = Fixtures.print8x10).copy(useAi = true, engine = JobSpec.ENGINE_CLOUD)

    @Test fun workerRunsCloudJobAndFinishesOnPhone() = runBlocking {
        fake = FakeCloudServer()
        graph.settings.setCloudLink(fake!!.link)
        val info = Fixtures.import(Fixtures.writePng(Fixtures.artwork(160, 200, transparent = true), "cloud.png"))
        // 8 x 10 in at 300 DPI from a 160 x 200 crop: server returns 640 x 800, the phone resizes to 2400 x 3000
        val (id, result) = Fixtures.runJob(Fixtures.app, cloudSpec(info.id, 2400, 3000))
        assertTrue("result $result", result is ListenableWorker.Result.Success)
        assertEquals(Triple(160, 200, true), fake!!.lastUpload)
        val o = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(Paths(Fixtures.app).jobMaster(id).path, o)
        assertEquals(2400, o.outWidth); assertEquals(3000, o.outHeight)
        val item = graph.history.get(id)!!
        assertEquals(JobSpec.ENGINE_CLOUD, item.engine)
        assertTrue(item.hasAlpha)
        assertEquals("server copy deleted after download", 1, fake!!.deleted.size)
        assertTrue("temporary transfer files removed", Paths(Fixtures.app).jobDir(id).listFiles()!!.none { it.name.startsWith("upload") || it.name.startsWith("cloud_") })
    }

    @Test fun clearErrorsWhenCloudIsUnavailable() = runBlocking {
        val info = Fixtures.import(Fixtures.writePng(Fixtures.artwork(120, 150), "c2.png"))
        // no server connected
        val (_, noLink) = Fixtures.runJob(Fixtures.app, cloudSpec(info.id, 960, 1200))
        assertTrue((noLink as ListenableWorker.Result.Failure).outputData.getString("error")!!.contains("No cloud GPU is connected"))
        // server stopped (notebook closed)
        fake = FakeCloudServer(); val link = fake!!.link; fake!!.close(); fake = null
        graph.settings.setCloudLink(link)
        val (_, down) = Fixtures.runJob(Fixtures.app, cloudSpec(info.id, 960, 1200))
        assertTrue((down as ListenableWorker.Result.Failure).outputData.getString("error")!!.contains("Can't reach the server"))
        // GPU error on the server is passed on
        fake = FakeCloudServer(failJobs = true)
        graph.settings.setCloudLink(fake!!.link)
        val (_, failed) = Fixtures.runJob(Fixtures.app, cloudSpec(info.id, 960, 1200))
        assertTrue((failed as ListenableWorker.Result.Failure).outputData.getString("error")!!.contains("CUDA out of memory"))
    }

    /** Android worker against the real Python AuraSR server: PRINTSCALE_TEST_SERVER=http://localhost:8765/?key=... */
    @Test fun workerAgainstRealAuraSrServer() = runBlocking {
        val real = System.getProperty("cloudServer").orEmpty()
        assumeTrue("set PRINTSCALE_TEST_SERVER to run", real.isNotEmpty())
        graph.settings.setCloudLink(real)
        val info = Fixtures.import(Fixtures.writeJpeg(Fixtures.artwork(96, 120), "real.jpg"))
        val (id, result) = Fixtures.runJob(Fixtures.app, cloudSpec(info.id, 450, 562))
        assertTrue("result $result", result is ListenableWorker.Result.Success)
        val o = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        BitmapFactory.decodeFile(Paths(Fixtures.app).jobMaster(id).path, o)
        assertEquals(450, o.outWidth)
        println("real AuraSR job finished in ${graph.history.get(id)!!.durationMs} ms")
    }

    @Test fun connectSheetChecksAndSavesLink() {
        fake = FakeCloudServer()
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { HomeScreen(graph, { _, _, _ -> }, {}, {}, {}, {}) } }
        rule.waitUntil(10_000) { rule.onAllNodesWithText("Connect a cloud GPU").fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithText("Connect a cloud GPU").performScrollTo().performClick()
        val field = rule.onNode(hasSetTextAction())
        field.performTextInput("https://example.com/no-key")
        rule.onNodeWithText("doesn't look like a server link", substring = true).assertExists()
        field.performTextReplacement(fake!!.link)
        rule.onNode(androidx.compose.ui.test.hasText("Connect") and androidx.compose.ui.test.hasClickAction()).performScrollTo().performClick()
        rule.waitUntil(10_000) { rule.onAllNodesWithText("Connected: AuraSR v2 on Fake T4").fetchSemanticsNodes().isNotEmpty() }
        assertEquals(fake!!.link, graph.settings.cloudLink.value)
        rule.onNodeWithText("Disconnect").performScrollTo().performClick()
        assertNull(graph.settings.cloudLink.value)
    }

    @Test fun editorOffersCloudEngineWhenConnected() {
        fake = FakeCloudServer()
        graph.settings.setCloudLink(fake!!.link)
        val info = runBlocking { Fixtures.import(Fixtures.writePng(Fixtures.artwork(1024, 1536), "e.png")) }
        rule.setContent { PrintScaleTheme(ThemeChoice.DARK) { EditorScreen(graph, info.id, null, null, {}, {}) } }
        rule.waitUntil(15_000) { rule.onAllNodesWithText("Output size").fetchSemanticsNodes().isNotEmpty() }
        rule.onNodeWithText("Cloud GPU").performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("AuraSR has no adjustable settings", substring = true).performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("AuraSR 4× (cloud GPU)", substring = true).performScrollTo().assertIsDisplayed()
        rule.onNodeWithText("Data transfer").assertExists()
        Fixtures.screenshot(rule, "11_editor_cloud")
        rule.onNodeWithText("This phone").performScrollTo().performClick()
        rule.onNodeWithText("Noise reduction").assertDoesNotExist()
        rule.onNodeWithText("Advanced").performScrollTo().assertIsDisplayed()
    }

    @Test fun qrDeepLinkConnectsTheApp() {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse("printscale://connect?server=https%3A%2F%2Fcalm-river.trycloudflare.com&key=AbCdEfGh1234"))
        Robolectric.buildActivity(MainActivity::class.java, intent).setup()
        assertEquals("https://calm-river.trycloudflare.com/?key=AbCdEfGh1234", graph.settings.cloudLink.value)
        assertTrue(graph.cloudNotice.value!!.contains("connected"))
    }
}

