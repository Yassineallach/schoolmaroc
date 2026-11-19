@file:OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)

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
import androidx.compose.foundation.layout.FlowRow
import com.mardev.nearshelf.ui.components.nearshelfCard
import com.mardev.nearshelf.ui.components.StatusPill
import androidx.compose.foundation.layout.offset
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
                Column(Modifier.animateItem().padding(horizontal = Gutter, vertical = Space.s)) {
                    WatchCard(item, onOpen = { onOpen(item) }, onRemove = { onRemove(item) })
                    // Native ad in the middle of the list: after the 2nd book (or the last, if fewer).
                    if (index == minOf(1, list.lastIndex)) adSlot(Modifier.padding(top = Space.l))
                }
            }
        }
    }
}

/**
 * One watched book as a card: cover, serif title, author, what is watched; then the latest
 * status as a label with its detail, and when it was checked. Tapping opens the results.
 */
@Composable
private fun WatchCard(item: WatchItem, onOpen: () -> Unit, onRemove: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    val status = LocalStatusColors.current
    Column(
        Modifier
            .fillMaxWidth()
            .nearshelfCard()
            .clickable(onClickLabel = stringResource(R.string.cd_open_results), role = Role.Button, onClick = onOpen)
            .padding(Space.l),
    ) {
        Row(verticalAlignment = Alignment.Top) {
            CoverThumb(item.coverUrl, title = item.title, width = 56.dp, height = 84.dp, elevated = true)
            Spacer(Modifier.width(Space.l))
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(item.title, style = BookTitle, color = colors.onSurface, maxLines = 3, overflow = TextOverflow.Ellipsis)
                item.author?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = colors.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis) }
                // What this watch covers, when it isn't everything.
                if (!item.scope.isEverything) {
                    val formats = if (item.scope.formats.isEmpty()) stringResource(R.string.watch_all_formats)
                    else listOf(Format.EBOOK, Format.AUDIOBOOK, Format.PHYSICAL).filter { it in item.scope.formats }.map { formatName(it) }.joinToString(", ")
                    Text(
                        if (item.scope.libraryIds.isEmpty()) stringResource(R.string.watchlist_scope, formats)
                        else stringResource(R.string.watchlist_scope_at, formats, item.scope.libraryNames.joinToString(", ")),
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.primary,
                        maxLines = 3,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.padding(top = Space.xs),
                    )
                }
            }
            IconButton(onClick = onRemove, modifier = Modifier.offset(x = 12.dp, y = (-12).dp)) {
                Icon(painterResource(R.drawable.ic_trash), stringResource(R.string.cd_remove_watch, item.title), tint = colors.onSurfaceVariant, modifier = Modifier.size(20.dp))
            }
        }
        HorizontalDivider(Modifier.padding(top = Space.l), color = colors.outlineVariant)
        val s = Watch.status(item.snapshot)
        // Label and detail flow: the detail drops under the label rather than being cut short.
        FlowRow(
            Modifier.padding(top = Space.m),
            horizontalArrangement = Arrangement.spacedBy(Space.s),
            verticalArrangement = Arrangement.spacedBy(Space.xs),
            itemVerticalAlignment = Alignment.CenterVertically,
        ) {
            when (s) {
                is Watch.Status.Available -> StatusPill(stringResource(R.string.badge_available), status.availableContainer, status.onAvailableContainer)
                is Watch.Status.OnShelf -> StatusPill(stringResource(R.string.badge_on_shelf), status.availableContainer, status.onAvailableContainer)
                is Watch.Status.Waiting -> StatusPill(stringResource(R.string.badge_waitlist), status.waitlistContainer, status.onWaitlistContainer)
                Watch.Status.NotYet -> StatusPill(stringResource(R.string.watch_pill_not_yet), colors.surfaceContainer, colors.onSurfaceVariant)
                null -> StatusPill(stringResource(R.string.watch_pill_unchecked), colors.surfaceContainer, colors.onSurfaceVariant)
            }
            val detail = when (s) {
                is Watch.Status.Available -> stringResource(R.string.watch_detail_service, s.service, s.library)
                is Watch.Status.OnShelf -> stringResource(R.string.watch_detail_service, s.branch, s.library)
                is Watch.Status.Waiting -> pluralStringResource(R.plurals.watch_detail_wait, s.days, s.days, s.library)
                else -> null
            }
            if (detail != null) Text(detail, style = MaterialTheme.typography.bodyMedium, color = colors.onSurface)
        }
        // Never checked: the label already says so.
        item.lastCheckedAt?.let {
            Text(
                stringResource(R.string.watchlist_checked, DateUtils.getRelativeTimeSpanString(it, System.currentTimeMillis(), DateUtils.MINUTE_IN_MILLIS).toString()),
                style = MaterialTheme.typography.bodySmall,
                color = colors.onSurfaceVariant,
                modifier = Modifier.padding(top = Space.s),
            )
        }
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
