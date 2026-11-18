package com.mardev.nearshelf.ui.results

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ElevatedCard
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil3.compose.SubcomposeAsyncImage
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.ui.theme.LocalStatusColors
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.search.ServiceState
import com.mardev.nearshelf.ui.components.EmptyState
import com.mardev.nearshelf.ui.components.lightswind.Badge
import com.mardev.nearshelf.ui.components.lightswind.BadgeSize
import com.mardev.nearshelf.ui.components.lightswind.BadgeVariant
import com.mardev.nearshelf.ui.components.lightswind.CountUp
import com.mardev.nearshelf.ui.components.lightswind.Skeleton
import com.mardev.nearshelf.ui.components.lightswind.SkeletonLines
import com.mardev.nearshelf.ui.components.lightswind.TopLoader
import com.mardev.nearshelf.ui.components.openExternal
import com.mardev.nearshelf.ui.libraries.locationLine
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ResultsScreen(
    onBack: () -> Unit,
    onAddLibrary: () -> Unit,
    onSearchManually: (String) -> Unit,
    vm: ResultsViewModel = hiltViewModel(),
) {
    val state by vm.state.collectAsStateWithLifecycle()
    val context = LocalContext.current

    Scaffold(
        topBar = {
            Column {
                TopAppBar(
                    title = { Text(stringResource(R.string.results_title)) },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(painterResource(R.drawable.ic_arrow_left), stringResource(R.string.cd_back))
                        }
                    },
                )
                TopLoader(progress = if (state.libraries == null) 0.1f else state.progress)
            }
        },
    ) { padding ->
        if (state.phase == Phase.SHARE_NOT_UNDERSTOOD) {
            EmptyState(
                icon = R.drawable.ic_warning,
                title = stringResource(R.string.share_not_understood_title),
                body = stringResource(R.string.share_not_understood_body),
                action = stringResource(R.string.share_search_manually),
                onAction = { onSearchManually(state.sharedText.orEmpty()) },
                modifier = Modifier.padding(padding),
            )
            return@Scaffold
        }
        if (state.phase == Phase.READING_SHARE || state.phase == Phase.LOOKING_UP) {
            Column(Modifier.padding(padding).padding(16.dp)) {
                PendingHeader(state)
            }
            return@Scaffold
        }
        val libraries = state.libraries ?: return@Scaffold
        if (libraries.isEmpty()) {
            EmptyState(
                icon = R.drawable.ic_library,
                title = stringResource(R.string.home_no_libraries_title),
                body = stringResource(R.string.home_no_libraries_body),
                action = stringResource(R.string.libraries_add),
                onAction = onAddLibrary,
                modifier = Modifier.padding(padding),
            )
            return@Scaffold
        }
        LazyColumn(
            Modifier.fillMaxSize().padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            item(key = "header") { BookHeaderView(state) }
            items(libraries, key = { it.library.id }) { lr ->
                LibraryCard(
                    result = lr,
                    onBorrow = { ref, m -> context.openExternal(vm.borrowLink(ref, m)) },
                    onRetry = { ref -> vm.retry(lr.library.id, ref) },
                    onOpenCatalog = { ref -> vm.searchLink(ref)?.let(context::openExternal) },
                    modifier = Modifier.animateItem(),
                )
            }
        }
    }
}

@Composable
private fun PendingHeader(state: ResultsUiState) {
    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
        Skeleton(Modifier.size(84.dp, 126.dp).clip(RoundedCornerShape(8.dp)))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            state.query?.title?.let { Text(it, style = MaterialTheme.typography.headlineSmall) }
                ?: SkeletonLines(2, lineHeight = 22.dp)
            Text(
                stringResource(if (state.phase == Phase.READING_SHARE) R.string.phase_reading_share else R.string.phase_looking_up),
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.semantics { liveRegion = LiveRegionMode.Polite },
            )
        }
    }
}

