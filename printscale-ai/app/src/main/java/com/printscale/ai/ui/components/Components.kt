package com.printscale.ai.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.Info
import androidx.compose.material.icons.outlined.WarningAmber
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.printscale.ai.ui.theme.LocalExtras
import com.printscale.ai.ui.theme.Numeric

/** Printer's crop marks just outside each corner: the app's recurring frame motif. */
fun Modifier.cropMarks(color: Color, length: Dp = 14.dp, gap: Dp = 5.dp, stroke: Dp = 1.5.dp): Modifier =
    drawWithContent {
        drawContent()
        drawCropMarks(color, length.toPx(), gap.toPx(), stroke.toPx(), 0f, 0f, size.width, size.height)
    }

fun DrawScope.drawCropMarks(color: Color, len: Float, gap: Float, stroke: Float, l: Float, t: Float, r: Float, b: Float) {
    fun line(x1: Float, y1: Float, x2: Float, y2: Float) =
        drawLine(color, Offset(x1, y1), Offset(x2, y2), stroke, cap = StrokeCap.Square)
    // horizontal ticks
    line(l - gap - len, t, l - gap, t); line(r + gap, t, r + gap + len, t)
    line(l - gap - len, b, l - gap, b); line(r + gap, b, r + gap + len, b)
    // vertical ticks
    line(l, t - gap - len, l, t - gap); line(r, t - gap - len, r, t - gap)
    line(l, b + gap, l, b + gap + len); line(r, b + gap, r, b + gap + len)
}

/** Brand mark: crop marks around the vermilion proof square. */
@Composable
fun BrandMark(size: Dp = 28.dp) {
    val accent = MaterialTheme.colorScheme.primary
    val ink = MaterialTheme.colorScheme.onBackground
    Canvas(Modifier.size(size)) {
        val s = this.size.width
        val sq = s * 0.34f
        val o = (s - sq) / 2
        drawRect(accent, Offset(o, o), androidx.compose.ui.geometry.Size(sq, sq))
        val inset = s * 0.12f
        val len = s * 0.16f
        val st = s * 0.07f
        fun corner(x: Float, y: Float, dx: Float, dy: Float) {
            drawLine(ink, Offset(x, y), Offset(x + dx * len, y), st, StrokeCap.Square)
            drawLine(ink, Offset(x, y), Offset(x, y + dy * len), st, StrokeCap.Square)
        }
        corner(inset, inset, 1f, 1f); corner(s - inset, inset, -1f, 1f)
        corner(inset, s - inset, 1f, -1f); corner(s - inset, s - inset, -1f, -1f)
    }
}

@Composable
fun SectionLabel(text: String, modifier: Modifier = Modifier, trailing: @Composable (() -> Unit)? = null) {
    Row(modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Text(text, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
        trailing?.invoke()
    }
}

@Composable
fun PrimaryButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true, icon: ImageVector? = null) {
    Button(
        onClick = onClick, enabled = enabled, modifier = modifier.heightIn(min = 52.dp),
        shape = MaterialTheme.shapes.medium,
        colors = ButtonDefaults.buttonColors(),
    ) {
        if (icon != null) {
            Icon(icon, contentDescription = null, modifier = Modifier.size(20.dp))
            Spacer(Modifier.width(10.dp))
        }
        Text(text, style = MaterialTheme.typography.labelLarge, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

@Composable
fun SecondaryButton(text: String, onClick: () -> Unit, modifier: Modifier = Modifier, enabled: Boolean = true, icon: ImageVector? = null) {
    OutlinedButton(
        onClick = onClick, enabled = enabled, modifier = modifier.heightIn(min = 48.dp),
        shape = MaterialTheme.shapes.medium,
    ) {
        if (icon != null) {
            Icon(icon, contentDescription = null, modifier = Modifier.size(18.dp))
            Spacer(Modifier.width(8.dp))
        }
        Text(text, style = MaterialTheme.typography.labelLarge, maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

@Composable
fun StatRow(label: String, value: String, modifier: Modifier = Modifier) {
    Row(modifier.fillMaxWidth().padding(vertical = 7.dp), verticalAlignment = Alignment.Top) {
        Text(label, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
            modifier = Modifier.width(132.dp))
        Text(value, style = MaterialTheme.typography.bodyMedium.merge(Numeric), fontWeight = FontWeight.Medium,
            modifier = Modifier.weight(1f))
    }
}

enum class NoteTone { INFO, WARNING, ERROR }

@Composable
fun Note(text: String, tone: NoteTone = NoteTone.INFO, modifier: Modifier = Modifier) {
    val c = MaterialTheme.colorScheme
    val (icon, tint) = when (tone) {
        NoteTone.INFO -> Icons.Outlined.Info to c.onSurfaceVariant
        NoteTone.WARNING -> Icons.Outlined.WarningAmber to LocalExtras.current.warning
        NoteTone.ERROR -> Icons.Outlined.ErrorOutline to c.error
    }
    Row(modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Icon(icon, contentDescription = null, tint = tint, modifier = Modifier.size(18.dp).padding(top = 1.dp))
        Text(text, style = MaterialTheme.typography.bodySmall,
            color = if (tone == NoteTone.ERROR) c.error else c.onSurfaceVariant)
    }
}

@Composable
fun Panel(modifier: Modifier = Modifier, content: @Composable () -> Unit) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        color = MaterialTheme.colorScheme.surfaceContainer,
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
    ) {
        Column(Modifier.padding(16.dp)) { content() }
    }
}

@Composable
fun EmptyState(title: String, body: String, modifier: Modifier = Modifier, action: @Composable (() -> Unit)? = null) {
    Column(modifier.fillMaxWidth().padding(vertical = 28.dp, horizontal = 8.dp), horizontalAlignment = Alignment.CenterHorizontally) {
        Box(Modifier.size(56.dp).padding(8.dp).cropMarks(MaterialTheme.colorScheme.outline, length = 8.dp, gap = 3.dp))
        Spacer(Modifier.height(16.dp))
        Text(title, style = MaterialTheme.typography.headlineSmall)
        Spacer(Modifier.height(6.dp))
        Text(body, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = androidx.compose.ui.text.style.TextAlign.Center)
        if (action != null) { Spacer(Modifier.height(16.dp)); action() }
    }
}

fun formatBytes(b: Long): String = when {
    b >= 1L shl 30 -> String.format("%.1f GB", b / (1L shl 30).toDouble())
    b >= 1L shl 20 -> String.format("%.1f MB", b / (1L shl 20).toDouble())
    b >= 1L shl 10 -> String.format("%.0f KB", b / 1024.0)
    else -> "$b B"
}

fun formatPx(w: Int, h: Int) = "$w × $h px"

fun formatDuration(ms: Long): String {
    val s = (ms / 1000).coerceAtLeast(0)
    return when {
        s < 60 -> "${s}s"
        s < 3600 -> "${s / 60} min ${s % 60}s"
        else -> "${s / 3600} h ${(s % 3600) / 60} min"
    }
}

val ChipShape = RoundedCornerShape(8.dp)
