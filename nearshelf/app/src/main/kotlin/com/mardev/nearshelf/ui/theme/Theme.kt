package com.mardev.nearshelf.ui.theme

import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.dynamicDarkColorScheme
import androidx.compose.material3.dynamicLightColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext

// Fallback palette for devices without dynamic color (< Android 12):
// library green with a warm paper background.
private val Light = lightColorScheme(
    primary = Color(0xFF1F4E3D),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFCDE8DA),
    onPrimaryContainer = Color(0xFF062016),
    secondary = Color(0xFF8A5A12),
    secondaryContainer = Color(0xFFFFDDB0),
    background = Color(0xFFFBF7F0),
    surface = Color(0xFFFBF7F0),
)

private val Dark = darkColorScheme(
    primary = Color(0xFF9FD3BB),
    onPrimary = Color(0xFF00382A),
    primaryContainer = Color(0xFF1F4E3D),
    onPrimaryContainer = Color(0xFFCDE8DA),
    secondary = Color(0xFFF1BE6E),
    secondaryContainer = Color(0xFF6A4400),
    background = Color(0xFF15130F),
    surface = Color(0xFF15130F),
)

@Composable
fun NearshelfTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
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
    MaterialTheme(colorScheme = colors, content = content)
}
