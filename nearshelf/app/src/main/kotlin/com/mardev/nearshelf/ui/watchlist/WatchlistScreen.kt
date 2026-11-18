package com.mardev.nearshelf.ui.watchlist

import android.text.format.DateUtils
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.AsyncImage
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.watch.Watch
import com.mardev.nearshelf.data.WatchItem
import com.mardev.nearshelf.ui.components.EmptyState
import com.mardev.nearshelf.ui.theme.LocalStatusColors
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WatchlistScreen(onOpen: (WatchItem) -> Unit, onSearch: () -> Unit, vm: WatchlistViewModel = hiltViewModel()) {
    val items by vm.items.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val removedMsg = stringResource(R.string.watchlist_removed)
    val undo = stringResource(R.string.action_undo)
    val checking = stringResource(R.string.watchlist_checking)

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.watchlist_title)) },
                actions = {
                    if (!items.isNullOrEmpty()) {
                        TextButton(onClick = {
                            vm.checkNow()
                            scope.launch { snackbar.showSnackbar(checking) }
                        }) { Text(stringResource(R.string.watchlist_check_now)) }
                    }
                },
            )
        },
        snackbarHost = { SnackbarHost(snackbar) },
    ) { padding ->
        val list = items ?: return@Scaffold
        if (list.isEmpty()) {
            EmptyState(
                icon = R.drawable.ic_watchlist,
                title = stringResource(R.string.watchlist_empty_title),
                body = stringResource(R.string.watchlist_empty_body),
                action = stringResource(R.string.nav_search),
                onAction = onSearch,
                modifier = Modifier.padding(padding),
            )
            return@Scaffold
        }
        LazyColumn(
            Modifier.fillMaxSize().padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            item {
                Text(
                    stringResource(R.string.watchlist_explainer),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            items(list, key = { it.key }) { item ->
                WatchRow(item, onOpen = { onOpen(item) }, onRemove = {
                    vm.remove(item)
                    scope.launch {
                        if (snackbar.showSnackbar(removedMsg.format(item.title), undo, duration = SnackbarDuration.Long) == SnackbarResult.ActionPerformed) {
                            vm.restore(item)
                        }
                    }
                }, modifier = Modifier.animateItem())
            }
        }
    }
}

@Composable
private fun WatchRow(item: WatchItem, onOpen: () -> Unit, onRemove: () -> Unit, modifier: Modifier = Modifier) {
    ElevatedCard(modifier.fillMaxWidth().clickable(onClickLabel = stringResource(R.string.cd_open_results), onClick = onOpen)) {
        Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            if (item.coverUrl != null) {
                AsyncImage(
                    model = item.coverUrl,
                    contentDescription = null,
                    contentScale = ContentScale.Crop,
                    modifier = Modifier.size(48.dp, 72.dp).clip(RoundedCornerShape(6.dp)),
                )
            } else {
                Icon(painterResource(R.drawable.ic_books), null, modifier = Modifier.size(48.dp))
            }
            Spacer(Modifier.width(12.dp))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(item.title, style = MaterialTheme.typography.titleLarge)
                item.author?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant) }
                StatusLine(Watch.status(item.snapshot))
                Text(
                    item.lastCheckedAt?.let {
                        stringResource(R.string.watchlist_checked, DateUtils.getRelativeTimeSpanString(it, System.currentTimeMillis(), DateUtils.MINUTE_IN_MILLIS).toString())
                    } ?: stringResource(R.string.watchlist_not_checked),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            IconButton(onClick = onRemove) {
                Icon(painterResource(R.drawable.ic_trash), stringResource(R.string.cd_remove_watch, item.title))
            }
        }
    }
}

@Composable
private fun StatusLine(status: Watch.Status?) {
    val colors = LocalStatusColors.current
    val (text, color) = when (status) {
        is Watch.Status.Available -> stringResource(R.string.watch_status_available, status.service, status.library) to colors.available
        is Watch.Status.OnShelf -> stringResource(R.string.watch_status_on_shelf, status.branch) to colors.available
        is Watch.Status.Waiting -> pluralStringResource(R.plurals.watch_status_waiting, status.days, status.days, status.library) to MaterialTheme.colorScheme.onSurface
        Watch.Status.NotYet -> stringResource(R.string.watch_status_not_yet) to MaterialTheme.colorScheme.onSurfaceVariant
        null -> return
    }
    Text(text, style = MaterialTheme.typography.bodyMedium, color = color)
}
