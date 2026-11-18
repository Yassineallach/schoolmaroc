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

// Nearshelf palette: warm paper, ink, and one leather-brown accent.
//   page #FAF9F6 · ink #292722 · secondary ink #6F6B64 (the brief's #77736D, one step
//   darker so it passes 4.5:1 on every surface) · accent #75452D · secondary accent
//   #A77A57 (icons and indicators only: 3.6:1, not for text) · subtle #F1EEE8 ·
//   hairline #E6E1D9 · white #FFFFFF.
internal val Light = lightColorScheme(
    primary = Color(0xFF75452D),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFF1E5DB),
    onPrimaryContainer = Color(0xFF3A2010),
    secondary = Color(0xFFA77A57),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFF1EEE8),
    onSecondaryContainer = Color(0xFF292722),
    tertiary = Color(0xFF75452D),
    onTertiary = Color.White,
    tertiaryContainer = Color(0xFFF1EEE8),
    onTertiaryContainer = Color(0xFF292722),
    background = Color(0xFFFAF9F6),
    onBackground = Color(0xFF292722),
    surface = Color(0xFFFAF9F6),
    onSurface = Color(0xFF292722),
    surfaceVariant = Color(0xFFF1EEE8),
    onSurfaceVariant = Color(0xFF6F6B64),
    surfaceContainerLowest = Color(0xFFFFFFFF),
    surfaceContainerLow = Color(0xFFF6F4F0),
    surfaceContainer = Color(0xFFF1EEE8),
    surfaceContainerHigh = Color(0xFFECE8E1),
    surfaceContainerHighest = Color(0xFFE6E1D9),
    outline = Color(0xFF8F8A82),
    outlineVariant = Color(0xFFE6E1D9),
    error = Color(0xFFB3261E),
)

// The same roles at night: lamp-lit brown on warm black.
internal val Dark = darkColorScheme(
    primary = Color(0xFFD9A784),
    onPrimary = Color(0xFF2B1A10),
    primaryContainer = Color(0xFF4A2E1E),
    onPrimaryContainer = Color(0xFFF3DCCB),
    secondary = Color(0xFFC49A76),
    onSecondary = Color(0xFF2B1A10),
    secondaryContainer = Color(0xFF2A2622),
    onSecondaryContainer = Color(0xFFEDE8E1),
    tertiary = Color(0xFFD9A784),
    onTertiary = Color(0xFF2B1A10),
    tertiaryContainer = Color(0xFF2A2622),
    onTertiaryContainer = Color(0xFFEDE8E1),
    background = Color(0xFF161412),
    onBackground = Color(0xFFEDE8E1),
    surface = Color(0xFF161412),
    onSurface = Color(0xFFEDE8E1),
    surfaceVariant = Color(0xFF2A2622),
    onSurfaceVariant = Color(0xFFA9A39B),
    surfaceContainerLowest = Color(0xFF110F0E),
    surfaceContainerLow = Color(0xFF1B1917),
    surfaceContainer = Color(0xFF211E1B),
    surfaceContainerHigh = Color(0xFF2A2622),
    surfaceContainerHighest = Color(0xFF34302B),
    outline = Color(0xFF7D776F),
    outlineVariant = Color(0xFF35312C),
    error = Color(0xFFF2B8B5),
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
        MaterialTheme(colorScheme = colors, typography = NearshelfTypography, shapes = NearshelfShapes, content = content)
    }
}
