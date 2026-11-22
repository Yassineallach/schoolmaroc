package com.printscale.ai.ui.cloud

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.OpenInNew
import androidx.compose.material.icons.outlined.DriveFolderUpload
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.printscale.ai.cloud.CloudNotebooks
import com.printscale.ai.ui.components.Note
import com.printscale.ai.ui.components.NoteTone
import com.printscale.ai.ui.components.PrimaryButton
import com.printscale.ai.ui.components.SecondaryButton
import com.printscale.ai.ui.theme.Numeric
import java.io.File

/** The artwork the user may want to hand to Drive or Files before opening a notebook. */
data class Artwork(val file: File, val displayName: String)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StudioQualitySheet(artwork: Artwork?, onDismiss: () -> Unit) {
    val context = LocalContext.current
    var error by remember { mutableStateOf<String?>(null) }
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = MaterialTheme.colorScheme.surfaceContainer,
    ) {
        Column(Modifier.navigationBarsPadding().padding(horizontal = 20.dp).padding(bottom = 20.dp).verticalScroll(rememberScrollState())) {
            Text("Studio quality upscaling", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(8.dp))
            Text(
                "Runs AuraSR v2, a model about 500 times larger than the one on this phone, on a free cloud GPU in " +
                    "Google Colab or Kaggle. Worth it for large prints and fine texture. You need a Google or Kaggle account.",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(16.dp))
            listOf(
                if (artwork != null) "Save this artwork to Google Drive or Files (button below)." else "Have your artwork in Google Drive or on this phone.",
                "Open a notebook and sign in.",
                "Colab selects a T4 GPU for you. On Kaggle, open Settings and choose Accelerator: GPU T4 x2, with Internet on.",
                "Run all cells, pick your print size, upload the artwork, then download the zip.",
            ).forEachIndexed { i, step ->
                Row(Modifier.padding(vertical = 4.dp)) {
                    Text("${i + 1}", style = MaterialTheme.typography.titleSmall.merge(Numeric), fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.primary, modifier = Modifier.width(22.dp))
                    Text(step, style = MaterialTheme.typography.bodyMedium)
                }
            }
            Spacer(Modifier.height(12.dp))
            Note("Your artwork is uploaded to Google's or Kaggle's servers while the notebook runs. The PrintScale app itself never uploads anything.",
                NoteTone.WARNING)
            Spacer(Modifier.height(20.dp))
            if (artwork != null) {
                SecondaryButton("Save artwork to Drive or Files", icon = Icons.Outlined.DriveFolderUpload, modifier = Modifier.fillMaxWidth(),
                    onClick = { error = shareArtwork(context, artwork) })
                Spacer(Modifier.height(10.dp))
            }
            PrimaryButton("Open in Colab", icon = Icons.AutoMirrored.Outlined.OpenInNew, modifier = Modifier.fillMaxWidth(),
                onClick = { error = openUrl(context, CloudNotebooks.colabUrl()) })
            Spacer(Modifier.height(10.dp))
            SecondaryButton("Open in Kaggle", icon = Icons.AutoMirrored.Outlined.OpenInNew, modifier = Modifier.fillMaxWidth(),
                onClick = { error = openUrl(context, CloudNotebooks.kaggleUrl()) })
            error?.let { Spacer(Modifier.height(10.dp)); Note(it, NoteTone.ERROR) }
        }
    }
}

/** Returns an error message, or null when the browser opened. */
private fun openUrl(context: Context, url: String): String? = try {
    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)).addCategory(Intent.CATEGORY_BROWSABLE))
    null
} catch (e: ActivityNotFoundException) {
    "No web browser is installed to open the notebook."
}

private fun shareArtwork(context: Context, artwork: Artwork): String? = try {
    // Share a copy under its real name; the app stores imports without file names.
    val dir = File(context.cacheDir, "exports/share").apply { deleteRecursively(); mkdirs() }
    val (ext, mime) = sniffFormat(artwork.file)
    val base = artwork.displayName.replace(Regex("[\\\\/:*?\"<>|]"), "_").substringBeforeLast('.').ifBlank { "Artwork" }
    val copy = artwork.file.copyTo(File(dir, "$base.$ext"), overwrite = true)
    val uri = FileProvider.getUriForFile(context, context.packageName + ".files", copy)
    val send = Intent(Intent.ACTION_SEND).apply {
        type = mime
        putExtra(Intent.EXTRA_STREAM, uri)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(send, "Save artwork to"))
    null
} catch (e: Exception) {
    "Could not share the artwork: ${e.message}"
}

/** Real format from the file's first bytes; import names can be missing or wrong. */
private fun sniffFormat(file: File): Pair<String, String> {
    val h = ByteArray(12)
    val n = file.inputStream().use { it.read(h) }
    return when {
        n >= 4 && h[0] == 0x89.toByte() && h[1] == 'P'.code.toByte() -> "png" to "image/png"
        n >= 2 && h[0] == 0xFF.toByte() && h[1] == 0xD8.toByte() -> "jpg" to "image/jpeg"
        n >= 12 && String(h, 0, 4, Charsets.ISO_8859_1) == "RIFF" && String(h, 8, 4, Charsets.ISO_8859_1) == "WEBP" -> "webp" to "image/webp"
        else -> (file.extension.ifBlank { "img" }) to "image/*"
    }
}
