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

// Palette from the ui-ux-pro-max design system for Nearshelf: "book brown +
// page amber" on paper, stone neutrals. Text pairs meet WCAG AA (4.5:1).
internal val Light = lightColorScheme(
    primary = Color(0xFF7C3A10),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFFFDCC2),
    onPrimaryContainer = Color(0xFF2E1500),
    secondary = Color(0xFF57534E),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFE7E5E4),
    onSecondaryContainer = Color(0xFF1C1917),
    tertiary = Color(0xFF92400E),
    onTertiary = Color.White,
    tertiaryContainer = Color(0xFFFEF3C7),
    onTertiaryContainer = Color(0xFF451A03),
    background = Color(0xFFFDFBF7),
    onBackground = Color(0xFF1C1917),
    surface = Color(0xFFFDFBF7),
    onSurface = Color(0xFF1C1917),
    surfaceVariant = Color(0xFFF1ECE4),
    onSurfaceVariant = Color(0xFF57534E),
    surfaceContainerLowest = Color(0xFFFFFFFF),
    surfaceContainerLow = Color(0xFFFAF6EF),
    surfaceContainer = Color(0xFFF5F0E8),
    surfaceContainerHigh = Color(0xFFEFE9E0),
    surfaceContainerHighest = Color(0xFFE9E2D8),
    outline = Color(0xFF8A847E),
    outlineVariant = Color(0xFFE2DCD3),
    error = Color(0xFFB91C1C),
)

internal val Dark = darkColorScheme(
    primary = Color(0xFFFFB68A),
    onPrimary = Color(0xFF4A1F00),
    primaryContainer = Color(0xFF6B2F0B),
    onPrimaryContainer = Color(0xFFFFDCC2),
    secondary = Color(0xFFD6D3D1),
    onSecondary = Color(0xFF292524),
    secondaryContainer = Color(0xFF44403C),
    onSecondaryContainer = Color(0xFFE7E5E4),
    tertiary = Color(0xFFFCD34D),
    onTertiary = Color(0xFF451A03),
    tertiaryContainer = Color(0xFF78350F),
    onTertiaryContainer = Color(0xFFFEF3C7),
    background = Color(0xFF171412),
    onBackground = Color(0xFFEDE7E3),
    surface = Color(0xFF171412),
    onSurface = Color(0xFFEDE7E3),
    surfaceVariant = Color(0xFF2A2522),
    onSurfaceVariant = Color(0xFFC9C1BA),
    surfaceContainerLowest = Color(0xFF110F0D),
    surfaceContainerLow = Color(0xFF1C1916),
    surfaceContainer = Color(0xFF211D1A),
    surfaceContainerHigh = Color(0xFF2B2623),
    surfaceContainerHighest = Color(0xFF36302C),
    outline = Color(0xFF9A928B),
    outlineVariant = Color(0xFF433C37),
    error = Color(0xFFFCA5A5),
)

/** Availability colours, outside Material's roles. */
@Immutable
data class StatusColors(
    val available: Color,
    val onAvailable: Color,
    val waitlist: Color,
    val onWaitlist: Color,
)

private val LightStatus = StatusColors(
    available = Color(0xFF15803D), onAvailable = Color.White,
    waitlist = Color(0xFFB45309), onWaitlist = Color.White,
)
private val DarkStatus = StatusColors(
    available = Color(0xFF86EFAC), onAvailable = Color(0xFF052E16),
    waitlist = Color(0xFFFCD34D), onWaitlist = Color(0xFF451A03),
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
        MaterialTheme(colorScheme = colors, typography = NearshelfTypography, content = content)
    }
}
