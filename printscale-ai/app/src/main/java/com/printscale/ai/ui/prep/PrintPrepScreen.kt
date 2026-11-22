package com.printscale.ai.ui.prep

import android.content.ActivityNotFoundException
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.automirrored.outlined.OpenInNew
import androidx.compose.material.icons.outlined.AlignHorizontalCenter
import androidx.compose.material.icons.outlined.AlignVerticalCenter
import androidx.compose.material.icons.outlined.Check
import androidx.compose.material.icons.outlined.Contrast
import androidx.compose.material.icons.outlined.FitScreen
import androidx.compose.material.icons.outlined.RestartAlt
import androidx.compose.material.icons.outlined.ScreenRotation
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.ZoomIn
import androidx.compose.material.icons.outlined.ZoomOut
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
import androidx.compose.material3.Slider
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.printscale.ai.AppGraph
import com.printscale.ai.export.ExportFormat
import com.printscale.ai.processing.BackgroundMode
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
import com.printscale.ai.ui.theme.LocalExtras
import com.printscale.ai.ui.theme.Numeric
import com.printscale.engine.LengthUnit
import com.printscale.engine.Level
import com.printscale.engine.PrintMath
import com.printscale.engine.PrintMethod
import com.printscale.engine.QualityReport
import com.printscale.engine.ResolutionStatus
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PrintPrepScreen(graph: AppGraph, importId: String, method: PrintMethod, tab: PrepTab, onBack: () -> Unit, onUpscale: (String) -> Unit) {
    val vm: PrintPrepViewModel = viewModel(key = "prep-$importId") { PrintPrepViewModel(graph, importId, method, tab) }
    val ui by vm.ui.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    var showExport by remember { mutableStateOf(false) }
    LaunchedEffect(ui.message) { ui.message?.let { snackbar.showSnackbar(it); vm.clearMessage() } }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("${ui.method.title} print prep", style = MaterialTheme.typography.titleLarge) },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        bottomBar = {
            if (ui.art != null) Surface(color = MaterialTheme.colorScheme.surfaceContainer) {
                Column(Modifier.navigationBarsPadding().padding(horizontal = 20.dp, vertical = 12.dp)) {
                    val (w, h) = ui.canvasPx
                    PrimaryButton("Export print file ($w × $h px)", onClick = { showExport = true }, enabled = ui.working == null && !ui.exporting,
                        modifier = Modifier.fillMaxWidth())
                }
            }
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        when {
            ui.loading -> Box(Modifier.fillMaxSize().padding(pad), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator(); Spacer(Modifier.height(12.dp)); Text("Opening artwork")
                }
            }
            ui.info == null -> Box(Modifier.fillMaxSize().padding(pad).padding(20.dp)) {
                EmptyState("Can't open this artwork", ui.error ?: "Unknown error.") { SecondaryButton("Back", onClick = onBack) }
            }
            else -> PrepContent(vm, ui, Modifier.padding(pad), onUpscale = { onUpscale(importId) })
        }
    }
    if (showExport) PrepExportSheet(vm, ui, onDismiss = { showExport = false })
    ui.exported?.let { PrepDoneSheet(vm, it) }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun PrepContent(vm: PrintPrepViewModel, ui: PrepUi, modifier: Modifier, onUpscale: () -> Unit) {
    val info = ui.info!!
    val report = remember(ui) { ui.report() }
    var viewZoom by remember { mutableFloatStateOf(1f) }

    Column(modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        Column(Modifier.padding(horizontal = 20.dp)) {
            // 1. method
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                PrintMethod.entries.forEachIndexed { i, m ->
                    SegmentedButton(ui.method == m, { vm.setMethod(m) }, SegmentedButtonDefaults.itemShape(i, 2)) {
                        Text(if (m == PrintMethod.DTF) "DTF transfer" else "DTG direct print", maxLines = 1)
                    }
                }
            }
            Spacer(Modifier.height(6.dp))
            Text(
                if (ui.method == PrintMethod.DTF) "Film transfer: a transparent PNG at the exact size of the transfer."
                else "Printed straight onto the garment: the file is the print area, placed from the top.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Spacer(Modifier.height(14.dp))
            // views: what you started with, what is exported, what it looks like worn
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                PrepTab.entries.forEachIndexed { i, t ->
                    SegmentedButton(ui.tab == t, { vm.setTab(t) }, SegmentedButtonDefaults.itemShape(i, PrepTab.entries.size),
                        icon = {}) { Text(t.label, maxLines = 1, style = MaterialTheme.typography.labelMedium) }
                }
            }
        }
        Spacer(Modifier.height(8.dp))
        Box(Modifier.fillMaxWidth().padding(horizontal = 8.dp), contentAlignment = Alignment.Center) {
            val art = ui.art
            when (ui.tab) {
                PrepTab.ORIGINAL -> Column(Modifier.padding(horizontal = 12.dp)) {
                    ui.original?.let {
                        Image(it.asImageBitmap(), "Original artwork", contentScale = ContentScale.Fit,
                            modifier = Modifier.fillMaxWidth().height(340.dp).padding(16.dp).cropMarks(MaterialTheme.colorScheme.onBackground))
                    }
                    Text("A. Original artwork, as imported. It is never changed.", style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                PrepTab.PRINT -> Column {
                    if (art != null && ui.placement != null) {
                        PrintCanvas(art.preview, ui.printW, ui.printH, ui.placement, ui.canvasBg, GARMENT_COLORS[ui.garmentColor].color, viewZoom, vm::setPlacement)
                    } else Box(Modifier.fillMaxWidth().height(380.dp))
                    PlacementControls(vm, ui, viewZoom) { viewZoom = it }
                    Text("B. The print file. Exactly this canvas is exported. Backdrop (${ui.canvasBg.label.lowercase()}) is for viewing only.", style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(horizontal = 12.dp))
                }
                PrepTab.GARMENT -> Column {
                    if (art != null && ui.placement != null) {
                        GarmentPreview(art.preview, ui.garment, GARMENT_COLORS[ui.garmentColor], ui.printW, ui.printH, ui.placement, ui.collarIn, ui.showPrintArea)
                    }
                    GarmentControls(vm, ui)
                }
                PrepTab.QUALITY -> Column(Modifier.padding(horizontal = 12.dp)) {
                    report?.let { QualityPanel(it, ui, onUpscale) } ?: Box(Modifier.height(200.dp))
                }
            }
            ui.working?.let { msg ->
                Surface(shape = MaterialTheme.shapes.medium, color = MaterialTheme.colorScheme.surfaceContainerHigh) {
                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                        CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp); Spacer(Modifier.width(10.dp)); Text(msg)
                    }
                }
            }
        }

        Column(Modifier.padding(horizontal = 20.dp)) {
            report?.let { if (ui.tab != PrepTab.QUALITY) QualityBanner(it) { vm.setTab(PrepTab.QUALITY) } }

            // 2. print size and calculator
            Spacer(Modifier.height(22.dp))
            SectionLabel("Print size") {
                IconButton(onClick = vm::rotateCanvas) { Icon(Icons.Outlined.ScreenRotation, "Swap width and height") }
            }
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                PREP_SIZES.forEach { (id, s) ->
                    Chip("${PrintMath.formatInches(s.first)} × ${PrintMath.formatInches(s.second)} in", ui.sizeId == id) { vm.setSize(id) }
                }
            }
            Spacer(Modifier.height(10.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                LengthUnit.entries.forEach { u -> Chip(if (u == LengthUnit.INCH) "Inches" else "Centimetres", ui.unit == u) { vm.setUnit(u) } }
            }
            Spacer(Modifier.height(8.dp))
            DimensionFields(ui.unit, ui.printW, ui.printH, label = "Print") { w, h -> vm.setCustomSize(w, h) }
            Spacer(Modifier.height(12.dp))
            Text("Resolution", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(6.dp))
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                PrintMath.DPI_OPTIONS.forEach { o -> Chip(if (o.dpi == 300) "300 DPI (recommended)" else "${o.dpi} DPI", ui.dpi == o.dpi) { vm.setDpi(o.dpi) } }
            }
            Spacer(Modifier.height(12.dp))
            report?.let { CalculatorPanel(ui, it) }

            // 3. artwork size on the canvas
            Spacer(Modifier.height(22.dp))
            SectionLabel("Artwork size")
            ui.placement?.let { p ->
                DimensionFields(ui.unit, p.wIn, p.hIn, label = "Artwork") { w, h ->
                    // pass only the side that changed, so locked proportions follow it
                    val dw = kotlin.math.abs(ui.unit.toInches(w) - p.wIn) > 0.005
                    val dh = kotlin.math.abs(ui.unit.toInches(h) - p.hIn) > 0.005
                    if (dw || dh) vm.setArtworkSize(if (dw) w else null, if (dh) h else null)
                }
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text("Keep proportions", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                Switch(ui.lockRatio, vm::setLockRatio)
            }

            // 4. background
            Spacer(Modifier.height(22.dp))
            SectionLabel("Background")
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                BackgroundMode.entries.forEachIndexed { i, m ->
                    SegmentedButton(ui.bgMode == m, { vm.setBackground(m) }, SegmentedButtonDefaults.itemShape(i, 3)) { Text(m.label, maxLines = 1) }
                }
            }
            Spacer(Modifier.height(6.dp))
            Note(when (ui.bgMode) {
                BackgroundMode.KEEP -> if (info.hasAlpha) "Your file already has transparency; it is kept." else "The image prints as a full rectangle, background included."
                BackgroundMode.PLAIN -> "Removes a flat background colour (white, black, any solid colour) from the edges inwards, with clean anti-aliased edges. Best for designs made on a plain background."
                BackgroundMode.AI -> "An on-device model cuts out the main subject. Works on busy backgrounds; check fine edges such as hair or text."
            })
            if (ui.bgMode == BackgroundMode.PLAIN) {
                Spacer(Modifier.height(8.dp))
                Text("Colour tolerance ${(ui.tolerance * 100).roundToInt()}", style = MaterialTheme.typography.titleSmall)
                Slider(ui.tolerance, vm::setTolerance, valueRange = 0.02f..0.35f, onValueChangeFinished = vm::applyTolerance)
                ToggleRow("Also remove it inside shapes", "For holes in letters and enclosed areas of the background colour.", ui.enclosed, vm::setEnclosed)
            }
            ToggleRow("Trim empty space", "Crops transparent margins so the artwork fills its size.", ui.trim, vm::setTrim)
            ToggleRow("Solid edges", if (ui.method == PrintMethod.DTF) "Makes partly transparent pixels fully solid or clear. Recommended for DTF, where soft shadows can print speckled."
                else "Makes partly transparent pixels fully solid or clear.", ui.solidEdges, vm::setSolidEdges)
            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun PlacementControls(vm: PrintPrepViewModel, ui: PrepUi, zoom: Float, setZoom: (Float) -> Unit) {
    Row(Modifier.fillMaxWidth().horizontalScroll(rememberScrollState()).padding(horizontal = 4.dp), verticalAlignment = Alignment.CenterVertically) {
        IconButton(onClick = vm::centerH) { Icon(Icons.Outlined.AlignHorizontalCenter, "Center horizontally") }
        IconButton(onClick = vm::centerV) { Icon(Icons.Outlined.AlignVerticalCenter, "Center vertically") }
        IconButton(onClick = vm::fit) { Icon(Icons.Outlined.FitScreen, "Fit to canvas") }
        IconButton(onClick = vm::reset) { Icon(Icons.Outlined.RestartAlt, "Reset placement") }
        IconButton(onClick = { setZoom((zoom / 1.25f).coerceAtLeast(1f)) }) { Icon(Icons.Outlined.ZoomOut, "Zoom out") }
        IconButton(onClick = { setZoom((zoom * 1.25f).coerceAtMost(4f)) }) { Icon(Icons.Outlined.ZoomIn, "Zoom in") }
        IconButton(onClick = { vm.setCanvasBg(CanvasBackground.entries[(ui.canvasBg.ordinal + 1) % CanvasBackground.entries.size]) }) {
            Icon(Icons.Outlined.Contrast, "Change backdrop, now ${ui.canvasBg.label.lowercase()}")
        }
    }
}

@Composable
private fun GarmentControls(vm: PrintPrepViewModel, ui: PrepUi) {
    Column(Modifier.padding(horizontal = 12.dp)) {
        Text("C. Preview only. The mockup is never part of the exported file.", style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(10.dp))
        SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
            Garment.entries.forEachIndexed { i, g -> SegmentedButton(ui.garment == g, { vm.setGarment(g) }, SegmentedButtonDefaults.itemShape(i, 2)) { Text(g.label) } }
        }
        Spacer(Modifier.height(10.dp))
        Row(Modifier.horizontalScroll(rememberScrollState()), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
            GARMENT_COLORS.forEachIndexed { i, c ->
                val selected = ui.garmentColor == i
                Box(
                    Modifier.size(40.dp).clip(CircleShape).background(c.color)
                        .border(if (selected) 3.dp else 1.dp, if (selected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.outline, CircleShape)
                        .clickable(role = Role.RadioButton) { vm.setGarmentColor(i) }
                        .semantics { contentDescription = c.name + if (selected) ", selected" else "" },
                    contentAlignment = Alignment.Center,
                ) { if (selected) Icon(Icons.Outlined.Check, null, tint = if (c.dark) Color.White else Color.Black, modifier = Modifier.size(18.dp)) }
            }
        }
        Text(GARMENT_COLORS[ui.garmentColor].name, style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(top = 4.dp))
        Spacer(Modifier.height(8.dp))
        Text("Print top ${PrintMath.formatInches(ui.collarIn)} in below the collar", style = MaterialTheme.typography.titleSmall)
        Slider(ui.collarIn.toFloat(), { vm.setCollar((it * 2).roundToInt() / 2.0) }, valueRange = 1f..6f)
        ToggleRow("Show print area", "Dashed box: the usual largest print for this garment (${PrintMath.formatInches(ui.garment.maxPrintIn.first)} × ${PrintMath.formatInches(ui.garment.maxPrintIn.second)} in).",
            ui.showPrintArea, vm::setShowPrintArea)
    }
}

@Composable
private fun CalculatorPanel(ui: PrepUi, report: QualityReport) {
    val a = ui.art ?: return
    val p = ui.placement ?: return
    val (cw, ch) = ui.canvasPx
    Panel {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("$cw × $ch px", style = MaterialTheme.typography.headlineMedium.merge(Numeric), modifier = Modifier.weight(1f))
            StatusChip(report.resolution)
        }
        Text("Pixels = inches × DPI", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(6.dp)); HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        StatRow("Your artwork", "${a.width} × ${a.height} px")
        StatRow("Print size", "${fmt(ui.unit, ui.printW)} × ${fmt(ui.unit, ui.printH)} ${ui.unit.label}")
        StatRow("DPI", "${ui.dpi}")
        StatRow("Required", "$cw × $ch px for the full print area")
        val needW = PrintMath.pixels(p.wIn, ui.dpi)
        val needH = PrintMath.pixels(p.hIn, ui.dpi)
        StatRow("Artwork needs", "$needW × $needH px at ${fmt(ui.unit, p.wIn)} × ${fmt(ui.unit, p.hIn)} ${ui.unit.label}")
        StatRow("Artwork gives", "about ${report.pixelDpi.roundToInt()} DPI" + (report.detailDpi?.let { ", ${it.roundToInt()} DPI of original detail" } ?: ""))
    }
}

