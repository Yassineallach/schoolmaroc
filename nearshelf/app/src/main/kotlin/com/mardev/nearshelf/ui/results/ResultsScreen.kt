package com.mardev.nearshelf.ui.results

import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.background
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
import com.mardev.nearshelf.core.metadata.WorkCandidate
import com.mardev.nearshelf.core.watch.WatchScope
import androidx.compose.foundation.verticalScroll
import com.mardev.nearshelf.ui.theme.BookTitle
import com.mardev.nearshelf.ui.components.CoverThumb
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
    val watchScope by vm.watchScope.collectAsStateWithLifecycle()
    val here by vm.here.collectAsStateWithLifecycle()
    val prefs by vm.prefs.collectAsStateWithLifecycle()
    val offline by vm.offline.collectAsStateWithLifecycle()
    val context = LocalContext.current
    var askedLocation by rememberSaveable { mutableStateOf(false) }
    val locationLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) vm.refreshLocation()
    }
    val notifyLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { }
    val onWatchSave: (WatchScope) -> Unit = { scope ->
        if (!watched && Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) notifyLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
        vm.watch(scope)
        Unit
    }

    ResultsContent(
        state = state, watched = watched, here = here, prefs = prefs, offline = offline,
        onChoose = vm::choose,
        showLocationCard = here == null && !vm.hasLocationPermission && !askedLocation,
        onBack = onBack, onPreferences = onPreferences, onAddLibrary = onAddLibrary, onSearchManually = onSearchManually,
        watchScope = watchScope,
        onWatchSave = onWatchSave,
        onUnwatch = { vm.unwatch() },
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
    onRetry: (String, LibraryRef) -> Unit,
    onBorrow: (LibraryRef, MatchedHolding) -> Unit,
    onOpenCatalog: (LibraryRef) -> Unit,
    onAllowLocation: () -> Unit,
    onDismissLocation: () -> Unit,
    adSlot: @Composable (Modifier) -> Unit = { NativeAdCard(it) },
    initialTab: Format? = null,
    onChoose: (WorkCandidate?) -> Unit = {},
    watchScope: WatchScope? = null,
    onWatchSave: (WatchScope) -> Unit = {},
    onUnwatch: () -> Unit = {},
    initialWatchDialog: Boolean = false,
) {
    var showWatch by rememberSaveable { mutableStateOf(initialWatchDialog) }
    // null until the reader taps a tab: then follow the best format as results arrive.
    var chosenTab by rememberSaveable { mutableStateOf(initialTab) }
    Scaffold(
        topBar = {
            Column {
                NearshelfTopBar(stringResource(R.string.results_title), onBack = onBack) {
                    IconButton(onClick = onPreferences) {
                        Icon(painterResource(R.drawable.ic_sliders), stringResource(R.string.cd_reading_preferences), modifier = Modifier.size(22.dp))
                    }
                }
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
        if (state.phase == Phase.CHOOSING) {
            ChooseBook(state.query?.title.orEmpty(), state.candidates, onChoose, Modifier.padding(padding))
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
        // Organised by format (one tab each), ranked fastest first; see ResultsOrganizer.
        val organized = remember(libraries, prefs) { organizeResults(libraries, prefs) }
        val multiLibrary = libraries.size > 1
        // Opens on the preferred format if a library has it, else on the one available soonest.
        val tab = chosenTab ?: organized.bestFormat(prefs) ?: prefs.preferredFormat?.takeIf { it in TAB_FORMATS } ?: Format.EBOOK
        if (showWatch) {
            WatchDialog(
                libraries = libraries.map { it.library },
                current = watchScope.takeIf { watched },
                defaultFormat = tab,
                onSave = { showWatch = false; onWatchSave(it) },
                onStop = { showWatch = false; onUnwatch() },
                onDismiss = { showWatch = false },
            )
        }
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
                    state, watched, onWatch = { showWatch = true },
                    Modifier.padding(start = Gutter, end = Gutter, top = Space.s, bottom = Space.l),
                    watchLabel = if (watched) watchingLabel(watchScope) else null,
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
            val nothingAnywhere = organized.sections.isEmpty() && organized.loading == 0
            if (nothingAnywhere && !allFailed) {
                item(key = "none") {
                    Column(Modifier.fillMaxWidth().padding(horizontal = Gutter, vertical = Space.l), verticalArrangement = Arrangement.spacedBy(Space.xs)) {
                        HorizontalDivider(Modifier.padding(bottom = Space.l), color = MaterialTheme.colorScheme.outlineVariant)
                        Text(stringResource(R.string.results_none_title), style = MaterialTheme.typography.titleLarge)
                        Text(stringResource(R.string.results_none_body), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
            if (!nothingAnywhere && !allFailed) {
                // Pinned while the options scroll.
                stickyHeader(key = "tabs") { FormatTabs(organized, tab, onSelect = { chosenTab = it }) }
                val section = organized.section(tab)
                when {
                    section != null && (section.options.isNotEmpty() || section.otherLanguages.isNotEmpty()) -> item(key = "section-$tab") {
                        FormatSectionView(
                            section = section,
                            multiLibrary = multiLibrary,
                            here = here,
                            onBorrow = onBorrow,
                            locationPrompt = if (tab == Format.PHYSICAL && showLocationCard) {
                                { LocationCard(onAllow = onAllowLocation, onDismiss = onDismissLocation, modifier = Modifier.padding(start = Gutter, end = Gutter, top = Space.s, bottom = Space.s)) }
                            } else null,
                            // One native ad, right after the first library card; never offline.
                            afterFirst = if (offline) null else { { adSlot(Modifier) } },
                        )
                    }
                    // Placeholder cards in the real cards' shape, so nothing jumps when results land.
                    organized.loading > 0 -> item(key = "pending-$tab") {
                        Column(Modifier.padding(horizontal = Gutter, vertical = Space.s), verticalArrangement = Arrangement.spacedBy(Space.l)) {
                            repeat(2) { OptionCardSkeleton() }
                        }
                    }
                    else -> item(key = "empty-$tab") { EmptyTab(tab) }
                }

            }
            if (organized.notes.isNotEmpty() && !allFailed) {
                item(key = "notes") {
                    NotesFooter(notes = organized.notes, multiLibrary = multiLibrary, onRetry = onRetry, onOpenCatalog = onOpenCatalog)
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
            ProgressStatus(
                stringResource(if (state.phase == Phase.READING_SHARE) R.string.phase_reading_share else R.string.phase_looking_up),
                progress = null,
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
    watchLabel: String? = null,
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
            // Progress lives in the words: a small ring fills as each catalog answers.
            ProgressStatus(
                if (single != null) "$status · $single" else status,
                progress = if (state.finished < state.total) state.progress else null,
                done = state.finished >= state.total,
                modifier = Modifier.padding(top = 4.dp),
            )
            val buttonLabel = watchLabel ?: stringResource(if (watched) R.string.action_watching else R.string.action_watch)
            Row(Modifier.padding(top = Space.s), horizontalArrangement = Arrangement.spacedBy(Space.s)) {
                if (watched) {
                    FilledTonalButton(shape = ButtonShape, colors = accentTonalColors(), onClick = onWatch, modifier = Modifier.heightIn(min = 44.dp)) {
                        Icon(painterResource(R.drawable.ic_watchlist_fill), null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(buttonLabel, maxLines = 1, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
                    }
                } else {
                    OutlinedButton(shape = ButtonShape, border = hairline(), colors = quietOutlinedColors(), onClick = onWatch, modifier = Modifier.heightIn(min = 44.dp)) {
                        Icon(painterResource(R.drawable.ic_watchlist), null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(buttonLabel)
                    }
                }
            }
        }
    }
}

private const val MAX_WAIT_SHOWN = 365

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

/**
 * A bare title matched several books: list them (cover, serif title, author, year and
 * editions) so the search covers only the reader's book. Last line: search them all.
 */
@Composable
private fun ChooseBook(title: String, candidates: List<WorkCandidate>, onChoose: (WorkCandidate?) -> Unit, modifier: Modifier = Modifier) {
    val colors = MaterialTheme.colorScheme
    LazyColumn(modifier.fillMaxSize().readableWidth(), contentPadding = PaddingValues(bottom = Space.xl)) {
        item(key = "intro") {
            Column(Modifier.padding(start = Gutter, end = Gutter, top = Space.s, bottom = Space.m), verticalArrangement = Arrangement.spacedBy(Space.xs)) {
                Text(stringResource(R.string.choose_title), style = MaterialTheme.typography.headlineSmall, modifier = Modifier.semantics { heading() })
                Text(stringResource(R.string.choose_body, title), style = MaterialTheme.typography.bodyMedium, color = colors.onSurfaceVariant)
            }
        }
        itemsIndexed(candidates, key = { _, c -> c.work.workKey.ifEmpty { c.work.title + c.work.authors } }) { i, c ->
            Row(
                Modifier.fillMaxWidth().clickable(role = androidx.compose.ui.semantics.Role.Button) { onChoose(c) }
                    .padding(start = Gutter, end = Gutter - Space.xs, top = Space.m, bottom = Space.m),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CoverThumb(c.work.coverUrl, title = c.work.title, width = 48.dp, height = 72.dp)
                Spacer(Modifier.width(Space.l))
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                    Text(c.work.title, style = BookTitle, maxLines = 2, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
                    Text(c.work.authors.take(2).joinToString(", "), style = MaterialTheme.typography.bodyMedium, color = colors.onSurfaceVariant, maxLines = 1, overflow = androidx.compose.ui.text.style.TextOverflow.Ellipsis)
                    Text(
                        listOfNotNull(c.firstPublished?.toString(), c.editions.takeIf { it > 0 }?.let { pluralStringResource(R.plurals.choose_editions, it, it) }).joinToString(" · "),
                        style = MaterialTheme.typography.bodySmall,
                        color = colors.onSurfaceVariant,
                    )
                }
                Icon(painterResource(R.drawable.ic_caret_right), null, tint = colors.outline, modifier = Modifier.size(18.dp))
            }
            if (i < candidates.lastIndex) HorizontalDivider(Modifier.padding(start = Gutter + 48.dp + Space.l, end = Gutter), color = colors.outlineVariant)
        }
        item(key = "any") {
            HorizontalDivider(Modifier.padding(horizontal = Gutter, vertical = Space.s), color = colors.outlineVariant)
            TextButton(onClick = { onChoose(null) }, modifier = Modifier.padding(horizontal = Gutter - 12.dp)) {
                Text(stringResource(R.string.choose_any, title), style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}

/** "Watching" for everything, else "Watching · Audiobook" or "Watching · Print at Toronto Public Library". */
@Composable
internal fun watchingLabel(scope: WatchScope?): String {
    if (scope == null || scope.isEverything) return stringResource(R.string.action_watching)
    val formats = if (scope.formats.isEmpty()) stringResource(R.string.watch_all_formats)
    else TAB_FORMATS.filter { it in scope.formats }.map { formatLabel(it) }.joinToString(", ")
    return if (scope.libraryIds.isEmpty()) stringResource(R.string.watching_scope, formats)
    else stringResource(R.string.watching_scope_at, formats, scope.libraryNames.joinToString(", "))
}

/**
 * What to watch: formats (the open tab ticked by default), and libraries when there are
 * several. Everything ticked is stored as "everything", so new libraries are covered too.
 */
@Composable
private fun WatchDialog(
    libraries: List<com.mardev.nearshelf.core.model.Library>,
    current: WatchScope?,
    defaultFormat: Format,
    onSave: (WatchScope) -> Unit,
    onStop: () -> Unit,
    onDismiss: () -> Unit,
) {
    var formats by rememberSaveable {
        mutableStateOf((current?.formats?.takeIf { it.isNotEmpty() } ?: if (current != null) TAB_FORMATS.toSet() else setOf(defaultFormat)).map { it.name })
    }
    var libs by rememberSaveable {
        mutableStateOf((current?.libraryIds?.takeIf { it.isNotEmpty() } ?: libraries.map { it.id }.toSet()).toList())
    }
    fun toggle(list: List<String>, v: String) = if (v in list) list - v else list + v
    NearshelfDialog(
        title = stringResource(R.string.watch_title),
        body = stringResource(R.string.watch_body),
        confirm = stringResource(if (current != null) R.string.watch_update else R.string.watch_save),
        confirmEnabled = formats.isNotEmpty() && libs.isNotEmpty(),
        onConfirm = {
            val f = formats.map { Format.valueOf(it) }.toSet()
            val l = libs.toSet()
            onSave(
                WatchScope(
                    formats = if (f.containsAll(TAB_FORMATS)) emptySet() else f,
                    libraryIds = if (l.containsAll(libraries.map { it.id })) emptySet() else l,
                    libraryNames = if (l.containsAll(libraries.map { it.id })) emptyList() else libraries.filter { it.id in l }.map { it.name },
                ),
            )
        },
        onDismiss = onDismiss,
        secondary = stringResource(if (current != null) R.string.watch_stop else R.string.watch_cancel),
        onSecondary = if (current != null) onStop else onDismiss,
    ) {
        Column(Modifier.verticalScroll(androidx.compose.foundation.rememberScrollState())) {
            Text(
                stringResource(R.string.watch_formats).uppercase(androidx.compose.ui.platform.LocalConfiguration.current.locales[0]),
                style = com.mardev.nearshelf.ui.theme.ServiceOverline,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(start = Space.xs, bottom = Space.xs),
            )
            TAB_FORMATS.forEach { f ->
                com.mardev.nearshelf.ui.components.ChoiceRow(formatLabel(f), checked = f.name in formats, role = androidx.compose.ui.semantics.Role.Checkbox, onClick = { formats = toggle(formats, f.name) }) {
                    androidx.compose.material3.Checkbox(checked = f.name in formats, onCheckedChange = null)
                }
            }
            if (libraries.size > 1) {
                HorizontalDivider(Modifier.padding(vertical = Space.s), color = MaterialTheme.colorScheme.outlineVariant)
                Text(
                    stringResource(R.string.watch_libraries).uppercase(androidx.compose.ui.platform.LocalConfiguration.current.locales[0]),
                    style = com.mardev.nearshelf.ui.theme.ServiceOverline,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(start = Space.xs, bottom = Space.xs),
                )
                libraries.forEach { lib ->
                    com.mardev.nearshelf.ui.components.ChoiceRow(lib.name, checked = lib.id in libs, role = androidx.compose.ui.semantics.Role.Checkbox, onClick = { libs = toggle(libs, lib.id) }) {
                        androidx.compose.material3.Checkbox(checked = lib.id in libs, onCheckedChange = null)
                    }
                }
            }
        }
    }
}

/**
 * Status text with its progress beside it: a small ring that fills as catalogs answer
 * ([progress] 0..1), spins while the amount is unknown ([progress] null and not [done]),
 * and disappears once everything has answered. Read out politely as it changes.
 */
@Composable
private fun ProgressStatus(text: String, progress: Float?, modifier: Modifier = Modifier, done: Boolean = false) {
    val colors = MaterialTheme.colorScheme
    val reduced = com.mardev.nearshelf.ui.components.lightswind.rememberReducedMotion()
    Row(modifier.semantics(mergeDescendants = true) { liveRegion = LiveRegionMode.Polite }, verticalAlignment = Alignment.CenterVertically) {
        if (!done) {
            val ring = Modifier.size(14.dp)
            if (progress != null) {
                val shown by androidx.compose.animation.core.animateFloatAsState(
                    progress.coerceIn(0f, 1f),
                    animationSpec = androidx.compose.animation.core.tween(if (reduced) 0 else 300),
                    label = "progress",
                )
                androidx.compose.material3.CircularProgressIndicator(
                    progress = { shown },
                    modifier = ring,
                    color = colors.primary,
                    trackColor = colors.outlineVariant,
                    strokeWidth = 2.dp,
                    gapSize = 0.dp,
                )
            } else if (!reduced) {
                androidx.compose.material3.CircularProgressIndicator(modifier = ring, color = colors.primary, trackColor = colors.outlineVariant, strokeWidth = 2.dp)
            }
            Spacer(Modifier.width(Space.s))
        }
        Text(text, style = MaterialTheme.typography.labelLarge, color = colors.primary)
    }
}
