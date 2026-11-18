package com.mardev.nearshelf.ui.results

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.geo.LatLng
import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.search.ResultFilter.Companion.isBorrowableNow
import com.mardev.nearshelf.core.search.ServiceState
import com.mardev.nearshelf.ui.components.accentTonalColors
import com.mardev.nearshelf.ui.components.hairline
import com.mardev.nearshelf.ui.components.lightswind.Badge
import com.mardev.nearshelf.ui.components.lightswind.BadgeSize
import com.mardev.nearshelf.ui.components.lightswind.BadgeVariant
import com.mardev.nearshelf.ui.components.lightswind.CountUp
import com.mardev.nearshelf.ui.components.quietOutlinedColors
import com.mardev.nearshelf.ui.theme.ButtonShape
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.LocalStatusColors
import com.mardev.nearshelf.ui.theme.ServiceOverline
import com.mardev.nearshelf.ui.theme.Space

/*
 * Results, organised by format. Each section: the format, its answer in one line
 * (the verdict), then every way to get it, fastest first. Rows are compact: who and
 * how on the left, the deciding number on the right, one action underneath.
 */

private val TextColumnStart = Gutter

@Composable
internal fun FormatSectionView(
    section: FormatSection,
    multiLibrary: Boolean,
    here: LatLng?,
    onBorrow: (LibraryRef, MatchedHolding) -> Unit,
    locationPrompt: (@Composable () -> Unit)?,
    modifier: Modifier = Modifier,
) {
    Column(modifier.fillMaxWidth()) {
        HorizontalDivider(Modifier.padding(horizontal = Gutter), color = MaterialTheme.colorScheme.outlineVariant)
        SectionTitle(section, here)
        locationPrompt?.invoke()
        section.options.forEachIndexed { i, o ->
            if (i > 0) OptionDivider()
            OptionRow(o, multiLibrary, here, onBorrow)
        }
        if (section.otherLanguages.isNotEmpty()) OtherLanguages(section.otherLanguages, multiLibrary, here, onBorrow, showDivider = section.options.isNotEmpty())
    }
}

@Composable
private fun OptionDivider() = HorizontalDivider(
    Modifier.padding(horizontal = Gutter),
    color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.6f),
)

/** Format icon and name, and underneath the section's answer in its status colour. */
@Composable
private fun SectionTitle(section: FormatSection, here: LatLng?) {
    Row(
        Modifier.fillMaxWidth().padding(start = Gutter, end = Gutter, top = Space.l + Space.xs, bottom = Space.xs),
        verticalAlignment = Alignment.Top,
    ) {
        Icon(painterResource(formatIcon(section.format)), null, tint = MaterialTheme.colorScheme.secondary, modifier = Modifier.padding(top = 3.dp).size(22.dp))
        Spacer(Modifier.width(Space.m))
        Column {
            Text(formatLabel(section.format), style = MaterialTheme.typography.titleLarge, modifier = Modifier.semantics { heading() })
            // The answer only earns a line when there is a choice to sum up; one option says it itself.
            if (section.options.size + section.otherLanguages.size > 1) VerdictLine(section.verdict, here, Modifier.padding(top = 2.dp))
        }
    }
}

