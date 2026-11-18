package com.mardev.nearshelf.ui.home

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.lerp
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.pluralStringResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.data.HistoryItem
import com.mardev.nearshelf.ui.components.CoverThumb
import com.mardev.nearshelf.ui.components.Monogram
import com.mardev.nearshelf.ui.components.RowDivider
import com.mardev.nearshelf.ui.components.SectionHeader
import com.mardev.nearshelf.ui.components.Tag
import com.mardev.nearshelf.ui.components.readableWidth
import com.mardev.nearshelf.ui.components.lightswind.Skeleton
import com.mardev.nearshelf.ui.components.lightswind.SkeletonVariant
import com.mardev.nearshelf.ui.components.lightswind.rememberReducedMotion
import com.mardev.nearshelf.ui.theme.BookTitleSmall
import com.mardev.nearshelf.ui.theme.ButtonShape
import com.mardev.nearshelf.ui.theme.ControlShape
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space
import com.mardev.nearshelf.ui.theme.Wordmark

@Composable
fun HomeScreen(
    prefill: String?,
    onPrefillConsumed: () -> Unit,
    onScan: () -> Unit,
    onSearch: (BookQuery) -> Unit,
    onManageLibraries: () -> Unit,
    onAddLibrary: () -> Unit,
    onOpenHistory: (HistoryItem?) -> Unit,
    onPreferences: () -> Unit,
    onSettings: () -> Unit,
    vm: HomeViewModel = hiltViewModel(),
) {
    val recent by vm.recent.collectAsStateWithLifecycle()
    val input by vm.input.collectAsStateWithLifecycle()
    val libraries by vm.libraries.collectAsStateWithLifecycle()
    val keyboard = LocalSoftwareKeyboardController.current
    val hasCamera = androidx.compose.ui.platform.LocalContext.current.packageManager
        .hasSystemFeature(android.content.pm.PackageManager.FEATURE_CAMERA_ANY)
    LaunchedEffect(prefill) {
        if (prefill != null) {
            vm.input.value = prefill
            onPrefillConsumed()
        }
    }
    val submit = {
        vm.parsedQuery()?.let {
            keyboard?.hide()
            onSearch(it)
        }
    }

    HomeContent(
        input = input,
        onInputChange = { vm.input.value = it },
        libraries = libraries,
        recent = recent,
        hasCamera = hasCamera,
        onSubmit = { submit() },
        onScan = onScan,
        onManageLibraries = onManageLibraries,
        onAddLibrary = onAddLibrary,
        onOpenHistory = onOpenHistory,
        onPreferences = onPreferences,
        onSettings = onSettings,
    )
}

/**
 * Stateless Home UI (rendered with sample data in the screenshot tests).
 *
 * Composition, top to bottom: a compact masthead (wordmark, tagline, two actions), the
 * search block (field, contextual tip, primary and secondary action), the reader's
 * libraries, then recently checked books as a small shelf of covers.
 */
