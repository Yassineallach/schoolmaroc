package com.mardev.nearshelf.ui.results

import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.background
import com.mardev.nearshelf.core.search.ResultFilter
import com.mardev.nearshelf.ui.components.NearshelfDialog
import com.mardev.nearshelf.ui.components.ChoiceRow
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.ui.semantics.Role
import com.mardev.nearshelf.ui.components.Monogram
import androidx.compose.foundation.layout.offset
import com.mardev.nearshelf.ui.components.NearshelfTopBar
import com.mardev.nearshelf.ui.components.accentTonalColors
import com.mardev.nearshelf.ui.components.hairline
import com.mardev.nearshelf.ui.components.quietOutlinedColors
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.ServiceOverline
import com.mardev.nearshelf.ui.theme.Space
import com.mardev.nearshelf.ui.theme.ButtonShape
import com.mardev.nearshelf.ui.components.readableWidth
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
import androidx.compose.foundation.lazy.itemsIndexed
import com.mardev.nearshelf.ads.NativeAdCard
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ButtonDefaults
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
import com.mardev.nearshelf.core.geo.LatLng
import com.mardev.nearshelf.core.prefs.ReadingPrefs
import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.core.content.ContextCompat
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
    onPreferences: () -> Unit,
    vm: ResultsViewModel = hiltViewModel(),
) {
    val state by vm.state.collectAsStateWithLifecycle()
    val watched by vm.watched.collectAsStateWithLifecycle()
    val here by vm.here.collectAsStateWithLifecycle()
    val prefs by vm.prefs.collectAsStateWithLifecycle()
    val filter by vm.filter.collectAsStateWithLifecycle()
    val offline by vm.offline.collectAsStateWithLifecycle()
    val context = LocalContext.current
    var askedLocation by rememberSaveable { mutableStateOf(false) }
    val locationLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) vm.refreshLocation()
    }
    val notifyLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { }
    val onWatch: () -> Unit = {
        if (!watched && Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) notifyLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        vm.toggleWatch()
        Unit
    }

    ResultsContent(
        state = state, watched = watched, here = here, prefs = prefs, offline = offline,
        filter = filter, onFilterChange = vm::setFilter,
        showLocationCard = here == null && !vm.hasLocationPermission && !askedLocation,
        onBack = onBack, onPreferences = onPreferences, onAddLibrary = onAddLibrary, onSearchManually = onSearchManually,
        onWatch = onWatch,
        onRetry = { id, ref -> vm.retry(id, ref) },
        onBorrow = { ref, m -> context.openExternal(vm.borrowLink(ref, m)) },
        onOpenCatalog = { ref -> vm.searchLink(ref)?.let(context::openExternal) },
        onAllowLocation = {
            askedLocation = true
            locationLauncher.launch(Manifest.permission.ACCESS_COARSE_LOCATION)
        },
        onDismissLocation = { askedLocation = true },
    )
}

