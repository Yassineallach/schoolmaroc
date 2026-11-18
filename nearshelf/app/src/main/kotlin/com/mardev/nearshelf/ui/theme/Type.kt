package com.mardev.nearshelf.ui.theme

import androidx.compose.material3.Typography
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.sp
import com.mardev.nearshelf.R

/*
 * Two families, each with one job (both OFL, bundled, variable):
 *
 * - Newsreader, an editorial serif drawn for reading on screens: the wordmark,
 *   headlines, section titles, book titles and headline numbers. Its optical-size
 *   axis is set per role, so big text gets finer contrast and small text sturdier
 *   strokes.
 * - Instrument Sans, a compact modern grotesque: everything you read in passing or
 *   tap: rows, metadata, tags, buttons, navigation.
 *
 * Scale (size/line height, sp): 36/44, 30/36, 26/32, 22/28, 20/26 serif;
 * 16/22, 14/20 titles; 16/24, 14/20, 12/16 body; 14/20, 12/16, 11/16 labels.
 */
private fun newsreader(weight: Int, opticalSize: Float) = Font(
    R.font.newsreader,
    weight = FontWeight(weight),
    variationSettings = FontVariation.Settings(FontVariation.weight(weight), FontVariation.Setting("opsz", opticalSize)),
)

private fun instrumentSans(weight: Int) = Font(
    R.font.instrument_sans,
    weight = FontWeight(weight),
    variationSettings = FontVariation.Settings(FontVariation.weight(weight), FontVariation.Setting("wdth", 100f)),
)

/** Serif tuned for display sizes (24 sp and up). */
val SerifDisplay = FontFamily(newsreader(400, 36f), newsreader(500, 36f), newsreader(600, 36f))

/** Serif tuned for title sizes (16–22 sp). */
val SerifText = FontFamily(newsreader(400, 16f), newsreader(500, 16f), newsreader(600, 16f))

val Sans = FontFamily(instrumentSans(400), instrumentSans(500), instrumentSans(600), instrumentSans(700))

private fun style(family: FontFamily, weight: Int, size: Int, line: Int, tracking: TextUnit = 0.sp) = TextStyle(
    fontFamily = family,
    fontWeight = FontWeight(weight),
    fontSize = size.sp,
    lineHeight = line.sp,
    letterSpacing = tracking,
)

val NearshelfTypography = Typography(
    displayLarge = style(SerifDisplay, 500, 48, 56, (-0.5).sp),
    displayMedium = style(SerifDisplay, 500, 40, 48, (-0.4).sp),
    displaySmall = style(SerifDisplay, 500, 36, 44, (-0.3).sp),
    headlineLarge = style(SerifDisplay, 500, 30, 36, (-0.3).sp),
    headlineMedium = style(SerifDisplay, 500, 26, 32, (-0.2).sp),
    headlineSmall = style(SerifDisplay, 500, 24, 30, (-0.2).sp),
    titleLarge = style(SerifText, 600, 20, 26, (-0.1).sp),
    titleMedium = style(Sans, 600, 16, 22),
    titleSmall = style(Sans, 600, 14, 20, 0.1.sp),
    bodyLarge = style(Sans, 400, 16, 24),
    bodyMedium = style(Sans, 400, 14, 20, 0.1.sp),
    bodySmall = style(Sans, 400, 12, 16, 0.2.sp),
    labelLarge = style(Sans, 600, 14, 20, 0.1.sp),
    labelMedium = style(Sans, 600, 12, 16, 0.2.sp),
    labelSmall = style(Sans, 600, 11, 16, 0.4.sp),
)

/** The wordmark: the serif at title size, a touch tighter. */
val Wordmark = style(SerifDisplay, 600, 24, 28, (-0.4).sp)

/** Book titles in lists and shelves: the serif at reading size. */
val BookTitleSmall = style(SerifText, 600, 15, 19)

/** Library monogram initial (40 dp tile). */
val MonogramStyle = style(SerifDisplay, 500, 22, 22)

/** Initial on a cover placeholder ("cloth binding"). */
val CoverInitial = style(SerifDisplay, 500, 30, 34)

/** Service tags: label size at medium weight, so a row of tags stays quiet. */
val TagLabel = style(Sans, 500, 12, 16, 0.2.sp)

/** Book titles as row headings (watchlist, results header). */
val BookTitle = style(SerifText, 600, 17, 22)
