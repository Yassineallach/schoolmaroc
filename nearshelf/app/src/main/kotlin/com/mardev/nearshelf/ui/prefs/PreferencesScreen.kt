package com.mardev.nearshelf.ui.prefs

import androidx.annotation.DrawableRes
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.TextButton
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.SwitchDefaults
import androidx.compose.foundation.layout.size
import androidx.compose.ui.res.painterResource
import com.mardev.nearshelf.ui.components.NearshelfTopBar
import com.mardev.nearshelf.ui.components.SectionHeader
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space
import com.mardev.nearshelf.ui.components.readableWidth
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.selection.toggleable
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.prefs.ReadingPrefs
import com.mardev.nearshelf.data.PreferencesRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.util.Locale
import javax.inject.Inject

@HiltViewModel
class PreferencesViewModel @Inject constructor(private val repo: PreferencesRepository) : ViewModel() {
    val prefs: StateFlow<ReadingPrefs?> = repo.prefs.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)
    fun setFormat(f: Format?) = viewModelScope.launch { repo.update { it.copy(preferredFormat = f) } }
    fun toggleLanguage(code: String) = viewModelScope.launch {
        repo.update { p -> p.copy(languages = if (code in p.languages) p.languages - code else p.languages + code) }
    }
    fun setShowOther(show: Boolean) = viewModelScope.launch { repo.update { it.copy(showOtherLanguages = show) } }
}

/** Languages most catalogs in Nearshelf's markets carry, shown in their own names. */
private val LANGUAGES = listOf("en", "fr", "ar", "es", "de", "it", "pt", "nl", "zh", "ja", "ko", "ru", "tr", "hi", "pl", "vi", "tl", "fa")

@Composable
fun PreferencesScreen(onBack: () -> Unit, vm: PreferencesViewModel = hiltViewModel()) {
    val prefs by vm.prefs.collectAsStateWithLifecycle()
    PreferencesContent(prefs, onBack, onFormat = vm::setFormat, onToggleLanguage = vm::toggleLanguage, onShowOther = vm::setShowOther)
}

/** Which preferences pop-up is open. */
internal enum class PrefsDialog { FORMAT, LANGUAGES }

/**
 * Stateless preferences UI (rendered in the screenshot tests): two summary rows that open
 * pop-ups (format: pick one; languages: pick several), then the other-languages switch.
 */
@Composable
internal fun PreferencesContent(
    prefs: ReadingPrefs?,
    onBack: () -> Unit,
    onFormat: (Format?) -> Unit,
    onToggleLanguage: (String) -> Unit,
    onShowOther: (Boolean) -> Unit,
    initialDialog: PrefsDialog? = null,
) {
    val colors = MaterialTheme.colorScheme
    var dialog by rememberSaveable { mutableStateOf(initialDialog) }
    Scaffold(
        topBar = { NearshelfTopBar(stringResource(R.string.prefs_title), onBack = onBack) },
        containerColor = colors.background,
    ) { padding ->
        val p = prefs ?: return@Scaffold
        LazyColumn(Modifier.fillMaxSize().padding(padding).readableWidth(), contentPadding = PaddingValues(top = Space.s, bottom = Space.xxl)) {
            item {
                PickerRow(
                    icon = R.drawable.ic_books,
                    title = stringResource(R.string.prefs_format_heading),
                    value = stringResource(formatLabel(p.preferredFormat)),
                    onClick = { dialog = PrefsDialog.FORMAT },
                )
            }
            item {
                PickerRow(
                    icon = R.drawable.ic_language,
                    title = stringResource(R.string.prefs_languages_heading),
                    value = p.languages.takeIf { it.isNotEmpty() }
                        ?.let { codes -> orderedLanguages(codes).filter { it in codes }.joinToString(", ") { languageName(it) } }
                        ?: stringResource(R.string.prefs_languages_none),
                    onClick = { dialog = PrefsDialog.LANGUAGES },
                    divider = false,
                )
            }
            item {
                HorizontalDivider(Modifier.padding(horizontal = Gutter, vertical = Space.l), color = colors.outlineVariant)
            }
            item {
                Row(
                    Modifier.fillMaxWidth().heightIn(min = 64.dp)
                        .toggleable(value = p.showOtherLanguages, role = Role.Switch, onValueChange = onShowOther)
                        .padding(horizontal = Gutter),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f).padding(end = Space.l), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                        Text(stringResource(R.string.prefs_show_other), style = MaterialTheme.typography.titleMedium)
                        Text(stringResource(R.string.prefs_languages_body), style = MaterialTheme.typography.bodyMedium, color = colors.onSurfaceVariant)
                    }
                    Switch(
                        checked = p.showOtherLanguages,
                        onCheckedChange = null,
                        colors = SwitchDefaults.colors(
                            checkedTrackColor = colors.primary,
                            uncheckedTrackColor = colors.surfaceContainerHigh,
                            uncheckedBorderColor = colors.outlineVariant,
                            uncheckedThumbColor = colors.outline,
                        ),
                    )
                }
            }
        }
        when (dialog) {
            PrefsDialog.FORMAT -> FormatDialog(
                selected = p.preferredFormat,
                onPick = {
                    onFormat(it)
                    dialog = null
                },
                onDismiss = { dialog = null },
            )
            PrefsDialog.LANGUAGES -> LanguagesDialog(
                selected = p.languages,
                onToggle = onToggleLanguage,
                onDismiss = { dialog = null },
            )
            null -> Unit
        }
    }
}

