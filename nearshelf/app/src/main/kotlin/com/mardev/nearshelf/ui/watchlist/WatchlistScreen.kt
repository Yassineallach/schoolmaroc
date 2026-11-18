package com.mardev.nearshelf.ui.watchlist

import com.mardev.nearshelf.ui.components.readableWidth
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
import androidx.compose.foundation.lazy.itemsIndexed
import com.mardev.nearshelf.ads.NativeAdCard
import androidx.compose.foundation.shape.RoundedCornerShape
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
import com.mardev.nearshelf.core.model.Format
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import com.mardev.nearshelf.ui.components.CoverThumb
import com.mardev.nearshelf.ui.components.NearshelfTopBar
import com.mardev.nearshelf.ui.theme.BookTitle
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space
import com.mardev.nearshelf.ui.components.EmptyState
import com.mardev.nearshelf.ui.theme.LocalStatusColors
import kotlinx.coroutines.launch

@Composable
fun WatchlistScreen(onOpen: (WatchItem) -> Unit, onSearch: () -> Unit, vm: WatchlistViewModel = hiltViewModel()) {
    val items by vm.items.collectAsStateWithLifecycle()
    val snackbar = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()
    val removedMsg = stringResource(R.string.watchlist_removed)
    val undo = stringResource(R.string.action_undo)
    val checking = stringResource(R.string.watchlist_checking)
    WatchlistContent(
        items = items,
        snackbar = snackbar,
        onOpen = onOpen,
        onSearch = onSearch,
        onCheckNow = {
            vm.checkNow()
            scope.launch { snackbar.showSnackbar(checking) }
        },
        onRemove = { item ->
            vm.remove(item)
            scope.launch {
                if (snackbar.showSnackbar(removedMsg.format(item.title), undo, duration = SnackbarDuration.Long) == SnackbarResult.ActionPerformed) {
                    vm.restore(item)
                }
            }
        },
    )
}

/** Stateless Watchlist UI (rendered with sample data in the screenshot tests). */
@Composable
internal fun WatchlistContent(
    items: List<WatchItem>?,
    snackbar: SnackbarHostState,
    onOpen: (WatchItem) -> Unit,
    onSearch: () -> Unit,
    onCheckNow: () -> Unit,
    onRemove: (WatchItem) -> Unit,
    adSlot: @Composable (Modifier) -> Unit = { NativeAdCard(it) },
) {
    Scaffold(
        topBar = {
            NearshelfTopBar(stringResource(R.string.watchlist_title), large = true) {
                if (!items.isNullOrEmpty()) {
                    TextButton(onClick = onCheckNow) { Text(stringResource(R.string.watchlist_check_now), style = MaterialTheme.typography.labelLarge) }
                }
            }
        },
        snackbarHost = { SnackbarHost(snackbar) },
        containerColor = MaterialTheme.colorScheme.background,
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
            Modifier.fillMaxSize().padding(padding).readableWidth(),
            contentPadding = PaddingValues(bottom = Space.xl),
        ) {
            item(key = "explainer") {
                Text(
                    stringResource(R.string.watchlist_explainer),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(start = Gutter, end = Gutter, bottom = Space.s),
                )
            }
            itemsIndexed(list, key = { _, it -> it.key }) { index, item ->
                Column(Modifier.animateItem()) {
                    WatchRow(item, onOpen = { onOpen(item) }, onRemove = { onRemove(item) })
                    if (index < list.lastIndex) BookDivider()
                    // Native ad in the middle of the list: after the 2nd book (or the last, if fewer).
                    if (index == minOf(1, list.lastIndex)) adSlot(Modifier.padding(horizontal = Gutter, vertical = Space.m))
                }
            }
        }
    }
}

/** Hairline under a book row, starting at the text column (after a 48 dp cover). */
@Composable
private fun BookDivider() = HorizontalDivider(
    Modifier.padding(start = Gutter + 48.dp + Space.l, end = Gutter),
    color = MaterialTheme.colorScheme.outlineVariant,
)

/** One watched book: cover, serif title, author, the latest status, when it was checked. */
@Composable
private fun WatchRow(item: WatchItem, onOpen: () -> Unit, onRemove: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clickable(onClickLabel = stringResource(R.string.cd_open_results), role = Role.Button, onClick = onOpen)
            .padding(start = Gutter, end = Gutter - Space.m, top = Space.l, bottom = Space.l),
        verticalAlignment = Alignment.Top,
    ) {
        CoverThumb(item.coverUrl, title = item.title, width = 48.dp, height = 72.dp)
        Spacer(Modifier.width(Space.l))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(item.title, style = BookTitle, color = MaterialTheme.colorScheme.onSurface, maxLines = 3, overflow = TextOverflow.Ellipsis)
            item.author?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis) }
            // What this watch covers, when it isn't everything.
            if (!item.scope.isEverything) {
                val formats = if (item.scope.formats.isEmpty()) stringResource(R.string.watch_all_formats)
                else listOf(Format.EBOOK, Format.AUDIOBOOK, Format.PHYSICAL).filter { it in item.scope.formats }.map { formatName(it) }.joinToString(", ")
                Text(
                    if (item.scope.libraryIds.isEmpty()) stringResource(R.string.watchlist_scope, formats)
                    else stringResource(R.string.watchlist_scope_at, formats, item.scope.libraryNames.joinToString(", ")),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.primary,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                )
            }
            StatusLine(Watch.status(item.snapshot), Modifier.padding(top = Space.xs))
            Text(
                item.lastCheckedAt?.let {
                    stringResource(R.string.watchlist_checked, DateUtils.getRelativeTimeSpanString(it, System.currentTimeMillis(), DateUtils.MINUTE_IN_MILLIS).toString())
                } ?: stringResource(R.string.watchlist_not_checked),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        IconButton(onClick = onRemove) {
            Icon(
                painterResource(R.drawable.ic_trash),
                stringResource(R.string.cd_remove_watch, item.title),
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.size(20.dp),
            )
        }
    }
}

/** Status in its colour with a small leading dot, so it reads without relying on colour alone. */
@Composable
private fun StatusLine(status: Watch.Status?, modifier: Modifier = Modifier) {
    val colors = LocalStatusColors.current
    val (text, color) = when (status) {
        is Watch.Status.Available -> stringResource(R.string.watch_status_available, status.service, status.library) to colors.available
        is Watch.Status.OnShelf -> stringResource(R.string.watch_status_on_shelf, status.branch) to colors.available
        is Watch.Status.Waiting -> pluralStringResource(R.plurals.watch_status_waiting, status.days, status.days, status.library) to MaterialTheme.colorScheme.onSurface
        Watch.Status.NotYet -> stringResource(R.string.watch_status_not_yet) to MaterialTheme.colorScheme.onSurfaceVariant
        null -> return
    }
    Row(modifier, verticalAlignment = Alignment.Top) {
        Box(Modifier.padding(top = 7.dp).size(6.dp).clip(CircleShape).background(color))
        Spacer(Modifier.width(Space.s))
        Text(text, style = MaterialTheme.typography.bodyMedium.copy(fontWeight = FontWeight.Medium), color = color)
    }
}

@Composable
private fun formatName(f: Format) = stringResource(
    when (f) {
        Format.EBOOK -> R.string.format_ebook
        Format.AUDIOBOOK -> R.string.format_audiobook
        else -> R.string.format_physical
    },
)
