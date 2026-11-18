package com.mardev.nearshelf.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mardev.nearshelf.ui.theme.Gutter

/**
 * Section title with an optional count and one text action. The action's label lines
 * up with the screen gutter (TextButton carries 12 dp of its own padding).
 */
@Composable
fun SectionHeader(title: String, modifier: Modifier = Modifier, count: Int? = null, action: String? = null, onAction: () -> Unit = {}) {
    Row(
        modifier.fillMaxWidth().heightIn(min = 48.dp).padding(start = Gutter, end = Gutter - 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(title, style = MaterialTheme.typography.titleLarge, modifier = Modifier.semantics { heading() })
        if (count != null) {
            Spacer(Modifier.width(8.dp))
            Text(count.toString(), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        Spacer(Modifier.weight(1f))
        if (action != null) {
            TextButton(onClick = onAction, contentPadding = PaddingValues(horizontal = 12.dp)) { Text(action, style = MaterialTheme.typography.labelLarge) }
        }
    }
}

/** Width of a row's leading slot; dividers are inset to the text column. */
val RowLeadingWidth: Dp = 40.dp
private val RowLeadingGap: Dp = 16.dp

/**
 * The one list row used across Home: leading visual, a title, up to two lines of
 * metadata, optional trailing content. 72 dp minimum, gutter-aligned.
 */
@Composable
fun ListRow(
    title: String,
    meta: String?,
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    onClickLabel: String? = null,
    leading: @Composable () -> Unit,
    trailing: @Composable RowScope.() -> Unit = {},
) {
    Row(
        modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable(onClickLabel = onClickLabel, role = Role.Button, onClick = onClick) else Modifier)
            .heightIn(min = 72.dp)
            .padding(start = Gutter, end = Gutter, top = 12.dp, bottom = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.width(RowLeadingWidth), contentAlignment = Alignment.CenterStart) { leading() }
        Spacer(Modifier.width(RowLeadingGap))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(2.dp)) {
            Text(title, style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurface, maxLines = 2, overflow = TextOverflow.Ellipsis)
            if (!meta.isNullOrEmpty()) {
                Text(meta, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, maxLines = 2, overflow = TextOverflow.Ellipsis)
            }
        }
        trailing()
    }
}

/** Hairline between rows, starting under the text column. */
@Composable
fun RowDivider() = HorizontalDivider(
    Modifier.padding(start = Gutter + RowLeadingWidth + RowLeadingGap, end = Gutter),
    color = MaterialTheme.colorScheme.outlineVariant,
)

/** A library's initial set in the serif, on a quiet tile: identifies it at a glance. */
@Composable
fun Monogram(name: String, modifier: Modifier = Modifier) {
    val letter = name.split(' ').firstOrNull { it.isNotBlank() && !it.equals("The", ignoreCase = true) }
        ?.firstOrNull { it.isLetterOrDigit() }?.uppercaseChar() ?: '·'
    Box(
        modifier.size(RowLeadingWidth).clip(MaterialTheme.shapes.small).background(MaterialTheme.colorScheme.surfaceContainer),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            letter.toString(),
            style = com.mardev.nearshelf.ui.theme.MonogramStyle,
            color = MaterialTheme.colorScheme.primary,
        )
    }
}

/** Small book cover for a row; a quiet placeholder spine when there is none. */
@Composable
fun CoverThumb(url: String?, modifier: Modifier = Modifier, title: String? = null, width: Dp = 34.dp, height: Dp = 48.dp) {
    Box(
        modifier.size(width = width, height = height).clip(MaterialTheme.shapes.extraSmall).background(MaterialTheme.colorScheme.surfaceContainer),
        contentAlignment = Alignment.Center,
    ) {
        if (url != null) {
            coil3.compose.AsyncImage(
                model = url,
                contentDescription = null,
                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                modifier = Modifier.matchParentSize(),
            )
        } else if (title != null && width >= 56.dp) {
            // No cover: a plain cloth binding with the title's initial and a short rule.
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(
                    title.firstOrNull { it.isLetterOrDigit() }?.uppercase() ?: "",
                    style = com.mardev.nearshelf.ui.theme.CoverInitial,
                    color = MaterialTheme.colorScheme.primary,
                )
                Box(Modifier.padding(top = 6.dp).size(width = 16.dp, height = 1.dp).background(MaterialTheme.colorScheme.secondary))
            }
        } else {
            androidx.compose.material3.Icon(
                androidx.compose.ui.res.painterResource(com.mardev.nearshelf.R.drawable.ic_books),
                contentDescription = null,
                tint = MaterialTheme.colorScheme.secondary,
                modifier = Modifier.size(18.dp),
            )
        }
    }
}
