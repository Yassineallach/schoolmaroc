package com.mardev.nearshelf.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.unit.dp

/** White paper on the light theme, one step above the page at night. */
@Composable
fun cardColor(): Color {
    val c = MaterialTheme.colorScheme
    return if (c.background.luminance() > 0.5f) c.surfaceContainerLowest else c.surfaceContainer
}

/** The app's card: 16 dp corners, card colour, hairline edge. Apply before clickable/padding. */
@Composable
fun Modifier.nearshelfCard(): Modifier {
    val shape = MaterialTheme.shapes.large
    return this.clip(shape).background(cardColor()).border(1.dp, MaterialTheme.colorScheme.outlineVariant, shape)
}

/** Status label: a dot and a short word on its tint (Available, Waitlist, On shelf…). */
@Composable
fun StatusPill(text: String, bg: Color, fg: Color, modifier: Modifier = Modifier) {
    Row(
        modifier.clip(CircleShape).background(bg).padding(horizontal = 10.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(Modifier.size(7.dp).clip(CircleShape).background(fg))
        Spacer(Modifier.width(6.dp))
        Text(text, style = MaterialTheme.typography.labelLarge, color = fg, maxLines = 1)
    }
}
