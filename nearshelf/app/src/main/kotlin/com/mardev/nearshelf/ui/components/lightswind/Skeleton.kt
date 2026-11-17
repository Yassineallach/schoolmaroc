package com.mardev.nearshelf.ui.components.lightswind

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.semantics.clearAndSetSemantics
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

/** Lightswind `Skeleton` variants: rounded-md, rounded-full, rounded-xl, rounded-none. */
enum class SkeletonVariant { Default, Circle, Rounded, Square }

/** Lightswind `animation` prop. Wave = the 2 s shimmer sweep (its default). */
enum class SkeletonAnimation { Wave, Pulse, None }

@Composable
fun Skeleton(
    modifier: Modifier = Modifier,
    variant: SkeletonVariant = SkeletonVariant.Default,
    animation: SkeletonAnimation = SkeletonAnimation.Wave,
) {
    val shape = when (variant) {
        SkeletonVariant.Default -> RoundedCornerShape(6.dp)
        SkeletonVariant.Circle -> CircleShape
        SkeletonVariant.Rounded -> RoundedCornerShape(12.dp)
        SkeletonVariant.Square -> RectangleShape
    }
    val reduced = rememberReducedMotion()
    val base = MaterialTheme.colorScheme.surfaceVariant
    // via-white/20 in light mode, via-white/10 in dark, as in the original.
    val sheen = Color.White.copy(alpha = if (isSystemInDarkTheme()) 0.10f else 0.20f)
    val anim = if (reduced) SkeletonAnimation.None else animation

    val transition = rememberInfiniteTransition(label = "skeleton")
    val sweep by transition.animateFloat(
        initialValue = -1f, targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(2000, easing = LinearEasing)),
        label = "sweep",
    )
    val pulse by transition.animateFloat(
        initialValue = 1f, targetValue = 0.5f,
        animationSpec = infiniteRepeatable(tween(1000), RepeatMode.Reverse),
        label = "pulse",
    )

    Box(
        modifier
        .clip(shape)
        .clearAndSetSemantics { }
        .background(if (anim == SkeletonAnimation.Pulse) base.copy(alpha = base.alpha * pulse) else base)
        .let { m ->
            if (anim != SkeletonAnimation.Wave) m else m.drawWithContent {
                drawContent()
                val w = size.width
                val x = sweep * w
                drawRect(Brush.horizontalGradient(listOf(Color.Transparent, sheen, Color.Transparent), startX = x, endX = x + w))
            }
        },
    )
}

/** Lightswind's `count` prop: a column of [count] bars with gap-2. */
@Composable
fun SkeletonLines(count: Int, modifier: Modifier = Modifier, lineHeight: Dp = 14.dp, lastLineFraction: Float = 0.6f) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(8.dp)) {
        repeat(count) { i ->
            Skeleton(
                Modifier.fillMaxWidth(if (i == count - 1 && count > 1) lastLineFraction else 1f).height(lineHeight),
            )
        }
    }
}