@Composable
private fun VerdictLine(v: Verdict, here: LatLng?, modifier: Modifier = Modifier) {
    val status = LocalStatusColors.current
    val muted = MaterialTheme.colorScheme.onSurfaceVariant
    val (text, color) = when (v) {
        is Verdict.AvailableNow -> stringResource(R.string.verdict_available_now, v.via.ref.provider.displayName) to status.available
        is Verdict.OnService -> stringResource(R.string.verdict_on_service, v.service) to MaterialTheme.colorScheme.onSurface
        is Verdict.ShortestWait -> pluralStringResource(R.plurals.verdict_shortest_wait, v.days, v.days) to status.waitlist
        Verdict.Waitlist -> stringResource(R.string.verdict_waitlist) to status.waitlist
        is Verdict.OnShelf -> {
            val branch = remember(v, here) {
                summarizeBranches(v.via.holding.copies, v.via.library.homeBranch?.name, here).firstOrNull { it.onShelf > 0 }
            }
            (branch?.let { stringResource(R.string.verdict_on_shelf_at, it.name) + (it.distanceKm?.let { d -> " · " + formatDistance(d) } ?: "") }
                ?: stringResource(R.string.verdict_on_shelf)) to status.available
        }
        Verdict.AllCheckedOut -> stringResource(R.string.verdict_all_out) to muted
        Verdict.Unknown -> stringResource(R.string.verdict_unknown) to muted
    }
    Row(modifier, verticalAlignment = Alignment.Top) {
        Box(Modifier.padding(top = 7.dp).size(6.dp).clip(CircleShape).background(color))
        Spacer(Modifier.width(Space.s))
        Text(text, style = MaterialTheme.typography.bodyMedium.copy(fontWeight = androidx.compose.ui.text.font.FontWeight.Medium), color = color)
    }
}

@Composable
private fun OptionRow(o: OptionUi, multiLibrary: Boolean, here: LatLng?, onBorrow: (LibraryRef, MatchedHolding) -> Unit) {
    if (o.isPrint) PrintOption(o, multiLibrary, here, onBorrow) else DigitalOption(o, multiLibrary, onBorrow)
}

