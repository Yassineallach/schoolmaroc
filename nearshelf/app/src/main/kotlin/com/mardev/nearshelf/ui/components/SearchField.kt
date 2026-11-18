package com.mardev.nearshelf.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.interaction.collectIsFocusedAsState
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.R
import com.mardev.nearshelf.ui.components.lightswind.rememberReducedMotion
import com.mardev.nearshelf.ui.theme.ControlShape
import com.mardev.nearshelf.ui.theme.Space

/**
 * White field on the paper page with a hairline edge. Focus draws a brown edge and
 * colours the search glyph; text gets a Clear action.
 */
@Composable
fun PaperSearchField(
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    label: String,
    modifier: Modifier = Modifier,
    onSearch: () -> Unit = {},
) {
    val interaction = remember { MutableInteractionSource() }
    val focused by interaction.collectIsFocusedAsState()
    val colors = MaterialTheme.colorScheme
    // White paper on the light theme; one step above the page on the dark one (never a hole).
    val fill = if (colors.background.luminance() > 0.5f) colors.surfaceContainerLowest else colors.surfaceContainerHigh
    val reduced = rememberReducedMotion()
    val edge by animateColorAsState(if (focused) colors.primary else colors.outlineVariant, tween(if (reduced) 0 else 150), label = "edge")
    BasicTextField(
        value = value,
        onValueChange = onValueChange,
        singleLine = true,
        textStyle = MaterialTheme.typography.bodyLarge.copy(color = colors.onSurface),
        cursorBrush = SolidColor(colors.primary),
        interactionSource = interaction,
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
        keyboardActions = KeyboardActions(onSearch = { onSearch() }),
        modifier = modifier.fillMaxWidth().semantics { contentDescription = label },
        decorationBox = { inner ->
            Row(
                Modifier
                    .fillMaxWidth()
                    .height(52.dp)
                    .clip(ControlShape)
                    .background(fill)
                    .border(if (focused) 1.5.dp else 1.dp, edge, ControlShape)
                    .padding(start = Space.l, end = Space.xs),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(
                    painterResource(R.drawable.ic_search),
                    contentDescription = null,
                    tint = if (focused) colors.primary else colors.onSurfaceVariant,
                    modifier = Modifier.size(20.dp),
                )
                Spacer(Modifier.width(Space.m))
                Box(Modifier.weight(1f), contentAlignment = Alignment.CenterStart) {
                    if (value.isEmpty()) {
                        Text(
                            placeholder,
                            style = MaterialTheme.typography.bodyLarge,
                            color = colors.onSurfaceVariant,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis,
                        )
                    }
                    inner()
                }
                if (value.isNotEmpty()) {
                    IconButton(onClick = { onValueChange("") }) {
                        Icon(painterResource(R.drawable.ic_x), stringResource(R.string.cd_clear), tint = colors.onSurfaceVariant, modifier = Modifier.size(18.dp))
                    }
                } else {
                    Spacer(Modifier.width(Space.m))
                }
            }
        },
    )
}

/** A footnote to a field: short accent label, then the hint. */
@Composable
fun FieldHint(label: String, body: String, modifier: Modifier = Modifier) {
    val colors = MaterialTheme.colorScheme
    Text(
        buildAnnotatedString {
            withStyle(SpanStyle(color = colors.primary, fontWeight = FontWeight.SemiBold)) { append(label) }
            append("  ")
            append(body)
        },
        style = MaterialTheme.typography.bodySmall,
        color = colors.onSurfaceVariant,
        modifier = modifier,
    )
}
