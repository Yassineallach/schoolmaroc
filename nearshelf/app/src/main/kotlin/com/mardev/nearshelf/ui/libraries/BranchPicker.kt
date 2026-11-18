package com.mardev.nearshelf.ui.libraries

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
    ModalBottomSheet(onDismissRequest = onDismiss, sheetState = sheet) {
        Column(Modifier.navigationBarsPadding()) {
            Text(
                stringResource(R.string.branch_picker_title, library.name),
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.padding(horizontal = 16.dp),
            )
            if (library.branches.size > 8) {
                OutlinedTextField(
                    value = filter,
                    onValueChange = { filter = it },
                    label = { Text(stringResource(R.string.branch_picker_filter)) },
                    leadingIcon = { Icon(painterResource(R.drawable.ic_search), null) },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth().padding(16.dp),
                )
            }
            LazyColumn(Modifier.fillMaxWidth().heightIn(max = 520.dp)) {
                items(shown, key = { it.id }) { b ->
                    BranchRow(b, selected = b.id == library.homeBranchId) { onPick(b.id) }
                    HorizontalDivider(Modifier.padding(start = 56.dp))
                }
            }
            if (library.homeBranchId != null) {
                TextButton(onClick = { onPick(null) }, modifier = Modifier.padding(8.dp)) {
                    Text(stringResource(R.string.branch_picker_clear))
                }
            }
        }
    }
}

@Composable
private fun BranchRow(branch: Branch, selected: Boolean, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().heightIn(min = 56.dp)
            .clickable(role = Role.RadioButton, onClick = onClick)
            .padding(horizontal = 8.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RadioButton(selected = selected, onClick = null, modifier = Modifier.padding(horizontal = 8.dp))
        Column {
            Text(branch.name, style = MaterialTheme.typography.bodyLarge)
            listOfNotNull(branch.address, branch.city).joinToString(", ").takeIf { it.isNotEmpty() }?.let {
                Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun HomeBranchButton(library: Library, onClick: () -> Unit) {
    if (library.branches.isEmpty()) return
    TextButton(onClick = onClick) {
        Icon(painterResource(R.drawable.ic_map_pin), null, modifier = Modifier.size(18.dp))
        Text(
            library.homeBranch?.let { stringResource(R.string.home_branch_value, it.name) }
                ?: stringResource(R.string.home_branch_choose),
            modifier = Modifier.padding(start = 6.dp),
        )
    }
}
