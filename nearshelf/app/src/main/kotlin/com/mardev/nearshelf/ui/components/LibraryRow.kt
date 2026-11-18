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
 * services as tags: filled for digital lending, outlined for the physical catalog.
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
    trailing: @Composable RowScope.() -> Unit = {},
    footer: @Composable ColumnScope.() -> Unit = {},
) {
    val colors = MaterialTheme.colorScheme
    Row(
        modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable(onClickLabel = onClickLabel, role = role, onClick = onClick) else Modifier)
            .padding(start = Gutter, end = Gutter - Space.xs, top = Space.l, bottom = Space.l),
        verticalAlignment = Alignment.Top,
    ) {
        Monogram(library.name)
        Spacer(Modifier.width(Space.l))
        Column(Modifier.weight(1f)) {
            Text(library.name, style = MaterialTheme.typography.titleMedium, color = colors.onSurface, maxLines = 3, overflow = TextOverflow.Ellipsis)
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
            footer()
        }
        trailing()
    }
}

/** Right-hand "opens something" affordance for a row. */
@Composable
fun RowChevron() = Icon(
    painterResource(R.drawable.ic_caret_right),
    contentDescription = null,
    tint = MaterialTheme.colorScheme.outline,
    modifier = Modifier.padding(start = Space.s, top = 10.dp).size(18.dp),
)

/** Placeholder with the same proportions as [LibraryRow]. */
@Composable
fun LibraryRowSkeleton() {
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
