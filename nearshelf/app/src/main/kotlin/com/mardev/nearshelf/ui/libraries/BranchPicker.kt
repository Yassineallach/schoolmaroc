package com.mardev.nearshelf.ui.libraries

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.offset
import com.mardev.nearshelf.ui.components.PaperSearchField
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.match.TextNormalizer
import com.mardev.nearshelf.core.model.Branch
import com.mardev.nearshelf.core.model.Library

/** Home branch: shown first in physical results. Searchable because big systems have 100+ branches. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BranchPickerSheet(library: Library, onPick: (String?) -> Unit, onDismiss: () -> Unit) {
    val sheet = rememberModalBottomSheetState(skipPartiallyExpanded = true)
    var filter by rememberSaveable { mutableStateOf("") }
    val shown = remember(filter, library.branches) {
        val f = TextNormalizer.basic(filter)
        library.branches.filter { f.isEmpty() || f in TextNormalizer.basic("${it.name} ${it.address.orEmpty()} ${it.city.orEmpty()}") }
    }
    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheet,
        containerColor = MaterialTheme.colorScheme.background,
        shape = MaterialTheme.shapes.extraLarge.copy(bottomStart = androidx.compose.foundation.shape.CornerSize(0.dp), bottomEnd = androidx.compose.foundation.shape.CornerSize(0.dp)),
    ) {
        Column(Modifier.navigationBarsPadding()) {
            Text(
                stringResource(R.string.branch_picker_title, library.name),
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.padding(horizontal = Gutter).padding(bottom = Space.m),
            )
            if (library.branches.size > 8) {
                PaperSearchField(
                    value = filter,
                    onValueChange = { filter = it },
                    placeholder = stringResource(R.string.branch_picker_filter),
                    label = stringResource(R.string.branch_picker_filter),
                    modifier = Modifier.padding(start = Gutter, end = Gutter, bottom = Space.s),
                )
            }
            LazyColumn(Modifier.fillMaxWidth().heightIn(max = 520.dp)) {
                items(shown, key = { it.id }) { b ->
                    BranchRow(b, selected = b.id == library.homeBranchId) { onPick(b.id) }
                    HorizontalDivider(Modifier.padding(start = Gutter + 40.dp, end = Gutter), color = MaterialTheme.colorScheme.outlineVariant)
                }
            }
            if (library.homeBranchId != null) {
                TextButton(onClick = { onPick(null) }, modifier = Modifier.padding(horizontal = Gutter - 12.dp, vertical = Space.s)) {
                    Text(stringResource(R.string.branch_picker_clear), style = MaterialTheme.typography.labelLarge)
                }
            }
        }
    }
}

@Composable
private fun BranchRow(branch: Branch, selected: Boolean, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().heightIn(min = 64.dp)
            .clickable(role = Role.RadioButton, onClick = onClick)
            .padding(horizontal = Gutter - 12.dp, vertical = Space.s),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RadioButton(selected = selected, onClick = null, modifier = Modifier.padding(start = 12.dp, end = Space.l))
        Column {
            Text(branch.name, style = MaterialTheme.typography.titleMedium)
            listOfNotNull(branch.address, branch.city).joinToString(", ").takeIf { it.isNotEmpty() }?.let {
                Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun HomeBranchButton(library: Library, onClick: () -> Unit) {
    if (library.branches.isEmpty()) return
    // Text action that starts on the text column (offset cancels the button's own padding).
    TextButton(onClick = onClick, contentPadding = PaddingValues(horizontal = 12.dp), modifier = Modifier.padding(top = Space.xs).offset(x = (-12).dp)) {
        Icon(painterResource(R.drawable.ic_map_pin), null, modifier = Modifier.size(16.dp))
        Text(
            library.homeBranch?.let { stringResource(R.string.home_branch_value, it.name) }
                ?: stringResource(R.string.home_branch_choose),
            style = MaterialTheme.typography.labelLarge,
            maxLines = 2,
            overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis,
            modifier = Modifier.padding(start = 6.dp),
        )
    }
}