/** Who: the service (and library, when you have several). */
@Composable
private fun WhoLine(primary: String, library: String?) {
    Row(verticalAlignment = Alignment.Bottom) {
        Text(primary, style = MaterialTheme.typography.titleMedium, maxLines = 1)
        if (library != null) {
            Text(
                "  ·  $library",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun DigitalOption(o: OptionUi, multiLibrary: Boolean, onBorrow: (LibraryRef, MatchedHolding) -> Unit) {
    val h = o.holding
    val m = o.match
    val muted = MaterialTheme.colorScheme.onSurfaceVariant
    Column(Modifier.fillMaxWidth().padding(horizontal = TextColumnStart, vertical = Space.m + Space.xs)) {
        Row(verticalAlignment = Alignment.Top) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                WhoLine(o.ref.provider.displayName, o.library.name.takeIf { multiLibrary })
                // Status words only where there is no number to say it.
                val tags = buildList<@Composable () -> Unit> {
                    if (!h.availabilityKnown) add { Badge(stringResource(R.string.badge_instant_or_flex), variant = BadgeVariant.Info, size = BadgeSize.Sm) }
                    else if (!h.isAvailableNow && h.waitDays == null) add { Badge(stringResource(R.string.badge_waitlist), variant = BadgeVariant.Warning, size = BadgeSize.Sm) }
                    if (m.otherLanguage && h.language != null) add { Badge(languageName(h.language!!), variant = BadgeVariant.Outline, size = BadgeSize.Sm) }
                    h.edition?.let { add { Badge(it, variant = BadgeVariant.Info, size = BadgeSize.Sm) } }
                }
                if (tags.isNotEmpty()) {
                    FlowRow(Modifier.padding(vertical = 2.dp), horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) { tags.forEach { it() } }
                }
                if (m.otherLanguage) Text(h.title, style = MaterialTheme.typography.bodyMedium, color = muted)
                if (h.availabilityKnown) Text(detailLine(m), style = MaterialTheme.typography.bodyMedium, color = muted)
                val meta = listOfNotNull(
                    o.ref.borrowLimitPerMonth?.takeIf { !h.availabilityKnown }?.let { pluralStringResource(R.plurals.hoopla_limit_short, it, it) },
                    o.moreEditions.takeIf { it > 0 }?.let { pluralStringResource(R.plurals.more_editions, it, it) },
                    o.staleSince?.let { stringResource(R.string.results_saved_from, relativeTimeText(it)) },
                )
                meta.forEach { Text(it, style = MaterialTheme.typography.bodySmall, color = muted) }
            }
            HeadlineNumber(m)
        }
        val label = stringResource(
            when {
                !h.availabilityKnown -> R.string.action_open_in
                h.isAvailableNow -> R.string.action_borrow_in
                else -> R.string.action_hold_in
            },
            o.ref.provider.displayName,
        )
        // Borrowing now (or opening hoopla) is the strong action; a hold is a quieter one.
        OptionAction(label, strong = h.isAvailableNow || !h.availabilityKnown) { onBorrow(o.ref, m) }
    }
}

@Composable
private fun OptionAction(label: String, strong: Boolean, onClick: () -> Unit) {
    val content: @Composable () -> Unit = {
        Text(label, style = MaterialTheme.typography.labelLarge, maxLines = 1, overflow = TextOverflow.Ellipsis)
        Spacer(Modifier.width(Space.s))
        Icon(painterResource(R.drawable.ic_open_external), null, modifier = Modifier.size(16.dp))
    }
    val m = Modifier.padding(top = Space.m).heightIn(min = 40.dp)
    val pad = PaddingValues(horizontal = Space.l)
    if (strong) FilledTonalButton(onClick, m, shape = ButtonShape, colors = accentTonalColors(), contentPadding = pad) { content() }
    else OutlinedButton(onClick, m, shape = ButtonShape, border = hairline(), colors = quietOutlinedColors(), contentPadding = pad) { content() }
}

private const val BRANCHES_SHOWN = 3

/** Print: copies at this library's catalog, nearest or home branch first, the rest on request. */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun PrintOption(o: OptionUi, multiLibrary: Boolean, here: LatLng?, onBorrow: (LibraryRef, MatchedHolding) -> Unit) {
    val h = o.holding
    val m = o.match
    val muted = MaterialTheme.colorScheme.onSurfaceVariant
    val branches = remember(h.copies, o.library.homeBranch?.name, here) { summarizeBranches(h.copies, o.library.homeBranch?.name, here) }
    var expanded by rememberSaveable(o.library.id, h.providerItemId) { mutableStateOf(false) }
    val onShelfNow = h.isBorrowableNow()
    Column(Modifier.fillMaxWidth().padding(horizontal = TextColumnStart, vertical = Space.m + Space.xs)) {
        Row(verticalAlignment = Alignment.Top) {
            Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
                WhoLine(if (multiLibrary) o.library.name else stringResource(R.string.print_catalog), null)
                val tags = buildList<@Composable () -> Unit> {
                    if (!h.availabilityKnown) add { Badge(stringResource(R.string.badge_unknown), variant = BadgeVariant.Secondary, size = BadgeSize.Sm) }
                    else if (!onShelfNow) add { Badge(stringResource(R.string.badge_all_out), variant = BadgeVariant.Warning, size = BadgeSize.Sm) }
                    h.edition?.let { add { Badge(it, variant = BadgeVariant.Info, size = BadgeSize.Sm) } }
                    if (m.otherLanguage && h.language != null) add { Badge(languageName(h.language!!), variant = BadgeVariant.Outline, size = BadgeSize.Sm) }
                }
                if (tags.isNotEmpty()) {
                    FlowRow(Modifier.padding(vertical = 2.dp), horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) { tags.forEach { it() } }
                }
                val owned = h.owned ?: h.copies.size.takeUnless { h.branchLevelOnly } ?: 0
                if (owned > 0) {
                    val copies = pluralStringResource(R.plurals.copies, owned, owned)
                    Text(
                        h.holds?.takeIf { it > 0 }?.let { stringResource(R.string.detail_waitlist, pluralStringResource(R.plurals.holds, it, it), copies) } ?: copies,
                        style = MaterialTheme.typography.bodyMedium,
                        color = muted,
                    )
                }
                if (o.moreEditions > 0) Text(pluralStringResource(R.plurals.more_editions, o.moreEditions, o.moreEditions), style = MaterialTheme.typography.bodySmall, color = muted)
                o.staleSince?.let { Text(stringResource(R.string.results_saved_from, relativeTimeText(it)), style = MaterialTheme.typography.bodySmall, color = muted) }
            }
            val onShelf = branches.sumOf { it.onShelf }.takeIf { h.copies.isNotEmpty() } ?: h.available
            if (onShelf != null && h.availabilityKnown) {
                Spacer(Modifier.width(Space.m))
                Column(horizontalAlignment = Alignment.End) {
                    CountUp(onShelf, style = MaterialTheme.typography.headlineMedium.copy(fontFeatureSettings = "lnum"), color = MaterialTheme.colorScheme.primary)
                    Text(
                        stringResource(if (h.branchLevelOnly) R.string.caption_branches_on_shelf else R.string.caption_on_shelf),
                        style = MaterialTheme.typography.labelMedium,
                        color = muted,
                    )
                }
            }
        }
        if (branches.isNotEmpty()) {
            val preferred = branches.filter { it.isHome || it.onShelf > 0 }.take(BRANCHES_SHOWN).ifEmpty { branches.take(1) }
            val shown = if (expanded) branches else preferred
            Column(Modifier.padding(top = Space.s)) { shown.forEach { BranchLineFor(it, h.branchLevelOnly) } }
            if (branches.size > preferred.size) {
                TextButton(onClick = { expanded = !expanded }, modifier = Modifier.offset(x = (-12).dp)) {
                    Text(
                        if (expanded) stringResource(R.string.show_fewer_branches)
                        else pluralStringResource(R.plurals.show_all_branches, branches.size, branches.size),
                        style = MaterialTheme.typography.labelLarge,
                    )
                }
            }
        }
        OptionAction(stringResource(if (onShelfNow) R.string.action_view_catalog else R.string.action_hold_catalog), strong = false) { onBorrow(o.ref, m) }
    }
}

/** Other-language editions: one line until asked for. */
@Composable
private fun OtherLanguages(options: List<OptionUi>, multiLibrary: Boolean, here: LatLng?, onBorrow: (LibraryRef, MatchedHolding) -> Unit, showDivider: Boolean) {
    var open by rememberSaveable(options.firstOrNull()?.holding?.providerItemId) { mutableStateOf(false) }
    val names = options.mapNotNull { it.holding.language }.distinct().joinToString(", ") { languageName(it) }
    if (showDivider) OptionDivider()
    Row(
        Modifier.fillMaxWidth().heightIn(min = 48.dp).clickable(role = Role.Button) { open = !open }.padding(horizontal = Gutter),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            stringResource(R.string.other_languages, names.ifEmpty { "${options.size}" }),
            style = MaterialTheme.typography.labelLarge,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.weight(1f),
        )
        Icon(painterResource(if (open) R.drawable.ic_caret_up else R.drawable.ic_caret_down), null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(18.dp))
    }
    if (open) options.forEachIndexed { i, o ->
        if (i > 0) OptionDivider()
        OptionRow(o, multiLibrary, here, onBorrow)
    }
}

