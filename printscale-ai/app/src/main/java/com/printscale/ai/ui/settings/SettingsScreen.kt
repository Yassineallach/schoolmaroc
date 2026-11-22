package com.printscale.ai.ui.settings

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.printscale.ai.AppGraph
import com.printscale.ai.BuildConfig
import com.printscale.ai.data.ThemeChoice
import com.printscale.ai.processing.ModelProvider
import com.printscale.ai.ui.components.Panel
import com.printscale.ai.ui.components.SecondaryButton
import com.printscale.ai.ui.components.SectionLabel
import com.printscale.ai.ui.components.formatBytes
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(graph: AppGraph, onBack: () -> Unit) {
    val theme by graph.settings.theme.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    var refresh by remember { mutableIntStateOf(0) }
    val storage by produceState(-1L, refresh) { value = graph.history.storageBytes() }
    var confirmClear by remember { mutableStateOf(false) }
    var license by remember { mutableStateOf<Pair<String, String>?>(null) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings", style = MaterialTheme.typography.titleLarge) },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        Column(Modifier.fillMaxSize().padding(pad).verticalScroll(rememberScrollState()).padding(horizontal = 20.dp)) {
            SectionLabel("Theme")
            ThemeChoice.entries.forEach { t ->
                Row(
                    Modifier.fillMaxWidth().selectable(t == theme, role = Role.RadioButton) { graph.settings.setTheme(t) }.padding(vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    RadioButton(selected = t == theme, onClick = null)
                    Text(when (t) {
                        ThemeChoice.SYSTEM -> "Follow system"
                        ThemeChoice.DARK -> "Dark (best for judging colour)"
                        ThemeChoice.LIGHT -> "Light"
                    }, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(start = 8.dp))
                }
            }

            Spacer(Modifier.height(24.dp))
            SectionLabel("Storage")
            Spacer(Modifier.height(6.dp))
            Text(if (storage < 0) "Measuring" else "Processed files and imported copies use ${formatBytes(storage)}.",
                style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.height(10.dp))
            SecondaryButton("Delete processed files", enabled = storage > 0, onClick = { confirmClear = true })

            Spacer(Modifier.height(24.dp))
            SectionLabel("Privacy")
            Spacer(Modifier.height(6.dp))
            Panel {
                Text(
                    "Your artwork never leaves this phone. Upscaling runs on the device with ONNX Runtime; the app has no internet permission, no account and no analytics. " +
                        "Files stay in the app's private storage until you export, share or delete them.",
                    style = MaterialTheme.typography.bodyMedium,
                )
            }

            Spacer(Modifier.height(24.dp))
            SectionLabel("About the AI model")
            Spacer(Modifier.height(6.dp))
            Text(
                "${ModelProvider.MODEL_NAME} by Xintao Wang et al., a 1.2 million parameter super-resolution network trained on degraded real-world images. " +
                    "It enlarges 4× per pass and is bundled in the app (about 10 MB for both checkpoints). " +
                    "Noise reduction interpolates between its standard and weak-denoise checkpoints, as the original project does.",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(10.dp))
            TextButton(onClick = { license = "Real-ESRGAN (BSD-3-Clause)" to readAsset(graph, "models/LICENSE-Real-ESRGAN.txt") }) { Text("Real-ESRGAN licence") }
            TextButton(onClick = { license = "Manrope (OFL)" to readAsset(graph, "OFL-Manrope.txt") }) { Text("Manrope font licence") }
            TextButton(onClick = { license = "Instrument Serif (OFL)" to readAsset(graph, "OFL-InstrumentSerif.txt") }) { Text("Instrument Serif font licence") }
            Spacer(Modifier.height(16.dp))
            Text("Version ${BuildConfig.VERSION_NAME}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(32.dp))
        }
    }

    if (confirmClear) {
        AlertDialog(
            onDismissRequest = { confirmClear = false },
            title = { Text("Delete processed files?") },
            text = { Text("History and all working files are removed from the app. Images you saved to the gallery or Files are not affected.") },
            confirmButton = { TextButton(onClick = { confirmClear = false; scope.launch { graph.history.clearAll(); refresh++ } }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirmClear = false }) { Text("Cancel") } },
        )
    }
    license?.let { (title, text) ->
        AlertDialog(
            onDismissRequest = { license = null },
            title = { Text(title) },
            text = { Text(text, style = MaterialTheme.typography.bodySmall, modifier = Modifier.verticalScroll(rememberScrollState())) },
            confirmButton = { TextButton(onClick = { license = null }) { Text("Close") } },
        )
    }
}

private fun readAsset(graph: AppGraph, path: String): String =
    runCatching { graph.app.assets.open(path).use { it.readBytes().decodeToString() } }.getOrDefault("Not available.")
