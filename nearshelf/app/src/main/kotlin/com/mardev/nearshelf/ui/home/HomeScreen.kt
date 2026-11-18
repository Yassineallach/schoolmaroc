package com.mardev.nearshelf.ui.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.data.HistoryItem
import com.mardev.nearshelf.ui.history.HistoryRow
import com.mardev.nearshelf.ui.libraries.locationLine
import com.mardev.nearshelf.ui.libraries.servicesLine

@Composable
fun HomeScreen(
    prefill: String?,
    onPrefillConsumed: () -> Unit,
    onScan: () -> Unit,
    onSearch: (BookQuery) -> Unit,
    onManageLibraries: () -> Unit,
    onAddLibrary: () -> Unit,
    onOpenHistory: (HistoryItem?) -> Unit,
    onPreferences: () -> Unit,
    onSettings: () -> Unit,
    vm: HomeViewModel = hiltViewModel(),
) {
    val recent by vm.recent.collectAsStateWithLifecycle()
    val input by vm.input.collectAsStateWithLifecycle()
    val libraries by vm.libraries.collectAsStateWithLifecycle()
    val keyboard = LocalSoftwareKeyboardController.current
    val hasCamera = androidx.compose.ui.platform.LocalContext.current.packageManager
        .hasSystemFeature(android.content.pm.PackageManager.FEATURE_CAMERA_ANY)
    LaunchedEffect(prefill) {
        if (prefill != null) {
            vm.input.value = prefill
            onPrefillConsumed()
        }
    }
    val submit = {
        vm.parsedQuery()?.let {
            keyboard?.hide()
            onSearch(it)
        }
    }

    LazyColumn(
        Modifier.fillMaxSize().statusBarsPadding(),
        contentPadding = PaddingValues(start = 20.dp, end = 20.dp, top = 32.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Spacer(Modifier.weight(1f))
                    IconButton(onClick = onPreferences) {
                        Icon(painterResource(R.drawable.ic_sliders), stringResource(R.string.cd_reading_preferences))
                    }
                    IconButton(onClick = onSettings) {
                        Icon(painterResource(R.drawable.ic_settings), stringResource(R.string.settings_title))
                    }
                }
                Text(
                    stringResource(R.string.app_name),
                    style = MaterialTheme.typography.displaySmall,
                    color = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.semantics { heading() },
                )
                Text(
                    stringResource(R.string.tagline),
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
        item {
            OutlinedTextField(
                value = input,
                onValueChange = { vm.input.value = it },
                label = { Text(stringResource(R.string.search_label)) },
                placeholder = { Text(stringResource(R.string.search_hint)) },
                supportingText = { Text(stringResource(R.string.search_supporting)) },
                leadingIcon = { Icon(painterResource(R.drawable.ic_search), contentDescription = null) },
                trailingIcon = {
                    if (input.isNotEmpty()) {
                        IconButton(onClick = { vm.input.value = "" }) {
                            Icon(painterResource(R.drawable.ic_x), stringResource(R.string.cd_clear))
                        }
                    } else if (hasCamera) {
                        IconButton(onClick = onScan) {
                            Icon(painterResource(R.drawable.ic_barcode), stringResource(R.string.cd_scan_barcode))
                        }
                    }
                },
                singleLine = true,
                shape = RoundedCornerShape(16.dp),
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                keyboardActions = KeyboardActions(onSearch = { submit() }),
                modifier = Modifier.fillMaxWidth(),
            )
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(
                    onClick = { submit() },
                    enabled = input.isNotBlank() && libraries?.isNotEmpty() == true,
                    modifier = Modifier.weight(1f).heightIn(min = 52.dp),
                ) {
                    Text(stringResource(R.string.search_action))
                }
                if (hasCamera) OutlinedButton(
                    onClick = onScan,
                    enabled = libraries?.isNotEmpty() == true,
                    modifier = Modifier.heightIn(min = 52.dp),
                ) {
                    Icon(painterResource(R.drawable.ic_barcode), null, modifier = Modifier.size(20.dp))
                    Spacer(Modifier.size(8.dp))
                    Text(stringResource(R.string.action_scan))
                }
            }
        }
        if (recent.isNotEmpty()) {
            item {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 8.dp)) {
                    Text(
                        stringResource(R.string.home_recent),
                        style = MaterialTheme.typography.titleLarge,
                        modifier = Modifier.weight(1f).semantics { heading() },
                    )
                    TextButton(onClick = { onOpenHistory(null) }) { Text(stringResource(R.string.home_see_all)) }
                }
            }
            items(recent, key = { "h-" + it.key }) { h -> HistoryRow(h, onOpen = { onOpenHistory(h) }) }
        }
        item {
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 8.dp)) {
                Text(
                    stringResource(R.string.home_your_libraries),
                    style = MaterialTheme.typography.titleLarge,
                    modifier = Modifier.weight(1f).semantics { heading() },
                )
                if (libraries?.isNotEmpty() == true) {
                    TextButton(onClick = onManageLibraries) { Text(stringResource(R.string.home_manage)) }
                }
            }
        }
        val list = libraries
        when {
            list == null -> Unit
            list.isEmpty() -> item { NoLibrariesCard(onAddLibrary) }
            else -> items(list, key = { it.id }) { LibrarySummary(it) }
        }
    }
}

@Composable
private fun LibrarySummary(library: Library) {
    Row(verticalAlignment = Alignment.CenterVertically) {
        Icon(
            painterResource(R.drawable.ic_library),
            null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.size(20.dp),
        )
        Spacer(Modifier.size(12.dp))
        Column {
            Text(library.name, style = MaterialTheme.typography.bodyLarge)
            Text(
                listOf(library.locationLine(), library.servicesLine()).filter { it.isNotEmpty() }.joinToString(" · "),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun NoLibrariesCard(onAdd: () -> Unit) {
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiaryContainer)) {
        Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Icon(painterResource(R.drawable.ic_books), null, modifier = Modifier.size(32.dp))
            Text(stringResource(R.string.home_no_libraries_title), style = MaterialTheme.typography.titleLarge)
            Text(stringResource(R.string.home_no_libraries_body), style = MaterialTheme.typography.bodyMedium)
            Button(onClick = onAdd, modifier = Modifier.padding(top = 4.dp)) {
                Icon(painterResource(R.drawable.ic_plus), null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.size(8.dp))
                Text(stringResource(R.string.libraries_add))
            }
        }
    }
}
