package com.printscale.ai.ui.cloud

import android.content.ActivityNotFoundException
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.OpenInNew
import androidx.compose.material.icons.outlined.CheckCircle
import androidx.compose.material.icons.outlined.ContentPaste
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.printscale.ai.AppGraph
import com.printscale.ai.cloud.CloudNotebooks
import com.printscale.ai.ui.components.Note
import com.printscale.ai.ui.components.NoteTone
import com.printscale.ai.ui.components.PrimaryButton
import com.printscale.ai.ui.components.SecondaryButton
import com.printscale.ai.ui.theme.Numeric
import com.printscale.engine.CloudClient
import com.printscale.engine.CloudLink
import com.printscale.engine.ServerInfo
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

private sealed interface Check {
    data object Idle : Check
    data object Checking : Check
    data class Ok(val info: ServerInfo) : Check
    data class Failed(val message: String) : Check
}

/** Connects the app to an AuraSR server running in the user's own Colab or Kaggle notebook. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CloudGpuSheet(graph: AppGraph, onDismiss: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val saved by graph.settings.cloudLink.collectAsStateWithLifecycle()
    var text by remember { mutableStateOf("") }
    var check by remember { mutableStateOf<Check>(Check.Idle) }
    var openError by remember { mutableStateOf<String?>(null) }

    fun verify(link: CloudLink, save: Boolean) {
        check = Check.Checking
        scope.launch {
            check = try {
                val info = withContext(Dispatchers.IO) { CloudClient(link, connectTimeoutMs = 10_000, readTimeoutMs = 20_000).health() }
                if (save) { graph.settings.setCloudLink(link.asText()); text = "" }
                Check.Ok(info)
            } catch (e: Exception) {
                Check.Failed(e.message ?: "Could not reach the server.")
            }
        }
    }
    // Re-check a saved link when the sheet opens: notebook links stop working when the session ends.
    LaunchedEffect(saved) { saved?.let(CloudLink::parse)?.let { verify(it, save = false) } }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = MaterialTheme.colorScheme.surfaceContainer,
    ) {
        Column(Modifier.navigationBarsPadding().padding(horizontal = 20.dp).padding(bottom = 20.dp).verticalScroll(rememberScrollState())) {
            Text("Cloud GPU", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(8.dp))
            Text(
                "Use AuraSR v2, a model about 500 times larger than the one on this phone, running on a free GPU in your own " +
                    "Colab or Kaggle notebook. You still do everything in this app; only the AI step runs in the cloud.",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(16.dp))

            when (val c = check) {
                Check.Checking -> Row(verticalAlignment = Alignment.CenterVertically) {
                    CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp)
                    Spacer(Modifier.width(10.dp)); Text("Checking the server", style = MaterialTheme.typography.bodyMedium)
                }
                is Check.Ok -> Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Outlined.CheckCircle, null, tint = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.width(10.dp))
                    Text("Connected: ${c.info.model} on ${c.info.gpu.ifBlank { c.info.device.uppercase() }}",
                        style = MaterialTheme.typography.titleSmall)
                }
                is Check.Failed -> Note(c.message, NoteTone.ERROR)
                Check.Idle -> {}
            }
            if (saved != null) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Choose Cloud GPU in the editor to use it.", style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.weight(1f))
                    TextButton(onClick = { graph.settings.setCloudLink(null); check = Check.Idle }) { Text("Disconnect") }
                }
                Spacer(Modifier.height(12.dp))
            }

            Text(if (saved == null) "Connect" else "Connect a new server", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            listOf(
                "Open the server notebook below and sign in.",
                "Colab selects a T4 GPU for you. On Kaggle, open Settings and choose Accelerator: GPU T4 x2, with Internet on.",
                "Run all cells. The last one shows a link and a QR code.",
                "Scan the QR code with this phone's camera, or paste the link here.",
            ).forEachIndexed { i, step ->
                Row(Modifier.padding(vertical = 3.dp)) {
                    Text("${i + 1}", style = MaterialTheme.typography.titleSmall.merge(Numeric), fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.primary, modifier = Modifier.width(22.dp))
                    Text(step, style = MaterialTheme.typography.bodyMedium)
                }
            }
            Spacer(Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                SecondaryButton("Open in Colab", icon = Icons.AutoMirrored.Outlined.OpenInNew, modifier = Modifier.weight(1f),
                    onClick = { openError = openUrl(context, CloudNotebooks.colabUrl()) })
                SecondaryButton("Open in Kaggle", icon = Icons.AutoMirrored.Outlined.OpenInNew, modifier = Modifier.weight(1f),
                    onClick = { openError = openUrl(context, CloudNotebooks.kaggleUrl()) })
            }
            openError?.let { Spacer(Modifier.height(6.dp)); Note(it, NoteTone.ERROR) }
            Spacer(Modifier.height(14.dp))
            OutlinedTextField(
                value = text, onValueChange = { text = it; if (check is Check.Failed) check = Check.Idle },
                label = { Text("Server link") }, placeholder = { Text("https://….trycloudflare.com/?key=…") },
                singleLine = true, modifier = Modifier.fillMaxWidth(),
                trailingIcon = {
                    IconButton(onClick = { clipboardText(context)?.let { text = it } }) {
                        Icon(Icons.Outlined.ContentPaste, contentDescription = "Paste link")
                    }
                },
            )
            val parsed = CloudLink.parse(text)
            if (text.isNotBlank() && parsed == null) {
                Spacer(Modifier.height(4.dp))
                Note("That doesn't look like a server link. It starts with https:// and ends with ?key= followed by the key.", NoteTone.ERROR)
            }
            Spacer(Modifier.height(10.dp))
            PrimaryButton(if (check == Check.Checking) "Connecting" else "Connect", enabled = parsed != null && check != Check.Checking,
                modifier = Modifier.fillMaxWidth(), onClick = { parsed?.let { verify(it, save = true) } })
            Spacer(Modifier.height(14.dp))
            Note(
                "When you use the cloud GPU, the cropped artwork is uploaded to your notebook on Google's or Kaggle's servers and " +
                    "the result is downloaded back. The server deletes both once the job is done. Colab's free tier may disconnect " +
                    "notebooks used as servers; Kaggle sessions end after 12 hours. If it stops answering, restart the notebook and connect the new link.",
                NoteTone.WARNING,
            )
        }
    }
}

private fun clipboardText(context: Context): String? =
    context.getSystemService(ClipboardManager::class.java)?.primaryClip?.takeIf { it.itemCount > 0 }
        ?.getItemAt(0)?.coerceToText(context)?.toString()

/** Returns an error message, or null when the browser opened. */
private fun openUrl(context: Context, url: String): String? = try {
    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addCategory(Intent.CATEGORY_BROWSABLE))
    null
} catch (e: ActivityNotFoundException) {
    "No web browser is installed to open the notebook."
}
