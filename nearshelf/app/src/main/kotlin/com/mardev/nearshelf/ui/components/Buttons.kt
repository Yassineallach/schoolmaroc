package com.mardev.nearshelf.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.material3.ButtonColors
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp

/** Hairline edge for secondary (outlined) buttons: the same line as dividers and fields. */
@Composable
fun hairline() = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)

/** Outlined buttons in ink rather than accent, so the accent stays for the primary action. */
@Composable
fun quietOutlinedColors(): ButtonColors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.onSurface)

/** Tonal action in the accent's tint (e.g. "Borrow in Libby"): clearly actionable, lighter than primary. */
@Composable
fun accentTonalColors(): ButtonColors = ButtonDefaults.filledTonalButtonColors(
    containerColor = MaterialTheme.colorScheme.primaryContainer,
    contentColor = MaterialTheme.colorScheme.onPrimaryContainer,
)