@Composable
internal fun HomeContent(
    input: String,
    onInputChange: (String) -> Unit,
    libraries: List<Library>?,
    recent: List<HistoryItem>,
    hasCamera: Boolean,
    onSubmit: () -> Unit,
    onScan: () -> Unit,
    onManageLibraries: () -> Unit,
    onAddLibrary: () -> Unit,
    onOpenHistory: (HistoryItem?) -> Unit,
    onPreferences: () -> Unit,
    onSettings: () -> Unit,
) {
    val count = libraries?.size ?: 0
    LazyColumn(
        Modifier.fillMaxSize().statusBarsPadding().readableWidth(),
        contentPadding = PaddingValues(bottom = Space.xl),
    ) {
        item(key = "masthead") { Masthead(onPreferences, onSettings) }
        item(key = "search") {
            Column(Modifier.padding(start = Gutter, end = Gutter, top = Space.l)) {
                SearchField(value = input, onValueChange = onInputChange, onSearch = onSubmit)
                SearchTip(Modifier.padding(top = Space.s, start = 2.dp))
                SearchActions(
                    label = if (count > 0) pluralStringResource(R.plurals.search_action_count, count, count) else stringResource(R.string.search_action),
                    canSearch = input.isNotBlank() && count > 0,
                    canScan = count > 0,
                    hasCamera = hasCamera,
                    onSubmit = onSubmit,
                    onScan = onScan,
                    modifier = Modifier.padding(top = Space.l),
                )
            }
        }
        item(key = "librariesHeader") {
            SectionHeader(
                stringResource(R.string.home_your_libraries),
                Modifier.padding(top = Space.xxl - Space.s),
                count = count.takeIf { it > 0 },
                action = if (count > 0) stringResource(R.string.home_manage) else null,
                onAction = onManageLibraries,
            )
        }
        val list = libraries
        when {
            // Libraries come from the local database; skeleton rows hold their place meanwhile.
            list == null -> items(2, key = { "skeleton-$it" }) { LibraryRowSkeleton() }
            list.isEmpty() -> item(key = "noLibraries") { NoLibraries(onAddLibrary) }
            else -> itemsIndexed(list, key = { _, l -> l.id }) { index, library ->
                LibraryRow(library, onClick = onManageLibraries)
                if (index < list.lastIndex) RowDivider()
            }
        }
        if (recent.isNotEmpty()) {
            item(key = "recentHeader") {
                SectionHeader(
                    stringResource(R.string.home_recent),
                    Modifier.padding(top = Space.xl),
                    action = stringResource(R.string.home_see_all),
                    onAction = { onOpenHistory(null) },
                )
            }
            item(key = "recentShelf") { RecentShelf(recent, onOpen = { onOpenHistory(it) }) }
        }
    }
}

/** Wordmark and tagline on the left, the two global actions on the right. */
@Composable
private fun Masthead(onPreferences: () -> Unit, onSettings: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().padding(start = Gutter, end = Gutter - 12.dp, top = Space.m),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Text(
                stringResource(R.string.app_name),
                style = Wordmark,
                color = MaterialTheme.colorScheme.primary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                stringResource(R.string.tagline),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 2.dp),
            )
        }
        val tint = MaterialTheme.colorScheme.onSurfaceVariant
        IconButton(onClick = onPreferences) {
            Icon(painterResource(R.drawable.ic_sliders), stringResource(R.string.cd_reading_preferences), tint = tint, modifier = Modifier.size(22.dp))
        }
        IconButton(onClick = onSettings) {
            Icon(painterResource(R.drawable.ic_settings), stringResource(R.string.settings_title), tint = tint, modifier = Modifier.size(22.dp))
        }
    }
}

/**
 * White field on the paper page with a hairline edge. Focus draws a brown edge and
 * colours the search glyph; text gets a Clear action.
 */
