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
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.mardev.nearshelf.ui.components.lightswind.rememberReducedMotion

data class NavDestinationItem(@StringRes val label: Int, @DrawableRes val icon: Int, @DrawableRes val selectedIcon: Int)

/**
 * The app's bottom navigation: 64 dp on the page's own paper, a hairline above it,
 * and a short accent rule over the selected tab instead of a large pill. The
 * selected tab's icon takes the accent colour and its label turns semibold.
 */
@Composable
fun NearshelfNavBar(items: List<NavDestinationItem>, selectedIndex: Int, onSelect: (Int) -> Unit) {
    val colors = MaterialTheme.colorScheme
    val reduced = rememberReducedMotion()
    Column(Modifier.fillMaxWidth().background(colors.background)) {
        HorizontalDivider(color = colors.outlineVariant)
        Row(
            Modifier.fillMaxWidth().navigationBarsPadding().selectableGroup(),
            horizontalArrangement = Arrangement.SpaceEvenly,
        ) {
            items.forEachIndexed { i, t ->
                val selected = i == selectedIndex
                val tint by animateColorAsState(if (selected) colors.primary else colors.onSurfaceVariant, androidx.compose.animation.core.tween(if (reduced) 0 else 200), label = "tint")
                val rule by animateDpAsState(if (selected) 24.dp else 0.dp, label = "rule", animationSpec = androidx.compose.animation.core.tween(if (reduced) 0 else 200))
                Box(
                    Modifier
                        .weight(1f)
                        .heightIn(min = 64.dp)
                        .selectable(selected = selected, role = Role.Tab, onClick = { onSelect(i) }),
                    contentAlignment = Alignment.Center,
                ) {
                    Box(
                        Modifier.align(Alignment.TopCenter).width(rule).height(2.dp)
                            .clip(RoundedCornerShape(bottomStart = 2.dp, bottomEnd = 2.dp)).background(colors.primary),
                    )
                    Column(Modifier.padding(vertical = 10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                        // One stroke weight in both states; colour, label weight and the rule mark selection.
                        Icon(painterResource(t.icon), contentDescription = null, tint = tint, modifier = Modifier.size(24.dp))
                        Spacer(Modifier.height(4.dp))
                        Text(
                            stringResource(t.label),
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = if (selected) FontWeight.SemiBold else FontWeight.Medium,
                            color = if (selected) colors.onSurface else colors.onSurfaceVariant,
                        )
                    }
                }
            }
        }
    }
}
