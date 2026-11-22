package com.mardev.nearshelf.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.ui.components.lightswind.Skeleton
import com.mardev.nearshelf.ui.components.lightswind.SkeletonVariant
import com.mardev.nearshelf.ui.theme.Gutter
import com.mardev.nearshelf.ui.theme.Space

/**
 * One library, the same everywhere: identity (monogram + name), location, then its
 * services as tags (a reader icon for digital lending, a row of books for the catalog).
 * [footer] adds per-screen controls under the tags; [trailing] sits on the right.
 */
@OptIn(ExperimentalLayoutApi::class)
@Composable
fun LibraryRow(
    library: Library,
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null,
    onClickLabel: String? = null,
    role: Role = Role.Button,
    inset: androidx.compose.ui.unit.Dp = Gutter,
    trailing: @Composable RowScope.() -> Unit = {},
    footer: @Composable ColumnScope.() -> Unit = {},
) {
    val colors = MaterialTheme.colorScheme
    Row(
        modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable(onClickLabel = onClickLabel, role = role, onClick = onClick) else Modifier)
            .padding(start = inset, end = inset - Space.xs, top = Space.l, bottom = Space.l),
        verticalAlignment = Alignment.Top,
    ) {
        Monogram(library.name)
        Spacer(Modifier.width(Space.l))
        Column(Modifier.weight(1f)) {
            Text(library.name, style = com.mardev.nearshelf.ui.theme.LibraryName, color = colors.onSurface, maxLines = 3, overflow = TextOverflow.Ellipsis)
            val place = listOfNotNull(library.city, library.region).joinToString(", ")
            if (place.isNotEmpty()) {
                Row(Modifier.padding(top = 2.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(painterResource(R.drawable.ic_map_pin), contentDescription = null, tint = colors.onSurfaceVariant, modifier = Modifier.size(15.dp))
                    Spacer(Modifier.width(6.dp))
                    Text(place, style = MaterialTheme.typography.bodyMedium, color = colors.onSurfaceVariant, maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
            }
            val (digital, physical) = remember(library) {
                library.digitalServices.map { it.provider.displayName }.distinct() to
                    library.physicalServices.map { it.provider.displayName }.distinct()
            }
            if (digital.isNotEmpty() || physical.isNotEmpty()) {
                FlowRow(
                    Modifier.padding(top = Space.m),
                    horizontalArrangement = Arrangement.spacedBy(Space.s),
                    verticalArrangement = Arrangement.spacedBy(Space.s),
                ) {
                    digital.forEach { Tag(it, R.drawable.ic_ebook) }
                    physical.forEach { Tag(it, R.drawable.ic_books) }
                }
            }
            footer()
        }
        trailing()
    }
}

/** Right-hand "opens something" affordance for a row: an oxblood caret level with the title. */
@Composable
fun RowChevron() = Icon(
    painterResource(R.drawable.ic_caret_right),
    contentDescription = null,
    tint = MaterialTheme.colorScheme.primary,
    modifier = Modifier.padding(start = Space.s, top = 14.dp).size(20.dp),
)

/** Placeholder with the same proportions as [LibraryRow]. */
@Composable
fun LibraryRowSkeleton(inset: androidx.compose.ui.unit.Dp = Gutter) {
    Row(Modifier.fillMaxWidth().padding(horizontal = inset, vertical = Space.l)) {
        Skeleton(Modifier.size(MonogramSize), variant = SkeletonVariant.Rounded)
        Spacer(Modifier.width(Space.l))
        Column(Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(Space.s)) {
            Skeleton(Modifier.fillMaxWidth(0.7f).height(16.dp))
            Skeleton(Modifier.fillMaxWidth(0.4f).height(12.dp))
            Skeleton(Modifier.fillMaxWidth(0.55f).height(22.dp))
        }
    }
}
