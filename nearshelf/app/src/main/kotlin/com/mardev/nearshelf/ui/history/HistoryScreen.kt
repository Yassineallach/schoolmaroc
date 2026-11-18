package com.mardev.nearshelf.ui.history

import android.text.format.DateUtils
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import com.mardev.nearshelf.ads.NativeAdCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewModelScope
import com.mardev.nearshelf.R
import com.mardev.nearshelf.data.HistoryItem
import com.mardev.nearshelf.data.HistoryRepository
import com.mardev.nearshelf.ui.components.EmptyState
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HistoryViewModel @Inject constructor(private val repo: HistoryRepository) : ViewModel() {
    val items: StateFlow<List<HistoryItem>?> = repo.recent().stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)
    fun remove(key: String) = viewModelScope.launch { repo.remove(key) }
    fun clear() = viewModelScope.launch { repo.clear() }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(onBack: () -> Unit, onOpen: (HistoryItem) -> Unit, vm: HistoryViewModel = hiltViewModel()) {
    val items by vm.items.collectAsStateWithLifecycle()
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.history_title)) },
                navigationIcon = { IconButton(onClick = onBack) { Icon(painterResource(R.drawable.ic_arrow_left), stringResource(R.string.cd_back)) } },
                actions = { if (!items.isNullOrEmpty()) TextButton(onClick = vm::clear) { Text(stringResource(R.string.history_clear)) } },
            )
        },
    ) { padding ->
        val list = items ?: return@Scaffold
        if (list.isEmpty()) {
            EmptyState(R.drawable.ic_history, stringResource(R.string.history_empty_title), stringResource(R.string.history_empty_body), Modifier.padding(padding))
            return@Scaffold
        }
        LazyColumn(Modifier.fillMaxSize().padding(padding), contentPadding = PaddingValues(vertical = 8.dp)) {
            itemsIndexed(list, key = { _, it -> it.key }) { index, item ->
                HistoryRow(item, onOpen = { onOpen(item) }, onRemove = { vm.remove(item.key) })
                HorizontalDivider(Modifier.padding(start = 16.dp))
                // Native ad in the middle of the list: after the 3rd entry (or the last, if fewer).
                if (index == minOf(2, list.lastIndex)) NativeAdCard(Modifier.padding(16.dp))
            }
        }
    }
}

@Composable
fun HistoryRow(item: HistoryItem, onOpen: () -> Unit, onRemove: (() -> Unit)? = null) {
    Row(
        Modifier.fillMaxWidth().heightIn(min = 56.dp).clickable(role = androidx.compose.ui.semantics.Role.Button, onClick = onOpen).padding(start = 16.dp, end = 4.dp, top = 6.dp, bottom = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(painterResource(R.drawable.ic_history), null, tint = MaterialTheme.colorScheme.onSurfaceVariant, modifier = Modifier.size(20.dp))
        Column(Modifier.weight(1f).padding(start = 12.dp)) {
            Text(item.title, style = MaterialTheme.typography.bodyLarge)
            Text(
                listOfNotNull(item.author, DateUtils.getRelativeTimeSpanString(item.searchedAt, System.currentTimeMillis(), DateUtils.MINUTE_IN_MILLIS).toString())
                    .joinToString(" · "),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        if (onRemove != null) {
            IconButton(onClick = onRemove) { Icon(painterResource(R.drawable.ic_x), stringResource(R.string.cd_remove_history, item.title)) }
        }
    }
}
