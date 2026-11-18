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
import androidx.compose.material3.HorizontalDivider
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
import com.mardev.nearshelf.ui.components.LibraryRow
import com.mardev.nearshelf.ui.components.LibraryRowSkeleton
import com.mardev.nearshelf.ui.components.RowChevron
import com.mardev.nearshelf.ui.components.FieldHint
import com.mardev.nearshelf.ui.components.PaperSearchField
import com.mardev.nearshelf.ui.components.Monogram
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
    val colors = MaterialTheme.colorScheme
    val light = colors.background.luminance() > 0.5f
    val cardColor = if (light) colors.surfaceContainerLowest else colors.surfaceContainer
    LazyColumn(
        Modifier.fillMaxSize(),
        contentPadding = PaddingValues(bottom = Space.xl),
    ) {
        // A warm panel holds the masthead and the search: the first layer, where the page starts.
        item(key = "top") {
            Box(
                Modifier
                    .fillMaxWidth()
                    .clip(androidx.compose.foundation.shape.RoundedCornerShape(bottomStart = 28.dp, bottomEnd = 28.dp))
                    .background(colors.surfaceContainer),
                contentAlignment = Alignment.TopCenter,
            ) {
                Column(Modifier.statusBarsPadding().readableWidth().padding(bottom = Space.xl)) {
                    Masthead(onPreferences, onSettings)
                    Column(Modifier.padding(start = Gutter, end = Gutter, top = Space.l)) {
                        PaperSearchField(
                            value = input,
                            onValueChange = onInputChange,
                            placeholder = stringResource(R.string.search_hint),
                            label = stringResource(R.string.search_label),
                            onSearch = onSubmit,
                            raised = true,
                        )
                        FieldHint(stringResource(R.string.search_tip_label), stringResource(R.string.search_tip_body), Modifier.padding(top = Space.s, start = 2.dp))
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
            }
        }
        item(key = "librariesHeader") {
            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
                SectionHeader(
                    stringResource(R.string.home_your_libraries),
                    Modifier.readableWidth().padding(top = Space.l),
                    count = count.takeIf { it > 0 },
                    action = if (count > 0) stringResource(R.string.home_manage) else null,
                    onAction = onManageLibraries,
                )
            }
        }
        // The libraries as one white card, the same surface as the results cards.
        item(key = "libraries") {
            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
                val list = libraries
                if (list != null && list.isEmpty()) {
                    Box(Modifier.readableWidth()) { NoLibraries(onAddLibrary) }
                } else {
                    val shape = MaterialTheme.shapes.large
                    Column(
                        Modifier.readableWidth().padding(horizontal = Gutter, vertical = Space.xs)
                            .clip(shape).background(cardColor).border(1.dp, colors.outlineVariant, shape),
                    ) {
                        if (list == null) {
                            // Libraries come from the local database; skeleton rows hold their place meanwhile.
                            repeat(2) { LibraryRowSkeleton(inset = Space.l) }
                        } else list.forEachIndexed { index, library ->
                            LibraryRow(
                                library,
                                onClick = onManageLibraries,
                                onClickLabel = stringResource(R.string.home_manage),
                                inset = Space.l,
                                trailing = { RowChevron() },
                            )
                            if (index < list.lastIndex) {
                                HorizontalDivider(Modifier.padding(start = Space.l + 40.dp + Space.l, end = Space.l), color = colors.outlineVariant)
                            }
                        }
                    }
                }
            }
        }
        if (recent.isNotEmpty()) {
            item(key = "recentHeader") {
                Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
                    SectionHeader(
                        stringResource(R.string.home_recent),
                        Modifier.readableWidth().padding(top = Space.l),
                        action = stringResource(R.string.home_see_all),
                        onAction = { onOpenHistory(null) },
                    )
                }
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
                // Tinted from the panel it sits on, so it stays visible as a waiting button.
                disabledContainerColor = lerp(colors.surfaceContainer, colors.primary, 0.16f),
                disabledContentColor = lerp(colors.surfaceContainer, colors.primary, 0.6f),
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
            // On the tinted panel the secondary action is a white (or lifted) surface.
            colors = ButtonDefaults.filledTonalButtonColors(
                containerColor = if (colors.background.luminance() > 0.5f) colors.surfaceContainerLowest else colors.surfaceContainerHighest,
                contentColor = colors.onSurface,
                disabledContainerColor = colors.surfaceContainerHigh,
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

/** Recently checked books, face out, like a shelf. */
@Composable
private fun RecentShelf(recent: List<HistoryItem>, onOpen: (HistoryItem) -> Unit) {
    val shelf = MaterialTheme.colorScheme.secondary.copy(alpha = 0.45f)
    LazyRow(contentPadding = PaddingValues(horizontal = Gutter - Space.s)) {
        items(recent, key = { it.key }) { h ->
            Column(Modifier.width(112.dp).clip(MaterialTheme.shapes.small).clickable(role = Role.Button, onClick = { onOpen(h) })) {
                // Covers stand on a thin shelf that runs under the whole row.
                CoverThumb(h.coverUrl, title = h.title, width = 88.dp, height = 128.dp, elevated = true, modifier = Modifier.padding(start = 12.dp, end = 12.dp, top = Space.s))
                Box(Modifier.fillMaxWidth().height(3.dp).background(shelf))
                Column(Modifier.padding(horizontal = 12.dp, vertical = Space.s)) {
                    Text(h.title, style = BookTitleSmall, color = MaterialTheme.colorScheme.onSurface, maxLines = 2, overflow = TextOverflow.Ellipsis)
                    h.author?.let {
                        Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    }
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
