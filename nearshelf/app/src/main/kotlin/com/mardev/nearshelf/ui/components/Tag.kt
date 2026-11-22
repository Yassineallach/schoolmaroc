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
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.luminance
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp

/**
 * A service label: a soft tan pill, lifted a hair off the card. The icon tells
 * digital lending (reader) from the physical catalog (books). [filled] = false
 * draws an outlined tag for quieter contexts.
 */
@Composable
fun Tag(text: String, @DrawableRes icon: Int, modifier: Modifier = Modifier, filled: Boolean = true) {
    val colors = MaterialTheme.colorScheme
    val shape = RoundedCornerShape(10.dp)
    Row(
        modifier
            .then(if (filled) Modifier.shadow(1.dp, shape, ambientColor = colors.secondary, spotColor = colors.secondary) else Modifier)
            .clip(shape)
            .then(if (filled) Modifier.background(if (colors.background.luminance() > 0.5f) colors.surfaceContainer else colors.surfaceContainerHighest) else Modifier.border(1.dp, colors.outlineVariant, shape))
            .heightIn(min = 30.dp)
            .padding(horizontal = 10.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
    ) {
        Icon(painterResource(icon), contentDescription = null, tint = colors.onSurface, modifier = Modifier.size(16.dp))
        Text(text, style = com.mardev.nearshelf.ui.theme.TagLabel, color = colors.onSurface, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}
