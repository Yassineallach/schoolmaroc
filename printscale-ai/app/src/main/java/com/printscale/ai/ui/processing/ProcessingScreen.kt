package com.printscale.ai.ui.processing

import android.graphics.BitmapFactory
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.produceState
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.printscale.ai.AppGraph
import com.printscale.ai.data.JobSpec
import com.printscale.ai.data.Paths
import com.printscale.ai.processing.JobStage
import com.printscale.ai.processing.JobStatus
import com.printscale.ai.ui.components.EmptyState
import com.printscale.ai.ui.components.PrimaryButton
import com.printscale.ai.ui.components.SecondaryButton
import com.printscale.ai.ui.components.cropMarks
import com.printscale.ai.ui.components.formatDuration
import com.printscale.ai.ui.theme.Numeric
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import org.json.JSONObject

private val STAGES = listOf(JobStage.PREPARING, JobStage.ANALYZING, JobStage.UPSCALING, JobStage.FINALIZING)

@Composable
fun ProcessingScreen(graph: AppGraph, jobId: String, onDone: () -> Unit, onLeave: () -> Unit) {
    val status by graph.processing.observe(jobId).collectAsStateWithLifecycle(initialValue = null)
    var confirmCancel by remember { mutableStateOf(false) }
    val paths = remember { Paths(graph.app) }
    val spec by produceState<JobSpec?>(null, jobId) {
        value = withContext(Dispatchers.IO) { runCatching { JobSpec.fromJson(JSONObject(paths.jobSpec(jobId).readText())) }.getOrNull() }
    }
    val thumb by produceState<ImageBitmap?>(null, spec) {
        val s = spec ?: return@produceState
        value = withContext(Dispatchers.IO) {
            runCatching { BitmapFactory.decodeFile(graph.imports.thumb(s.importId).path)?.asImageBitmap() }.getOrNull()
        }
    }
    var now by remember { mutableLongStateOf(System.currentTimeMillis()) }
    LaunchedEffect(Unit) { while (true) { delay(1000); now = System.currentTimeMillis() } }
    LaunchedEffect(status) { if (status == JobStatus.Succeeded) onDone() }
    BackHandler(enabled = status is JobStatus.Running) { onLeave() }

    ProcessingBody(status, thumb, now, onCancel = { confirmCancel = true }, onLeave = onLeave)

    if (confirmCancel) {
        AlertDialog(
            onDismissRequest = { confirmCancel = false },
            title = { Text("Cancel upscaling?") },
            text = { Text("Progress so far will be discarded.") },
            confirmButton = { TextButton(onClick = { confirmCancel = false; graph.processing.cancel(jobId) }) { Text("Cancel upscaling") } },
            dismissButton = { TextButton(onClick = { confirmCancel = false }) { Text("Keep going") } },
        )
    }
}

/** Stateless so every status can be rendered and checked directly. */
@Composable
fun ProcessingBody(status: JobStatus?, thumb: ImageBitmap?, now: Long, onCancel: () -> Unit, onLeave: () -> Unit) {
    Column(
        Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background).safeDrawingPadding().verticalScroll(rememberScrollState()).padding(horizontal = 24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(32.dp))
        Box(Modifier.fillMaxWidth().heightIn(max = 300.dp).height(300.dp), contentAlignment = Alignment.Center) {
            thumb?.let {
                val ratio = it.width.toFloat() / it.height
                Image(
                    it, contentDescription = "Artwork being processed", contentScale = ContentScale.Fit,
                    modifier = Modifier.padding(20.dp).then(
                        if (ratio >= 1) Modifier.fillMaxWidth() else Modifier.height(260.dp),
                    ).cropMarks(MaterialTheme.colorScheme.onBackground),
                )
            }
        }
        Spacer(Modifier.height(28.dp))

        when (val s = status) {
            null -> CircularProgressIndicator()
            is JobStatus.Running -> RunningBlock(s, now, onCancel)
            JobStatus.Succeeded -> CircularProgressIndicator()
            is JobStatus.Failed -> {
                val cancelled = s.message == "Cancelled."
                EmptyState(
                    if (cancelled) "Cancelled" else "Processing stopped",
                    if (cancelled) "Nothing was saved. Temporary files were removed." else s.message,
                ) { PrimaryButton("Back to editor", onClick = onLeave) }
            }
            JobStatus.Cancelled -> EmptyState("Cancelled", "Nothing was saved. Temporary files were removed.") {
                PrimaryButton("Back to editor", onClick = onLeave)
            }
            JobStatus.Missing -> EmptyState("Job not found", "This job is no longer tracked.") {
                PrimaryButton("Back", onClick = onLeave)
            }
        }
        Spacer(Modifier.height(32.dp))
    }

}

@Composable
private fun RunningBlock(s: JobStatus.Running, now: Long, onCancel: () -> Unit) {
    Column(Modifier.fillMaxWidth()) {
        Text(s.stage.label, style = MaterialTheme.typography.headlineMedium,
            modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite })
        Spacer(Modifier.height(12.dp))
        val determinate = s.stage == JobStage.UPSCALING && s.total > 1
        if (determinate) {
            val f = (s.done.toFloat() / s.total).coerceIn(0f, 1f)
            LinearProgressIndicator(progress = { f }, modifier = Modifier.fillMaxWidth().height(6.dp))
            Spacer(Modifier.height(8.dp))
            Row {
                Text("${(f * 100).toInt()}% of the artwork through the model", style = MaterialTheme.typography.bodySmall.merge(Numeric),
                    color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.weight(1f))
                s.etaMs?.let {
                    Text("about ${formatDuration(it)} left", style = MaterialTheme.typography.bodySmall.merge(Numeric),
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        } else {
            // No measurable progress in these stages, so the bar does not pretend to have any.
            LinearProgressIndicator(modifier = Modifier.fillMaxWidth().height(6.dp))
        }
        if (s.startedAt > 0) {
            Spacer(Modifier.height(4.dp))
            Text("Elapsed ${formatDuration(now - s.startedAt)}", style = MaterialTheme.typography.bodySmall.merge(Numeric),
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Spacer(Modifier.height(24.dp))
        val current = STAGES.indexOf(s.stage)
        STAGES.forEachIndexed { i, st ->
            Row(Modifier.padding(vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(20.dp), contentAlignment = Alignment.Center) {
                    when {
                        i < current -> Icon(Icons.Outlined.Check, contentDescription = "Done", tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(18.dp))
                        i == current -> CircularProgressIndicator(Modifier.size(14.dp), strokeWidth = 2.dp)
                        else -> Box(Modifier.size(6.dp).cropMarks(MaterialTheme.colorScheme.outline, length = 3.dp, gap = 1.dp, stroke = 1.dp))
                    }
                }
                Spacer(Modifier.width(12.dp))
                Text(st.label, style = MaterialTheme.typography.bodyMedium,
                    color = if (i <= current) MaterialTheme.colorScheme.onBackground else MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
        Spacer(Modifier.height(20.dp))
        Text("You can leave this screen or the app. Processing continues in the background and a notification shows progress.",
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(20.dp))
        Row(horizontalArrangement = Arrangement.End, modifier = Modifier.fillMaxWidth()) {
            SecondaryButton("Cancel", onClick = onCancel)
        }
    }
}
