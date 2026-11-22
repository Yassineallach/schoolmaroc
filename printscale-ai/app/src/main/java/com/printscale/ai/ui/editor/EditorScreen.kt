package com.printscale.ai.ui.editor

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import androidx.compose.ui.platform.LocalContext
import androidx.core.content.ContextCompat
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
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
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.CropPortrait
import androidx.compose.material.icons.outlined.ExpandLess
import androidx.compose.material.icons.outlined.ExpandMore
import androidx.compose.material.icons.outlined.RestartAlt
import androidx.compose.material.icons.outlined.Rotate90DegreesCw
import androidx.compose.material.icons.outlined.ScreenRotation
import androidx.compose.material.icons.outlined.ZoomIn
import androidx.compose.material.icons.outlined.ZoomOut
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Slider
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.printscale.ai.AppGraph
import com.printscale.ai.data.JobSpec
import com.printscale.ai.ui.cloud.CloudGpuSheet
import com.printscale.ai.ui.components.ChipShape
import com.printscale.ai.ui.components.EmptyState
import com.printscale.ai.ui.components.Note
import com.printscale.ai.ui.components.NoteTone
import com.printscale.ai.ui.components.Panel
import com.printscale.ai.ui.components.PrimaryButton
import com.printscale.ai.ui.components.SecondaryButton
import com.printscale.ai.ui.components.SectionLabel
import com.printscale.ai.ui.components.StatRow
import com.printscale.ai.ui.components.formatBytes
import com.printscale.ai.ui.components.formatPx
import com.printscale.ai.ui.theme.Numeric
import com.printscale.engine.FitMode
import com.printscale.engine.LengthUnit
import com.printscale.engine.PresetGroup
import com.printscale.engine.PrintMath
import com.printscale.engine.PrintSize
import com.printscale.engine.UpscalePlan
import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditorScreen(
    graph: AppGraph,
    importId: String,
    initialPreset: String?,
    initialFactor: Int?,
    onBack: () -> Unit,
    onStarted: (String) -> Unit,
) {
    val vm: EditorViewModel = viewModel(key = "editor-$importId") { EditorViewModel(graph, importId, initialPreset, initialFactor) }
    val ui by vm.ui.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    val context = LocalContext.current
    var askedNotifications by rememberSaveable { mutableStateOf(false) }
    val notifPermission = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {
        vm.start(onStarted)
    }

    LaunchedEffect(ui.error, ui.info) {
        val e = ui.error
        if (e != null && ui.info != null) { snackbar.showSnackbar(e); vm.clearError() }
    }

    val plan = remember(ui) { vm.plan(ui) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("Prepare for print", style = MaterialTheme.typography.titleLarge)
                        ui.info?.let {
                            Text(it.displayName, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                                maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    }
                },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.AutoMirrored.Outlined.ArrowBack, "Back") } },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
        bottomBar = {
            if (ui.info != null && plan != null) {
                Surface(color = MaterialTheme.colorScheme.surfaceContainer, tonalElevation = 0.dp) {
                    Column(Modifier.navigationBarsPadding().padding(horizontal = 20.dp, vertical = 12.dp)) {
                        PrimaryButton(
                            text = if (ui.starting) "Starting" else "Upscale to ${plan.targetW} × ${plan.targetH} px",
                            onClick = {
                                val needsAsk = Build.VERSION.SDK_INT >= 33 && !askedNotifications &&
                                    ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
                                if (needsAsk) {
                                    askedNotifications = true
                                    notifPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
                                } else vm.start(onStarted)
                            },
                            enabled = plan.feasible && !ui.starting,
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                }
            }
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { pad ->
        when {
            ui.loading -> Box(Modifier.fillMaxSize().padding(pad), contentAlignment = Alignment.Center) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(12.dp))
                    Text("Opening image", style = MaterialTheme.typography.bodyMedium)
                }
            }
            ui.info == null || ui.preview == null -> Box(Modifier.fillMaxSize().padding(pad).padding(20.dp)) {
                EmptyState("Can't open this image", ui.error ?: "Unknown error.") {
                    SecondaryButton("Back", onClick = onBack)
                }
            }
            else -> EditorContent(vm, ui, plan, Modifier.padding(pad))
        }
    }
}