/** Stateless Results UI, so it can be rendered with sample data in screenshot tests. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
internal fun ResultsContent(
    state: ResultsUiState,
    watched: Boolean,
    here: LatLng?,
    prefs: ReadingPrefs,
    offline: Boolean,
    showLocationCard: Boolean,
    onBack: () -> Unit,
    onPreferences: () -> Unit,
    onAddLibrary: () -> Unit,
    onSearchManually: (String) -> Unit,
    onWatch: () -> Unit,
    onRetry: (String, LibraryRef) -> Unit,
    onBorrow: (LibraryRef, MatchedHolding) -> Unit,
    onOpenCatalog: (LibraryRef) -> Unit,
    onAllowLocation: () -> Unit,
    onDismissLocation: () -> Unit,
    adSlot: @Composable (Modifier) -> Unit = { NativeAdCard(it) },
    filter: ResultFilter = ResultFilter(),
    onFilterChange: (ResultFilter) -> Unit = {},
    initialFilterDialog: Boolean = false,
) {
    var showFilter by rememberSaveable { mutableStateOf(initialFilterDialog) }
    Scaffold(
        topBar = {
            Column {
                NearshelfTopBar(stringResource(R.string.results_title), onBack = onBack) {
                    IconButton(onClick = onPreferences) {
                        Icon(painterResource(R.drawable.ic_sliders), stringResource(R.string.cd_reading_preferences), modifier = Modifier.size(22.dp))
                    }
                }
                TopLoader(progress = if (state.libraries == null) 0.1f else state.progress)
            }
        },
        containerColor = MaterialTheme.colorScheme.background,
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
            Column(Modifier.padding(padding).padding(horizontal = Gutter, vertical = Space.s)) {
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
        // Formats actually found, in the order results list them.
        val foundFormats = libraries.flatMap { lr -> lr.services.flatMap { (it.state as? ServiceState.Done)?.matches.orEmpty() } }
            .map { with(ResultFilter) { it.holding.format.filterKey() } }.distinct()
            .sortedBy { listOf(Format.EBOOK, Format.AUDIOBOOK, Format.PHYSICAL).indexOf(it) }
        if (showFilter) FilterDialog(filter, foundFormats, onFilterChange, onDismiss = { showFilter = false })
        LazyColumn(
            Modifier.fillMaxSize().padding(padding).readableWidth(),
            contentPadding = PaddingValues(bottom = Space.xl),
        ) {
            if (offline) {
                item(key = "offline") {
                    Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(start = Gutter, end = Gutter, bottom = Space.s).semantics { liveRegion = LiveRegionMode.Polite }) {
                        Icon(painterResource(R.drawable.ic_offline), null, tint = MaterialTheme.colorScheme.tertiary, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(stringResource(R.string.results_offline), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.tertiary)
                    }
                }
            }
            item(key = "header") {
                BookHeaderView(
                    state, watched, onWatch,
                    Modifier.padding(start = Gutter, end = Gutter, top = Space.s, bottom = Space.xl),
                    // The Filter button appears once there is something to filter.
                    filterCount = if (foundFormats.isEmpty()) null else filter.formats.size + (if (filter.availableNow) 1 else 0),
                    onFilter = { showFilter = true },
                )
            }
            val services = libraries.flatMap { lr -> lr.services.map { lr.library.id to it } }
            val allFailed = services.isNotEmpty() && state.finished == state.total && services.none { it.second.state is ServiceState.Done }
            if (allFailed) {
                item(key = "allFailed") {
                    androidx.compose.material3.Surface(
                        color = MaterialTheme.colorScheme.errorContainer,
                        shape = MaterialTheme.shapes.medium,
                        modifier = Modifier.padding(start = Gutter, end = Gutter, bottom = Space.l),
                    ) {
                        Column(Modifier.padding(Space.l), verticalArrangement = Arrangement.spacedBy(Space.s)) {
                            Text(stringResource(R.string.results_all_failed_title), style = MaterialTheme.typography.titleMedium, color = MaterialTheme.colorScheme.onErrorContainer)
                            Text(
                                stringResource(if (offline) R.string.results_all_failed_offline else R.string.results_all_failed_body),
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onErrorContainer,
                            )
                            androidx.compose.material3.Button(shape = ButtonShape, onClick = { services.forEach { (id, svc) -> onRetry(id, svc.ref) } }) {
                                Text(stringResource(R.string.action_retry_all))
                            }
                        }
                    }
                }
            }
            // Organised by format, ranked fastest first; see ResultsOrganizer.
            val organized = organizeResults(libraries, prefs, filter)
            val multiLibrary = libraries.size > 1
            if (organized.sections.isEmpty() && organized.loading > 0) {
                item(key = "pending") { SkeletonLines(4, Modifier.fillMaxWidth().padding(Gutter, Space.l)) }
            }
            if (organized.sections.isEmpty() && organized.loading == 0 && !allFailed) {
                item(key = "none") {
                    NoneFound(filterActive = organized.filteredOut, onClear = { onFilterChange(ResultFilter()) })
                }
            }
            organized.sections.forEachIndexed { si, section ->
                item(key = "section-${section.format}") {
                    FormatSectionView(
                        section = section,
                        multiLibrary = multiLibrary,
                        here = here,
                        onBorrow = onBorrow,
                        locationPrompt = if (section.format == Format.PHYSICAL && showLocationCard) {
                            { LocationCard(onAllow = onAllowLocation, onDismiss = onDismissLocation, modifier = Modifier.padding(start = Gutter, end = Gutter, bottom = Space.m)) }
                        } else null,
                        modifier = Modifier.animateItem(),
                    )
                }
                // One native ad, in the middle of the content: after the first format, never offline.
                if (si == 0 && !offline) item(key = "ad") { adSlot(Modifier.padding(horizontal = Gutter, vertical = Space.l)) }
            }
            if (organized.notes.isNotEmpty() && !allFailed) {
                item(key = "notes") {
                    NotesFooter(
                        notes = organized.notes,
                        multiLibrary = multiLibrary,
                        onRetry = onRetry,
                        onOpenCatalog = onOpenCatalog,
                        onClearFilter = { onFilterChange(ResultFilter()) },
                    )
                }
            }
        }
    }
}

@Composable
private fun PendingHeader(state: ResultsUiState) {
    Row(horizontalArrangement = Arrangement.spacedBy(Space.l)) {
        Skeleton(Modifier.size(84.dp, 126.dp).clip(MaterialTheme.shapes.extraSmall))
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
private fun BookHeaderView(
    state: ResultsUiState,
    watched: Boolean,
    onWatch: () -> Unit,
    modifier: Modifier = Modifier,
    filterCount: Int? = null,
    onFilter: () -> Unit = {},
) {
    val header = state.header
    Row(modifier, horizontalArrangement = Arrangement.spacedBy(Space.l)) {
        val coverModifier = Modifier.width(84.dp).heightIn(min = 120.dp).clip(MaterialTheme.shapes.extraSmall)
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
            // With one library, name it once here rather than on every row.
            val single = state.libraries?.singleOrNull()?.library?.name
            Text(
                if (single != null) "$status · $single" else status,
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.padding(top = 4.dp).semantics { liveRegion = LiveRegionMode.Polite },
            )
            val watchLabel = stringResource(if (watched) R.string.action_watching else R.string.action_watch)
            Row(Modifier.padding(top = Space.s), horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                if (watched) {
                    FilledTonalButton(shape = ButtonShape, colors = accentTonalColors(), onClick = onWatch, modifier = Modifier.heightIn(min = 44.dp)) {
                        Icon(painterResource(R.drawable.ic_watchlist_fill), null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(watchLabel)
                    }
                } else {
                    OutlinedButton(shape = ButtonShape, border = hairline(), colors = quietOutlinedColors(), onClick = onWatch, modifier = Modifier.heightIn(min = 44.dp)) {
                        Icon(painterResource(R.drawable.ic_watchlist), null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(watchLabel)
                    }
                }
                // Filter: quiet when off; tinted with a count when any filter is on.
                if (filterCount != null) {
                    val label = if (filterCount > 0) stringResource(R.string.filter_button_count, filterCount) else stringResource(R.string.filter_button)
                    if (filterCount > 0) {
                        FilledTonalButton(shape = ButtonShape, colors = accentTonalColors(), onClick = onFilter, modifier = Modifier.heightIn(min = 44.dp)) {
                            Icon(painterResource(R.drawable.ic_filter), null, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text(label)
                        }
                    } else {
                        OutlinedButton(shape = ButtonShape, border = hairline(), colors = quietOutlinedColors(), onClick = onFilter, modifier = Modifier.heightIn(min = 44.dp)) {
                            Icon(painterResource(R.drawable.ic_filter), null, modifier = Modifier.size(18.dp))
                            Spacer(Modifier.width(8.dp))
                            Text(label)
                        }
                    }
                }
            }
        }
    }
}

/** Filter pop-up: availability, then the formats found. Changes apply as you tap. */
@Composable
private fun FilterDialog(filter: ResultFilter, formats: List<Format>, onChange: (ResultFilter) -> Unit, onDismiss: () -> Unit) {
    NearshelfDialog(
        title = stringResource(R.string.filter_label),
        confirm = stringResource(R.string.action_done),
        onDismiss = onDismiss,
        secondary = if (filter.isActive) stringResource(R.string.filter_clear) else null,
        onSecondary = { onChange(ResultFilter()) },
    ) {
        Column {
            ChoiceRow(
                stringResource(R.string.filter_available_now),
                checked = filter.availableNow,
                role = Role.Checkbox,
                onClick = { onChange(filter.copy(availableNow = !filter.availableNow)) },
                supporting = stringResource(R.string.filter_available_now_sub),
            ) { Checkbox(checked = filter.availableNow, onCheckedChange = null, colors = CheckboxDefaults.colors(checkedColor = MaterialTheme.colorScheme.primary)) }
            if (formats.size > 1) {
                HorizontalDivider(Modifier.padding(vertical = Space.s), color = MaterialTheme.colorScheme.outlineVariant)
                Text(
                    stringResource(R.string.filter_formats).uppercase(androidx.compose.ui.platform.LocalConfiguration.current.locales[0]),
                    style = ServiceOverline,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(start = Space.xs, bottom = Space.xs),
                )
                formats.forEach { f ->
                    ChoiceRow(formatLabel(f), checked = f in filter.formats, role = Role.Checkbox, onClick = { onChange(filter.toggle(f)) }) {
                        Checkbox(checked = f in filter.formats, onCheckedChange = null, colors = CheckboxDefaults.colors(checkedColor = MaterialTheme.colorScheme.primary))
                    }
                }
            }
        }
    }
}

