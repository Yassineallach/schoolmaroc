package com.mardev.nearshelf.ui.components

import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.wrapContentWidth
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Keeps lists and text at a readable width on landscape phones and tablets, centred,
 * instead of stretching numbers far away from the rows they belong to.
 */
fun Modifier.readableWidth(): Modifier = wrapContentWidth(Alignment.CenterHorizontally).widthIn(max = 640.dp)
