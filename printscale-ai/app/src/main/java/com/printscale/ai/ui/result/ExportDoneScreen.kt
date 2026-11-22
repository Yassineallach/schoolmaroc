package com.printscale.ai.ui.result

import android.content.ActivityNotFoundException
import android.net.Uri
import androidx.compose.foundation.background
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.OpenInNew
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.printscale.ai.AppGraph
import com.printscale.ai.data.HistoryItem
import com.printscale.ai.data.Paths
import com.printscale.ai.export.ExportFormat
import com.printscale.ai.ui.components.BrandMark
import com.printscale.ai.ui.components.Note
import com.printscale.ai.ui.components.NoteTone
import com.printscale.ai.ui.components.Panel
import com.printscale.ai.ui.components.PrimaryButton
import com.printscale.ai.ui.components.SecondaryButton
import com.printscale.ai.ui.components.StatRow
import com.printscale.ai.ui.components.formatBytes
import com.printscale.engine.PrintMath
import java.io.File

@Composable
fun ExportDoneScreen(graph: AppGraph, jobId: String, onDone: () -> Unit, onBack: () -> Unit) {
    val context = LocalContext.current
    val item by produceState<HistoryItem?>(null, jobId) { value = graph.history.get(jobId) }
    var error by remember { mutableStateOf<String?>(null) }
    val record = item?.exports?.lastOrNull()

    Column(Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).safeDrawingPadding().verticalScroll(rememberScrollState()).padding(horizontal = 24.dp)) {
        Spacer(Modifier.height(40.dp))
        if (item == null || record == null) {
            Box(Modifier.fillMaxWidth().padding(40.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            return@Column
        }
        val it = item!!
        val format = ExportFormat.forFileName(record.fileName)
        BrandMark(40.dp)
        Spacer(Modifier.height(20.dp))
        Text("Saved", style = MaterialTheme.typography.displayMedium)
        Text(record.fileName, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(24.dp))
        Panel {
            StatRow("Resolution", "${it.finalW} × ${it.finalH} px")
            StatRow("File size", formatBytes(record.sizeBytes))
            if (it.printWIn != null && it.printHIn != null) {
                StatRow("Print size", PrintMath.describe(it.printWIn, it.printHIn))
            }
            StatRow("DPI", if (format == ExportFormat.WEBP) "${it.dpi ?: 300} (WebP files carry no DPI tag)" else "${it.dpi ?: 300}")
            StatRow("Format", record.format)
            StatRow("Location", record.location)
        }
        if (record.sizeBytes > PrintMath.ETSY_FILE_LIMIT_BYTES) {
            Spacer(Modifier.height(10.dp))
            Note("This file is over Etsy's 20 MB limit for digital downloads. Export it as \"Etsy download\" to fit, or share it through a download link.", NoteTone.WARNING)
        }
        Spacer(Modifier.height(24.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            SecondaryButton("Open with", icon = Icons.AutoMirrored.Outlined.OpenInNew, modifier = Modifier.weight(1f), onClick = {
                try {
                    context.startActivity(graph.exporter.viewIntent(Uri.parse(record.uri), format))
                } catch (e: ActivityNotFoundException) {
                    error = "No installed app can open ${format.label} files."
                } catch (e: SecurityException) {
                    error = "Access to the saved file was revoked."
                }
            })
            SecondaryButton("Share", icon = Icons.Outlined.Share, modifier = Modifier.weight(1f), onClick = {
                val cached = File(Paths(graph.app).exports, record.fileName)
                try {
                    if (cached.exists()) context.startActivity(graph.exporter.shareIntent(cached, format))
                    else context.startActivity(android.content.Intent.createChooser(
                        android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                            type = format.mime
                            putExtra(android.content.Intent.EXTRA_STREAM, Uri.parse(record.uri))
                            addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
                        }, "Share artwork"))
                } catch (e: Exception) {
                    error = "Sharing failed: ${e.message}"
                }
            })
        }
        error?.let { Spacer(Modifier.height(10.dp)); Note(it, NoteTone.ERROR) }
        Spacer(Modifier.height(12.dp))
        PrimaryButton("Done", onClick = onDone, modifier = Modifier.fillMaxWidth())
        Spacer(Modifier.height(8.dp))
        androidx.compose.material3.TextButton(onClick = onBack, modifier = Modifier.fillMaxWidth()) { Text("Back to result") }
        Spacer(Modifier.height(24.dp))
    }
}
