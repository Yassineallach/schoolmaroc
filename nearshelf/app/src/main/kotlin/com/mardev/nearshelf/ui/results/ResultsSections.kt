package com.mardev.nearshelf.ui.results

import androidx.compose.foundation.border
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.height
import androidx.compose.material3.IconButton
import androidx.compose.ui.graphics.luminance
import com.mardev.nearshelf.ui.components.openExternal
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
import androidx.compose.foundation.text.BasicText
import androidx.compose.foundation.text.TextAutoSize
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
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
import com.mardev.nearshelf.core.search.Availability.isBorrowableNow
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
    Column(modifier.fillMaxWidth().padding(top = Space.s)) {
        // The tab names the format; above the options goes only its answer, when there's a choice to sum up.
        if (section.options.size + section.otherLanguages.size > 1) {
            VerdictLine(section.verdict, here, Modifier.padding(start = Gutter, end = Gutter, top = Space.m, bottom = Space.xs))
        }
        locationPrompt?.invoke()
        if (section.format == Format.PHYSICAL) {
            // Print: one card per library edition, with its branches attached underneath.
            Column(Modifier.padding(horizontal = Gutter, vertical = Space.s), verticalArrangement = Arrangement.spacedBy(Space.l)) {
                section.options.forEach { PrintCard(it, multiLibrary, section.options.size > 1, here, onBorrow) }
            }
        } else section.options.forEachIndexed { i, o ->
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
            (branch?.let { stringResource(R.string.verdict_on_shelf_at, it.name) + (it.distanceKm?.takeIf { d -> d <= NEARBY_KM }?.let { d -> " · " + formatDistance(d) } ?: "") }
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
    if (o.isPrint) {
        Box(Modifier.padding(horizontal = Gutter, vertical = Space.s)) { PrintCard(o, multiLibrary, true, here, onBorrow) }
    } else DigitalOption(o, multiLibrary, onBorrow)
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
        OptionTop(stats = digitalStats(h)) {
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
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
                val meta = listOfNotNull(
                    o.ref.borrowLimitPerMonth?.takeIf { !h.availabilityKnown }?.let { pluralStringResource(R.plurals.hoopla_limit_short, it, it) },
                    o.moreEditions.takeIf { it > 0 }?.let { pluralStringResource(R.plurals.more_editions, it, it) },
                    o.staleSince?.let { stringResource(R.string.results_saved_from, relativeTimeText(it)) },
                )
                meta.forEach { Text(it, style = MaterialTheme.typography.bodySmall, color = muted) }
            }
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
private const val MAX_WAIT = 365

/** One number in an option's figures: value over a small label. The primary one decides. */
private data class Stat(val value: Int?, val label: String, val primary: Boolean = false, val suffix: String = "")

/** Copies · holds · then what decides it: days to wait, or copies free now. */
@Composable
private fun digitalStats(h: com.mardev.nearshelf.core.model.Holding): List<Stat>? {
    if (!h.availabilityKnown) return null // hoopla gives no numbers
    val copies = h.owned
    val holds = h.holds
    val primary = when {
        h.isAvailableNow -> (h.available ?: 1).let { Stat(it, pluralStringResource(R.plurals.caption_available, it), primary = true) }
        h.waitDays != null -> Stat(
            h.waitDays!!.coerceAtMost(MAX_WAIT),
            pluralStringResource(R.plurals.caption_days_wait, h.waitDays!!),
            primary = true,
            // OverDrive's estimate can run to thousands of days when one copy has hundreds of holds.
            suffix = if (h.waitDays!! > MAX_WAIT) "+" else "",
        )
        else -> Stat(null, pluralStringResource(R.plurals.caption_days_wait, 2), primary = true)
    }
    return listOf(
        Stat(copies, pluralStringResource(R.plurals.stat_copies, copies ?: 2)),
        Stat(holds, pluralStringResource(R.plurals.stat_holds, holds ?: 2)),
        primary,
    )
}

/** Copies · holds · on the shelf now. */
@Composable
private fun printStats(h: com.mardev.nearshelf.core.model.Holding, onShelf: Int?): List<Stat>? {
    if (!h.availabilityKnown) return null
    val copies = h.owned ?: h.copies.size.takeUnless { h.branchLevelOnly || h.copies.isEmpty() }
    return listOf(
        Stat(copies, pluralStringResource(R.plurals.stat_copies, copies ?: 2)),
        Stat(h.holds, pluralStringResource(R.plurals.stat_holds, h.holds ?: 2)),
        Stat(onShelf, stringResource(if (h.branchLevelOnly) R.string.caption_branches_on_shelf else R.string.caption_on_shelf), primary = true),
    )
}

/**
 * Who on the left, the figures on the right in fixed-width columns, so numbers line up
 * from row to row like a table. At large font sizes the figures go under the name.
 */
@Composable
private fun OptionTop(stats: List<Stat>?, left: @Composable () -> Unit) {
    val stacked = androidx.compose.ui.platform.LocalDensity.current.fontScale >= 1.5f
    if (stats == null) { left(); return }
    if (stacked) {
        Column {
            left()
            StatsCluster(stats, Modifier.padding(top = Space.s), fixedColumns = false)
        }
    } else {
        Row(verticalAlignment = Alignment.Top) {
            Box(Modifier.weight(1f)) { left() }
            Spacer(Modifier.width(Space.s))
            StatsCluster(stats)
        }
    }
}

@Composable
private fun StatsCluster(stats: List<Stat>, modifier: Modifier = Modifier, fixedColumns: Boolean = true) {
    val muted = MaterialTheme.colorScheme.onSurfaceVariant
    // Bottom-aligned: every label sits on one line, every number directly above its label.
    Row(modifier, verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(if (fixedColumns) 0.dp else Space.l)) {
        stats.forEach { st ->
            val col = if (fixedColumns) Modifier.width(if (st.primary) 72.dp else 52.dp) else Modifier
            Column(col, horizontalAlignment = if (fixedColumns) Alignment.End else Alignment.Start) {
                when {
                    st.value == null -> Text("–", style = if (st.primary) MaterialTheme.typography.headlineMedium else MaterialTheme.typography.titleMedium, color = muted)
                    st.primary -> CountUp(
                        st.value,
                        suffix = st.suffix,
                        // Lining figures, so numbers sit on the baseline whatever the font's default.
                        style = MaterialTheme.typography.headlineMedium.copy(fontFeatureSettings = "lnum"),
                        color = MaterialTheme.colorScheme.primary,
                    )
                    else -> Text(
                        st.value.toString(),
                        // Tabular figures keep columns aligned; baseline-matched to the big number.
                        style = MaterialTheme.typography.titleMedium.copy(fontFeatureSettings = "tnum"),
                    )
                }
                Text(st.label, style = MaterialTheme.typography.labelSmall, color = muted, maxLines = 1, softWrap = false)
            }
        }
    }
}

/** Branches further than this are shown without a distance: the number would be true but useless. */
internal const val NEARBY_KM = 200.0

/**
 * Print, one card per library edition:
 *  - header: library tile, name, status label (on shelf / all copies out), edition when
 *    the library has several, a chevron that opens the branch list;
 *  - figures: total copies | holds | available, in three equal columns;
 *  - the home or nearest branch, with its status and shelf location;
 *  - Place hold / View in catalog;
 *  - attached underneath: "Show all N branches".
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun PrintCard(o: OptionUi, multiLibrary: Boolean, nameEdition: Boolean, here: LatLng?, onBorrow: (LibraryRef, MatchedHolding) -> Unit) {
    val h = o.holding
    val m = o.match
    val colors = MaterialTheme.colorScheme
    val status = LocalStatusColors.current
    val branches = remember(h.copies, o.library.homeBranch?.name, here) { summarizeBranches(h.copies, o.library.homeBranch?.name, here) }
    var expanded by rememberSaveable(o.library.id, h.providerItemId) { mutableStateOf(false) }
    val onShelfNow = h.isBorrowableNow()
    val onShelf = branches.sumOf { it.onShelf }.takeIf { h.copies.isNotEmpty() } ?: h.available ?: if (onShelfNow) null else 0
    val cardColor = if (colors.background.luminance() > 0.5f) colors.surfaceContainerLowest else colors.surfaceContainer
    val shape = MaterialTheme.shapes.large

    Column(verticalArrangement = Arrangement.spacedBy(Space.s)) {
        Column(
            Modifier.fillMaxWidth().clip(shape).background(cardColor).border(1.dp, colors.outlineVariant, shape).padding(Space.l),
        ) {
            // Header
            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(Modifier.size(48.dp).clip(MaterialTheme.shapes.medium).background(colors.primaryContainer), contentAlignment = Alignment.Center) {
                    Icon(painterResource(R.drawable.ic_library), null, tint = colors.primary, modifier = Modifier.size(26.dp))
                }
                Spacer(Modifier.width(Space.m))
                Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(Space.xs)) {
                    Text(
                        o.library.name,
                        style = MaterialTheme.typography.titleMedium.copy(fontSize = MaterialTheme.typography.titleLarge.fontSize, lineHeight = MaterialTheme.typography.titleLarge.lineHeight),
                        maxLines = 2,
                        overflow = TextOverflow.Ellipsis,
                    )
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(6.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        when {
                            !h.availabilityKnown -> StatusPill(stringResource(R.string.badge_unknown), colors.surfaceContainer, colors.onSurfaceVariant)
                            onShelfNow -> StatusPill(stringResource(R.string.badge_on_shelf), status.availableContainer, status.onAvailableContainer)
                            else -> StatusPill(stringResource(R.string.badge_all_out), status.waitlistContainer, status.onWaitlistContainer)
                        }
                        // Several editions at one library look alike; say what differs.
                        if (nameEdition) h.edition?.let { Badge(it, variant = BadgeVariant.Outline, size = BadgeSize.Sm) }
                        if (m.otherLanguage && h.language != null) Badge(languageName(h.language!!), variant = BadgeVariant.Outline, size = BadgeSize.Sm)
                    }
                }
                if (branches.size > 1) {
                    IconButton(onClick = { expanded = !expanded }) {
                        Icon(
                            painterResource(if (expanded) R.drawable.ic_caret_up else R.drawable.ic_caret_down),
                            stringResource(if (expanded) R.string.show_fewer_branches else R.string.cd_show_branches),
                            tint = colors.onSurface,
                            modifier = Modifier.size(22.dp),
                        )
                    }
                }
            }
            if (o.moreEditions > 0 || o.staleSince != null) {
                val notes = listOfNotNull(
                    o.moreEditions.takeIf { it > 0 }?.let { pluralStringResource(R.plurals.more_editions, it, it) },
                    o.staleSince?.let { stringResource(R.string.results_saved_from, relativeTimeText(it)) },
                )
                notes.forEach { Text(it, style = MaterialTheme.typography.bodySmall, color = colors.onSurfaceVariant, modifier = Modifier.padding(top = Space.s)) }
            }
            // Figures
            if (h.availabilityKnown) {
                val copies = h.owned ?: h.copies.size.takeUnless { h.branchLevelOnly || h.copies.isEmpty() }
                Row(Modifier.fillMaxWidth().padding(top = Space.l).height(androidx.compose.foundation.layout.IntrinsicSize.Min)) {
                    Figure(copies, stringResource(R.string.stat_total_copies), Modifier.weight(1f))
                    FigureDivider()
                    Figure(h.holds, stringResource(R.string.stat_holds_title), Modifier.weight(1f))
                    FigureDivider()
                    Figure(
                        onShelf,
                        stringResource(if (h.branchLevelOnly) R.string.stat_branches_with else R.string.stat_available),
                        Modifier.weight(1f),
                        color = if ((onShelf ?: 0) > 0) status.available else colors.onSurface,
                    )
                }
            }
            // Home or nearest branch
            branches.firstOrNull()?.let { b ->
                HorizontalDivider(Modifier.padding(top = Space.l), color = colors.outlineVariant)
                CardBranchLine(b, h.branchLevelOnly, Modifier.padding(top = Space.s))
            }
            Button(
                onClick = { onBorrow(o.ref, m) },
                shape = ButtonShape,
                modifier = Modifier.fillMaxWidth().padding(top = Space.m).heightIn(min = 48.dp),
            ) {
                Icon(painterResource(R.drawable.ic_open_external), null, modifier = Modifier.size(18.dp))
                Spacer(Modifier.width(Space.s))
                Text(stringResource(if (onShelfNow) R.string.action_view_catalog else R.string.action_place_hold), style = MaterialTheme.typography.labelLarge)
            }
        }
        // Attached branch list
        if (branches.size > 1) {
            Column(Modifier.fillMaxWidth().clip(shape).background(cardColor).border(1.dp, colors.outlineVariant, shape)) {
                Row(
                    Modifier.fillMaxWidth().heightIn(min = 52.dp).clickable(role = Role.Button) { expanded = !expanded }.padding(horizontal = Space.l),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Icon(painterResource(if (expanded) R.drawable.ic_caret_up else R.drawable.ic_caret_down), null, tint = colors.onSurface, modifier = Modifier.size(20.dp))
                    Spacer(Modifier.width(Space.m))
                    Text(
                        if (expanded) stringResource(R.string.show_fewer_branches)
                        else pluralStringResource(R.plurals.show_all_branches, branches.size, branches.size),
                        style = MaterialTheme.typography.titleSmall,
                    )
                }
                if (expanded) {
                    branches.drop(1).forEach { b ->
                        HorizontalDivider(Modifier.padding(horizontal = Space.l), color = colors.outlineVariant)
                        CardBranchLine(b, h.branchLevelOnly, Modifier.padding(horizontal = Space.l, vertical = Space.xs))
                    }
                }
            }
        }
    }
}

@Composable
private fun StatusPill(text: String, bg: Color, fg: Color) {
    Row(
        Modifier.clip(CircleShape).background(bg).padding(horizontal = 10.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.size(7.dp).clip(CircleShape).background(fg))
        Spacer(Modifier.width(6.dp))
        Text(text, style = MaterialTheme.typography.labelLarge, color = fg)
    }
}

@Composable
private fun Figure(value: Int?, label: String, modifier: Modifier = Modifier, color: Color = MaterialTheme.colorScheme.onSurface) {
    Column(modifier, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            value?.toString() ?: "–",
            style = MaterialTheme.typography.headlineSmall.copy(fontFamily = com.mardev.nearshelf.ui.theme.Sans, fontWeight = androidx.compose.ui.text.font.FontWeight.SemiBold, fontFeatureSettings = "tnum"),
            color = if (value == null) MaterialTheme.colorScheme.onSurfaceVariant else color,
        )
        val labelStyle = MaterialTheme.typography.bodySmall.copy(color = MaterialTheme.colorScheme.onSurfaceVariant)
        // Shrinks a step at large font sizes instead of cutting "Total copies" short.
        BasicText(label, style = labelStyle, maxLines = 1, autoSize = TextAutoSize.StepBased(minFontSize = 9.sp, maxFontSize = labelStyle.fontSize), modifier = Modifier.padding(horizontal = 2.dp))
    }
}

@Composable
private fun FigureDivider() = Box(Modifier.fillMaxHeight().width(1.dp).background(MaterialTheme.colorScheme.outlineVariant))

/** A branch: pin, name · distance (when near), then its status and shelf location. Taps open maps. */
@Composable
private fun CardBranchLine(b: BranchSummary, branchLevelOnly: Boolean, modifier: Modifier = Modifier) {
    val status = LocalStatusColors.current
    val context = androidx.compose.ui.platform.LocalContext.current
    val muted = MaterialTheme.colorScheme.onSurfaceVariant
    val mapLabel = stringResource(R.string.cd_open_map, b.name)
    val tap = b.location?.let { loc ->
        Modifier.clickable(onClickLabel = mapLabel, role = Role.Button) {
            // geo: URI opens the user's maps app at the branch; nothing is sent by Nearshelf.
            context.openExternal("geo:${loc.latitude},${loc.longitude}?q=${loc.latitude},${loc.longitude}(${android.net.Uri.encode(b.name)})")
        }
    } ?: Modifier
    Row(modifier.fillMaxWidth().then(tap).heightIn(min = 52.dp).padding(vertical = Space.s).semantics(mergeDescendants = true) {}, verticalAlignment = Alignment.Top) {
        Icon(
            painterResource(R.drawable.ic_map_pin),
            null,
            tint = if (b.onShelf > 0) status.available else muted,
            modifier = Modifier.padding(top = 2.dp).size(22.dp),
        )
        Spacer(Modifier.width(Space.m))
        Column(Modifier.weight(1f)) {
            FlowRow(verticalArrangement = Arrangement.Center, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                Text(b.name, style = MaterialTheme.typography.titleMedium)
                if (b.isHome) Badge(stringResource(R.string.badge_home), variant = BadgeVariant.Outline, size = BadgeSize.Sm)
                b.distanceKm?.takeIf { it <= NEARBY_KM }?.let { Text("·  " + formatDistance(it), style = MaterialTheme.typography.bodyMedium, color = muted) }
            }
            Text(
                listOfNotNull(
                    if (branchLevelOnly) stringResource(if (b.onShelf > 0) R.string.branch_has_it else R.string.branch_unavailable) else branchStatus(b),
                    b.callNumber,
                ).joinToString(" · "),
                style = MaterialTheme.typography.bodyMedium,
                color = if (b.onShelf > 0) status.available else muted,
            )
        }
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

/** This tab's format isn't at any of the reader's libraries. */
@Composable
internal fun EmptyTab(format: Format) {
    Column(Modifier.fillMaxWidth().padding(horizontal = Gutter, vertical = Space.xl), verticalArrangement = Arrangement.spacedBy(Space.xs)) {
        Text(stringResource(R.string.tab_empty, formatLabel(format)), style = MaterialTheme.typography.titleLarge)
        Text(stringResource(R.string.tab_empty_hint), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

/** Short status under each tab label: where the reader can see availability before tapping. */
@Composable
internal fun tabStatus(section: FormatSection?, checking: Boolean): Pair<String, Color> {
    val status = LocalStatusColors.current
    val muted = MaterialTheme.colorScheme.onSurfaceVariant
    val v = section?.takeIf { it.options.isNotEmpty() }?.verdict
        ?: return (if (checking) stringResource(R.string.tab_checking) else stringResource(R.string.tab_none)) to muted
    return when (v) {
        is Verdict.AvailableNow -> stringResource(R.string.tab_now) to status.available
        is Verdict.OnService -> stringResource(R.string.tab_on_service, v.service) to MaterialTheme.colorScheme.onSurface
        is Verdict.ShortestWait -> pluralStringResource(R.plurals.tab_days, v.days, v.days) to status.waitlist
        Verdict.Waitlist -> stringResource(R.string.tab_waitlist) to status.waitlist
        is Verdict.OnShelf -> stringResource(R.string.tab_on_shelf) to status.available
        Verdict.AllCheckedOut -> stringResource(R.string.tab_all_out) to muted
        Verdict.Unknown -> stringResource(R.string.tab_unknown) to muted
    }
}

internal val TAB_FORMATS = listOf(Format.EBOOK, Format.AUDIOBOOK, Format.PHYSICAL)

/**
 * eBook | Audiobook | Print, always in that order. Each tab: icon and name, and under it
 * the format's status in its colour. Selection: a short accent rule, like the bottom bar.
 */
@Composable
internal fun FormatTabs(organized: OrganizedResults, selected: Format, onSelect: (Format) -> Unit) {
    val colors = MaterialTheme.colorScheme
    val largeFont = androidx.compose.ui.platform.LocalDensity.current.fontScale >= 1.3f
    Column(Modifier.fillMaxWidth().background(colors.background)) {
        Row(Modifier.fillMaxWidth().padding(horizontal = Gutter - Space.s).selectableGroup()) {
            TAB_FORMATS.forEach { f ->
                val isSelected = f == selected
                val (statusText, statusColor) = tabStatus(organized.section(f), organized.loading > 0)
                Box(
                    Modifier
                        .weight(1f)
                        .heightIn(min = 56.dp)
                        .clip(MaterialTheme.shapes.small)
                        .selectable(selected = isSelected, role = Role.Tab, onClick = { onSelect(f) }),
                    contentAlignment = Alignment.Center,
                ) {
                    Column(Modifier.padding(vertical = Space.s), horizontalAlignment = Alignment.CenterHorizontally) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            // At large font sizes the icon gives its room to the word.
                            if (!largeFont) {
                                Icon(painterResource(formatIcon(f)), null, tint = if (isSelected) colors.primary else colors.onSurfaceVariant, modifier = Modifier.size(18.dp))
                                Spacer(Modifier.width(6.dp))
                            }
                            val labelStyle = MaterialTheme.typography.titleSmall.copy(color = if (isSelected) colors.onSurface else colors.onSurfaceVariant)
                            BasicText(
                                formatLabel(f),
                                style = labelStyle,
                                maxLines = 1,
                                // Shrinks a step or two rather than cutting "Audiobook" short.
                                autoSize = TextAutoSize.StepBased(minFontSize = 10.sp, maxFontSize = labelStyle.fontSize),
                            )
                        }
                        Text(statusText, style = MaterialTheme.typography.labelMedium, color = statusColor, maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.padding(top = 2.dp))
                    }
                    Box(
                        Modifier.align(Alignment.BottomCenter).size(width = if (isSelected) 32.dp else 0.dp, height = 2.dp)
                            .clip(androidx.compose.foundation.shape.RoundedCornerShape(topStart = 2.dp, topEnd = 2.dp)).background(colors.primary),
                    )
                }
            }
        }
        HorizontalDivider(color = colors.outlineVariant)
    }
}