/** Everything that isn't a result: not found, still checking, failures. Last on the page. */
@Composable
internal fun NotesFooter(
    notes: List<ServiceNote>,
    multiLibrary: Boolean,
    onRetry: (String, LibraryRef) -> Unit,
    onOpenCatalog: (LibraryRef) -> Unit,
    onClearFilter: () -> Unit,
) {
    val muted = MaterialTheme.colorScheme.onSurfaceVariant
    val catalog = stringResource(R.string.print_catalog)
    // Catalog software (BiblioCommons, Polaris…) means nothing to readers; it's "the library catalog".
    fun who(n: ServiceNote) = (if (n.ref.isCatalog()) catalog else n.ref.provider.displayName) + if (multiLibrary) " · ${n.library.name}" else ""
    Column(Modifier.fillMaxWidth().padding(top = Space.l)) {
        HorizontalDivider(Modifier.padding(horizontal = Gutter), color = MaterialTheme.colorScheme.outlineVariant)
        Text(
            stringResource(R.string.notes_title).uppercase(LocalConfiguration.current.locales[0]),
            style = ServiceOverline,
            color = muted,
            modifier = Modifier.padding(start = Gutter, end = Gutter, top = Space.l, bottom = Space.xs),
        )
        val loading = notes.filter { it.reason == ServiceNote.Reason.LOADING }
        if (loading.isNotEmpty()) NoteLine(stringResource(R.string.still_checking, loading.joinToString(", ") { who(it) }), muted)
        notes.filter { it.reason == ServiceNote.Reason.NOT_FOUND }.forEach { n ->
            val text = when {
                !n.ref.isCatalog() -> stringResource(R.string.note_not_found, who(n))
                multiLibrary -> stringResource(R.string.note_no_print_at, n.library.name)
                else -> stringResource(R.string.note_no_print)
            }
            NoteLine(text, muted)
        }
        notes.filter { it.reason == ServiceNote.Reason.HIDDEN_BY_LANGUAGE }.forEach { NoteLine(stringResource(R.string.note_hidden_language, who(it)), muted) }
        if (notes.any { it.reason == ServiceNote.Reason.FILTERED_OUT }) {
            NoteLine(stringResource(R.string.note_filtered), muted) {
                TextButton(onClick = onClearFilter) { Text(stringResource(R.string.filter_clear), style = MaterialTheme.typography.labelLarge) }
            }
        }
        notes.filter { it.reason == ServiceNote.Reason.UNAVAILABLE }.forEach { n ->
            NoteLine(stringResource(R.string.results_temporarily_unavailable, who(n)), muted) {
                TextButton(onClick = { onRetry(n.library.id, n.ref) }) { Text(stringResource(R.string.action_retry), style = MaterialTheme.typography.labelLarge) }
            }
        }
        notes.filter { it.reason == ServiceNote.Reason.FAILED }.forEach { n ->
            val f = n.state as ServiceState.Failed
            if (f.kind == ProviderException.Kind.BLOCKED) {
                // The catalog answers automated requests with a bot check; Nearshelf never tries to get past one.
                NoteLine(who(n) + ": " + stringResource(R.string.results_blocked), MaterialTheme.colorScheme.onSurface) {
                    TextButton(onClick = { onOpenCatalog(n.ref) }) { Text(stringResource(R.string.action_search_catalog), style = MaterialTheme.typography.labelLarge) }
                }
            } else {
                NoteLine(
                    stringResource(if (f.kind == ProviderException.Kind.RATE_LIMITED) R.string.results_rate_limited else R.string.results_failed, who(n)),
                    MaterialTheme.colorScheme.error,
                ) {
                    TextButton(onClick = { onRetry(n.library.id, n.ref) }) { Text(stringResource(R.string.action_retry), style = MaterialTheme.typography.labelLarge) }
                }
            }
        }
    }
}

