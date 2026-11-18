package com.mardev.nearshelf.ui.libraries

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.size
import androidx.compose.material3.FloatingActionButtonDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.offset
import com.mardev.nearshelf.ui.components.LibraryRow
import com.mardev.nearshelf.ui.components.LibraryRowSkeleton
import com.mardev.nearshelf.ui.components.NearshelfTopBar
import com.mardev.nearshelf.ui.components.RowDivider
import com.mardev.nearshelf.ui.theme.ButtonShape
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space
import com.mardev.nearshelf.ui.components.readableWidth
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

@Composable
fun LibrariesScreen(onAddLibrary: () -> Unit, vm: LibrariesViewModel = hiltViewModel()) {
    val libraries by vm.libraries.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    var picking by remember { mutableStateOf<Library?>(null) }
    val removedMsg = stringResource(R.string.libraries_removed)
    val undo = stringResource(R.string.action_undo)

    LibrariesContent(
        libraries = libraries,
        snackbar = snackbar,
        onAddLibrary = onAddLibrary,
        onUp = { vm.moveUp(it.id) },
        onDown = { vm.moveDown(it.id) },
        onRemove = { lib ->
            vm.remove(lib.id)
            scope.launch {
                val r = snackbar.showSnackbar(removedMsg.format(lib.name), undo, duration = SnackbarDuration.Long)
                if (r == SnackbarResult.ActionPerformed) vm.restore(lib)
            }
        },
        onPickBranch = { picking = it },
    )
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

/** Stateless Libraries UI (rendered with sample data in the screenshot tests). */
@Composable
internal fun LibrariesContent(
    libraries: List<Library>?,
    snackbar: SnackbarHostState,
    onAddLibrary: () -> Unit,
    onUp: (Library) -> Unit,
    onDown: (Library) -> Unit,
    onRemove: (Library) -> Unit,
    onPickBranch: (Library) -> Unit,
) {
    Scaffold(
        topBar = { NearshelfTopBar(stringResource(R.string.libraries_title), large = true) },
        floatingActionButton = {
            if (!libraries.isNullOrEmpty()) {
                // Flat, same radius as every control: a clear action without a heavy shadow.
                ExtendedFloatingActionButton(
                    onClick = onAddLibrary,
                    icon = { Icon(painterResource(R.drawable.ic_plus), contentDescription = null, modifier = Modifier.size(20.dp)) },
                    text = { Text(stringResource(R.string.libraries_add), style = MaterialTheme.typography.labelLarge) },
                    shape = ButtonShape,
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = MaterialTheme.colorScheme.onPrimary,
                    elevation = FloatingActionButtonDefaults.elevation(0.dp, 0.dp, 0.dp, 0.dp),
                )
            }
        },
        snackbarHost = { SnackbarHost(snackbar) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        val list = libraries
        if (list != null && list.isEmpty()) {
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
            Modifier.fillMaxSize().padding(padding).readableWidth(),
            contentPadding = PaddingValues(bottom = 96.dp),
        ) {
            item(key = "hint") {
                Text(
                    stringResource(R.string.libraries_order_hint),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(start = Gutter, end = Gutter, bottom = Space.xs),
                )
            }
            if (list == null) {
                items(3, key = { "skeleton-$it" }) { LibraryRowSkeleton() }
            } else {
                itemsIndexed(list, key = { _, lib -> lib.id }) { index, lib ->
                    Column(Modifier.animateItem()) {
                        SavedLibraryRow(
                            library = lib,
                            canMoveUp = index > 0,
                            canMoveDown = index < list.lastIndex,
                            onUp = { onUp(lib) },
                            onDown = { onDown(lib) },
                            onRemove = { onRemove(lib) },
                            onPickBranch = { onPickBranch(lib) },
                        )
                        if (index < list.lastIndex) RowDivider()
                    }
                }
            }
        }
    }
}

/**
 * A saved library: the shared [LibraryRow] with its home branch underneath, and an
 * overflow menu for order and removal, so the branch name gets the full line.
 */
@Composable
private fun SavedLibraryRow(
    library: Library,
    canMoveUp: Boolean,
    canMoveDown: Boolean,
    onUp: () -> Unit,
    onDown: () -> Unit,
    onRemove: () -> Unit,
    onPickBranch: () -> Unit,
) {
    var menu by remember { mutableStateOf(false) }
    LibraryRow(
        library,
        trailing = {
            Box {
                IconButton(onClick = { menu = true }, modifier = Modifier.offset(y = (-4).dp)) {
                    Icon(
                        painterResource(R.drawable.ic_more),
                        stringResource(R.string.cd_library_options, library.name),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(20.dp),
                    )
                }
                DropdownMenu(
                    expanded = menu,
                    onDismissRequest = { menu = false },
                    shape = MaterialTheme.shapes.medium,
                    containerColor = MaterialTheme.colorScheme.surfaceContainerLowest,
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
                    shadowElevation = 2.dp,
                ) {
                    MenuItem(R.drawable.ic_caret_up, stringResource(R.string.action_move_up), enabled = canMoveUp) { menu = false; onUp() }
                    MenuItem(R.drawable.ic_caret_down, stringResource(R.string.action_move_down), enabled = canMoveDown) { menu = false; onDown() }
                    MenuItem(R.drawable.ic_trash, stringResource(R.string.action_remove)) { menu = false; onRemove() }
                }
            }
        },
        footer = { HomeBranchButton(library, onPickBranch) },
    )
}

@Composable
private fun MenuItem(icon: Int, text: String, enabled: Boolean = true, onClick: () -> Unit) = DropdownMenuItem(
    text = { Text(text, style = MaterialTheme.typography.bodyLarge) },
    leadingIcon = { Icon(painterResource(icon), null, modifier = Modifier.size(20.dp)) },
    enabled = enabled,
    onClick = onClick,
)
