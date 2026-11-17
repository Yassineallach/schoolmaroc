package com.mardev.nearshelf

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.mardev.nearshelf.ui.debug.ProviderDebugScreen
import com.mardev.nearshelf.ui.theme.NearshelfTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent {
            NearshelfTheme {
                ProviderDebugScreen()
            }
        }
    }
}
