package com.mardev.nearshelf.ui.libraries

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.stateDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.ui.components.lightswind.Skeleton
import com.mardev.nearshelf.ui.components.lightswind.SkeletonLines
import com.mardev.nearshelf.ui.theme.LocalStatusColors

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddLibraryScreen(onBack: () -> Unit, vm: AddLibraryViewModel = hiltViewModel()) {
    val query by vm.query.collectAsStateWithLifecycle()
    val results by vm.results.collectAsStateWithLifecycle()
    val saved by vm.savedIds.collectAsStateWithLifecycle()
    val focus = remember { FocusRequester() }
    LaunchedEffect(Unit) { focus.requestFocus() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.add_library_title)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(painterResource(R.drawable.ic_arrow_left), stringResource(R.string.cd_back))
                    }
                },
            )
        },
    ) { padding ->
        LazyColumn(Modifier.fillMaxSize().padding(padding), contentPadding = PaddingValues(bottom = 24.dp)) {
            item {
                OutlinedTextField(
                    value = query,
                    onValueChange = { vm.query.value = it },
                    label = { Text(stringResource(R.string.add_library_field)) },
                    placeholder = { Text(stringResource(R.string.add_library_hint)) },
                    leadingIcon = { Icon(painterResource(R.drawable.ic_search), contentDescription = null) },
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                    modifier = Modifier.fillMaxWidth().padding(16.dp).focusRequester(focus),
                )
            }
            when (val r = results) {
                LibrarySearchUi.Idle -> item {
                    Text(
                        stringResource(R.string.add_library_idle),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.padding(horizontal = 16.dp),
                    )
                }
                LibrarySearchUi.Loading -> items(4) { LoadingRow() }
                is LibrarySearchUi.Results -> {
                    if (r.failed.isNotEmpty()) item {
                        Text(
                            stringResource(R.string.add_library_partial, r.failed.joinToString { it.displayName }),
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.error,
                            modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                        )
                    }
                    if (r.libraries.isEmpty()) item {
                        Text(
                            stringResource(R.string.add_library_none, r.query),
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.padding(horizontal = 16.dp),
                        )
                    }
                    items(r.libraries, key = { it.id }) { lib ->
                        val added = lib.id in saved
                        CandidateRow(lib, added) { if (added) vm.remove(lib.id) else vm.add(lib) }
                        HorizontalDivider(Modifier.padding(start = 16.dp))
                    }
                }
            }
        }
    }
}

@Composable
private fun CandidateRow(library: Library, added: Boolean, onToggle: () -> Unit) {
    val stateText = stringResource(if (added) R.string.state_added else R.string.state_not_added)
    Row(
        Modifier.fillMaxWidth().heightIn(min = 64.dp)
            .clickable(role = Role.Checkbox, onClick = onToggle)
            .semantics { stateDescription = stateText }
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(library.name, style = MaterialTheme.typography.titleMedium)
            library.locationLine().takeIf { it.isNotEmpty() }?.let {
                Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Text(library.servicesLine(), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary)
        }
        if (added) {
            Icon(painterResource(R.drawable.ic_check_circle), null, tint = LocalStatusColors.current.available, modifier = Modifier.size(28.dp))
        } else {
            Icon(painterResource(R.drawable.ic_plus), null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(24.dp))
        }
    }
}

@Composable
private fun LoadingRow() {
    Row(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 14.dp), verticalAlignment = Alignment.CenterVertically) {
        SkeletonLines(count = 3, modifier = Modifier.weight(1f), lineHeight = 12.dp)
        Skeleton(Modifier.padding(start = 16.dp).size(24.dp))
    }
}
