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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.widthIn
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.BlendMode
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.semantics.contentDescription
import com.mardev.nearshelf.ui.components.MonogramSize
import com.mardev.nearshelf.ui.theme.Tagline
import com.mardev.nearshelf.ui.theme.WordmarkLarge

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
 * search field (the keyboard's Search key runs it; Scan sits inside), the reader's
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
        // The masthead over the header art, then the search field overlapping the art's foot.
        item(key = "top") {
            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
                HeaderArt(Modifier.align(Alignment.TopEnd))
                Column(Modifier.statusBarsPadding().readableWidth().padding(bottom = Space.s)) {
                    Masthead(onPreferences, onSettings)
                    Column(Modifier.padding(start = Gutter, end = Gutter, top = Space.xl)) {
                        // One control: the keyboard's Search key checks the libraries; Scan sits inside the field.
                        PaperSearchField(
                            value = input,
                            onValueChange = onInputChange,
                            placeholder = stringResource(R.string.search_hint),
                            label = stringResource(R.string.search_label),
                            onSearch = { if (count > 0) onSubmit() },
                            raised = true,
                            pill = true,
                            trailing = if (hasCamera) {
                                {
                                    IconButton(onClick = onScan, enabled = count > 0) {
                                        Icon(
                                            painterResource(R.drawable.ic_barcode),
                                            stringResource(R.string.cd_scan),
                                            tint = if (count > 0) colors.primary else colors.outline,
                                            modifier = Modifier.size(26.dp),
                                        )
                                    }
                                }
                            } else null,
                        )
                    }
                }
            }
        }
        item(key = "librariesHeader") {
            Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.TopCenter) {
                SectionHeader(
                    stringResource(R.string.home_your_libraries),
                    Modifier.readableWidth().padding(top = Space.xl, bottom = Space.s),
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
                    val shape = androidx.compose.foundation.shape.RoundedCornerShape(24.dp)
                    Column(
                        Modifier.readableWidth().padding(horizontal = Gutter, vertical = Space.xs)
                            .shadow(10.dp, shape, ambientColor = colors.primary.copy(alpha = 0.3f), spotColor = colors.primary.copy(alpha = 0.3f))
                            .clip(shape).background(cardColor).border(1.dp, colors.outlineVariant.copy(alpha = 0.6f), shape)
                            .padding(vertical = Space.xs),
                    ) {
                        if (list == null) {
                            // Libraries come from the local database; skeleton rows hold their place meanwhile.
                            repeat(2) { LibraryRowSkeleton(inset = Space.l) }
                        } else list.forEachIndexed { index, library ->
                            LibraryRow(
                                library,
                                onClick = onManageLibraries,
                                onClickLabel = stringResource(R.string.home_manage),
                                inset = Space.l + Space.xs,
                                trailing = { RowChevron() },
                            )
                            if (index < list.lastIndex) {
                                HorizontalDivider(Modifier.padding(start = Space.l + Space.xs + MonogramSize + Space.l, end = Space.xl), color = colors.outlineVariant)
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
                        Modifier.readableWidth().padding(top = Space.xl, bottom = Space.s),
                        action = stringResource(R.string.home_see_all),
                        onAction = { onOpenHistory(null) },
                    )
                }
            }
            item(key = "recentShelf") { RecentShelf(recent, onOpen = { onOpenHistory(it) }) }
        }
    }
}

/**
 * Header illustration on the right of the masthead. It fades into the page on its
 * left and bottom edges, so the art's own background melts into the paper. The
 * night theme loads its own version (res/drawable-night-nodpi/home_header.webp).
 */
@Composable
private fun HeaderArt(modifier: Modifier = Modifier) {
    androidx.compose.foundation.Image(
        painterResource(R.drawable.home_header),
        contentDescription = null,
        contentScale = androidx.compose.ui.layout.ContentScale.Crop,
        alignment = Alignment.CenterEnd,
        modifier = modifier
            .fillMaxWidth(0.66f)
            .widthIn(max = 420.dp)
            .height(HeaderArtHeight + WindowInsets.statusBars.asPaddingValues().calculateTopPadding())
            .graphicsLayer {
                compositingStrategy = androidx.compose.ui.graphics.CompositingStrategy.Offscreen
            }
            .drawWithContent {
                drawContent()
                drawRect(
                    Brush.horizontalGradient(0f to Color.Transparent, 0.35f to Color.Black),
                    blendMode = BlendMode.DstIn,
                )
                drawRect(
                    Brush.verticalGradient(0.6f to Color.Black, 1f to Color.Transparent),
                    blendMode = BlendMode.DstIn,
                )
            },
    )
}

private val HeaderArtHeight = 210.dp

/** Large wordmark and serif tagline with a short oxblood rule; the two global actions as round buttons. */
@Composable
private fun Masthead(onPreferences: () -> Unit, onSettings: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    Row(
        Modifier.fillMaxWidth().padding(start = Gutter, end = Gutter, top = Space.l),
        verticalAlignment = Alignment.Top,
    ) {
        Column(Modifier.weight(1f).padding(top = Space.l)) {
            Text(
                stringResource(R.string.app_name),
                style = WordmarkLarge,
                color = colors.primary,
                modifier = Modifier.semantics { heading() },
            )
            Text(
                stringResource(R.string.tagline),
                style = Tagline,
                color = colors.onSurface,
                modifier = Modifier.padding(top = Space.xs),
            )
            Box(Modifier.padding(top = Space.m).width(48.dp).height(3.dp).clip(RoundedCornerShape(2.dp)).background(colors.primary))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(Space.m)) {
            RoundAction(R.drawable.ic_sliders, stringResource(R.string.cd_reading_preferences), onPreferences)
            RoundAction(R.drawable.ic_settings, stringResource(R.string.settings_title), onSettings)
        }
    }
}

/** A round cream button with a soft shadow, readable over the header art. */
@Composable
private fun RoundAction(icon: Int, label: String, onClick: () -> Unit) {
    val colors = MaterialTheme.colorScheme
    val light = colors.background.luminance() > 0.5f
    Box(
        Modifier
            .size(48.dp)
            .shadow(6.dp, CircleShape, ambientColor = colors.primary.copy(alpha = 0.35f), spotColor = colors.primary.copy(alpha = 0.35f))
            .clip(CircleShape)
            .background(if (light) colors.surfaceContainerLowest else colors.surfaceContainerHigh)
            .clickable(onClickLabel = null, role = Role.Button, onClick = onClick)
            .semantics { contentDescription = label },
        contentAlignment = Alignment.Center,
    ) {
        Icon(painterResource(icon), contentDescription = null, tint = colors.onSurface, modifier = Modifier.size(22.dp))
    }
}

/** Recently checked books, face out: covers only, the title is in each cover's label. */
@Composable
private fun RecentShelf(recent: List<HistoryItem>, onOpen: (HistoryItem) -> Unit) {
    LazyRow(
        contentPadding = PaddingValues(start = Gutter, end = Gutter, top = Space.xs, bottom = Space.m),
        horizontalArrangement = Arrangement.spacedBy(Space.l),
    ) {
        items(recent, key = { it.key }) { h ->
            val label = listOfNotNull(h.title, h.author).joinToString(", ")
            CoverThumb(
                h.coverUrl,
                title = h.title,
                width = 100.dp,
                height = 144.dp,
                elevated = true,
                modifier = Modifier
                    .clip(MaterialTheme.shapes.extraSmall)
                    .clickable(role = Role.Button, onClick = { onOpen(h) })
                    .semantics { contentDescription = label },
            )
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
