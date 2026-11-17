package com.mardev.nearshelf.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.mardev.nearshelf.R

/**
 * Cormorant Garamond (OFL, variable weight) for display text and book titles, as
 * the ui-ux-pro-max "library / scholarly" pairing suggests. Body and UI text keep
 * the system sans for legibility at small sizes and for Arabic.
 */
private fun cormorant(weight: Int) = Font(
    R.font.cormorant_garamond,
    weight = FontWeight(weight),
    variationSettings = FontVariation.Settings(FontVariation.weight(weight)),
)

val Serif = FontFamily(cormorant(500), cormorant(600), cormorant(700))

private val base = Typography()

private fun TextStyle.serif(weight: Int, size: Int, line: Int) =
    copy(fontFamily = Serif, fontWeight = FontWeight(weight), fontSize = size.sp, lineHeight = line.sp, letterSpacing = 0.sp)

val NearshelfTypography = base.copy(
    displayLarge = base.displayLarge.serif(600, 57, 64),
    displayMedium = base.displayMedium.serif(600, 45, 52),
    displaySmall = base.displaySmall.serif(600, 38, 44),
    headlineLarge = base.headlineLarge.serif(600, 34, 40),
    headlineMedium = base.headlineMedium.serif(600, 30, 36),
    headlineSmall = base.headlineSmall.serif(700, 26, 32),
    titleLarge = base.titleLarge.serif(700, 24, 30),
)
