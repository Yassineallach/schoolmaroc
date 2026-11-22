package com.printscale.ai.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.ColorScheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.ExperimentalTextApi
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontVariation
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.printscale.ai.R
import com.printscale.ai.data.ThemeChoice

// Palette: charcoal and paper neutrals, one vermilion accent taken from printers' proof marks.
private val Charcoal = Color(0xFF121110)
private val CharcoalRaised = Color(0xFF1B1A18)
private val CharcoalHigh = Color(0xFF252320)
private val CharcoalHighest = Color(0xFF2F2C29)
private val Ivory = Color(0xFFF2EEE6)
private val IvoryMuted = Color(0xFFB8B1A6)
private val LineDark = Color(0xFF3D3A35)
private val Vermilion = Color(0xFFEA6440)
private val InkOnVermilion = Color(0xFF1A0F0B)

private val Paper = Color(0xFFF6F3EE)
private val PaperRaised = Color(0xFFFFFFFF)
private val PaperHigh = Color(0xFFEEEAE3)
private val PaperHighest = Color(0xFFE6E1D9)
private val Ink = Color(0xFF1A1816)
private val InkMuted = Color(0xFF5C564E)
private val LineLight = Color(0xFFD3CCC1)
private val VermilionDeep = Color(0xFFB0381A)

private val DarkScheme = darkColorScheme(
    primary = Vermilion, onPrimary = InkOnVermilion,
    primaryContainer = Color(0xFF3A1E15), onPrimaryContainer = Color(0xFFFFD9CD),
    secondary = Ivory, onSecondary = Charcoal,
    secondaryContainer = CharcoalHighest, onSecondaryContainer = Ivory,
    tertiary = IvoryMuted, onTertiary = Charcoal,
    background = Charcoal, onBackground = Ivory,
    surface = Charcoal, onSurface = Ivory,
    surfaceVariant = CharcoalHigh, onSurfaceVariant = IvoryMuted,
    surfaceContainerLowest = Color(0xFF0C0B0A), surfaceContainerLow = CharcoalRaised,
    surfaceContainer = CharcoalRaised, surfaceContainerHigh = CharcoalHigh, surfaceContainerHighest = CharcoalHighest,
    outline = LineDark, outlineVariant = Color(0xFF2C2A26),
    error = Color(0xFFFF8A80), onError = Color(0xFF2B0000),
    errorContainer = Color(0xFF3B1714), onErrorContainer = Color(0xFFFFDAD5),
    inverseSurface = Ivory, inverseOnSurface = Charcoal, inversePrimary = VermilionDeep,
)

private val LightScheme = lightColorScheme(
    primary = VermilionDeep, onPrimary = Color.White,
    primaryContainer = Color(0xFFFFDBCF), onPrimaryContainer = Color(0xFF3A0B00),
    secondary = Ink, onSecondary = Paper,
    secondaryContainer = PaperHighest, onSecondaryContainer = Ink,
    tertiary = InkMuted, onTertiary = Paper,
    background = Paper, onBackground = Ink,
    surface = Paper, onSurface = Ink,
    surfaceVariant = PaperHigh, onSurfaceVariant = InkMuted,
    surfaceContainerLowest = Color.White, surfaceContainerLow = PaperRaised,
    surfaceContainer = PaperRaised, surfaceContainerHigh = PaperHigh, surfaceContainerHighest = PaperHighest,
    outline = LineLight, outlineVariant = Color(0xFFE2DCD2),
    error = Color(0xFFB3261E), onError = Color.White,
    errorContainer = Color(0xFFF9DEDC), onErrorContainer = Color(0xFF410E0B),
    inverseSurface = Ink, inverseOnSurface = Paper, inversePrimary = Vermilion,
)

@OptIn(ExperimentalTextApi::class)
private fun manrope(weight: Int) = Font(
    R.font.manrope, FontWeight(weight), variationSettings = FontVariation.Settings(FontVariation.weight(weight)),
)

@OptIn(ExperimentalTextApi::class)
val Manrope = FontFamily(manrope(400), manrope(500), manrope(600), manrope(700))

/** Display serif: used for titles and the big resolution numbers only. */
val CatalogSerif = FontFamily(Font(R.font.instrument_serif))

private val AppTypography = Typography(
    displayLarge = TextStyle(fontFamily = CatalogSerif, fontSize = 46.sp, lineHeight = 50.sp, letterSpacing = (-0.5).sp),
    displayMedium = TextStyle(fontFamily = CatalogSerif, fontSize = 38.sp, lineHeight = 42.sp),
    displaySmall = TextStyle(fontFamily = CatalogSerif, fontSize = 32.sp, lineHeight = 36.sp),
    headlineLarge = TextStyle(fontFamily = CatalogSerif, fontSize = 30.sp, lineHeight = 34.sp),
    headlineMedium = TextStyle(fontFamily = CatalogSerif, fontSize = 26.sp, lineHeight = 30.sp),
    headlineSmall = TextStyle(fontFamily = CatalogSerif, fontSize = 22.sp, lineHeight = 26.sp),
    titleLarge = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.SemiBold, fontSize = 19.sp, lineHeight = 24.sp),
    titleMedium = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.SemiBold, fontSize = 16.sp, lineHeight = 22.sp),
    titleSmall = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, lineHeight = 20.sp),
    bodyLarge = TextStyle(fontFamily = Manrope, fontSize = 16.sp, lineHeight = 24.sp),
    bodyMedium = TextStyle(fontFamily = Manrope, fontSize = 14.sp, lineHeight = 21.sp),
    bodySmall = TextStyle(fontFamily = Manrope, fontSize = 12.5.sp, lineHeight = 18.sp),
    labelLarge = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.SemiBold, fontSize = 15.sp, lineHeight = 20.sp),
    labelMedium = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.Medium, fontSize = 13.sp, lineHeight = 18.sp),
    labelSmall = TextStyle(fontFamily = Manrope, fontWeight = FontWeight.Medium, fontSize = 11.5.sp, lineHeight = 16.sp),
)

private val AppShapes = Shapes(
    extraSmall = RoundedCornerShape(6.dp),
    small = RoundedCornerShape(8.dp),
    medium = RoundedCornerShape(10.dp),
    large = RoundedCornerShape(14.dp),
    extraLarge = RoundedCornerShape(18.dp),
)

/** Tabular figures so columns of pixel sizes line up. */
val Numeric = TextStyle(fontFeatureSettings = "tnum")

@Immutable
data class Extras(val isDark: Boolean, val checker: Color, val warning: Color)

val LocalExtras = staticCompositionLocalOf { Extras(true, Color(0xFF2A2825), Color(0xFFE8B45A)) }

@Composable
fun PrintScaleTheme(choice: ThemeChoice, content: @Composable () -> Unit) {
    val dark = when (choice) {
        ThemeChoice.SYSTEM -> isSystemInDarkTheme()
        ThemeChoice.DARK -> true
        ThemeChoice.LIGHT -> false
    }
    val scheme: ColorScheme = if (dark) DarkScheme else LightScheme
    val extras = if (dark) Extras(true, Color(0xFF2A2825), Color(0xFFE8B45A)) else Extras(false, Color(0xFFE4DFD7), Color(0xFF8A5A00))
    androidx.compose.runtime.CompositionLocalProvider(LocalExtras provides extras) {
        MaterialTheme(colorScheme = scheme, typography = AppTypography, shapes = AppShapes) {
            // Screens without a Scaffold or Surface still get readable text in both themes.
            androidx.compose.runtime.CompositionLocalProvider(
                androidx.compose.material3.LocalContentColor provides scheme.onBackground,
                content = content,
            )
        }
    }
}
