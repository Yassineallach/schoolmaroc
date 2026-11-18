package com.mardev.nearshelf.ui.components.lightswind

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.ui.theme.LocalStatusColors

/** Lightswind `badgeVariants.variant`. */
enum class BadgeVariant { Default, Secondary, Destructive, Outline, Success, Warning, Info }
enum class BadgeSize { Sm, Default, Lg }
enum class BadgeShape { Pill, Square, Rounded }

@Composable
fun Badge(
    text: String,
    modifier: Modifier = Modifier,
    variant: BadgeVariant = BadgeVariant.Default,
    size: BadgeSize = BadgeSize.Default,
    shape: BadgeShape = BadgeShape.Rounded,
    leading: (@Composable () -> Unit)? = null,
) {
    val scheme = MaterialTheme.colorScheme
    val status = LocalStatusColors.current
    val (bg, fg) = when (variant) {
        BadgeVariant.Default -> scheme.primary to scheme.onPrimary
        BadgeVariant.Secondary -> scheme.surfaceContainer to scheme.onSurfaceVariant
        BadgeVariant.Destructive -> scheme.error to scheme.onError
        BadgeVariant.Outline -> Color.Transparent to scheme.onSurface
        // Nearshelf: status reads as a tinted label, not a saturated sticker.
        BadgeVariant.Success -> status.availableContainer to status.onAvailableContainer
        BadgeVariant.Warning -> status.waitlistContainer to status.onWaitlistContainer
        BadgeVariant.Info -> scheme.surfaceContainer to scheme.onSurface
    }
    val padding = when (size) {
        BadgeSize.Sm -> PaddingValues(horizontal = 7.dp, vertical = 3.dp)
        BadgeSize.Default -> PaddingValues(horizontal = 10.dp, vertical = 2.dp)
        BadgeSize.Lg -> PaddingValues(horizontal = 12.dp, vertical = 4.dp)
    }
    val textStyle = if (size == BadgeSize.Lg) MaterialTheme.typography.labelLarge else MaterialTheme.typography.labelMedium
    Surface(
        modifier = modifier,
        shape = when (shape) {
            BadgeShape.Pill -> CircleShape
            BadgeShape.Square -> RoundedCornerShape(2.dp)
            BadgeShape.Rounded -> RoundedCornerShape(4.dp)
        },
        color = bg,
        contentColor = fg,
        border = if (variant == BadgeVariant.Outline) BorderStroke(1.dp, scheme.outlineVariant) else null,
    ) {
        Row(Modifier.padding(padding), verticalAlignment = Alignment.CenterVertically) {
            leading?.invoke()
            Text(text, style = textStyle, fontWeight = FontWeight.SemiBold)
        }
    }
}
