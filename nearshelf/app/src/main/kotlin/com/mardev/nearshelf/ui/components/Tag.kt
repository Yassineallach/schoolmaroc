package com.mardev.nearshelf.ui.components

import androidx.annotation.DrawableRes
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp

/**
 * Compact metadata label. [filled] tags (subtle surface) mark digital services;
 * outlined ones mark the physical catalog, so the two read apart at a glance.
 */
@Composable
fun Tag(text: String, @DrawableRes icon: Int, modifier: Modifier = Modifier, filled: Boolean = true) {
    val colors = MaterialTheme.colorScheme
    val shape = MaterialTheme.shapes.extraSmall
    Row(
        modifier
            .clip(shape)
            .then(if (filled) Modifier.background(colors.surfaceContainer) else Modifier.border(1.dp, colors.outlineVariant, shape))
            .heightIn(min = 24.dp)
            .padding(horizontal = 7.dp, vertical = 3.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(5.dp),
    ) {
        Icon(painterResource(icon), contentDescription = null, tint = colors.secondary, modifier = Modifier.size(13.dp))
        Text(text, style = com.mardev.nearshelf.ui.theme.TagLabel, color = colors.onSurface, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}
