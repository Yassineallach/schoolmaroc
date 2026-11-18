package com.mardev.nearshelf.ui.libraries

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.ui.components.FieldHint
import com.mardev.nearshelf.ui.components.LibraryRow
import com.mardev.nearshelf.ui.components.LibraryRowSkeleton
import com.mardev.nearshelf.ui.components.NearshelfTopBar
import com.mardev.nearshelf.ui.components.PaperSearchField
import com.mardev.nearshelf.ui.components.RowDivider
import com.mardev.nearshelf.ui.theme.ControlShape
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space
import com.mardev.nearshelf.ui.components.readableWidth
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

@Composable
fun AddLibraryScreen(onBack: () -> Unit, vm: AddLibraryViewModel = hiltViewModel()) {
    val query by vm.query.collectAsStateWithLifecycle()
    val results by vm.results.collectAsStateWithLifecycle()
    val saved by vm.saved.collectAsStateWithLifecycle()
    AddLibraryContent(
        query = query,
        onQueryChange = { vm.query.value = it },
        results = results,
        saved = saved,
        onToggle = { lib, added -> if (added) vm.remove(lib.id) else vm.add(lib) },
        onBack = onBack,
    )
}

/** Stateless Add-library UI (rendered with sample data in the screenshot tests). */
@Composable
internal fun AddLibraryContent(
    query: String,
    onQueryChange: (String) -> Unit,
    results: LibrarySearchUi,
    saved: Map<String, Set<Pair<ProviderId, String>>>,
    onToggle: (Library, Boolean) -> Unit,
    onBack: () -> Unit,
    autoFocus: Boolean = true,
) {
    val focus = remember { FocusRequester() }
    LaunchedEffect(Unit) { if (autoFocus) focus.requestFocus() }
    fun isAdded(lib: Library): Boolean {
        val have = saved[lib.id]
        return have != null && lib.services.all { (it.provider to it.key) in have }
    }

    Scaffold(
        topBar = { NearshelfTopBar(stringResource(R.string.add_library_title), onBack = onBack) },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        LazyColumn(Modifier.fillMaxSize().padding(padding).readableWidth(), contentPadding = PaddingValues(bottom = Space.xl)) {
            item(key = "field") {
                Column(Modifier.padding(start = Gutter, end = Gutter, top = Space.s, bottom = Space.l)) {
                    PaperSearchField(
                        value = query,
                        onValueChange = onQueryChange,
                        placeholder = stringResource(R.string.add_library_hint),
                        label = stringResource(R.string.add_library_field),
                        modifier = Modifier.focusRequester(focus),
                    )
                    FieldHint(
                        stringResource(R.string.search_tip_label),
                        stringResource(R.string.add_library_url_tip_body),
                        Modifier.padding(top = Space.s, start = 2.dp),
                    )
                }
            }
            when (val r = results) {
                LibrarySearchUi.Idle -> item(key = "idle") { Note(stringResource(R.string.add_library_idle)) }
                LibrarySearchUi.Loading -> items(4, key = { "sk-$it" }) { LibraryRowSkeleton() }
                is LibrarySearchUi.Detected -> item(key = "detected") {
                    val lib = r.library
                    if (lib == null) {
                        Note(stringResource(R.string.add_library_not_recognised))
                    } else {
                        Text(
                            stringResource(R.string.add_library_recognised, r.provider?.displayName.orEmpty()),
                            style = MaterialTheme.typography.labelLarge,
                            color = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.padding(horizontal = Gutter),
                        )
                        CandidateRow(lib, isAdded(lib)) { onToggle(lib, isAdded(lib)) }
                    }
                }
                is LibrarySearchUi.Results -> {
                    if (r.failed.isNotEmpty()) item(key = "partial") {
                        Note(stringResource(R.string.add_library_partial, r.failed.joinToString { it.displayName }), color = MaterialTheme.colorScheme.error)
                    }
                    if (r.libraries.isEmpty()) item(key = "none") { Note(stringResource(R.string.add_library_none, r.query)) }
                    itemsIndexed(r.libraries, key = { _, l -> l.id }) { i, lib ->
                        CandidateRow(lib, isAdded(lib)) { onToggle(lib, isAdded(lib)) }
                        if (i < r.libraries.lastIndex) RowDivider()
                    }
                }
            }
        }
    }
}

@Composable
private fun Note(text: String, color: androidx.compose.ui.graphics.Color = MaterialTheme.colorScheme.onSurfaceVariant) = Text(
    text,
    style = MaterialTheme.typography.bodyMedium,
    color = color,
    modifier = Modifier.padding(horizontal = Gutter, vertical = Space.xs),
)

/** A search result: the shared library row, toggled by tapping anywhere on it. */
@Composable
private fun CandidateRow(library: Library, added: Boolean, onToggle: () -> Unit) {
    val stateText = stringResource(if (added) R.string.state_added else R.string.state_not_added)
    val colors = MaterialTheme.colorScheme
    LibraryRow(
        library,
        modifier = Modifier.semantics { stateDescription = stateText },
        onClick = onToggle,
        role = Role.Checkbox,
        trailing = {
            // Added: filled brown check; not yet: a hairline square with a plus.
            Box(
                Modifier
                    .padding(start = Space.m)
                    .size(36.dp)
                    .clip(ControlShape)
                    .background(if (added) colors.primary else Color.Transparent)
                    .border(1.dp, if (added) colors.primary else colors.outlineVariant, ControlShape),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    painterResource(if (added) R.drawable.ic_check else R.drawable.ic_plus),
                    contentDescription = null,
                    tint = if (added) colors.onPrimary else colors.primary,
                    modifier = Modifier.size(18.dp),
                )
            }
        },
    )
}
