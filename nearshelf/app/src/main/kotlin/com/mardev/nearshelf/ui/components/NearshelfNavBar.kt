package com.mardev.nearshelf.ui.components

import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.luminance
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.widthIn
import com.mardev.nearshelf.ui.theme.Space
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.ui.components.lightswind.rememberReducedMotion

data class NavDestinationItem(@StringRes val label: Int, @DrawableRes val icon: Int, @DrawableRes val selectedIcon: Int)

/**
 * The app's bottom navigation: a floating cream card with a soft shadow, hairlines
 * between tabs, and the selected tab in oxblood with a short rule under its label.
 */
@Composable
fun NearshelfNavBar(items: List<NavDestinationItem>, selectedIndex: Int, onSelect: (Int) -> Unit) {
    val colors = MaterialTheme.colorScheme
    val reduced = rememberReducedMotion()
    val shape = RoundedCornerShape(28.dp)
    val light = colors.background.luminance() > 0.5f
    Box(
        Modifier.fillMaxWidth().navigationBarsPadding().padding(start = Space.l, end = Space.l, top = Space.s, bottom = Space.m),
        contentAlignment = Alignment.Center,
    ) {
        Row(
            Modifier
                .widthIn(max = 560.dp)
                .fillMaxWidth()
                .shadow(10.dp, shape, ambientColor = colors.primary.copy(alpha = 0.35f), spotColor = colors.primary.copy(alpha = 0.35f))
                .clip(shape)
                .background(if (light) colors.surfaceContainerLowest else colors.surfaceContainerHigh)
                .border(1.dp, colors.outlineVariant.copy(alpha = 0.6f), shape)
                .selectableGroup(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            items.forEachIndexed { i, t ->
                if (i > 0) Box(Modifier.width(1.dp).height(36.dp).background(colors.outlineVariant))
                val selected = i == selectedIndex
                val tint by animateColorAsState(if (selected) colors.primary else colors.onSurfaceVariant, androidx.compose.animation.core.tween(if (reduced) 0 else 200), label = "tint")
                val rule by animateDpAsState(if (selected) 36.dp else 0.dp, label = "rule", animationSpec = androidx.compose.animation.core.tween(if (reduced) 0 else 200))
                Column(
                    Modifier
                        .weight(1f)
                        .heightIn(min = 72.dp)
                        .selectable(selected = selected, role = Role.Tab, onClick = { onSelect(i) })
                        .padding(top = 12.dp, bottom = 8.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Icon(painterResource(t.icon), contentDescription = null, tint = tint, modifier = Modifier.size(26.dp))
                    Spacer(Modifier.height(4.dp))
                    Text(
                        stringResource(t.label),
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                        color = tint,
                        maxLines = 1,
                    )
                    Spacer(Modifier.height(6.dp))
                    Box(Modifier.width(rule).height(3.dp).clip(RoundedCornerShape(2.dp)).background(colors.primary))
                }
            }
        }
    }
}
