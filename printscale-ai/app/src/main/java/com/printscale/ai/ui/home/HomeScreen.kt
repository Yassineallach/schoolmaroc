package com.printscale.ai.ui.home

import android.graphics.BitmapFactory
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowForward
import androidx.compose.material.icons.outlined.AddPhotoAlternate
import androidx.compose.material.icons.outlined.FolderOpen
import androidx.compose.material.icons.outlined.History
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Snackbar
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.printscale.ai.AppGraph
import com.printscale.ai.data.HistoryItem
import com.printscale.ai.data.HistoryState
import com.printscale.ai.data.Paths
import com.printscale.ai.ui.components.BrandMark
import com.printscale.ai.ui.components.EmptyState
import com.printscale.ai.ui.components.PrimaryButton
import com.printscale.ai.ui.components.SecondaryButton
import com.printscale.ai.ui.components.SectionLabel
import com.printscale.ai.ui.components.cropMarks
import com.printscale.ai.ui.components.formatBytes
import com.printscale.ai.ui.theme.Numeric
import com.printscale.engine.PrintMath
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.DateFormat
import java.util.Date

/** What the user picked on Home before choosing an image, carried into the editor. */
private data class Intent(val preset: String? = null, val factor: Int? = null)

@Composable
fun HomeScreen(
    graph: AppGraph,
    openEditor: (String, String?, Int?) -> Unit,
    openResult: (String) -> Unit,
    openProcessing: (String) -> Unit,
    openHistory: () -> Unit,
    openSettings: () -> Unit,
) {
    val scope = rememberCoroutineScope()
    var pending by remember { mutableStateOf(Intent()) }
    var importing by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val history by graph.history.state.collectAsStateWithLifecycle()
    val active by graph.processing.active().collectAsStateWithLifecycle(initialValue = emptyList())
    val shared by graph.sharedImage.collectAsStateWithLifecycle()
    val storage by produceState(0L, history) { value = graph.history.storageBytes() }

    LaunchedEffect(Unit) { graph.history.load() }

    fun importUri(uri: Uri) {
        importing = true
        error = null
        scope.launch {
            try {
                val info = graph.imports.import(uri)
                openEditor(info.id, pending.preset, pending.factor)
            } catch (e: Exception) {
                error = e.message ?: "The image could not be opened."
            } finally {
                importing = false
                pending = Intent()
            }
        }
    }

    LaunchedEffect(shared) {
        shared?.let { graph.sharedImage.value = null; importUri(it) }
    }

    val photoPicker = rememberLauncherForActivityResult(ActivityResultContracts.PickVisualMedia()) { uri ->
        if (uri != null) importUri(uri)
    }
    val filePicker = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) importUri(uri)
    }
    fun pick(intent: Intent) {
        pending = intent
        photoPicker.launch(PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly))
    }

    Box(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)) {
        Column(
            Modifier.fillMaxSize().safeDrawingPadding().verticalScroll(rememberScrollState()).padding(horizontal = 20.dp),
        ) {
            Row(Modifier.fillMaxWidth().padding(top = 8.dp), verticalAlignment = Alignment.CenterVertically) {
                BrandMark(30.dp)
                Spacer(Modifier.width(10.dp))
                Text("PrintScale", style = MaterialTheme.typography.headlineMedium, modifier = Modifier.weight(1f))
                IconButton(onClick = openHistory) { Icon(Icons.Outlined.History, contentDescription = "History") }
                IconButton(onClick = openSettings) { Icon(Icons.Outlined.Settings, contentDescription = "Settings") }
            }

            Spacer(Modifier.height(36.dp))
            Text("Small artwork in.\nPrint-size files out.", style = MaterialTheme.typography.displayLarge)
            Spacer(Modifier.height(14.dp))
            Text(
                "Upscale with a Real-ESRGAN model that runs on this phone, size the file for a real print, and export it at the DPI your print lab asks for.",
                style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(24.dp))
            PrimaryButton("Upscale artwork", onClick = { pick(Intent()) }, enabled = !importing,
                icon = Icons.Outlined.AddPhotoAlternate, modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(10.dp))
            SecondaryButton("Open from Files", onClick = {
                pending = Intent(); filePicker.launch(arrayOf("image/png", "image/jpeg", "image/webp", "image/*"))
            }, enabled = !importing, icon = Icons.Outlined.FolderOpen, modifier = Modifier.fillMaxWidth())

            if (active.isNotEmpty()) {
                Spacer(Modifier.height(16.dp))
                Surface(
                    onClick = { openProcessing(active.first()) }, shape = MaterialTheme.shapes.medium,
                    color = MaterialTheme.colorScheme.primaryContainer, modifier = Modifier.fillMaxWidth(),
                ) {
                    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp, color = MaterialTheme.colorScheme.onPrimaryContainer)
                        Spacer(Modifier.width(12.dp))
                        Text("An upscale is running. View progress", style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.onPrimaryContainer, modifier = Modifier.weight(1f))
                        Icon(Icons.AutoMirrored.Outlined.ArrowForward, null, tint = MaterialTheme.colorScheme.onPrimaryContainer)
                    }
                }
            }

            Spacer(Modifier.height(36.dp))
            SectionLabel("Quick upscale")
            Spacer(Modifier.height(4.dp))
            Text("Pick a factor, then an image.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                listOf(2 to "1024 → 2048 px", 4 to "1024 → 4096 px", 8 to "1024 → 8192 px").forEach { (f, ex) ->
                    FactorTile(f, ex, Modifier.weight(1f)) { pick(Intent(factor = f)) }
                }
            }

            Spacer(Modifier.height(36.dp))
            SectionLabel("Print size presets")
            Spacer(Modifier.height(4.dp))
            Text("Pixel sizes at 300 DPI. All 14 sizes and other DPIs are in the editor.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(12.dp))
            Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                listOf("8x10", "11x14", "16x20", "18x24", "24x36", "36x48").forEach { id ->
                    val p = PrintMath.preset(id)!!
                    PresetTile(p.shortIn, p.longIn) { pick(Intent(preset = id)) }
                }
            }

            Spacer(Modifier.height(36.dp))
            SectionLabel("Recent projects") {
                val hasItems = (history as? HistoryState.Loaded)?.items?.isNotEmpty() == true
                if (hasItems) TextButton(onClick = openHistory) { Text("All projects") }
            }
            when (val h = history) {
                HistoryState.Loading -> Box(Modifier.fillMaxWidth().padding(24.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(Modifier.size(24.dp), strokeWidth = 2.dp)
                }
                is HistoryState.Failed -> Text(h.message, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium)
                is HistoryState.Loaded -> if (h.items.isEmpty()) {
                    EmptyState("Nothing here yet", "Upscaled artwork appears here, with its print size and where you saved it.")
                } else {
                    Spacer(Modifier.height(8.dp))
                    h.items.take(3).forEach { RecentRow(graph, it) { openResult(it.id) } }
                }
            }
            if (storage > 0) {
                Spacer(Modifier.height(20.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Working files on this phone: ${formatBytes(storage)}", style = MaterialTheme.typography.bodySmall.merge(Numeric),
                        color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.weight(1f))
                    TextButton(onClick = openSettings) { Text("Manage") }
                }
            }
            Spacer(Modifier.height(32.dp))
        }

        if (importing) {
            Box(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background.copy(alpha = 0.85f)), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(14.dp))
                    Text("Reading image", style = MaterialTheme.typography.titleMedium)
                }
            }
        }
        error?.let { msg ->
            Snackbar(
                modifier = Modifier.align(Alignment.BottomCenter).safeDrawingPadding().padding(16.dp),
                action = { TextButton(onClick = { error = null }) { Text("Dismiss") } },
            ) { Text(msg) }
        }
    }
}

