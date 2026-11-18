package com.mardev.nearshelf.ui.home

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.border
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextField
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalSoftwareKeyboardController
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.data.HistoryItem
import com.mardev.nearshelf.ui.components.ListRow
import com.mardev.nearshelf.ui.components.Monogram
import com.mardev.nearshelf.ui.components.RowDivider
import com.mardev.nearshelf.ui.components.SectionHeader
import com.mardev.nearshelf.ui.components.readableWidth
import com.mardev.nearshelf.ui.history.HistoryRow
import com.mardev.nearshelf.ui.theme.ButtonShape
import com.mardev.nearshelf.ui.theme.Gutter

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

/** Stateless Home UI (rendered with sample data in the screenshot tests). */
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
    val hasLibraries = libraries?.isNotEmpty() == true
    LazyColumn(
        Modifier.fillMaxSize().statusBarsPadding().readableWidth(),
        contentPadding = PaddingValues(bottom = 24.dp),
    ) {
        item(key = "bar") { HomeTopBar(onPreferences, onSettings) }
        item(key = "search") {
            Column(Modifier.padding(horizontal = Gutter)) {
                Text(
                    stringResource(R.string.home_headline),
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.padding(top = 4.dp, bottom = 24.dp),
                )
                SearchField(value = input, onValueChange = onInputChange, onSearch = onSubmit)
                Text(
                    stringResource(R.string.search_supporting),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 8.dp),
                )
                SearchActions(
                    canSearch = input.isNotBlank() && hasLibraries,
                    canScan = hasLibraries,
                    hasCamera = hasCamera,
                    onSubmit = onSubmit,
                    onScan = onScan,
                    modifier = Modifier.padding(top = 20.dp),
                )
            }
        }
        if (recent.isNotEmpty()) {
            item(key = "recentHeader") {
                SectionHeader(
                    stringResource(R.string.home_recent),
                    Modifier.padding(top = 24.dp),
                    action = stringResource(R.string.home_see_all),
                    onAction = { onOpenHistory(null) },
                )
            }
            itemsIndexed(recent, key = { _, h -> "h-" + h.key }) { index, h ->
                HistoryRow(h, onOpen = { onOpenHistory(h) })
                if (index < recent.lastIndex) RowDivider()
            }
        }
        item(key = "librariesHeader") {
            SectionHeader(
                stringResource(R.string.home_your_libraries),
                Modifier.padding(top = 24.dp),
                count = libraries?.size?.takeIf { it > 0 },
                action = if (hasLibraries) stringResource(R.string.home_manage) else null,
                onAction = onManageLibraries,
            )
        }
        val list = libraries
        when {
            list == null -> Unit
            list.isEmpty() -> item(key = "noLibraries") { NoLibraries(onAddLibrary) }
            else -> itemsIndexed(list, key = { _, l -> l.id }) { index, library ->
                ListRow(
                    title = library.name,
                    meta = library.summaryLine(),
                    onClick = onManageLibraries,
                    onClickLabel = stringResource(R.string.home_manage),
                    leading = { Monogram(library.name) },
                )
                if (index < list.lastIndex) RowDivider()
            }
        }
    }
}

/**
 * Primary action plus Scan, side by side; stacked full width at large font sizes so
 * neither label has to wrap inside its button.
 */
@Composable
private fun SearchActions(
    canSearch: Boolean,
    canScan: Boolean,
    hasCamera: Boolean,
    onSubmit: () -> Unit,
    onScan: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val stacked = LocalDensity.current.fontScale >= 1.5f
    val primary = @Composable { m: Modifier ->
        Button(
            onClick = onSubmit,
            enabled = canSearch,
            shape = ButtonShape,
            // Disabled reads as warm paper, not a grey slab.
            colors = ButtonDefaults.buttonColors(
                disabledContainerColor = MaterialTheme.colorScheme.surfaceContainer,
                disabledContentColor = MaterialTheme.colorScheme.outline,
            ),
            modifier = m.heightIn(min = 52.dp),
        ) { Text(stringResource(R.string.search_action), textAlign = TextAlign.Center) }
    }
    val scan = @Composable { m: Modifier ->
        OutlinedButton(
            onClick = onScan,
            enabled = canScan,
            shape = ButtonShape,
            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
            contentPadding = PaddingValues(horizontal = 18.dp),
            modifier = m.heightIn(min = 52.dp),
        ) {
            Icon(painterResource(R.drawable.ic_barcode), null, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(8.dp))
            Text(stringResource(R.string.action_scan))
        }
    }
    if (stacked) {
        Column(modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            primary(Modifier.fillMaxWidth())
            if (hasCamera) scan(Modifier.fillMaxWidth())
        }
    } else {
        Row(modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            primary(Modifier.weight(1f))
            if (hasCamera) scan(Modifier)
        }
    }
}

