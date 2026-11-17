package com.mardev.nearshelf.ui.components.lightswind

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.ProgressBarRangeInfo
import androidx.compose.ui.semantics.progressBarRangeInfo
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/**
 * Lightswind `TopLoader` in controlled mode (`progress` prop): a thin glowing bar
 * at the top of the screen that eases to [progress] and fades out at 1.
 */
@Composable
fun TopLoader(
    progress: Float,
    modifier: Modifier = Modifier,
    height: Dp = 3.dp,
    color: Color = MaterialTheme.colorScheme.primary,
    speedMillis: Int = 200,
) {
    val reduced = rememberReducedMotion()
    val shown by animateFloatAsState(progress.coerceIn(0f, 1f), tween(if (reduced) 0 else speedMillis), label = "toploader")
    AnimatedVisibility(visible = progress < 1f, exit = fadeOut(tween(if (reduced) 0 else 400)), modifier = modifier) {
        Box(
            Modifier.fillMaxWidth().height(height)
                .semantics { progressBarRangeInfo = ProgressBarRangeInfo(shown, 0f..1f) },
        ) {
            Box(
                Modifier.fillMaxHeight().fillMaxWidth(shown)
                    .shadow(6.dp, ambientColor = color, spotColor = color)
                    .background(color),
            )
        }
    }
}
