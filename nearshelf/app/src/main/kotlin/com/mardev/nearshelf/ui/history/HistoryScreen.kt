package com.mardev.nearshelf.ui.history

import com.mardev.nearshelf.ui.components.NearshelfTopBar
import com.mardev.nearshelf.ui.theme.BookTitle
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space
import com.mardev.nearshelf.ui.components.readableWidth
import android.text.format.DateUtils
import androidx.compose.foundation.layout.offset
import com.mardev.nearshelf.ui.components.CoverThumb
import com.mardev.nearshelf.ui.components.ListRow
import com.mardev.nearshelf.ui.components.RowDivider
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

@Composable
fun HistoryScreen(onBack: () -> Unit, onOpen: (HistoryItem) -> Unit, vm: HistoryViewModel = hiltViewModel()) {
    val items by vm.items.collectAsStateWithLifecycle()
    HistoryContent(items, onBack, onOpen, onRemove = { vm.remove(it.key) }, onClear = { vm.clear() })
}

/** Stateless History UI (rendered with sample data in the screenshot tests). */
@Composable
internal fun HistoryContent(
    items: List<HistoryItem>?,
    onBack: () -> Unit,
    onOpen: (HistoryItem) -> Unit,
    onRemove: (HistoryItem) -> Unit,
    onClear: () -> Unit,
    adSlot: @Composable (Modifier) -> Unit = { NativeAdCard(it) },
) {
    Scaffold(
        topBar = {
            NearshelfTopBar(stringResource(R.string.history_title), onBack = onBack) {
                if (!items.isNullOrEmpty()) {
                    TextButton(onClick = onClear) { Text(stringResource(R.string.history_clear), style = MaterialTheme.typography.labelLarge) }
                }
            }
        },
        containerColor = MaterialTheme.colorScheme.background,
    ) { padding ->
        val list = items ?: return@Scaffold
        if (list.isEmpty()) {
            EmptyState(R.drawable.ic_history, stringResource(R.string.history_empty_title), stringResource(R.string.history_empty_body), Modifier.padding(padding))
            return@Scaffold
        }
        LazyColumn(Modifier.fillMaxSize().padding(padding).readableWidth(), contentPadding = PaddingValues(bottom = Space.xl)) {
            itemsIndexed(list, key = { _, it -> it.key }) { index, item ->
                HistoryRow(item, onOpen = { onOpen(item) }, onRemove = { onRemove(item) })
                if (index < list.lastIndex) RowDivider()
                // Native ad in the middle of the list: after the 3rd entry (or the last, if fewer).
                if (index == minOf(2, list.lastIndex)) adSlot(Modifier.padding(horizontal = Gutter, vertical = Space.m))
            }
        }
    }
}

@Composable
fun HistoryRow(item: HistoryItem, onOpen: () -> Unit, onRemove: (() -> Unit)? = null) {
    ListRow(
        title = item.title,
        meta = listOfNotNull(
            item.author,
            DateUtils.getRelativeTimeSpanString(item.searchedAt, System.currentTimeMillis(), DateUtils.MINUTE_IN_MILLIS).toString(),
        ).joinToString(" · "),
        onClick = onOpen,
        leading = { CoverThumb(item.coverUrl) },
        titleStyle = BookTitle,
        trailing = {
            if (onRemove != null) {
                IconButton(onClick = onRemove, modifier = Modifier.padding(start = 4.dp).offset(x = 12.dp)) {
                    Icon(
                        painterResource(R.drawable.ic_x),
                        stringResource(R.string.cd_remove_history, item.title),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        modifier = Modifier.size(20.dp),
                    )
                }
            }
        },
    )
}