private const val MAX_WAIT_SHOWN = 365

@Composable
internal fun BranchLineFor(b: BranchSummary, branchLevelOnly: Boolean) {
    val status = LocalStatusColors.current
    val context = LocalContext.current
    val mapLabel = stringResource(R.string.cd_open_map, b.name)
    val rowModifier = b.location?.let { loc ->
        Modifier.clickable(onClickLabel = mapLabel, role = androidx.compose.ui.semantics.Role.Button) {
            // geo: URI opens the user's maps app at the branch; nothing is sent by Nearshelf.
            context.openExternal("geo:${loc.latitude},${loc.longitude}?q=${loc.latitude},${loc.longitude}(${Uri.encode(b.name)})")
        }
    } ?: Modifier
    Row(Modifier.fillMaxWidth().then(rowModifier).heightIn(min = 48.dp).semantics(mergeDescendants = true) {}, verticalAlignment = Alignment.Top) {
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
                b.distanceKm?.let {
                    Spacer(Modifier.width(8.dp))
                    Text(formatDistance(it), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
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
internal fun branchStatus(b: BranchSummary): String = when {
    b.onShelf > 0 -> pluralStringResource(R.plurals.branch_on_shelf, b.onShelf, b.onShelf)
    b.inTransit > 0 -> pluralStringResource(R.plurals.branch_in_transit, b.inTransit, b.inTransit)
    b.libraryUseOnly > 0 -> stringResource(R.string.branch_library_use)
    b.checkedOut > 0 && b.nextDue != null -> stringResource(R.string.branch_out_due, formatDate(b.nextDue))
    b.checkedOut > 0 -> pluralStringResource(R.plurals.branch_checked_out, b.checkedOut, b.checkedOut)
    else -> stringResource(R.string.branch_unavailable)
}

/** Miles where people use them (US, UK, Liberia, Myanmar), kilometres elsewhere. */
@Composable
internal fun formatDistance(km: Double): String {
    val locale = androidx.compose.ui.platform.LocalConfiguration.current.locales[0]
    return if (locale.country in setOf("US", "GB", "LR", "MM")) {
        val mi = km * 0.621371
        stringResource(R.string.distance_mi, if (mi < 10) String.format(locale, "%.1f", mi) else mi.toInt().toString())
    } else {
        stringResource(R.string.distance_km, if (km < 10) String.format(locale, "%.1f", km) else km.toInt().toString())
    }
}

@Composable
internal fun relativeTimeText(epochMillis: Long): String =
    android.text.format.DateUtils.getRelativeTimeSpanString(epochMillis, System.currentTimeMillis(), android.text.format.DateUtils.MINUTE_IN_MILLIS).toString()

@Composable
internal fun LocationCard(onAllow: () -> Unit, onDismiss: () -> Unit, modifier: Modifier = Modifier) {
    androidx.compose.material3.Surface(color = MaterialTheme.colorScheme.surfaceContainer, shape = MaterialTheme.shapes.medium, modifier = modifier) {
        Column(Modifier.padding(Space.l), verticalArrangement = Arrangement.spacedBy(Space.s)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(painterResource(R.drawable.ic_map_pin), null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(20.dp))
                Spacer(Modifier.width(8.dp))
                Text(stringResource(R.string.location_card_title), style = MaterialTheme.typography.titleMedium)
            }
            Text(stringResource(R.string.location_card_body), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                androidx.compose.material3.Button(shape = ButtonShape, onClick = onAllow) { Text(stringResource(R.string.location_card_allow)) }
                TextButton(onClick = onDismiss) { Text(stringResource(R.string.action_not_now)) }
            }
        }
    }
}

private fun formatDate(iso: String): String = runCatching {
    java.time.LocalDate.parse(iso).format(java.time.format.DateTimeFormatter.ofLocalizedDate(java.time.format.FormatStyle.MEDIUM))
}.getOrDefault(iso)

/** The one number that matters: copies on the shelf now, or days to wait. */
@Composable
internal fun HeadlineNumber(m: MatchedHolding) {
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
            // Lining figures, so numbers sit on the baseline whatever the font's default.
            style = MaterialTheme.typography.headlineMedium.copy(fontFeatureSettings = "lnum"),
            color = MaterialTheme.colorScheme.primary,
        )
        Text(caption, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, textAlign = TextAlign.End)
    }
}

@Composable
internal fun detailLine(m: MatchedHolding): String {
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

internal fun formatIcon(f: Format) = when (f) {
    Format.EBOOK -> R.drawable.ic_ebook
    Format.AUDIOBOOK -> R.drawable.ic_audiobook
    Format.PHYSICAL, Format.OTHER -> R.drawable.ic_books
}

@Composable
internal fun formatLabel(f: Format) = stringResource(
    when (f) {
        Format.EBOOK -> R.string.format_ebook
        Format.AUDIOBOOK -> R.string.format_audiobook
        Format.PHYSICAL -> R.string.format_physical
        Format.OTHER -> R.string.format_other
    },
)

internal fun languageName(code: String): String =
    Locale.forLanguageTag(code).getDisplayLanguage(Locale.getDefault()).replaceFirstChar { it.titlecase(Locale.getDefault()) }
