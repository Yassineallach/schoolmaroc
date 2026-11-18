package com.mardev.nearshelf.ui.prefs

import androidx.compose.material3.FilterChipDefaults
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.SwitchDefaults
import androidx.compose.foundation.layout.size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import com.mardev.nearshelf.ui.components.NearshelfTopBar
import com.mardev.nearshelf.ui.components.SectionHeader
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space
import com.mardev.nearshelf.ui.components.readableWidth
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
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
import androidx.compose.material3.FilterChip
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

/** Stateless preferences UI (rendered in the screenshot tests). */
@OptIn(ExperimentalLayoutApi::class)
@Composable
internal fun PreferencesContent(
    prefs: ReadingPrefs?,
    onBack: () -> Unit,
    onFormat: (Format?) -> Unit,
    onToggleLanguage: (String) -> Unit,
    onShowOther: (Boolean) -> Unit,
) {
    val colors = MaterialTheme.colorScheme
    Scaffold(
        topBar = { NearshelfTopBar(stringResource(R.string.prefs_title), onBack = onBack) },
        containerColor = colors.background,
    ) { padding ->
        val p = prefs ?: return@Scaffold
        LazyColumn(Modifier.fillMaxSize().padding(padding).readableWidth(), contentPadding = PaddingValues(bottom = Space.xxl)) {
            item { SectionHeader(stringResource(R.string.prefs_format_heading)) }
            item {
                Column(Modifier.selectableGroup()) {
                    listOf(null to R.string.prefs_format_any, Format.EBOOK to R.string.format_ebook, Format.AUDIOBOOK to R.string.format_audiobook, Format.PHYSICAL to R.string.format_physical)
                        .forEach { (f, label) ->
                            Row(
                                Modifier.fillMaxWidth().heightIn(min = 52.dp)
                                    .selectable(selected = p.preferredFormat == f, role = Role.RadioButton) { onFormat(f) }
                                    .padding(horizontal = Gutter - 12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                RadioButton(selected = p.preferredFormat == f, onClick = null, modifier = Modifier.padding(horizontal = 12.dp))
                                Text(stringResource(label), style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(start = Space.xs))
                            }
                        }
                }
            }
            item { SectionHeader(stringResource(R.string.prefs_languages_heading), Modifier.padding(top = Space.l)) }
            item {
                Text(
                    stringResource(R.string.prefs_languages_body),
                    style = MaterialTheme.typography.bodyMedium,
                    color = colors.onSurfaceVariant,
                    modifier = Modifier.padding(start = Gutter, end = Gutter, bottom = Space.m),
                )
            }
            item {
                FlowRow(
                    Modifier.padding(horizontal = Gutter),
                    horizontalArrangement = Arrangement.spacedBy(Space.s),
                    verticalArrangement = Arrangement.spacedBy(Space.s),
                ) {
                    (LANGUAGES + (p.languages - LANGUAGES.toSet())).forEach { code ->
                        val name = Locale.forLanguageTag(code).let { it.getDisplayLanguage(it) }.replaceFirstChar { it.titlecase() }
                        val selected = code in p.languages
                        FilterChip(
                            selected = selected,
                            onClick = { onToggleLanguage(code) },
                            label = { Text(name, style = MaterialTheme.typography.labelLarge) },
                            leadingIcon = if (selected) {
                                { Icon(painterResource(R.drawable.ic_check), null, modifier = Modifier.size(16.dp)) }
                            } else null,
                            shape = MaterialTheme.shapes.small,
                            colors = FilterChipDefaults.filterChipColors(
                                containerColor = Color.Transparent,
                                labelColor = colors.onSurface,
                                selectedContainerColor = colors.primaryContainer,
                                selectedLabelColor = colors.onPrimaryContainer,
                                selectedLeadingIconColor = colors.onPrimaryContainer,
                            ),
                            border = FilterChipDefaults.filterChipBorder(
                                enabled = true,
                                selected = selected,
                                borderColor = colors.outlineVariant,
                                selectedBorderColor = colors.primaryContainer,
                            ),
                        )
                    }
                }
            }
            item {
                HorizontalDivider(Modifier.padding(horizontal = Gutter, vertical = Space.xl), color = colors.outlineVariant)
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
                        Text(stringResource(R.string.prefs_show_other_body), style = MaterialTheme.typography.bodyMedium, color = colors.onSurfaceVariant)
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
    }
}
