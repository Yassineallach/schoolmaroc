package com.mardev.nearshelf.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

// Nearshelf palette: warm cream paper, ink, and one oxblood accent (the "library binding").
//   page #F9F0E3 · cards #FFFAF3 · tint #F3E5D2 (tags, badges) · hairline #E8DCCB ·
//   ink #231915 · secondary ink #5E534A (≥ 6:1 on every surface) · accent #5C1220 ·
//   secondary accent #8C5E45 (icons and indicators only).
internal val Light = lightColorScheme(
    primary = Color(0xFF5C1220),
    onPrimary = Color(0xFFFFFAF3),
    primaryContainer = Color(0xFFF3E1DA),
    onPrimaryContainer = Color(0xFF3A0A12),
    secondary = Color(0xFF8C5E45),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFF3E5D2),
    onSecondaryContainer = Color(0xFF231915),
    tertiary = Color(0xFF5C1220),
    onTertiary = Color.White,
    tertiaryContainer = Color(0xFFF3E5D2),
    onTertiaryContainer = Color(0xFF231915),
    background = Color(0xFFF9F0E3),
    onBackground = Color(0xFF231915),
    surface = Color(0xFFF9F0E3),
    onSurface = Color(0xFF231915),
    surfaceVariant = Color(0xFFF3E5D2),
    onSurfaceVariant = Color(0xFF5E534A),
    surfaceContainerLowest = Color(0xFFFFFAF3),
    surfaceContainerLow = Color(0xFFFCF5EB),
    surfaceContainer = Color(0xFFF3E5D2),
    surfaceContainerHigh = Color(0xFFEEDDC6),
    surfaceContainerHighest = Color(0xFFE8D5BB),
    outline = Color(0xFF8A7D70),
    outlineVariant = Color(0xFFE8DCCB),
    error = Color(0xFFB3261E),
)

// The same roles at night: rose-lit oxblood on warm black.
internal val Dark = darkColorScheme(
    primary = Color(0xFFEBB0AE),
    onPrimary = Color(0xFF3E0A12),
    primaryContainer = Color(0xFF4A1820),
    onPrimaryContainer = Color(0xFFF7DADA),
    secondary = Color(0xFFC9A086),
    onSecondary = Color(0xFF2B1A10),
    secondaryContainer = Color(0xFF2C2622),
    onSecondaryContainer = Color(0xFFF0E8DF),
    tertiary = Color(0xFFEBB0AE),
    onTertiary = Color(0xFF3E0A12),
    tertiaryContainer = Color(0xFF2C2622),
    onTertiaryContainer = Color(0xFFF0E8DF),
    background = Color(0xFF171311),
    onBackground = Color(0xFFF0E8DF),
    surface = Color(0xFF171311),
    onSurface = Color(0xFFF0E8DF),
    surfaceVariant = Color(0xFF2C2622),
    onSurfaceVariant = Color(0xFFADA49B),
    surfaceContainerLowest = Color(0xFF120F0D),
    surfaceContainerLow = Color(0xFF1C1816),
    surfaceContainer = Color(0xFF231E1B),
    surfaceContainerHigh = Color(0xFF2C2622),
    surfaceContainerHighest = Color(0xFF36302B),
    outline = Color(0xFF80776F),
    outlineVariant = Color(0xFF38312C),
    error = Color(0xFFF2B8B5),
)

/** Ink on a white control over the camera preview, where the theme's onSurface may be light. */
val InkOnWhite = Color(0xFF231915)

/** Availability colours, outside Material's roles. */
@Immutable
data class StatusColors(
    val available: Color,
    val onAvailable: Color,
    val waitlist: Color,
    val onWaitlist: Color,
    /** Tinted badge backgrounds and their text (≥5:1). */
    val availableContainer: Color,
    val onAvailableContainer: Color,
    val waitlistContainer: Color,
    val onWaitlistContainer: Color,
)

private val LightStatus = StatusColors(
    available = Color(0xFF1E7A43), onAvailable = Color.White,
    waitlist = Color(0xFF9A5514), onWaitlist = Color.White,
    availableContainer = Color(0xFFE4EFE6), onAvailableContainer = Color(0xFF1E6B3A),
    waitlistContainer = Color(0xFFF6E9DA), onWaitlistContainer = Color(0xFF8A4B12),
)
private val DarkStatus = StatusColors(
    available = Color(0xFF9FD8B0), onAvailable = Color(0xFF0B2414),
    waitlist = Color(0xFFF0C48E), onWaitlist = Color(0xFF2E1B08),
    availableContainer = Color(0xFF1E2B22), onAvailableContainer = Color(0xFF9FD8B0),
    waitlistContainer = Color(0xFF33271B), onWaitlistContainer = Color(0xFFF0C48E),
)

val LocalStatusColors = staticCompositionLocalOf { LightStatus }

/**
 * Brand palette by default. Wallpaper-based dynamic color is supported and will be
 * a user setting (milestone 10); availability colours stay fixed either way.
 */
@Composable
fun NearshelfTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit,
) {
    val colors = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val ctx = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(ctx) else dynamicLightColorScheme(ctx)
        }
        darkTheme -> Dark
        else -> Light
    }
    CompositionLocalProvider(LocalStatusColors provides if (darkTheme) DarkStatus else LightStatus) {
        MaterialTheme(colorScheme = colors, typography = NearshelfTypography, shapes = NearshelfShapes, content = content)
    }
}