@Composable
private fun FactorTile(factor: Int, example: String, modifier: Modifier, onClick: () -> Unit) {
    Surface(
        onClick = onClick, modifier = modifier, shape = MaterialTheme.shapes.medium,
        color = MaterialTheme.colorScheme.surfaceContainer, border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    ) {
        Column(Modifier.padding(horizontal = 14.dp, vertical = 14.dp)) {
            Text("$factor×", style = MaterialTheme.typography.displaySmall)
            Spacer(Modifier.height(2.dp))
            Text(example, style = MaterialTheme.typography.labelSmall.merge(Numeric), color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun PresetTile(shortIn: Double, longIn: Double, onClick: () -> Unit) {
    val (w, h) = PrintMath.pixels(shortIn, 300) to PrintMath.pixels(longIn, 300)
    Surface(
        onClick = onClick, shape = MaterialTheme.shapes.medium, color = MaterialTheme.colorScheme.surfaceContainer,
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    ) {
        Column(Modifier.padding(16.dp).width(118.dp)) {
            // A proportional outline of the print, framed with crop marks.
            Box(Modifier.height(64.dp).fillMaxWidth(), contentAlignment = Alignment.Center) {
                val hDp = 50.dp
                val wDp = hDp * (shortIn / longIn).toFloat()
                Box(
                    Modifier.size(wDp, hDp).background(MaterialTheme.colorScheme.surfaceContainerHighest)
                        .cropMarks(MaterialTheme.colorScheme.onSurfaceVariant, length = 6.dp, gap = 3.dp, stroke = 1.dp),
                )
            }
            Spacer(Modifier.height(10.dp))
            Text("${PrintMath.formatInches(shortIn)} × ${PrintMath.formatInches(longIn)} in", style = MaterialTheme.typography.titleSmall)
            Text("$w × $h px", style = MaterialTheme.typography.labelSmall.merge(Numeric), color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun RecentRow(graph: AppGraph, item: HistoryItem, onClick: () -> Unit) {
    val paths = remember { Paths(graph.app) }
    val thumb by produceState<androidx.compose.ui.graphics.ImageBitmap?>(null, item.id) {
        value = withContext(Dispatchers.IO) {
            runCatching {
                BitmapFactory.decodeFile(paths.jobPreview(item.id).path, BitmapFactory.Options().apply { inSampleSize = 8 })?.asImageBitmap()
            }.getOrNull()
        }
    }
    Row(
        Modifier.fillMaxWidth().clip(MaterialTheme.shapes.medium).clickable(role = Role.Button, onClick = onClick).padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.size(56.dp).clip(MaterialTheme.shapes.small).background(MaterialTheme.colorScheme.surfaceContainerHigh)) {
            thumb?.let { Image(it, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize()) }
        }
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text(item.displayName, style = MaterialTheme.typography.titleSmall, maxLines = 1)
            Text("${item.finalW} × ${item.finalH} px · ${PrintMath.formatFactor(item.effectiveScale)}",
                style = MaterialTheme.typography.bodySmall.merge(Numeric), color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text(DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT).format(Date(item.createdAt)),
                style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Normal)
        }
    }
}
