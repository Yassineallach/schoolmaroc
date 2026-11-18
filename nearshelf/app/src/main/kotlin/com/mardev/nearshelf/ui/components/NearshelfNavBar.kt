package com.mardev.nearshelf.ui.components

import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.size
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource

data class NavDestinationItem(@StringRes val label: Int, @DrawableRes val icon: Int, @DrawableRes val selectedIcon: Int)

/** The app's bottom navigation, separate from the nav graph so it can be rendered in tests. */
@Composable
fun NearshelfNavBar(items: List<NavDestinationItem>, selectedIndex: Int, onSelect: (Int) -> Unit) {
    val colors = MaterialTheme.colorScheme
    // Same paper as the screen, separated by a hairline instead of a grey slab.
    Column {
        HorizontalDivider(color = colors.outlineVariant)
        NavigationBar(containerColor = colors.background, tonalElevation = 0.dp) {
            items.forEachIndexed { i, t ->
                val selected = i == selectedIndex
                NavigationBarItem(
                    selected = selected,
                    onClick = { onSelect(i) },
                    icon = { Icon(painterResource(if (selected) t.selectedIcon else t.icon), contentDescription = null, modifier = Modifier.size(24.dp)) },
                    label = { Text(stringResource(t.label), style = MaterialTheme.typography.labelMedium) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = colors.primary,
                        selectedTextColor = colors.onSurface,
                        indicatorColor = colors.surfaceContainerHigh,
                        unselectedIconColor = colors.onSurfaceVariant,
                        unselectedTextColor = colors.onSurfaceVariant,
                    ),
                )
            }
        }
    }
}
