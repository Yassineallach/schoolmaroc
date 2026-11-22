package com.printscale.ai

import android.content.Context
import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Shader
import android.net.Uri
import androidx.compose.ui.test.junit4.ComposeContentTestRule
import androidx.exifinterface.media.ExifInterface
import androidx.test.core.app.ApplicationProvider
import androidx.work.testing.TestListenableWorkerBuilder
import androidx.work.workDataOf
import com.printscale.ai.data.JobSpec
import com.printscale.ai.data.Paths
import com.printscale.ai.processing.UpscaleWorker
import com.printscale.engine.CropState
import com.printscale.engine.EnhanceSettings
import com.printscale.engine.FitMode
import com.printscale.engine.PrintSize
import com.printscale.engine.PrintTarget
import java.io.File
import java.io.FileOutputStream
import java.util.UUID

object Fixtures {
    val app: PrintScaleApp get() = ApplicationProvider.getApplicationContext()

    /** Gradient "artwork" with a sun and lines, optionally on a transparent background. */
    fun artwork(w: Int, h: Int, transparent: Boolean = false): Bitmap {
        val b = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val c = Canvas(b)
        if (!transparent) {
            c.drawRect(0f, 0f, w.toFloat(), h.toFloat(), Paint().apply {
                shader = LinearGradient(0f, 0f, 0f, h.toFloat(), Color.rgb(232, 196, 150), Color.rgb(60, 52, 90), Shader.TileMode.CLAMP)
            })
        }
        c.drawCircle(w * 0.5f, h * 0.45f, minOf(w, h) * 0.28f, Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(234, 110, 60) })
        val line = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(30, 40, 60); strokeWidth = maxOf(1f, h / 120f) }
        for (i in 0 until 10) c.drawLine(0f, h * 0.7f + i * h / 40f, w.toFloat(), h * 0.55f + i * h / 28f, line)
        return b
    }

    fun writePng(b: Bitmap, name: String): File = File(app.cacheDir, name).also { f -> FileOutputStream(f).use { b.compress(Bitmap.CompressFormat.PNG, 100, it) } }

    fun writeJpeg(b: Bitmap, name: String, orientation: Int? = null): File {
        val f = File(app.cacheDir, name)
        FileOutputStream(f).use { b.compress(Bitmap.CompressFormat.JPEG, 90, it) }
        if (orientation != null) ExifInterface(f.path).apply { setAttribute(ExifInterface.TAG_ORIENTATION, orientation.toString()); saveAttributes() }
        return f
    }

    suspend fun import(f: File) = app.graph.imports.import(Uri.fromFile(f))

    /**
     * Runs the real worker for a job. useAi=false keeps it on the JVM (ONNX Runtime's Android
     * native library cannot load here); the AI path is covered by the engine tests with the real model.
     */
    suspend fun runJob(context: Context, spec: JobSpec): Pair<String, androidx.work.ListenableWorker.Result> {
        val id = UUID.randomUUID().toString()
        Paths(context).jobSpec(id).writeText(spec.toJson().toString())
        val worker = TestListenableWorkerBuilder<UpscaleWorker>(context).setInputData(workDataOf(UpscaleWorker.KEY_JOB to id)).build()
        return id to worker.doWork()
    }

    fun spec(importId: String, targetW: Int, targetH: Int, aspect: Double? = 1.0, fit: FitMode = FitMode.FILL, print: PrintTarget? = null) = JobSpec(
        importId = importId, crop = CropState(), aspect = aspect, fitMode = fit, background = if (fit == FitMode.FIT) Color.WHITE else null,
        targetW = targetW, targetH = targetH, useAi = false, print = print, settings = EnhanceSettings(),
    )

    val print8x10 = PrintTarget(PrintSize(8.0, 10.0), 300)

    /** Robolectric reports no free memory or storage by default; give it a mid-range phone's numbers. */
    fun realisticDevice() {
        val am = app.getSystemService(android.app.ActivityManager::class.java)
        org.robolectric.Shadows.shadowOf(am).setMemoryInfo(android.app.ActivityManager.MemoryInfo().apply { availMem = 3L shl 30; totalMem = 8L shl 30 })
        org.robolectric.shadows.ShadowStatFs.registerStats(app.filesDir, 1_000_000, 500_000, 500_000) // 4 KB blocks: about 2 GB free
    }

    /** Draws the window into a bitmap (software rendering under Robolectric's native graphics). */
    fun screenshot(rule: ComposeContentTestRule, name: String) {
        rule.waitForIdle()
        val dir = File(System.getProperty("screenshotDir") ?: "build/screenshots").apply { mkdirs() }
        val activity = (rule as androidx.compose.ui.test.junit4.AndroidComposeTestRule<*, *>).activity
        val root = activity.window.decorView
        val bmp = Bitmap.createBitmap(root.width, root.height, Bitmap.Config.ARGB_8888)
        root.draw(Canvas(bmp))
        FileOutputStream(File(dir, "$name.png")).use { bmp.compress(Bitmap.CompressFormat.PNG, 100, it) }
    }
}