@Composable
private fun SearchField(value: String, onValueChange: (String) -> Unit, onSearch: () -> Unit) {
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val colors = MaterialTheme.colorScheme
    val label = stringResource(R.string.search_label)
    // White paper on the light theme; one step above the page on the dark one (never a hole).
    val fill = if (colors.background.luminance() > 0.5f) colors.surfaceContainerLowest else colors.surfaceContainerHigh
    val reduced = rememberReducedMotion()
    val edge by animateColorAsState(if (focused) colors.primary else colors.outlineVariant, tween(if (reduced) 0 else 150), label = "edge")
    BasicTextField(
        value = value,
        onValueChange = onValueChange,
        singleLine = true,
        textStyle = MaterialTheme.typography.bodyLarge.copy(color = colors.onSurface),
        cursorBrush = SolidColor(colors.primary),
        interactionSource = interaction,
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
        keyboardActions = KeyboardActions(onSearch = { onSearch() }),
        modifier = Modifier.fillMaxWidth().semantics { contentDescription = label },
        decorationBox = { inner ->
            Row(
                Modifier
                    .fillMaxWidth()
                    .height(52.dp)
                    .clip(ControlShape)
                    .background(fill)
                    .border(if (focused) 1.5.dp else 1.dp, edge, ControlShape)
                    .padding(start = Space.l, end = Space.xs),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    painterResource(R.drawable.ic_search),
                    contentDescription = null,
                    tint = if (focused) colors.primary else colors.onSurfaceVariant,
                    modifier = Modifier.size(20.dp),
                )
                Spacer(Modifier.width(Space.m))
                Box(Modifier.weight(1f), contentAlignment = Alignment.CenterStart) {
                    if (value.isEmpty()) {
                        Text(
                            stringResource(R.string.search_hint),
                            style = MaterialTheme.typography.bodyLarge,
                            color = colors.onSurfaceVariant,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    inner()
                }
                if (value.isNotEmpty()) {
                    IconButton(onClick = { onValueChange("") }) {
                        Icon(painterResource(R.drawable.ic_x), stringResource(R.string.cd_clear), tint = colors.onSurfaceVariant, modifier = Modifier.size(18.dp))
                    }
                } else {
                    Spacer(Modifier.width(Space.m))
                }
            }
        },
    )
}

/** The example query as a quiet footnote to the field. */
@Composable
private fun SearchTip(modifier: Modifier = Modifier) {
    val colors = MaterialTheme.colorScheme
    val label = stringResource(R.string.search_tip_label)
    val body = stringResource(R.string.search_tip_body)
    Text(
        buildAnnotatedString {
            withStyle(SpanStyle(color = colors.primary, fontWeight = FontWeight.SemiBold)) { append(label) }
            append("  ")
            append(body)
        },
        style = MaterialTheme.typography.bodySmall,
        color = colors.onSurfaceVariant,
        modifier = modifier,
    )
}

/**
 * Primary action (leather brown) and Scan (subtle surface), same height and radius.
 * Stacked full width at large font sizes so neither label wraps inside its button.
 */
@Composable
private fun SearchActions(
    label: String,
    canSearch: Boolean,
    canScan: Boolean,
    hasCamera: Boolean,
    onSubmit: () -> Unit,
    onScan: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val colors = MaterialTheme.colorScheme
    val stacked = LocalDensity.current.fontScale >= 1.5f
    val primary = @Composable { m: Modifier ->
        Button(
            onClick = onSubmit,
            enabled = canSearch,
            shape = ButtonShape,
            // Disabled keeps the accent as a tint: still the primary, clearly waiting for input.
            colors = ButtonDefaults.buttonColors(
                disabledContainerColor = lerp(colors.background, colors.primary, 0.10f),
                disabledContentColor = lerp(colors.background, colors.primary, 0.55f),
            ),
            contentPadding = PaddingValues(horizontal = Space.l),
            modifier = m.height(48.dp),
        ) { Text(label, style = MaterialTheme.typography.labelLarge, textAlign = TextAlign.Center, maxLines = 1, overflow = TextOverflow.Ellipsis) }
    }
    val scan = @Composable { m: Modifier ->
        FilledTonalButton(
            onClick = onScan,
            enabled = canScan,
            shape = ButtonShape,
            colors = ButtonDefaults.filledTonalButtonColors(
                containerColor = colors.surfaceContainer,
                contentColor = colors.onSurface,
                disabledContainerColor = colors.surfaceContainerLow,
                disabledContentColor = colors.outline,
            ),
            contentPadding = PaddingValues(horizontal = Space.l),
            modifier = m.height(48.dp),
        ) {
            Icon(painterResource(R.drawable.ic_barcode), null, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(Space.s))
            Text(stringResource(R.string.action_scan), style = MaterialTheme.typography.labelLarge)
        }
    }
    if (stacked) {
        Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(Space.m)) {
            primary(Modifier.fillMaxWidth())
            if (hasCamera) scan(Modifier.fillMaxWidth())
        }
    } else {
        Row(modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(Space.m)) {
            primary(Modifier.weight(1f))
            if (hasCamera) scan(Modifier)
        }
    }
}