/** Wordmark on the left, the two global actions on the right; icons sit on the gutter. */
@Composable
private fun HomeTopBar(onPreferences: () -> Unit, onSettings: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().height(64.dp).padding(start = Gutter, end = Gutter - 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            stringResource(R.string.app_name),
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.primary,
            modifier = Modifier.weight(1f).semantics { heading() },
        )
        val tint = MaterialTheme.colorScheme.onSurfaceVariant
        IconButton(onClick = onPreferences) {
            Icon(painterResource(R.drawable.ic_sliders), stringResource(R.string.cd_reading_preferences), tint = tint)
        }
        IconButton(onClick = onSettings) {
            Icon(painterResource(R.drawable.ic_settings), stringResource(R.string.settings_title), tint = tint)
        }
    }
}

/**
 * White "paper" field with a hairline edge; the edge turns brand brown and thicker on
 * focus. Scanning lives in its own button, so the field only offers Clear.
 */
@Composable
private fun SearchField(value: String, onValueChange: (String) -> Unit, onSearch: () -> Unit) {
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val colors = MaterialTheme.colorScheme
    val label = stringResource(R.string.search_label)
    // White paper on the light theme; one step above the page on the dark one (never a hole).
    val fill = if (colors.background.luminance() > 0.5f) colors.surfaceContainerLowest else colors.surfaceContainerHigh
    TextField(
        value = value,
        onValueChange = onValueChange,
        placeholder = { Text(stringResource(R.string.search_hint)) },
        leadingIcon = { Icon(painterResource(R.drawable.ic_search), contentDescription = null, modifier = Modifier.size(22.dp)) },
        trailingIcon = if (value.isNotEmpty()) {
            {
                IconButton(onClick = { onValueChange("") }) {
                    Icon(painterResource(R.drawable.ic_x), stringResource(R.string.cd_clear), modifier = Modifier.size(20.dp))
                }
            }
        } else null,
        singleLine = true,
        textStyle = MaterialTheme.typography.bodyLarge,
        shape = MaterialTheme.shapes.medium,
        interactionSource = interaction,
        colors = TextFieldDefaults.colors(
            focusedContainerColor = fill,
            unfocusedContainerColor = fill,
            focusedIndicatorColor = Color.Transparent,
            unfocusedIndicatorColor = Color.Transparent,
            disabledIndicatorColor = Color.Transparent,
            focusedLeadingIconColor = colors.primary,
            unfocusedLeadingIconColor = colors.onSurfaceVariant,
            focusedPlaceholderColor = colors.onSurfaceVariant,
            unfocusedPlaceholderColor = colors.onSurfaceVariant,
            cursorColor = colors.primary,
        ),
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
        keyboardActions = KeyboardActions(onSearch = { onSearch() }),
        modifier = Modifier
            .fillMaxWidth()
            .heightIn(min = 56.dp)
            .border(
                width = if (focused) 2.dp else 1.dp,
                color = if (focused) colors.primary else colors.outlineVariant,
                shape = MaterialTheme.shapes.medium,
            )
            .semantics { contentDescription = label },
    )
}

/** "Chicago, IL · Libby, Hoopla, BiblioCommons" */
private fun Library.summaryLine(): String =
    listOf(
        listOfNotNull(city, region).joinToString(", "),
        services.map { it.provider.displayName }.distinct().joinToString(", "),
    ).filter { it.isNotEmpty() }.joinToString(" · ")

@Composable
private fun NoLibraries(onAdd: () -> Unit) {
    Column(
        Modifier
            .padding(horizontal = Gutter, vertical = 4.dp)
            .fillMaxWidth()
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, MaterialTheme.shapes.medium)
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(stringResource(R.string.home_no_libraries_title), style = MaterialTheme.typography.titleLarge)
        Text(
            stringResource(R.string.home_no_libraries_body),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Button(onClick = onAdd, shape = ButtonShape, modifier = Modifier.padding(top = 8.dp).heightIn(min = 48.dp)) {
            Icon(painterResource(R.drawable.ic_plus), null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
            Text(stringResource(R.string.libraries_add))
        }
    }
}