@Composable
private fun NoteLine(text: String, color: Color, action: (@Composable () -> Unit)? = null) {
    Row(
        Modifier.fillMaxWidth().heightIn(min = 40.dp).padding(start = Gutter, end = if (action != null) Gutter - 12.dp else Gutter),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(text, style = MaterialTheme.typography.bodyMedium, color = color, modifier = Modifier.weight(1f).padding(vertical = Space.xs))
        action?.invoke()
    }
}

/** No library has the book (or the filters hide everything). */
@Composable
internal fun NoneFound(filterActive: Boolean, onClear: () -> Unit) {
    Column(Modifier.fillMaxWidth().padding(horizontal = Gutter, vertical = Space.l), verticalArrangement = Arrangement.spacedBy(Space.s)) {
        HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)
        Text(
            if (filterActive) stringResource(R.string.results_filtered_out) else stringResource(R.string.results_none_title),
            style = MaterialTheme.typography.titleLarge,
            modifier = Modifier.padding(top = Space.l),
        )
        if (filterActive) {
            Button(onClick = onClear, shape = ButtonShape, modifier = Modifier.heightIn(min = 44.dp)) { Text(stringResource(R.string.filter_clear), style = MaterialTheme.typography.labelLarge) }
        } else {
            Text(stringResource(R.string.results_none_body), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}
