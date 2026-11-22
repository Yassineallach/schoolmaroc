package com.printscale.ai

import android.app.Application
import android.net.Uri
import com.printscale.ai.data.HistoryRepository
import com.printscale.ai.data.ImportRepository
import com.printscale.ai.data.SettingsRepository
import com.printscale.ai.export.Exporter
import com.printscale.ai.processing.ProcessingController
import kotlinx.coroutines.flow.MutableStateFlow

class PrintScaleApp : Application() {
    lateinit var graph: AppGraph
        private set

    override fun onCreate() {
        super.onCreate()
        graph = AppGraph(this)
    }
}

/** Hand-wired dependencies. Small enough that a DI framework would add more than it saves. */
class AppGraph(val app: Application) {
    val imports = ImportRepository(app)
    val history = HistoryRepository(app)
    val settings = SettingsRepository(app)
    val processing = ProcessingController(app)
    val exporter = Exporter(app)
    val features: FeatureGate = AllFeaturesUnlocked

    /** An image shared into the app from another app, waiting for Home to import it. */
    val sharedImage = MutableStateFlow<Uri?>(null)

    /** Set when a QR/deep link connected a cloud server, so Home can confirm it. */
    val cloudNotice = MutableStateFlow<String?>(null)
}

/**
 * Single switch point for a future free/premium split. Nothing is restricted in this version;
 * screens ask the gate instead of hard-coding limits, so a billing-backed gate can replace it.
 */
interface FeatureGate {
    fun maxAiFactor(): Int
    fun batchEnabled(): Boolean
}

object AllFeaturesUnlocked : FeatureGate {
    override fun maxAiFactor() = 8
    override fun batchEnabled() = false // batch processing is not built yet
}
