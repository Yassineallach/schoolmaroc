package com.mardev.nearshelf.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.unit.dp

/**
 * One corner scale for the whole app: 4 for thumbnails, 8 for small tiles, 12 for
 * fields, buttons and cards. Nothing is a full pill except chips and badges.
 */
val NearshelfShapes = Shapes(
    extraSmall = RoundedCornerShape(4.dp),
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(24.dp),
)

/** Buttons share the field radius instead of Material's default pill. */
val ButtonShape = RoundedCornerShape(12.dp)

/** Standard horizontal gutter for screen content. */
val Gutter = 20.dp
