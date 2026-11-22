package com.printscale.ai.ui.history

import android.graphics.BitmapFactory
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.DeleteOutline
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
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
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.printscale.ai.AppGraph
import com.printscale.ai.data.HistoryItem
import com.printscale.ai.data.HistoryState
import com.printscale.ai.data.Paths
import com.printscale.ai.ui.components.EmptyState
import com.printscale.ai.ui.components.SecondaryButton
import com.printscale.ai.ui.theme.Numeric
import com.printscale.engine.PrintMath
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.DateFormat
import java.util.Date

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(graph: AppGraph, onBack: () -> Unit, openResult: (String) -> Unit) {
    val state by graph.history.state.collectAsStateWithLifecycle()
    val scope = rememberCoroutineScope()
    var confirmDelete by remember { mutableStateOf<HistoryItem?>(null) }
    var confirmClear by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { graph.history.load() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("History", style = MaterialTheme.typography.titleLarge) },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") } },
                actions = {
                    if ((state as? HistoryState.Loaded)?.items?.isNotEmpty() == true) {
                        TextButton(onClick = { confirmClear = true }) { Text("Clear all") }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        when (val s = state) {
            HistoryState.Loading -> Box(Modifier.fillMaxSize().padding(pad), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            is HistoryState.Failed -> Box(Modifier.fillMaxSize().padding(pad).padding(20.dp)) {
                EmptyState("History unavailable", s.message) { SecondaryButton("Try again", onClick = { scope.launch { graph.history.load() } }) }
            }
            is HistoryState.Loaded -> if (s.items.isEmpty()) {
                Box(Modifier.fillMaxSize().padding(pad).padding(20.dp)) {
                    EmptyState("No projects yet", "Each upscale is listed here with its sizes and where you saved it.")
                }
            } else {
                LazyColumn(Modifier.fillMaxSize().padding(pad)) {
                    items(s.items, key = { it.id }) { item ->
                        HistoryRow(graph, item, onOpen = { openResult(item.id) }, onDelete = { confirmDelete = item })
                        HorizontalDivider(Modifier.padding(horizontal = 20.dp), color = MaterialTheme.colorScheme.outlineVariant)
                    }
                }
            }
        }
    }

    confirmDelete?.let { item ->
        AlertDialog(
            onDismissRequest = { confirmDelete = null },
            title = { Text("Delete this project?") },
            text = { Text("Removes the processed file from the app. Copies you saved to the gallery or Files stay where they are.") },
            confirmButton = { TextButton(onClick = { confirmDelete = null; scope.launch { graph.history.delete(item.id) } }) { Text("Delete") } },
            dismissButton = { TextButton(onClick = { confirmDelete = null }) { Text("Keep") } },
        )
    }
    if (confirmClear) {
        AlertDialog(
            onDismissRequest = { confirmClear = false },
            title = { Text("Clear all history?") },
            text = { Text("Removes every processed file and imported copy from the app. Saved exports are not touched.") },
            confirmButton = { TextButton(onClick = { confirmClear = false; scope.launch { graph.history.clearAll() } }) { Text("Clear all") } },
            dismissButton = { TextButton(onClick = { confirmClear = false }) { Text("Cancel") } },
        )
    }
}

@Composable
private fun HistoryRow(graph: AppGraph, item: HistoryItem, onOpen: () -> Unit, onDelete: () -> Unit) {
    val paths = remember { Paths(graph.app) }
    val thumb by produceState<ImageBitmap?>(null, item.id) {
        value = withContext(Dispatchers.IO) {
            runCatching { BitmapFactory.decodeFile(paths.jobPreview(item.id).path, BitmapFactory.Options().apply { inSampleSize = 8 })?.asImageBitmap() }.getOrNull()
        }
    }
    Row(
        Modifier.fillMaxWidth().clickable(role = Role.Button, onClick = onOpen).padding(start = 20.dp, end = 8.dp, top = 14.dp, bottom = 14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.size(72.dp).clip(MaterialTheme.shapes.small).background(MaterialTheme.colorScheme.surfaceContainerHigh)) {
            thumb?.let { Image(it, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize()) }
        }
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text(item.displayName, style = MaterialTheme.typography.titleSmall, maxLines = 1)
            Text(DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT).format(Date(item.createdAt)),
                style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("${item.originalW} × ${item.originalH} → ${item.finalW} × ${item.finalH} px · ${PrintMath.formatFactor(item.effectiveScale)}",
                style = MaterialTheme.typography.bodySmall.merge(Numeric))
            item.exports.lastOrNull()?.let {
                Text("Saved: ${it.location}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1)
            }
        }
        IconButton(onClick = onDelete) { Icon(Icons.Outlined.DeleteOutline, "Delete ${item.displayName}") }
    }
}
