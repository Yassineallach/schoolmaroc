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

/**
 * Two voices, each with one job:
 * - Serif (Cormorant Garamond): editorial moments only: the wordmark, headlines, book
 *   titles and headline numbers.
 * - Sans (the system's Roboto): everything you read or tap: section titles, rows,
 *   metadata, buttons. Tracking is tightened from Material's defaults so text sets
 *   like print rather than spread out.
 */
val NearshelfTypography = base.copy(
    displayLarge = base.displayLarge.serif(600, 57, 64),
    displayMedium = base.displayMedium.serif(600, 45, 52),
    displaySmall = base.displaySmall.serif(600, 36, 44),
    headlineLarge = base.headlineLarge.serif(600, 34, 40),
    headlineMedium = base.headlineMedium.serif(600, 30, 36),
    headlineSmall = base.headlineSmall.serif(600, 26, 32),
    titleLarge = base.titleLarge.serif(600, 23, 28),
    titleMedium = base.titleMedium.copy(fontWeight = FontWeight.SemiBold, letterSpacing = 0.sp),
    titleSmall = base.titleSmall.copy(fontWeight = FontWeight.SemiBold, letterSpacing = 0.1.sp),
    bodyLarge = base.bodyLarge.copy(letterSpacing = 0.15.sp),
    bodyMedium = base.bodyMedium.copy(letterSpacing = 0.1.sp),
    bodySmall = base.bodySmall.copy(letterSpacing = 0.2.sp),
    labelLarge = base.labelLarge.copy(fontWeight = FontWeight.SemiBold, letterSpacing = 0.1.sp),
)
