package com.printscale.ai.ui.result

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.aspectRatio
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Checkroom
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.Download
import androidx.compose.material.icons.outlined.Refresh
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.Storefront
import androidx.compose.material.icons.outlined.Tune
import androidx.compose.material.icons.outlined.ZoomIn
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.printscale.ai.AppGraph
import com.printscale.ai.data.HistoryItem
import com.printscale.ai.export.ExportFormat
import com.printscale.ai.export.ExportOptions
import com.printscale.ai.ui.components.ChipShape
import com.printscale.ai.ui.components.EmptyState
import com.printscale.ai.ui.components.Note
import com.printscale.ai.ui.components.NoteTone
import com.printscale.ai.ui.components.Panel
import com.printscale.ai.ui.components.PrimaryButton
import com.printscale.ai.ui.components.SecondaryButton
import com.printscale.ai.ui.components.SectionLabel
import com.printscale.ai.ui.components.StatRow
import com.printscale.ai.ui.components.cropMarks
import com.printscale.ai.ui.components.formatBytes
import com.printscale.ai.ui.components.formatDuration
import com.printscale.ai.ui.theme.Numeric
import com.printscale.engine.FileNaming
import com.printscale.engine.PrintMath

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultScreen(graph: AppGraph, jobId: String, onClose: () -> Unit, onUpscaleAgain: (String) -> Unit, onExported: () -> Unit,
                 onPrep: (String) -> Unit = {}) {
    val vm: ResultViewModel = viewModel(key = "result-$jobId") { ResultViewModel(graph, jobId) }
    val ui by vm.ui.collectAsStateWithLifecycle()
    val context = LocalContext.current
    val snackbar = remember { SnackbarHostState() }
    var mode by remember { mutableStateOf(CompareMode.SPLIT) }
    var showExport by remember { mutableStateOf(false) }

    LaunchedEffect(ui.message) { ui.message?.let { snackbar.showSnackbar(it); vm.clearMessage() } }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Result", style = MaterialTheme.typography.titleLarge) },
                navigationIcon = { IconButton(onClick = onClose) { Icon(Icons.Outlined.Close, "Close and go home") } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        val item = ui.item
        when {
            ui.loading -> Box(Modifier.fillMaxSize().padding(pad), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            item == null || ui.before == null || ui.after == null -> Box(Modifier.fillMaxSize().padding(pad).padding(20.dp)) {
                EmptyState("Result unavailable", ui.error ?: "Unknown error.") { SecondaryButton("Go home", onClick = onClose) }
            }
            else -> Column(Modifier.fillMaxSize().padding(pad).verticalScroll(rememberScrollState())) {
                val inspect = ui.inspect
                val ratio = ui.after!!.width.toFloat() / ui.after!!.height
                Box(Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 12.dp), contentAlignment = Alignment.Center) {
                    val viewerMod = Modifier.fillMaxWidth().heightIn(max = 460.dp)
                        .aspectRatio(if (inspect != null) 1f else ratio.coerceIn(0.5f, 2f))
                        .cropMarks(MaterialTheme.colorScheme.onBackground)
                    if (inspect != null) {
                        CompareViewer(inspect.before, inspect.after, mode, item.hasAlpha, viewerMod)
                    } else {
                        CompareViewer(ui.before!!, ui.after!!, mode, item.hasAlpha, viewerMod,
                            onTapImage = if (ui.inspectPicking) vm::inspectAt else null)
                    }
                    if (ui.inspectLoading) CircularProgressIndicator()
                }
                Column(Modifier.padding(horizontal = 20.dp)) {
                    SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                        CompareMode.entries.forEachIndexed { i, m ->
                            SegmentedButton(mode == m, { mode = m }, SegmentedButtonDefaults.itemShape(i, CompareMode.entries.size)) { Text(m.label) }
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                    when {
                        inspect != null -> Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("100% crop at ${inspect.rect.left}, ${inspect.rect.top} (${inspect.rect.width()} × ${inspect.rect.height()} px). Original shown enlarged with bilinear filtering.",
                                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.weight(1f))
                            TextButton(onClick = vm::endInspect) { Text("Full view") }
                        }
                        ui.inspectPicking -> Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Tap the area you want to inspect at 100%.", style = MaterialTheme.typography.bodySmall, modifier = Modifier.weight(1f))
                            TextButton(onClick = vm::endInspect) { Text("Cancel") }
                        }
                        ui.masterAvailable -> TextButton(onClick = vm::startInspect) {
                            Icon(Icons.Outlined.ZoomIn, null, Modifier.size(18.dp)); Text("  Inspect detail at 100%")
                        }
                        else -> {}
                    }
                    Text("Pinch to zoom, double tap to reset. The full view shows a reduced preview; use 100% inspection to judge fine detail.",
                        style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)

                    Spacer(Modifier.height(20.dp))
                    StatsPanel(item)
                    Spacer(Modifier.height(20.dp))

                    if (!ui.masterAvailable) {
                        Note("The full-resolution file was removed from this phone, so it can no longer be exported.", NoteTone.ERROR)
                    } else {
                        PrimaryButton(ui.busy ?: "Save PNG to gallery", enabled = ui.busy == null, icon = Icons.Outlined.Download,
                            modifier = Modifier.fillMaxWidth(), onClick = {
                                vm.export(ExportOptions(ExportFormat.PNG, fileName = vm.suggestedName(ExportFormat.PNG)), null, onExported)
                            })
                        Spacer(Modifier.height(10.dp))
                        SecondaryButton("Save for Etsy (under 20 MB)", enabled = ui.busy == null && vm.unavailable(ExportFormat.ETSY) == null,
                            icon = Icons.Outlined.Storefront, modifier = Modifier.fillMaxWidth(), onClick = {
                                vm.export(ExportOptions(ExportFormat.ETSY, fileName = vm.suggestedName(ExportFormat.ETSY)), null, onExported)
                            })
                        Spacer(Modifier.height(10.dp))
                        SecondaryButton("Prepare for DTF / DTG", enabled = ui.busy == null, icon = Icons.Outlined.Checkroom,
                            modifier = Modifier.fillMaxWidth(), onClick = { vm.prepareForPrint(onPrep) })
                        Spacer(Modifier.height(10.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            SecondaryButton("Share", onClick = { vm.share { context.startActivity(it) } }, enabled = ui.busy == null,
                                icon = Icons.Outlined.Share, modifier = Modifier.weight(1f))
                            SecondaryButton("Export as", onClick = { showExport = true }, enabled = ui.busy == null,
                                icon = Icons.Outlined.Tune, modifier = Modifier.weight(1f))
                        }
                    }
                    Spacer(Modifier.height(10.dp))
                    TextButton(onClick = { onUpscaleAgain(item.importId) }, modifier = Modifier.fillMaxWidth()) {
                        Icon(Icons.Outlined.Refresh, null, Modifier.size(18.dp)); Text("  Upscale again with other settings")
                    }

                    Spacer(Modifier.height(24.dp))
                }
            }
        }
    }

    if (showExport && ui.item != null) {
        ExportSheet(vm, ui.item!!, onDismiss = { showExport = false }, onExported = { showExport = false; onExported() })
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun StatsPanel(item: HistoryItem) {
    Panel {
        Text("${item.finalW} × ${item.finalH} px", style = MaterialTheme.typography.headlineLarge.merge(Numeric))
        Text("${PrintMath.formatFactor(item.effectiveScale)} from your ${item.preparedW} × ${item.preparedH} px crop",
            style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(10.dp)); HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant); Spacer(Modifier.height(6.dp))
        StatRow("File", "PNG, ${formatBytes(item.masterBytes)}, lossless")
        if (item.masterBytes > PrintMath.ETSY_FILE_LIMIT_BYTES) {
            Note("The PNG is over Etsy's 20 MB limit for digital downloads. Use Save for Etsy to get a JPEG that fits.", NoteTone.WARNING,
                Modifier.padding(vertical = 4.dp))
        }
        if (item.dpi != null && item.printWIn != null && item.printHIn != null) {
            StatRow("Print size", "${PrintMath.describe(item.printWIn, item.printHIn)} at ${item.dpi} DPI")
        } else {
            StatRow("DPI tag", "300 (no print size chosen)")
        }
        val aiW = item.preparedW * 4
        val ai = if (item.engine == com.printscale.ai.data.JobSpec.ENGINE_CLOUD) "AuraSR 4× (cloud GPU)" else "AI 4×"
        StatRow("Method", when {
            !item.aiUsed -> "Lanczos resize only"
            item.finalW > aiW * 1.02 -> "$ai to $aiW px wide, then Lanczos"
            item.finalW < aiW * 0.98 -> "$ai, then downsampled"
            else -> ai
        })
        StatRow("Processing time", formatDuration(item.durationMs))
        Spacer(Modifier.height(12.dp))
        Text("Largest print at each resolution", style = MaterialTheme.typography.titleSmall)
        Spacer(Modifier.height(4.dp))
        PrintMath.DPI_OPTIONS.forEach { o ->
            StatRow("${o.dpi} DPI", "${PrintMath.formatInches(PrintMath.maxInches(item.finalW, o.dpi))} × ${PrintMath.formatInches(PrintMath.maxInches(item.finalH, o.dpi))} in")
        }
        val dpi = item.dpi ?: 300
        val covered = PrintMath.coveredPresets(item.finalW, item.finalH, dpi)
        if (covered.isNotEmpty()) {
            Spacer(Modifier.height(8.dp))
            Text("Preset sizes covered at $dpi DPI", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(6.dp))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                covered.forEach {
                    val s = it.oriented(item.finalW > item.finalH)
                    Text(it.name ?: "${PrintMath.formatInches(s.widthIn)} × ${PrintMath.formatInches(s.heightIn)}", style = MaterialTheme.typography.labelMedium,
                        modifier = Modifier.background(MaterialTheme.colorScheme.surfaceContainerHigh, ChipShape).padding(horizontal = 8.dp, vertical = 4.dp))
                }
            }
            Spacer(Modifier.height(6.dp))
            Note("Covered means the pixel count is reached. Sizes with a different ratio need their own crop.")
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ExportSheet(vm: ResultViewModel, item: HistoryItem, onDismiss: () -> Unit, onExported: () -> Unit) {
    val state = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    val ui by vm.ui.collectAsStateWithLifecycle()
    var format by remember { mutableStateOf(ExportFormat.PNG) }
    var quality by remember { mutableStateOf(95) }
    var webpLossless by remember { mutableStateOf(true) }
    var name by remember { mutableStateOf(vm.suggestedName(ExportFormat.PNG).substringBeforeLast('.')) }
    val reason = vm.unavailable(format)
    fun options() = ExportOptions(format, quality, webpLossless, FileNaming.finalize(name, format.ext))

    val saf = mapOf(
        ExportFormat.PNG to rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("image/png")) { u -> u?.let { vm.export(options(), it, onExported) } },
        ExportFormat.JPEG to rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("image/jpeg")) { u -> u?.let { vm.export(options(), it, onExported) } },
        ExportFormat.WEBP to rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("image/webp")) { u -> u?.let { vm.export(options(), it, onExported) } },
    )

    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = state, containerColor = MaterialTheme.colorScheme.surfaceContainer) {
        Column(Modifier.navigationBarsPadding().padding(horizontal = 20.dp).padding(bottom = 20.dp).verticalScroll(rememberScrollState())) {
            Text("Export", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(16.dp))
            SectionLabel("Format")
            Spacer(Modifier.height(8.dp))
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                ExportFormat.entries.forEachIndexed { i, f ->
                    SegmentedButton(format == f, { format = f; name = vm.suggestedName(f).substringBeforeLast('.') },
                        SegmentedButtonDefaults.itemShape(i, ExportFormat.entries.size)) {
                        Text(if (f == ExportFormat.ETSY) "Etsy" else f.label, maxLines = 1)
                    }
                }
            }
            Spacer(Modifier.height(8.dp))
            when (format) {
                ExportFormat.PNG -> Note("Lossless. Keeps transparency, the DPI tag and the colour profile. Recommended for print labs that accept PNG.")
                ExportFormat.JPEG -> {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        listOf(90, 95, 100).forEach { q -> FilterChip(quality == q, { quality = q }, { Text("$q%") }, shape = ChipShape) }
                    }
                    Note(if (item.hasAlpha) "JPEG has no transparency: transparent areas become white." else "Most print labs accept JPEG at 95% or higher. The DPI tag is written into the file.")
                }
                ExportFormat.ETSY -> Note(
                    "JPEG at the highest quality (70 to 100%) that stays under Etsy's 20 MB limit per digital file, chosen automatically. " +
                        "The DPI tag is kept." + if (item.hasAlpha) " Transparent areas become white." else "",
                )
                ExportFormat.WEBP -> {
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        FilterChip(webpLossless, { webpLossless = true }, { Text("Lossless") }, shape = ChipShape)
                        FilterChip(!webpLossless, { webpLossless = false; quality = 95 }, { Text("Quality 95%") }, shape = ChipShape)
                    }
                    Note("Good for listing images and web use. Few print labs accept WebP.")
                }
            }
            reason?.let { Spacer(Modifier.height(6.dp)); Note(it, NoteTone.ERROR) }
            Spacer(Modifier.height(16.dp))
            SectionLabel("File name")
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(name, { name = it }, singleLine = true, modifier = Modifier.fillMaxWidth(),
                suffix = { Text(".${format.ext}") }, label = { Text("Name") })
            Spacer(Modifier.height(20.dp))
            PrimaryButton(ui.busy ?: "Save to gallery", enabled = reason == null && ui.busy == null && name.isNotBlank(),
                modifier = Modifier.fillMaxWidth(), onClick = { vm.export(options(), null, onExported) })
            Text("Saved in Pictures/PrintScale", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 6.dp))
            Spacer(Modifier.height(12.dp))
            SecondaryButton("Save to Files", enabled = reason == null && ui.busy == null && name.isNotBlank(), modifier = Modifier.fillMaxWidth(),
                onClick = { saf.getValue(format).launch(FileNaming.finalize(name, format.ext)) })
            Text("Choose any folder, including cloud drives", style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 6.dp))
        }
    }
}