/**
 * One library: identity (monogram + name), location, then its services as tags:
 * filled for digital lending, outlined for the physical catalog.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun LibraryRow(library: Library, onClick: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    Row(
        Modifier
            .fillMaxWidth()
            .clickable(onClickLabel = stringResource(R.string.home_manage), role = Role.Button, onClick = onClick)
            .padding(start = Gutter, end = Gutter - Space.xs, top = Space.l, bottom = Space.l),
        verticalAlignment = Alignment.Top,
    ) {
        Monogram(library.name)
        Spacer(Modifier.width(Space.l))
        Column(Modifier.weight(1f)) {
            Text(
                library.name,
                style = MaterialTheme.typography.titleMedium,
                color = colors.onSurface,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
            )
            val place = listOfNotNull(library.city, library.region).joinToString(", ")
            if (place.isNotEmpty()) {
                Text(place, style = MaterialTheme.typography.bodyMedium, color = colors.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
            }
            val (digital, physical) = remember(library) {
                library.digitalServices.map { it.provider.displayName }.distinct() to
                    library.physicalServices.map { it.provider.displayName }.distinct()
            }
            if (digital.isNotEmpty() || physical.isNotEmpty()) {
                FlowRow(
                    Modifier.padding(top = Space.s),
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    digital.forEach { Tag(it, R.drawable.ic_ebook) }
                    physical.forEach { Tag(it, R.drawable.ic_books, filled = false) }
                }
            }
        }
        Icon(
            painterResource(R.drawable.ic_caret_right),
            contentDescription = null,
            tint = colors.outline,
            modifier = Modifier.padding(start = Space.s, top = 10.dp).size(18.dp),
        )
    }
}

/** Placeholder with the same proportions as [LibraryRow]. */
@Composable
private fun LibraryRowSkeleton() {
    Row(Modifier.fillMaxWidth().padding(horizontal = Gutter, vertical = Space.l)) {
        Skeleton(Modifier.size(40.dp), variant = SkeletonVariant.Rounded)
        Spacer(Modifier.width(Space.l))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(Space.s)) {
            Skeleton(Modifier.fillMaxWidth(0.7f).height(16.dp))
            Skeleton(Modifier.fillMaxWidth(0.4f).height(12.dp))
            Skeleton(Modifier.fillMaxWidth(0.55f).height(22.dp))
        }
    }
}

/** Recently checked books, face out, like a shelf. */
@Composable
private fun RecentShelf(recent: List<HistoryItem>, onOpen: (HistoryItem) -> Unit) {
    LazyRow(
        contentPadding = PaddingValues(horizontal = Gutter - Space.s),
        horizontalArrangement = Arrangement.spacedBy(Space.xs),
    ) {
        items(recent, key = { it.key }) { h ->
            Column(
                Modifier
                    .width(104.dp)
                    .clip(MaterialTheme.shapes.small)
                    .clickable(role = Role.Button, onClick = { onOpen(h) })
                    .padding(Space.s),
            ) {
                CoverThumb(h.coverUrl, title = h.title, width = 88.dp, height = 128.dp)
                Text(
                    h.title,
                    style = BookTitleSmall,
                    color = MaterialTheme.colorScheme.onSurface,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.padding(top = Space.s),
                )
                h.author?.let {
                    Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
            }
        }
    }
}

@Composable
private fun NoLibraries(onAdd: () -> Unit) {
    Column(
        Modifier
            .padding(horizontal = Gutter, vertical = Space.xs)
            .fillMaxWidth()
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, MaterialTheme.shapes.medium)
            .padding(Space.xl - Space.xs),
        verticalArrangement = Arrangement.spacedBy(Space.s),
    ) {
        Text(stringResource(R.string.home_no_libraries_title), style = MaterialTheme.typography.titleLarge)
        Text(
            stringResource(R.string.home_no_libraries_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Button(
            onClick = onAdd,
            shape = ButtonShape,
            contentPadding = PaddingValues(horizontal = Space.l),
            modifier = Modifier.padding(top = Space.s).height(48.dp),
        ) {
            Icon(painterResource(R.drawable.ic_plus), null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(Space.s))
            Text(stringResource(R.string.libraries_add), style = MaterialTheme.typography.labelLarge)
        }
    }
}