@Composable
private fun StatusChip(s: ResolutionStatus) {
    val (bg, fg) = statusColors(when (s) { ResolutionStatus.EXCELLENT -> Level.OK; ResolutionStatus.GOOD -> Level.WARN; else -> Level.BAD })
    Text(s.label, style = MaterialTheme.typography.labelMedium, color = fg, fontWeight = FontWeight.SemiBold,
        modifier = Modifier.background(bg, ChipShape).padding(horizontal = 10.dp, vertical = 5.dp))
}

@Composable
private fun statusColors(l: Level): Pair<Color, Color> {
    val dark = LocalExtras.current.isDark
    return when (l) {
        Level.OK -> if (dark) Color(0xFF1E3A2A) to Color(0xFF8FE3A8) else Color(0xFFDDF3E3) to Color(0xFF14532D)
        Level.WARN -> if (dark) Color(0xFF3B3216) to Color(0xFFF2CF6B) else Color(0xFFFBF0CF) to Color(0xFF6B4E00)
        Level.BAD -> if (dark) Color(0xFF3F1C19) to Color(0xFFFF9C91) else Color(0xFFFADCD8) to Color(0xFF8A1C12)
    }
}

@Composable
private fun QualityBanner(r: QualityReport, onOpen: () -> Unit) {
    val (bg, fg) = statusColors(r.overall)
    Surface(onClick = onOpen, shape = MaterialTheme.shapes.medium, color = bg, modifier = Modifier.fillMaxWidth().padding(top = 12.dp)) {
        Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(12.dp).background(fg, CircleShape))
            Spacer(Modifier.width(10.dp))
            Text(r.headline, color = fg, style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
            Text("Report", color = fg, style = MaterialTheme.typography.labelLarge)
        }
    }
}