@OptIn(ExperimentalLayoutApi::class, ExperimentalMaterial3Api::class)
@Composable
private fun EditorContent(vm: EditorViewModel, ui: EditorUi, plan: UpscalePlan?, modifier: Modifier) {
    val info = ui.info!!
    val geom = ui.geometry()!!
    var showCustomRatio by remember { mutableStateOf(false) }
    var showCustomSize by remember { mutableStateOf(false) }
    var advanced by rememberSaveable { mutableStateOf(false) }
    var showCloud by remember { mutableStateOf(false) }
    val cloudLink by vm.graph.settings.cloudLink.collectAsStateWithLifecycle()

    Column(modifier.fillMaxSize().verticalScroll(rememberScrollState())) {
        // Source facts
        Text(
            buildString {
                append("${info.width} × ${info.height} px · ${PrintMath.ratioLabel(info.width, info.height)} · ${info.formatLabel} · ${formatBytes(info.fileSize)}")
            },
            style = MaterialTheme.typography.bodySmall.merge(Numeric), color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(horizontal = 20.dp),
        )
        val tags = buildList {
            if (info.hasAlpha) add("Transparency kept")
            if (info.exifRotated) add("Camera rotation applied")
            if (info.downscaledForWork) add("Reduced to ${info.workW} × ${info.workH} for processing")
            if (info.hasIcc) add("Colour profile: ${info.colorSpaceName}")
        }
        if (tags.isNotEmpty()) {
            FlowRow(Modifier.padding(horizontal = 20.dp, vertical = 6.dp), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                tags.forEach {
                    Text(it, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.background(MaterialTheme.colorScheme.surfaceContainerHigh, ChipShape).padding(horizontal = 8.dp, vertical = 4.dp))
                }
            }
        }

        CropCanvas(ui.preview!!, geom, if (ui.fitMode == FitMode.FIT) ui.backgroundArgb else null, vm::setCrop, vm::resetCrop)

        Row(Modifier.fillMaxWidth().padding(horizontal = 12.dp), verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = vm::rotate90) { Icon(Icons.Outlined.Rotate90DegreesCw, "Rotate 90 degrees") }
            IconButton(onClick = { vm.zoomBy(1 / 1.25f) }) { Icon(Icons.Outlined.ZoomOut, "Zoom out") }
            IconButton(onClick = { vm.zoomBy(1.25f) }) { Icon(Icons.Outlined.ZoomIn, "Zoom in") }
            Spacer(Modifier.weight(1f))
            Text("Canvas ${formatPx(geom.outW, geom.outH)}", style = MaterialTheme.typography.labelMedium.merge(Numeric),
                color = MaterialTheme.colorScheme.onSurfaceVariant)
            IconButton(onClick = vm::resetCrop) { Icon(Icons.Outlined.RestartAlt, "Reset crop") }
        }
        Row(Modifier.fillMaxWidth().padding(horizontal = 20.dp), verticalAlignment = Alignment.CenterVertically) {
            Text("Straighten", style = MaterialTheme.typography.labelMedium, modifier = Modifier.width(84.dp))
            Slider(value = ui.crop.straightenDeg, onValueChange = { vm.setStraighten((it * 2).roundToInt() / 2f) },
                valueRange = -15f..15f, modifier = Modifier.weight(1f))
            Text("${"%.1f".format(ui.crop.straightenDeg)}°", style = MaterialTheme.typography.labelMedium.merge(Numeric),
                modifier = Modifier.width(48.dp).padding(start = 8.dp))
        }

        Column(Modifier.padding(horizontal = 20.dp)) {
            Spacer(Modifier.height(20.dp))
            // ---------- Output target ----------
            SectionLabel("Output size")
            Spacer(Modifier.height(10.dp))
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                SegmentedButton(ui.outputMode == OutputMode.PRINT, { vm.setOutputMode(OutputMode.PRINT) },
                    SegmentedButtonDefaults.itemShape(0, 2)) { Text("Print size") }
                SegmentedButton(ui.outputMode == OutputMode.SCALE, { vm.setOutputMode(OutputMode.SCALE) },
                    SegmentedButtonDefaults.itemShape(1, 2)) { Text("Scale factor") }
            }
            Spacer(Modifier.height(14.dp))
            if (ui.outputMode == OutputMode.PRINT) {
                PrintSection(vm, ui, showCustomSize) { showCustomSize = it }
            } else {
                ScaleSection(vm, ui)
            }

            Spacer(Modifier.height(24.dp))
            // ---------- Framing ----------
            SectionLabel("Framing") {
                if (ui.printSize == null) {
                    IconButton(onClick = vm::toggleOrientation) {
                        Icon(if (ui.landscape) Icons.Outlined.ScreenRotation else Icons.Outlined.CropPortrait,
                            if (ui.landscape) "Switch to portrait" else "Switch to landscape")
                    }
                } else {
                    TextButton(onClick = vm::toggleOrientation) { Text(if (ui.landscape) "Landscape" else "Portrait") }
                }
            }
            if (ui.printSize != null) {
                Text("Ratio follows the ${PrintMath.formatInches(ui.printSize!!.widthIn)} × ${PrintMath.formatInches(ui.printSize!!.heightIn)} in print.",
                    style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            } else {
                Spacer(Modifier.height(6.dp))
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    RatioChip("Original", ui.aspect == null) { vm.setAspect(null) }
                    ASPECTS.forEach { a -> RatioChip(a.label(ui.landscape), ui.aspect == a) { vm.setAspect(a) } }
                    val custom = ui.aspect != null && ui.aspect !in ASPECTS
                    RatioChip(if (custom) "Custom ${ui.aspect!!.label(ui.landscape)}" else "Custom", custom || showCustomRatio) {
                        showCustomRatio = !showCustomRatio
                    }
                }
                if (showCustomRatio) {
                    Spacer(Modifier.height(10.dp))
                    CustomRatioForm(onCancel = { showCustomRatio = false }) { a, b ->
                        showCustomRatio = false
                        vm.setAspect(AspectChoice(minOf(a, b), maxOf(a, b)))
                        if ((a > b) != ui.landscape && a != b) vm.toggleOrientation()
                    }
                }
            }
            Spacer(Modifier.height(12.dp))
            SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                SegmentedButton(ui.fitMode == FitMode.FILL, { vm.setFitMode(FitMode.FILL) }, SegmentedButtonDefaults.itemShape(0, 2)) {
                    Text("Fill (crop edges)")
                }
                SegmentedButton(ui.fitMode == FitMode.FIT, { vm.setFitMode(FitMode.FIT) }, SegmentedButtonDefaults.itemShape(1, 2)) {
                    Text("Fit (add margin)")
                }
            }
            if (ui.fitMode == FitMode.FIT) {
                Spacer(Modifier.height(10.dp))
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Background.entries.forEach { b -> RatioChip(b.label, ui.background == b) { vm.setBackground(b) } }
                }
                if (ui.background == Background.TRANSPARENT) {
                    Spacer(Modifier.height(6.dp))
                    Note("Transparent margins are kept in PNG and WebP. JPEG has no transparency and exports them as white.")
                }
            }
            Spacer(Modifier.height(6.dp))
            Note("Extending artwork past its edges with AI (outpainting) is not available on device in this version. Fit adds a plain margin instead.")

            Spacer(Modifier.height(24.dp))
            // ---------- AI engine ----------
            SectionLabel("AI engine")
            Spacer(Modifier.height(8.dp))
            if (cloudLink == null) {
                Text("Real-ESRGAN on this phone.", style = MaterialTheme.typography.bodyMedium)
                TextButton(onClick = { showCloud = true }) { Text("Connect a cloud GPU for AuraSR v2") }
            } else {
                SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                    SegmentedButton(!ui.cloud, { vm.setEngine(JobSpec.ENGINE_DEVICE) }, SegmentedButtonDefaults.itemShape(0, 2)) { Text("This phone") }
                    SegmentedButton(ui.cloud, { vm.setEngine(JobSpec.ENGINE_CLOUD) }, SegmentedButtonDefaults.itemShape(1, 2)) { Text("Cloud GPU") }
                }
                Spacer(Modifier.height(6.dp))
                if (ui.cloud) {
                    Note("AuraSR v2 runs on your notebook's GPU. Your crop is uploaded there and the 4× result is downloaded; " +
                        "resizing to print size and the final file are made on this phone.", NoteTone.WARNING)
                    TextButton(onClick = { showCloud = true }) { Text("Check connection") }
                } else {
                    Text("Real-ESRGAN, private and offline.", style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }

            Spacer(Modifier.height(24.dp))
            if (ui.cloud && cloudLink != null) {
                SectionLabel("Enhancement")
                Spacer(Modifier.height(6.dp))
                Note("AuraSR has no adjustable settings: it decides detail and noise cleanup itself.")
            } else {
                // ---------- Enhancement ----------
                SectionLabel("Enhancement")
                Spacer(Modifier.height(10.dp))
                SingleChoiceSegmentedButtonRow(Modifier.fillMaxWidth()) {
                    Strength.entries.forEachIndexed { i, s ->
                        SegmentedButton(ui.strength == s, { vm.setStrength(s) }, SegmentedButtonDefaults.itemShape(i, Strength.entries.size)) { Text(s.label) }
                    }
                }
                TextButton(onClick = { advanced = !advanced }, modifier = Modifier.padding(top = 4.dp)) {
                    Text("Advanced")
                    Icon(if (advanced) Icons.Outlined.ExpandLess else Icons.Outlined.ExpandMore, null)
                }
                AnimatedVisibility(advanced) {
                    Column {
                        LabeledSlider("Detail recovery", ui.detail, vm::setDetail,
                            "How much of the AI-reconstructed detail to keep. Lower blends towards a smooth enlargement.")
                        LabeledSlider("Sharpening", ui.sharpen, vm::setSharpen, "Extra edge contrast after upscaling. Leave low for painterly art.")
                        LabeledSlider("Noise reduction", ui.denoise, vm::setDenoise,
                            "Real-ESRGAN's denoise strength. Higher removes grain and JPEG blocks; lower keeps fine texture.")
                    }
                }
            }

            Spacer(Modifier.height(24.dp))
            plan?.let { PlanPanel(ui.copy(engine = if (cloudLink == null) JobSpec.ENGINE_DEVICE else ui.engine), it) }
            Spacer(Modifier.height(24.dp))
        }
    }
    if (showCloud) CloudGpuSheet(vm.graph, onDismiss = { showCloud = false })

}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun PrintSection(vm: EditorViewModel, ui: EditorUi, customOpen: Boolean, setCustomOpen: (Boolean) -> Unit) {
    Text("Print resolution", style = MaterialTheme.typography.titleSmall)
    Spacer(Modifier.height(8.dp))
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        PrintMath.DPI_OPTIONS.forEach { o -> RatioChip("${o.dpi} DPI", ui.dpi == o.dpi) { vm.setDpi(o.dpi) } }
    }
    Text(PrintMath.DPI_OPTIONS.first { it.dpi == ui.dpi }.label, style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant)
    Spacer(Modifier.height(4.dp))
    Note("Pixels = inches × DPI. 300 DPI is the usual request from print labs. What a product really needs depends on the provider, the material and how far away it is viewed; large wall prints often look right at 150 to 200 DPI. Check your provider's guidelines.")
    PresetGroup.entries.forEach { group ->
        Spacer(Modifier.height(14.dp))
        Text(group.title, style = MaterialTheme.typography.titleSmall)
        Spacer(Modifier.height(6.dp))
        FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            PrintMath.PRESETS.filter { it.group == group }.forEach { p ->
                val s = p.oriented(ui.landscape)
                val (w, h) = s.pixels(ui.dpi)
                PresetChip("${PrintMath.formatInches(s.widthIn)} × ${PrintMath.formatInches(s.heightIn)}", "$w × $h",
                    selected = ui.presetId == p.id && ui.customPrint == null) { vm.setPreset(p.id) }
            }
        }
    }
    Spacer(Modifier.height(12.dp))
    val custom = ui.customPrint
    PresetChip(
        if (custom != null) "Custom ${PrintMath.formatInches(ui.printSize!!.widthIn)} × ${PrintMath.formatInches(ui.printSize!!.heightIn)} in" else "Custom size",
        if (custom != null) ui.printSize!!.pixels(ui.dpi).let { "${it.first} × ${it.second}" } else "inches or cm",
        selected = custom != null || customOpen, onClick = { setCustomOpen(!customOpen) },
    )
    if (customOpen) {
        Spacer(Modifier.height(10.dp))
        CustomSizeForm(onCancel = { setCustomOpen(false) }) { size ->
            setCustomOpen(false)
            vm.setCustomPrint(size)
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun ScaleSection(vm: EditorViewModel, ui: EditorUi) {
    val geom = ui.geometry() ?: return
    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        listOf(2, 4, 8).forEach { f ->
            val p = vm.plan(ui, f)
            val ok = p?.feasible == true
            PresetChip("$f×", "${geom.outW * f} × ${geom.outH * f}", selected = ui.factor == f, enabled = ok) { vm.setFactor(f) }
        }
    }
    Spacer(Modifier.height(8.dp))
    when (ui.factor) {
        2 -> Note("2× runs the 4× model, then downsamples with Lanczos. Downsampling keeps the reconstructed detail.")
        8 -> Note("The model works in 4× steps. 8× is the 4× AI result plus a 2× Lanczos enlargement, which adds pixels but not new detail.")
        else -> Note("4× is the model's native scale: every output pixel comes from the AI.")
    }
}

@Composable
private fun PlanPanel(ui: EditorUi, plan: UpscalePlan) {
    Panel {
        Text("${plan.targetW} × ${plan.targetH} px", style = MaterialTheme.typography.headlineLarge.merge(Numeric))
        ui.printSize?.let {
            Text("${PrintMath.formatInches(it.widthIn)} × ${PrintMath.formatInches(it.heightIn)} in at ${ui.dpi} DPI",
                style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Spacer(Modifier.height(10.dp))
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        Spacer(Modifier.height(6.dp))
        StatRow("From your crop", formatPx(plan.sourceW, plan.sourceH))
        StatRow("Needed", PrintMath.formatFactor(plan.effectiveScale))
        val ai = if (ui.cloud) "AuraSR 4× (cloud GPU)" else "AI 4×"
        StatRow("Method", when {
            !plan.useAi -> "Lanczos resize only"
            plan.interpolationBeyondAi > 1.02 -> "$ai to ${plan.aiW} × ${plan.aiH}, then Lanczos ${PrintMath.formatFactor(plan.interpolationBeyondAi)}"
            plan.interpolationBeyondAi < 0.98 -> "$ai to ${plan.aiW} × ${plan.aiH}, then downsample"
            else -> ai
        })
        if (ui.cloud && plan.useAi) {
            val ch = if (ui.outputHasAlpha) 4 else 3
            val up = plan.sourceW.toLong() * plan.sourceH * ch / 2
            val down = plan.aiW.toLong() * plan.aiH * ch / 2
            StatRow("Data transfer", "roughly ${formatBytes(up)} up, ${formatBytes(down)} down (estimate)")
        }
        plan.aiDetailDpi?.let { StatRow("AI detail reaches", "about ${it.roundToInt()} DPI at this size") }
        StatRow("PNG size", "roughly ${formatBytes(plan.estimatedPngBytes)} (estimate)")
        if (plan.warnings.isNotEmpty() || plan.blockers.isNotEmpty()) Spacer(Modifier.height(8.dp))
        plan.blockers.forEach { Note(it, NoteTone.ERROR, Modifier.padding(vertical = 4.dp)) }
        plan.warnings.forEach { Note(it, NoteTone.WARNING, Modifier.padding(vertical = 4.dp)) }
        if (ui.printSize != null) {
            Spacer(Modifier.height(6.dp))
            Note("Reaching the pixel count makes a file the right size. Whether it looks good printed depends on the artwork and how much was interpolated; check the result at 100% before you list it.")
        }
    }
}

@Composable
private fun RatioChip(label: String, selected: Boolean, enabled: Boolean = true, onClick: () -> Unit) {
    FilterChip(
        selected = selected, onClick = onClick, enabled = enabled, label = { Text(label) }, shape = ChipShape,
        colors = FilterChipDefaults.filterChipColors(
            selectedContainerColor = MaterialTheme.colorScheme.secondaryContainer,
            selectedLabelColor = MaterialTheme.colorScheme.onSecondaryContainer,
        ),
    )
}

@Composable
private fun PresetChip(title: String, sub: String, selected: Boolean, enabled: Boolean = true, onClick: () -> Unit) {
    val c = MaterialTheme.colorScheme
    Surface(
        onClick = onClick, enabled = enabled, shape = ChipShape,
        color = if (selected) c.primaryContainer else c.surfaceContainer,
        border = androidx.compose.foundation.BorderStroke(1.dp, if (selected) c.primary else c.outlineVariant),
    ) {
        Column(Modifier.padding(horizontal = 12.dp, vertical = 8.dp)) {
            Text(title, style = MaterialTheme.typography.titleSmall,
                color = if (!enabled) c.onSurface.copy(alpha = 0.38f) else if (selected) c.onPrimaryContainer else c.onSurface)
            Text(sub, style = MaterialTheme.typography.labelSmall.merge(Numeric),
                color = if (!enabled) c.onSurface.copy(alpha = 0.38f) else if (selected) c.onPrimaryContainer else c.onSurfaceVariant)
        }
    }
}

@Composable
private fun LabeledSlider(label: String, value: Float, onChange: (Float) -> Unit, help: String) {
    Column(Modifier.padding(vertical = 6.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(label, style = MaterialTheme.typography.titleSmall, modifier = Modifier.weight(1f))
            Text("${(value * 100).roundToInt()}", style = MaterialTheme.typography.labelMedium.merge(Numeric))
        }
        Slider(value = value, onValueChange = onChange, valueRange = 0f..1f)
        Text(help, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun CustomRatioForm(onCancel: () -> Unit, onConfirm: (Double, Double) -> Unit) {
    var a by remember { mutableStateOf("") }
    var b by remember { mutableStateOf("") }
    val av = a.replace(',', '.').toDoubleOrNull()
    val bv = b.replace(',', '.').toDoubleOrNull()
    val valid = av != null && bv != null && av > 0 && bv > 0 && av / bv in 0.1..10.0
    Panel {
        Text("Custom ratio", style = MaterialTheme.typography.titleSmall)
        Spacer(Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(a, { a = it }, label = { Text("Width") }, singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), modifier = Modifier.weight(1f))
            Text(":", modifier = Modifier.padding(horizontal = 8.dp))
            OutlinedTextField(b, { b = it }, label = { Text("Height") }, singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), modifier = Modifier.weight(1f))
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            TextButton(onClick = onCancel) { Text("Cancel") }
            TextButton(onClick = { onConfirm(av!!, bv!!) }, enabled = valid) { Text("Use ratio") }
        }
    }
}

@Composable
private fun CustomSizeForm(onCancel: () -> Unit, onConfirm: (PrintSize) -> Unit) {
    var w by remember { mutableStateOf("") }
    var h by remember { mutableStateOf("") }
    var unit by remember { mutableStateOf(LengthUnit.INCH) }
    val wv = w.replace(',', '.').toDoubleOrNull()
    val hv = h.replace(',', '.').toDoubleOrNull()
    val valid = wv != null && hv != null && wv > 0 && hv > 0 && unit.toInches(maxOf(wv, hv)) <= 80
    Panel {
        Text("Custom print size", style = MaterialTheme.typography.titleSmall)
        Spacer(Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            LengthUnit.entries.forEach { u ->
                RatioChip(if (u == LengthUnit.INCH) "Inches" else "Centimetres", unit == u) { unit = u }
            }
        }
        Spacer(Modifier.height(8.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(w, { w = it }, label = { Text("Width") }, singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), modifier = Modifier.weight(1f))
            Text("×", modifier = Modifier.padding(horizontal = 8.dp))
            OutlinedTextField(h, { h = it }, label = { Text("Height") }, singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal), modifier = Modifier.weight(1f))
        }
        if (wv != null && hv != null && !valid) {
            Spacer(Modifier.height(6.dp))
            Note("Up to 80 inches (203 cm) per side.", NoteTone.ERROR)
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
            TextButton(onClick = onCancel) { Text("Cancel") }
            TextButton(onClick = { onConfirm(PrintSize(unit.toInches(wv!!), unit.toInches(hv!!))) }, enabled = valid) { Text("Use size") }
        }
    }
}