private val FORMATS = listOf(null, Format.EBOOK, Format.AUDIOBOOK, Format.PHYSICAL)

private fun formatLabel(f: Format?) = when (f) {
    null -> R.string.prefs_format_any
    Format.EBOOK -> R.string.format_ebook
    Format.AUDIOBOOK -> R.string.format_audiobook
    Format.PHYSICAL, Format.OTHER -> R.string.format_physical
}

private fun orderedLanguages(selected: Set<String>) = LANGUAGES + (selected - LANGUAGES.toSet())

private fun languageName(code: String) =
    Locale.forLanguageTag(code).let { it.getDisplayLanguage(it) }.replaceFirstChar { it.titlecase() }

/** Setting title with its current value underneath; opens a pop-up. */
@Composable
private fun PickerRow(@DrawableRes icon: Int, title: String, value: String, onClick: () -> Unit, divider: Boolean = true) {
    Column {
        Row(
            Modifier.fillMaxWidth().heightIn(min = 64.dp).clickable(role = Role.Button, onClickLabel = title, onClick = onClick)
                .padding(horizontal = Gutter, vertical = Space.m),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(painterResource(icon), null, tint = MaterialTheme.colorScheme.secondary, modifier = Modifier.size(22.dp))
            Spacer(Modifier.width(Space.l + 2.dp))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Text(value, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary, maxLines = 2, overflow = TextOverflow.Ellipsis)
            }
            Icon(painterResource(R.drawable.ic_caret_right), null, tint = MaterialTheme.colorScheme.outline, modifier = Modifier.size(18.dp))
        }
        if (divider) HorizontalDivider(Modifier.padding(start = Gutter + 40.dp, end = Gutter), color = MaterialTheme.colorScheme.outlineVariant)
    }
}

/** Pick one: tapping a format applies it and closes, as Android's single-choice dialogs do. */
@Composable
private fun FormatDialog(selected: Format?, onPick: (Format?) -> Unit, onDismiss: () -> Unit) {
    PrefsDialogFrame(
        title = stringResource(R.string.prefs_format_heading),
        body = stringResource(R.string.prefs_format_dialog_body),
        confirm = stringResource(R.string.action_close),
        onDismiss = onDismiss,
    ) {
        Column(Modifier.selectableGroup()) {
            FORMATS.forEach { f ->
                ChoiceRow(stringResource(formatLabel(f)), checked = selected == f, role = Role.RadioButton, onClick = { onPick(f) }) {
                    RadioButton(selected = selected == f, onClick = null)
                }
            }
        }
    }
}

/** Pick several: each tap applies at once; Done closes. */
@Composable
private fun LanguagesDialog(selected: Set<String>, onToggle: (String) -> Unit, onDismiss: () -> Unit) {
    PrefsDialogFrame(
        title = stringResource(R.string.prefs_languages_heading),
        body = null,
        confirm = stringResource(R.string.action_done),
        onDismiss = onDismiss,
    ) {
        // Fixed height so the dialog doesn't jump; the list scrolls inside it.
        LazyColumn(Modifier.heightIn(max = 380.dp)) {
            items(orderedLanguages(selected), key = { it }) { code ->
                val on = code in selected
                ChoiceRow(languageName(code), checked = on, role = Role.Checkbox, onClick = { onToggle(code) }) {
                    Checkbox(checked = on, onCheckedChange = null, colors = CheckboxDefaults.colors(checkedColor = MaterialTheme.colorScheme.primary))
                }
            }
        }
    }
}

@Composable
private fun ChoiceRow(label: String, checked: Boolean, role: Role, onClick: () -> Unit, control: @Composable () -> Unit) {
    Row(
        Modifier.fillMaxWidth().heightIn(min = 48.dp).clip(MaterialTheme.shapes.small)
            .then(
                if (role == Role.RadioButton) Modifier.selectable(selected = checked, role = role, onClick = onClick)
                else Modifier.toggleable(value = checked, role = role, onValueChange = { onClick() }),
            )
            .padding(horizontal = Space.xs),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        control()
        Text(label, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(start = Space.m))
    }
}

/** The app's dialog: page-coloured, 16 dp corners, serif title, one text action. */
@Composable
private fun PrefsDialogFrame(title: String, body: String?, confirm: String, onDismiss: () -> Unit, content: @Composable () -> Unit) {
    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = { TextButton(onClick = onDismiss) { Text(confirm, style = MaterialTheme.typography.labelLarge) } },
        title = { Text(title, style = MaterialTheme.typography.titleLarge) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(Space.m)) {
                body?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant) }
                content()
            }
        },
        // Paper on the light theme; one step above the page at night so the pop-up separates.
        containerColor = MaterialTheme.colorScheme.run { if (background.luminance() > 0.5f) background else surfaceContainerHigh },
        titleContentColor = MaterialTheme.colorScheme.onSurface,
        textContentColor = MaterialTheme.colorScheme.onSurface,
        shape = MaterialTheme.shapes.large,
        tonalElevation = 0.dp,
    )
}
