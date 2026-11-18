package com.mardev.nearshelf.ui.theme

import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Shapes
import androidx.compose.ui.unit.dp

/**
 * One corner scale: 4 for covers and tags, 8 for tiles, 10 for controls (fields and
 * buttons), 12 for cards. Nothing is a full pill.
 */
val NearshelfShapes = Shapes(
    extraSmall = RoundedCornerShape(4.dp),
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(12.dp),
    large = RoundedCornerShape(16.dp),
    extraLarge = RoundedCornerShape(24.dp),
)

/** Fields and buttons. */
val ControlShape = RoundedCornerShape(10.dp)

/** Buttons share the field radius instead of Material's default pill. */
val ButtonShape = ControlShape

/** Spacing scale (4 dp grid) and the screen gutter. */
object Space {
    val xs = 4.dp
    val s = 8.dp
    val m = 12.dp
    val l = 16.dp
    val xl = 24.dp
    val xxl = 32.dp
}

val Gutter = 20.dp
