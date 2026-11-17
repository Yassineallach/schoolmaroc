package com.mardev.nearshelf.ui.components.lightswind

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.tween
import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.TextStyle
import java.text.NumberFormat
import kotlin.math.roundToInt

/** Lightswind `easeOut` = cubic-bezier(0, 0, 0.58, 1). */
private val EaseOut = CubicBezierEasing(0f, 0f, 0.58f, 1f)

/**
 * Lightswind `CountUp`: counts from 0 to [value] once, with the locale's grouping
 * separator. TalkBack only ever reads the final number.
 */
@Composable
fun CountUp(
    value: Int,
    modifier: Modifier = Modifier,
    durationMillis: Int = 700,
    prefix: String = "",
    suffix: String = "",
    style: TextStyle = LocalTextStyle.current,
    color: Color = Color.Unspecified,
) {
    val reduced = rememberReducedMotion()
    val format = remember { NumberFormat.getIntegerInstance() }
    val anim = remember { Animatable(if (reduced) value.toFloat() else 0f) }
    LaunchedEffect(value, reduced) {
        if (reduced) anim.snapTo(value.toFloat()) else anim.animateTo(value.toFloat(), tween(durationMillis, easing = EaseOut))
    }
    val final = prefix + format.format(value) + suffix
    Text(
        text = prefix + format.format(anim.value.roundToInt()) + suffix,
        modifier = modifier.semantics { contentDescription = final },
        style = style,
        color = color,
    )
}
