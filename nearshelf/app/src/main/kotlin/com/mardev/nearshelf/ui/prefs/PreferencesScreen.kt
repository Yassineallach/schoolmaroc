package com.mardev.nearshelf.ui.prefs

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

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PreferencesScreen(onBack: () -> Unit, vm: PreferencesViewModel = hiltViewModel()) {
    val prefs by vm.prefs.collectAsStateWithLifecycle()
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.prefs_title)) },
                navigationIcon = { IconButton(onClick = onBack) { Icon(painterResource(R.drawable.ic_arrow_left), stringResource(R.string.cd_back)) } },
            )
        },
    ) { padding ->
        val p = prefs ?: return@Scaffold
        LazyColumn(Modifier.fillMaxSize().padding(padding).readableWidth(), contentPadding = PaddingValues(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            item { Heading(stringResource(R.string.prefs_format_heading)) }
            item {
                Column(Modifier.selectableGroup()) {
                    listOf(null to R.string.prefs_format_any, Format.EBOOK to R.string.format_ebook, Format.AUDIOBOOK to R.string.format_audiobook, Format.PHYSICAL to R.string.format_physical)
                        .forEach { (f, label) ->
                            Row(
                                Modifier.fillMaxWidth().heightIn(min = 48.dp)
                                    .selectable(selected = p.preferredFormat == f, role = Role.RadioButton) { vm.setFormat(f) },
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                RadioButton(selected = p.preferredFormat == f, onClick = null)
                                Text(stringResource(label), style = MaterialTheme.typography.bodyLarge, modifier = Modifier.padding(start = 12.dp))
                            }
                        }
                }
            }
            item { Heading(stringResource(R.string.prefs_languages_heading)) }
            item {
                Text(stringResource(R.string.prefs_languages_body), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            item {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    (LANGUAGES + (p.languages - LANGUAGES.toSet())).forEach { code ->
                        val name = Locale.forLanguageTag(code).let { it.getDisplayLanguage(it) }.replaceFirstChar { it.titlecase() }
                        FilterChip(selected = code in p.languages, onClick = { vm.toggleLanguage(code) }, label = { Text(name) })
                    }
                }
            }
            item {
                Row(
                    Modifier.fillMaxWidth().heightIn(min = 56.dp)
                        .toggleable(value = p.showOtherLanguages, role = Role.Switch, onValueChange = vm::setShowOther),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(stringResource(R.string.prefs_show_other), style = MaterialTheme.typography.bodyLarge)
                        Text(stringResource(R.string.prefs_show_other_body), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    Switch(checked = p.showOtherLanguages, onCheckedChange = null)
                }
            }
        }
    }
}

@Composable
private fun Heading(text: String) =
    Text(text, style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(top = 8.dp).semantics { heading() })
