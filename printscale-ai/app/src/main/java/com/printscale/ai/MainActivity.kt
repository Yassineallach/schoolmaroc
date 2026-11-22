package com.printscale.ai

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.SystemBarStyle
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.printscale.ai.data.ThemeChoice
import com.printscale.ai.ui.AppNavHost
import com.printscale.ai.ui.theme.PrintScaleTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val graph = (application as PrintScaleApp).graph
        handleShare(intent)
        setContent {
            val theme by graph.settings.theme.collectAsStateWithLifecycle()
            val dark = theme != ThemeChoice.LIGHT && (theme == ThemeChoice.DARK || resources.configuration.isNightModeActive)
            enableEdgeToEdge(
                statusBarStyle = if (dark) SystemBarStyle.dark(android.graphics.Color.TRANSPARENT)
                else SystemBarStyle.light(android.graphics.Color.TRANSPARENT, android.graphics.Color.TRANSPARENT),
            )
            PrintScaleTheme(theme) { AppNavHost(graph) }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleShare(intent)
    }

    private fun handleShare(intent: Intent?) {
        if (intent?.action != Intent.ACTION_SEND) return
        @Suppress("DEPRECATION")
        val uri = intent.getParcelableExtra<Uri>(Intent.EXTRA_STREAM) ?: return
        (application as PrintScaleApp).graph.sharedImage.value = uri
    }
}
