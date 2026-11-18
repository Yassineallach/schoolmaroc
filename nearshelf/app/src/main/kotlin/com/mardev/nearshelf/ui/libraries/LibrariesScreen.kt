package com.mardev.nearshelf.ui.libraries

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExtendedFloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.ui.components.EmptyState
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LibrariesScreen(onAddLibrary: () -> Unit, vm: LibrariesViewModel = hiltViewModel()) {
    val libraries by vm.libraries.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    var picking by remember { mutableStateOf<Library?>(null) }
    val removedMsg = stringResource(R.string.libraries_removed)
    val undo = stringResource(R.string.action_undo)

    Scaffold(
        topBar = { TopAppBar(title = { Text(stringResource(R.string.libraries_title)) }) },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = onAddLibrary,
                icon = { Icon(painterResource(R.drawable.ic_plus), contentDescription = null) },
                text = { Text(stringResource(R.string.libraries_add)) },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        val list = libraries ?: return@Scaffold
        if (list.isEmpty()) {
            EmptyState(
                icon = R.drawable.ic_library,
                title = stringResource(R.string.libraries_empty_title),
                body = stringResource(R.string.libraries_empty_body),
                action = stringResource(R.string.libraries_add),
                onAction = onAddLibrary,
                modifier = Modifier.padding(padding),
            )
            return@Scaffold
        }
        LazyColumn(
            Modifier.fillMaxSize().padding(padding),
            contentPadding = PaddingValues(start = 16.dp, end = 16.dp, top = 8.dp, bottom = 96.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                Text(
                    stringResource(R.string.libraries_order_hint),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            itemsIndexed(list, key = { _, lib -> lib.id }) { index, lib ->
                SavedLibraryCard(
                    library = lib,
                    canMoveUp = index > 0,
                    canMoveDown = index < list.lastIndex,
                    onUp = { vm.moveUp(lib.id) },
                    onDown = { vm.moveDown(lib.id) },
                    onRemove = {
                        vm.remove(lib.id)
                        scope.launch {
                            val r = snackbar.showSnackbar(removedMsg.format(lib.name), undo, duration = SnackbarDuration.Long)
                            if (r == SnackbarResult.ActionPerformed) vm.restore(lib)
                        }
                    },
                    onPickBranch = { picking = lib },
                    modifier = Modifier.animateItem(),
                )
            }
        }
    }
    picking?.let { lib ->
        BranchPickerSheet(
            library = lib,
            onPick = { id ->
                vm.setHomeBranch(lib, id)
                picking = null
            },
            onDismiss = { picking = null },
        )
    }
}

@Composable
private fun SavedLibraryCard(
    library: Library,
    canMoveUp: Boolean,
    canMoveDown: Boolean,
    onUp: () -> Unit,
    onDown: () -> Unit,
    onRemove: () -> Unit,
    onPickBranch: () -> Unit,
    modifier: Modifier = Modifier,
) {
    ElevatedCard(modifier.fillMaxWidth()) {
        Column {
        Row(Modifier.padding(start = 16.dp, top = 12.dp, bottom = 4.dp, end = 4.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(library.name, style = MaterialTheme.typography.titleMedium, modifier = Modifier.semantics { heading() })
                library.locationLine().takeIf { it.isNotEmpty() }?.let {
                    Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                Text(library.servicesLine(), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.primary)
            }
            IconButton(onClick = onUp, enabled = canMoveUp) {
                Icon(painterResource(R.drawable.ic_caret_up), stringResource(R.string.cd_move_up, library.name))
            }
            IconButton(onClick = onDown, enabled = canMoveDown) {
                Icon(painterResource(R.drawable.ic_caret_down), stringResource(R.string.cd_move_down, library.name))
            }
            IconButton(onClick = onRemove) {
                Icon(painterResource(R.drawable.ic_trash), stringResource(R.string.cd_remove_library, library.name))
            }
        }
        Row(Modifier.padding(start = 4.dp, bottom = 4.dp)) { HomeBranchButton(library, onPickBranch) }
        }
    }
}