@Composable
private fun QualityPanel(r: QualityReport, ui: PrepUi, onUpscale: () -> Unit) {
    val (bg, fg) = statusColors(r.overall)
    Surface(shape = MaterialTheme.shapes.large, color = bg, modifier = Modifier.fillMaxWidth()) {
        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(Modifier.size(16.dp).background(fg, CircleShape))
            Spacer(Modifier.width(12.dp))
            Column {
                Text(r.headline, color = fg, style = MaterialTheme.typography.titleMedium)
                Text("${ui.method.title}, ${fmt(ui.unit, ui.printW)} × ${fmt(ui.unit, ui.printH)} ${ui.unit.label} at ${ui.dpi} DPI",
                    color = fg, style = MaterialTheme.typography.bodySmall)
            }
        }
    }
    Spacer(Modifier.height(10.dp))
    r.checks.forEach { c ->
        val (_, fgc) = statusColors(c.level)
        Row(Modifier.padding(vertical = 7.dp)) {
            Box(Modifier.padding(top = 5.dp).size(10.dp).background(fgc, CircleShape))
            Spacer(Modifier.width(12.dp))
            Column {
                Text(c.title, style = MaterialTheme.typography.titleSmall)
                Text(c.detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
    if (r.resolution != ResolutionStatus.EXCELLENT && ui.info?.provenance == null) {
        Spacer(Modifier.height(8.dp))
        SecondaryButton("Upscale this artwork first", onClick = onUpscale, modifier = Modifier.fillMaxWidth())
        Text("Opens the upscaler. From its result, choose Prepare for DTF / DTG to come back with the larger file.",
            style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 6.dp))
    }
}

@Composable
private fun DimensionFields(unit: LengthUnit, wIn: Double, hIn: Double, label: String, onChange: (Double, Double) -> Unit) {
    var wText by remember(unit) { mutableStateOf(fmt(unit, wIn)) }
    var hText by remember(unit) { mutableStateOf(fmt(unit, hIn)) }
    // Follow changes made elsewhere (preset, pinch, locked proportions) without fighting the typist.
    LaunchedEffect(wIn, unit) { if (parse(wText)?.let { kotlin.math.abs(unit.toInches(it) - wIn) > 0.005 } != false) wText = fmt(unit, wIn) }
    LaunchedEffect(hIn, unit) { if (parse(hText)?.let { kotlin.math.abs(unit.toInches(it) - hIn) > 0.005 } != false) hText = fmt(unit, hIn) }
    fun commit(w: String, h: String) {
        val wv = parse(w) ?: return
        val hv = parse(h) ?: return
        if (wv > 0 && hv > 0 && unit.toInches(wv) <= 80 && unit.toInches(hv) <= 80) onChange(wv, hv)
    }
    Row(verticalAlignment = Alignment.CenterVertically) {
        OutlinedTextField(wText, { wText = it; commit(it, hText) }, label = { Text("$label width") }, suffix = { Text(unit.label) }, singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), modifier = Modifier.weight(1f))
        Text("×", modifier = Modifier.padding(horizontal = 8.dp))
        OutlinedTextField(hText, { hText = it; commit(wText, it) }, label = { Text("$label height") }, suffix = { Text(unit.label) }, singleLine = true,
            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), modifier = Modifier.weight(1f))
    }
}

