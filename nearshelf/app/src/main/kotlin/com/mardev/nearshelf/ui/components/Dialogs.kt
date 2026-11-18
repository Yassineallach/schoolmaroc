package com.mardev.nearshelf.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.toggleable
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.ui.theme.Space

/**
 * The app's pop-up: page-coloured (one step lighter at night), 16 dp corners, serif
 * title, a text action, and optionally a second one on the left (e.g. Clear).
 */
@Composable
fun NearshelfDialog(
    title: String,
    confirm: String,
    onDismiss: () -> Unit,
    body: String? = null,
    secondary: String? = null,
    onSecondary: () -> Unit = {},
    onConfirm: () -> Unit = onDismiss,
    confirmEnabled: Boolean = true,
    content: @Composable () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        confirmButton = { TextButton(onClick = onConfirm, enabled = confirmEnabled) { Text(confirm, style = MaterialTheme.typography.labelLarge) } },
        dismissButton = secondary?.let {
            { TextButton(onClick = onSecondary) { Text(it, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.onSurfaceVariant) } }
        },
        title = { Text(title, style = MaterialTheme.typography.titleLarge) },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(Space.m)) {
                body?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant) }
                content()
            }
        },
        containerColor = MaterialTheme.colorScheme.run { if (background.luminance() > 0.5f) background else surfaceContainerHigh },
        titleContentColor = MaterialTheme.colorScheme.onSurface,
        textContentColor = MaterialTheme.colorScheme.onSurface,
        shape = MaterialTheme.shapes.large,
        tonalElevation = 0.dp,
    )
}

/** A choice inside a pop-up: the whole row toggles (radio or checkbox), 48 dp tall. */
@Composable
fun ChoiceRow(
    label: String,
    checked: Boolean,
    role: Role,
    onClick: () -> Unit,
    supporting: String? = null,
    control: @Composable () -> Unit,
) {
    Row(
        Modifier.fillMaxWidth().heightIn(min = 48.dp).clip(MaterialTheme.shapes.small)
            .then(
                if (role == Role.RadioButton) Modifier.selectable(selected = checked, role = role, onClick = onClick)
                else Modifier.toggleable(value = checked, role = role, onValueChange = { onClick() }),
            )
            .padding(horizontal = Space.xs, vertical = Space.xs),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        control()
        Column(Modifier.padding(start = Space.m)) {
            Text(label, style = MaterialTheme.typography.bodyLarge)
            supporting?.let { Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant) }
        }
    }
}