@Composable
private fun BookHeaderView(state: ResultsUiState) {
    val header = state.header
    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
        val coverModifier = Modifier.width(84.dp).heightIn(min = 120.dp).clip(RoundedCornerShape(8.dp))
        if (header.coverUrl != null) {
            SubcomposeAsyncImage(
                model = header.coverUrl,
                contentDescription = stringResource(R.string.cd_cover, header.title),
                contentScale = ContentScale.Crop,
                loading = { Skeleton(Modifier.fillMaxSize()) },
                modifier = coverModifier.size(84.dp, 126.dp),
            )
        } else if (state.finished < state.total) {
            Skeleton(coverModifier.size(84.dp, 126.dp))
        }
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(header.title, style = MaterialTheme.typography.headlineSmall, modifier = Modifier.semantics { heading() })
            if (header.authors.isNotEmpty()) {
                Text(header.authors.joinToString(), style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            val status = if (state.finished < state.total) {
                pluralStringResource(R.plurals.results_checking, state.total, state.finished, state.total)
            } else {
                pluralStringResource(R.plurals.results_checked, state.total, state.total)
            }
            Text(
                status,
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(top = 4.dp).semantics { liveRegion = LiveRegionMode.Polite },
            )
        }
    }
}

@Composable
private fun LibraryCard(
    result: LibraryResult,
    onBorrow: (LibraryRef, MatchedHolding) -> Unit,
    onRetry: (LibraryRef) -> Unit,
    onOpenCatalog: (LibraryRef) -> Unit,
    modifier: Modifier = Modifier,
) {
    ElevatedCard(modifier.fillMaxWidth()) {
        Column(Modifier.padding(vertical = 16.dp)) {
            Row(Modifier.padding(horizontal = 16.dp), verticalAlignment = Alignment.CenterVertically) {
                Icon(painterResource(R.drawable.ic_library), null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(22.dp))
                Spacer(Modifier.width(10.dp))
                Column {
                    Text(result.library.name, style = MaterialTheme.typography.titleLarge, modifier = Modifier.semantics { heading() })
                    result.library.locationLine().takeIf { it.isNotEmpty() }?.let {
                        Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
            result.services.forEach { svc ->
                HorizontalDivider(Modifier.padding(top = 12.dp), color = MaterialTheme.colorScheme.outlineVariant)
                Text(
                    if (svc.ref.provider.kind == ProviderId.Kind.PHYSICAL) {
                        stringResource(R.string.section_physical, svc.ref.provider.displayName)
                    } else {
                        svc.ref.provider.displayName
                    },
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(start = 16.dp, end = 16.dp, top = 12.dp, bottom = 4.dp),
                )
                AnimatedContent(
                    targetState = svc.state,
                    contentKey = { it::class },
                    transitionSpec = { fadeIn(tween(220)) togetherWith fadeOut(tween(120)) },
                    label = "service",
                ) { st ->
                    when (st) {
                        ServiceState.Loading -> SkeletonLines(3, Modifier.fillMaxWidth().padding(16.dp, 8.dp))
                        is ServiceState.Failed -> FailedRow(svc.ref, st, onRetry, onOpenCatalog)
                        is ServiceState.Done -> Column {
                            if (svc.ref.provider == ProviderId.HOOPLA && st.matches.isNotEmpty()) {
                                HooplaNote(svc.ref)
                            }
                            if (st.matches.isEmpty()) {
                                Text(
                                    stringResource(R.string.results_not_found, svc.ref.provider.displayName),
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                                )
                            }
                            ServiceResult(svc.ref, st).rows.forEachIndexed { i, row ->
                                if (i > 0) HorizontalDivider(Modifier.padding(horizontal = 16.dp), color = MaterialTheme.colorScheme.outlineVariant)
                                if (row.match.holding.format == Format.PHYSICAL) {
                                    PhysicalRow(svc.ref, row, result.library.homeBranch?.name, onBorrow)
                                } else {
                                    HoldingRow(svc.ref, row, onBorrow)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun FailedRow(
    ref: LibraryRef,
    failure: ServiceState.Failed,
    onRetry: (LibraryRef) -> Unit,
    onOpenCatalog: (LibraryRef) -> Unit,
) {
    if (failure.kind == ProviderException.Kind.BLOCKED) {
        // The catalog answers automated requests with a bot check. Nearshelf never tries to
        // get past one; the user searches it in their browser instead.
        Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(stringResource(R.string.results_blocked), style = MaterialTheme.typography.bodyMedium)
            OutlinedButton(onClick = { onOpenCatalog(ref) }, modifier = Modifier.heightIn(min = 48.dp)) {
                Text(stringResource(R.string.action_search_catalog))
                Spacer(Modifier.width(8.dp))
                Icon(painterResource(R.drawable.ic_open_external), null, modifier = Modifier.size(ButtonDefaults.IconSize))
            }
        }
        return
    }
    Row(Modifier.fillMaxWidth().padding(start = 16.dp, end = 8.dp), verticalAlignment = Alignment.CenterVertically) {
        Icon(painterResource(R.drawable.ic_warning), null, tint = MaterialTheme.colorScheme.error, modifier = Modifier.size(20.dp))
        Spacer(Modifier.width(8.dp))
        Text(
            stringResource(
                if (failure.kind == ProviderException.Kind.RATE_LIMITED) R.string.results_rate_limited else R.string.results_failed,
                ref.provider.displayName,
            ),
            style = MaterialTheme.typography.bodyMedium,
            modifier = Modifier.weight(1f),
        )
        TextButton(onClick = { onRetry(ref) }) {
            Icon(painterResource(R.drawable.ic_retry), null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(6.dp))
            Text(stringResource(R.string.action_retry))
        }
    }
}

/** Hoopla can't confirm a library's copy without a login; say so once per card. */
@Composable
private fun HooplaNote(ref: LibraryRef) {
    val limit = ref.borrowLimitPerMonth
    Text(
        listOfNotNull(
            limit?.let { pluralStringResource(R.plurals.hoopla_monthly_limit, it, it) },
            stringResource(R.string.hoopla_confirm_note),
        ).joinToString(" "),
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
        modifier = Modifier.padding(horizontal = 16.dp, vertical = 2.dp),
    )
}

@Composable
private fun HoldingRow(ref: LibraryRef, row: HoldingRowUi, onBorrow: (LibraryRef, MatchedHolding) -> Unit) {
    val m = row.match
    val h = m.holding
    Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(verticalAlignment = Alignment.Top) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(painterResource(formatIcon(h.format)), null, modifier = Modifier.size(20.dp))
                        Spacer(Modifier.width(6.dp))
                        Text(formatLabel(h.format), style = MaterialTheme.typography.titleMedium)
                    }
                    if (!h.availabilityKnown) {
                        Badge(stringResource(R.string.badge_instant_or_flex), variant = BadgeVariant.Info, size = BadgeSize.Sm)
                    } else if (h.isAvailableNow) {
                        Badge(stringResource(R.string.badge_available), variant = BadgeVariant.Success, size = BadgeSize.Sm)
                    } else {
                        Badge(stringResource(R.string.badge_waitlist), variant = BadgeVariant.Warning, size = BadgeSize.Sm)
                    }
                    if (m.otherLanguage && h.language != null) {
                        Badge(languageName(h.language!!), variant = BadgeVariant.Outline, size = BadgeSize.Sm)
                    }
                }
                if (m.otherLanguage) {
                    Text(h.title, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                if (h.availabilityKnown) {
                    Text(detailLine(m), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
                if (row.moreEditions > 0) {
                    Text(
                        pluralStringResource(R.plurals.more_editions, row.moreEditions, row.moreEditions),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            Spacer(Modifier.width(12.dp))
            HeadlineNumber(m)
        }
        val label = stringResource(
            when {
                !h.availabilityKnown -> R.string.action_open_in
                h.isAvailableNow -> R.string.action_borrow_in
                else -> R.string.action_hold_in
            },
            ref.provider.displayName,
        )
        val buttonModifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)
        val content: @Composable () -> Unit = {
            Text(label)
            Spacer(Modifier.width(8.dp))
            Icon(painterResource(R.drawable.ic_open_external), null, modifier = Modifier.size(ButtonDefaults.IconSize))
        }
        if (m.otherLanguage) {
            OutlinedButton(onClick = { onBorrow(ref, m) }, modifier = buttonModifier) { content() }
        } else {
            FilledTonalButton(onClick = { onBorrow(ref, m) }, modifier = buttonModifier) { content() }
        }
    }
}

private const val MAX_WAIT_SHOWN = 365
private const val BRANCHES_COLLAPSED = 4

/** A print edition: summary, then branch by branch (home branch first). */
@Composable
private fun PhysicalRow(ref: LibraryRef, row: HoldingRowUi, homeBranchName: String?, onBorrow: (LibraryRef, MatchedHolding) -> Unit) {
    val m = row.match
    val h = m.holding
    val branches = remember(h.copies, homeBranchName) { summarizeBranches(h.copies, homeBranchName) }
    var expanded by rememberSaveable(h.providerItemId) { mutableStateOf(false) }
    val anyShelf = branches.any { it.onShelf > 0 } || (h.copies.isEmpty() && h.isAvailableNow)
    Column(Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Row(verticalAlignment = Alignment.Top) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(painterResource(R.drawable.ic_books), null, modifier = Modifier.size(20.dp))
                        Spacer(Modifier.width(6.dp))
                        Text(stringResource(R.string.format_physical), style = MaterialTheme.typography.titleMedium)
                    }
                    when {
                        !h.availabilityKnown -> Badge(stringResource(R.string.badge_unknown), variant = BadgeVariant.Secondary, size = BadgeSize.Sm)
                        anyShelf -> Badge(stringResource(R.string.badge_on_shelf), variant = BadgeVariant.Success, size = BadgeSize.Sm)
                        else -> Badge(stringResource(R.string.badge_all_out), variant = BadgeVariant.Warning, size = BadgeSize.Sm)
                    }
                    h.edition?.let { Badge(it, variant = BadgeVariant.Info, size = BadgeSize.Sm) }
                    if (m.otherLanguage && h.language != null) Badge(languageName(h.language!!), variant = BadgeVariant.Outline, size = BadgeSize.Sm)
                }
                if (m.otherLanguage) Text(h.title, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                val owned = h.owned ?: h.copies.size.takeUnless { h.branchLevelOnly } ?: 0
                if (owned > 0) {
                    val copies = pluralStringResource(R.plurals.copies, owned, owned)
                    Text(
                        h.holds?.takeIf { it > 0 }?.let { stringResource(R.string.detail_waitlist, pluralStringResource(R.plurals.holds, it, it), copies) } ?: copies,
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                if (row.moreEditions > 0) {
                    Text(pluralStringResource(R.plurals.more_editions, row.moreEditions, row.moreEditions), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            val onShelf = branches.sumOf { it.onShelf }.takeIf { h.copies.isNotEmpty() } ?: h.available
            if (onShelf != null && h.availabilityKnown) {
                Spacer(Modifier.width(12.dp))
                Column(horizontalAlignment = Alignment.End) {
                    CountUp(onShelf, style = MaterialTheme.typography.headlineMedium.copy(fontFeatureSettings = "lnum"), color = MaterialTheme.colorScheme.primary)
                    Text(
                        stringResource(if (h.branchLevelOnly) R.string.caption_branches_on_shelf else R.string.caption_on_shelf),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
        val shown = if (expanded) branches else branches.filter { it.isHome || it.onShelf > 0 }.take(BRANCHES_COLLAPSED).ifEmpty { branches.take(1) }
        shown.forEach { BranchLine(it, h.branchLevelOnly) }
        if (branches.size > shown.size) {
            TextButton(onClick = { expanded = true }) {
                Text(pluralStringResource(R.plurals.show_all_branches, branches.size, branches.size))
            }
        }
        OutlinedButton(onClick = { onBorrow(ref, m) }, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
            Text(stringResource(if (anyShelf) R.string.action_view_catalog else R.string.action_hold_catalog))
            Spacer(Modifier.width(8.dp))
            Icon(painterResource(R.drawable.ic_open_external), null, modifier = Modifier.size(ButtonDefaults.IconSize))
        }
    }
}

@Composable
private fun BranchLine(b: BranchSummary, branchLevelOnly: Boolean) {
    val status = LocalStatusColors.current
    Row(Modifier.fillMaxWidth().semantics(mergeDescendants = true) {}, verticalAlignment = Alignment.Top) {
        Icon(
            painterResource(R.drawable.ic_map_pin),
            null,
            tint = if (b.onShelf > 0) status.available else MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.padding(top = 2.dp).size(18.dp),
        )
        Spacer(Modifier.width(8.dp))
        Column(Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(b.name, style = MaterialTheme.typography.bodyLarge, modifier = Modifier.weight(1f, fill = false))
                if (b.isHome) {
                    Spacer(Modifier.width(6.dp))
                    Badge(stringResource(R.string.badge_home), variant = BadgeVariant.Outline, size = BadgeSize.Sm)
                }
            }
            Text(
                listOfNotNull(
                    if (branchLevelOnly) stringResource(if (b.onShelf > 0) R.string.branch_has_it else R.string.branch_unavailable) else branchStatus(b),
                    b.callNumber,
                ).joinToString(" · "),
                style = MaterialTheme.typography.bodySmall,
                color = if (b.onShelf > 0) status.available else MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun branchStatus(b: BranchSummary): String = when {
    b.onShelf > 0 -> pluralStringResource(R.plurals.branch_on_shelf, b.onShelf, b.onShelf)
    b.inTransit > 0 -> pluralStringResource(R.plurals.branch_in_transit, b.inTransit, b.inTransit)
    b.libraryUseOnly > 0 -> stringResource(R.string.branch_library_use)
    b.checkedOut > 0 && b.nextDue != null -> stringResource(R.string.branch_out_due, formatDate(b.nextDue))
    b.checkedOut > 0 -> pluralStringResource(R.plurals.branch_checked_out, b.checkedOut, b.checkedOut)
    else -> stringResource(R.string.branch_unavailable)
}

private fun formatDate(iso: String): String = runCatching {
    java.time.LocalDate.parse(iso).format(java.time.format.DateTimeFormatter.ofLocalizedDate(java.time.format.FormatStyle.MEDIUM))
}.getOrDefault(iso)

/** The one number that matters: copies on the shelf now, or days to wait. */
@Composable
private fun HeadlineNumber(m: MatchedHolding) {
    val h = m.holding
    if (!h.availabilityKnown) return
    val (value, caption) = when {
        h.isAvailableNow -> (h.available ?: 1) to pluralStringResource(R.plurals.caption_available, h.available ?: 1)
        h.waitDays != null -> h.waitDays!!.coerceAtMost(MAX_WAIT_SHOWN) to pluralStringResource(R.plurals.caption_days_wait, h.waitDays!!)
        else -> return
    }
    Column(horizontalAlignment = Alignment.End) {
        CountUp(
            value,
            // OverDrive's estimate can run to thousands of days when one copy has hundreds of holds.
            suffix = if (!h.isAvailableNow && (h.waitDays ?: 0) > MAX_WAIT_SHOWN) "+" else "",
            // Lining figures: Cormorant's default old-style digits drop below the baseline.
            style = MaterialTheme.typography.headlineMedium.copy(fontFeatureSettings = "lnum"),
            color = MaterialTheme.colorScheme.primary,
        )
        Text(caption, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.End)
    }
}

@Composable
private fun detailLine(m: MatchedHolding): String {
    val h = m.holding
    val owned = h.owned ?: 0
    val copies = pluralStringResource(R.plurals.copies, owned, owned)
    return when {
        h.isAvailableNow -> stringResource(R.string.detail_available, h.available ?: 0, copies)
        else -> {
            val holds = h.holds ?: 0
            stringResource(R.string.detail_waitlist, pluralStringResource(R.plurals.holds, holds, holds), copies)
        }
    }
}

private fun formatIcon(f: Format) = when (f) {
    Format.EBOOK -> R.drawable.ic_ebook
    Format.AUDIOBOOK -> R.drawable.ic_audiobook
    Format.PHYSICAL, Format.OTHER -> R.drawable.ic_books
}

@Composable
private fun formatLabel(f: Format) = stringResource(
    when (f) {
        Format.EBOOK -> R.string.format_ebook
        Format.AUDIOBOOK -> R.string.format_audiobook
        Format.PHYSICAL -> R.string.format_physical
        Format.OTHER -> R.string.format_other
    },
)

private fun languageName(code: String): String =
    Locale.forLanguageTag(code).getDisplayLanguage(Locale.getDefault()).replaceFirstChar { it.titlecase(Locale.getDefault()) }