private fun parse(s: String) = s.replace(',', '.').toDoubleOrNull()

@Composable
private fun ToggleRow(title: String, detail: String, value: Boolean, onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(vertical = 6.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f).padding(end = 12.dp)) {
            Text(title, style = MaterialTheme.typography.bodyLarge)
            Text(detail, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Switch(value, onChange)
    }
}

@Composable
private fun Chip(label: String, selected: Boolean, onClick: () -> Unit) {
    FilterChip(selected, onClick, { Text(label) }, shape = ChipShape)
}

private fun fmt(unit: LengthUnit, inches: Double): String {
    val v = unit.fromInches(inches)
    val r = (v * 100).roundToInt() / 100.0
    return if (r == r.roundToInt().toDouble()) r.roundToInt().toString() else r.toString()
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PrepExportSheet(vm: PrintPrepViewModel, ui: PrepUi, onDismiss: () -> Unit) {
    var name by remember { mutableStateOf(vm.suggestedName()) }
    var level by remember { mutableIntStateOf(6) }
    val saf = rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument("image/png")) { u: Uri? ->
        u?.let { vm.export(name, level, it); onDismiss() }
    }
    val (w, h) = ui.canvasPx
    val report = ui.report()
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = MaterialTheme.colorScheme.surfaceContainer) {
        Column(Modifier.navigationBarsPadding().padding(horizontal = 20.dp).padding(bottom = 20.dp).verticalScroll(rememberScrollState())) {
            Text("Export print file", style = MaterialTheme.typography.headlineMedium)
            Spacer(Modifier.height(12.dp))
            StatRow("Format", "PNG with transparent background")
            StatRow("Print size", "${fmt(ui.unit, ui.printW)} × ${fmt(ui.unit, ui.printH)} ${ui.unit.label}")
            StatRow("DPI", "${ui.dpi} (written into the file)")
            StatRow("Pixels", "$w × $h px")
            StatRow("Colour", "sRGB")
            report?.let {
                Spacer(Modifier.height(6.dp))
                Note(it.headline + if (it.overall == Level.OK) "." else ". See the Quality tab for details.",
                    when (it.overall) { Level.OK -> NoteTone.INFO; Level.WARN -> NoteTone.WARNING; Level.BAD -> NoteTone.ERROR })
            }
            Spacer(Modifier.height(14.dp))
            Text("File size", style = MaterialTheme.typography.titleSmall)
            Spacer(Modifier.height(6.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Chip("Standard", level == 6) { level = 6 }
                Chip("Smallest (slower)", level == 9) { level = 9 }
            }
            Text("PNG is lossless either way: every pixel is identical, only the compression differs.",
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.padding(top = 4.dp))
            Spacer(Modifier.height(14.dp))
            OutlinedTextField(name, { name = it }, label = { Text("File name") }, suffix = { Text(".png") }, singleLine = true, modifier = Modifier.fillMaxWidth())
            Spacer(Modifier.height(18.dp))
            PrimaryButton(if (ui.exporting) "Exporting" else "Save to gallery", enabled = !ui.exporting && name.isNotBlank(), modifier = Modifier.fillMaxWidth(),
                onClick = { vm.export(name, level, null); onDismiss() })
            Spacer(Modifier.height(10.dp))
            SecondaryButton("Save to Files", enabled = !ui.exporting && name.isNotBlank(), modifier = Modifier.fillMaxWidth(),
                onClick = { saf.launch(name.removeSuffix(".png") + ".png") })
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun PrepDoneSheet(vm: PrintPrepViewModel, e: PrepExport) {
    val context = LocalContext.current
    var error by remember { mutableStateOf<String?>(null) }
    ModalBottomSheet(onDismissRequest = vm::clearExported, containerColor = MaterialTheme.colorScheme.surfaceContainer) {
        Column(Modifier.navigationBarsPadding().padding(horizontal = 20.dp).padding(bottom = 20.dp)) {
            Text("Print file saved", style = MaterialTheme.typography.headlineMedium)
            Text(e.fileName, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(12.dp))
            StatRow("Pixels", "${e.widthPx} × ${e.heightPx} px")
            StatRow("Print size", "${PrintMath.formatInches(e.widthIn)} × ${PrintMath.formatInches(e.heightIn)} in at ${e.dpi} DPI")
            StatRow("File", "PNG, transparent, ${formatBytes(e.bytes)}")
            StatRow("Location", e.location)
            Spacer(Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                SecondaryButton("Open with", icon = Icons.AutoMirrored.Outlined.OpenInNew, modifier = Modifier.weight(1f), onClick = {
                    try { context.startActivity(vm.graph.exporter.viewIntent(Uri.parse(e.uri), ExportFormat.PNG)) }
                    catch (x: ActivityNotFoundException) { error = "No installed app can open PNG files." }
                    catch (x: SecurityException) { error = "Access to the saved file was revoked." }
                })
                SecondaryButton("Share", icon = Icons.Outlined.Share, modifier = Modifier.weight(1f), onClick = {
                    runCatching { context.startActivity(vm.graph.exporter.shareIntent(e.cacheFile, ExportFormat.PNG)) }
                        .onFailure { error = "Sharing failed: ${it.message}" }
                })
            }
            error?.let { Spacer(Modifier.height(8.dp)); Note(it, NoteTone.ERROR) }
            Spacer(Modifier.height(10.dp))
            PrimaryButton("Done", onClick = vm::clearExported, modifier = Modifier.fillMaxWidth())
        }
    }
}
