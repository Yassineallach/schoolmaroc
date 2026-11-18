package com.mardev.nearshelf.ui.components

import androidx.annotation.DrawableRes
import androidx.compose.foundation.layout.size
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.R

/**
 * The app's filter chip: hairline and transparent when off; the accent's tint with a
 * tick when on. 8 dp corners like other small tiles.
 */
@Composable
fun NearshelfChip(label: String, selected: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier, @DrawableRes icon: Int? = null) {
    val colors = MaterialTheme.colorScheme
    FilterChip(
        selected = selected,
        onClick = onClick,
        label = { Text(label, style = MaterialTheme.typography.labelLarge) },
        leadingIcon = when {
            selected -> { { Icon(painterResource(R.drawable.ic_check), null, modifier = Modifier.size(16.dp)) } }
            icon != null -> { { Icon(painterResource(icon), null, modifier = Modifier.size(16.dp)) } }
            else -> null
        },
        shape = MaterialTheme.shapes.small,
        colors = FilterChipDefaults.filterChipColors(
            containerColor = Color.Transparent,
            labelColor = colors.onSurface,
            iconColor = colors.secondary,
            selectedContainerColor = colors.primaryContainer,
            selectedLabelColor = colors.onPrimaryContainer,
            selectedLeadingIconColor = colors.onPrimaryContainer,
        ),
        border = FilterChipDefaults.filterChipBorder(
            enabled = true,
            selected = selected,
            borderColor = colors.outlineVariant,
            selectedBorderColor = colors.primaryContainer,
        ),
        modifier = modifier,
    )
}
