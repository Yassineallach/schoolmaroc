package com.mardev.nearshelf.ui.debug

import android.content.ActivityNotFoundException
import android.content.Intent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.core.net.toUri
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding

/** Milestone-1 spike screen: exercises OverDriveProvider end to end. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProviderDebugScreen(vm: ProviderDebugViewModel = hiltViewModel()) {
    val state by vm.state.collectAsStateWithLifecycle()
    val context = LocalContext.current

    Scaffold(topBar = { TopAppBar(title = { Text(stringResource(R.string.debug_title)) }) }) { padding ->
        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            val selected = state.selected
            if (selected == null) {
                item {
                    OutlinedTextField(
                        value = state.libraryQuery,
                        onValueChange = vm::onLibraryQuery,
                        label = { Text(stringResource(R.string.debug_library_label)) },
                        placeholder = { Text(stringResource(R.string.debug_library_hint)) },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                items(state.libraries, key = { it.key }) { lib ->
                    Column(
                        Modifier.fillMaxWidth().heightIn(min = 48.dp).clickable { vm.select(lib) }.padding(vertical = 8.dp),
                    ) {
                        Text(lib.name, style = MaterialTheme.typography.titleMedium)
                        Text(
                            listOfNotNull(lib.city, lib.region, lib.countryCode).joinToString(", ") + " · " + lib.key,
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                    HorizontalDivider()
                }
            } else {
                item {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(selected.name, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                        TextButton(onClick = { vm.select(null) }) { Text(stringResource(R.string.debug_change_library)) }
                    }
                }
                item {
                    OutlinedTextField(
                        value = state.bookQuery,
                        onValueChange = vm::onBookQuery,
                        label = { Text(stringResource(R.string.debug_book_label)) },
                        singleLine = true,
                        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                        keyboardActions = KeyboardActions(onSearch = { vm.search() }),
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
                item { Button(onClick = vm::search) { Text(stringResource(R.string.debug_search)) } }
                if (state.loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
                state.holdings?.let { list ->
                    if (list.isEmpty()) item { Text(stringResource(R.string.debug_no_results)) }
                    items(list, key = { it.providerItemId }) { h ->
                        HoldingCard(h) {
                            vm.libbyLink(h)?.let { url ->
                                try {
                                    context.startActivity(Intent(Intent.ACTION_VIEW, url.toUri()))
                                } catch (_: ActivityNotFoundException) {
                                }
                            }
                        }
                    }
                }
            }
            state.error?.let { msg ->
                item { Text(msg, color = MaterialTheme.colorScheme.error) }
            }
        }
    }
}

@Composable
private fun HoldingCard(h: Holding, onOpen: () -> Unit) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                AssistChip(onClick = {}, label = { Text(formatLabel(h.format)) })
                Spacer(Modifier.width(8.dp))
                h.language?.let { Text(it.uppercase(), style = MaterialTheme.typography.labelMedium) }
            }
            Text(h.title, style = MaterialTheme.typography.titleMedium)
            if (h.authors.isNotEmpty()) Text(h.authors.joinToString(), style = MaterialTheme.typography.bodyMedium)
            Text(availabilityLine(h), style = MaterialTheme.typography.bodyMedium)
            Button(onClick = onOpen) { Text(stringResource(R.string.debug_open_libby)) }
        }
    }
}

@Composable
private fun formatLabel(f: Format) = stringResource(
    when (f) {
        Format.EBOOK -> R.string.format_ebook
        Format.AUDIOBOOK -> R.string.format_audiobook
        Format.PHYSICAL -> R.string.format_physical
        Format.OTHER -> R.string.format_other
    },
)

@Composable
private fun availabilityLine(h: Holding): String {
    val owned = h.owned ?: 0
    return when {
        h.isAvailableNow -> stringResource(R.string.debug_available_now, h.available ?: 0, owned)
        h.waitDays != null -> stringResource(R.string.debug_waitlist, h.holds ?: 0, owned, h.waitDays!!)
        else -> stringResource(R.string.debug_waitlist_no_estimate, h.holds ?: 0, owned)
    }
}
