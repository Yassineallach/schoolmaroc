package com.mardev.nearshelf

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.mardev.nearshelf.nav.AddLibraryRoute
import com.mardev.nearshelf.nav.HomeRoute
import com.mardev.nearshelf.nav.LibrariesRoute
import com.mardev.nearshelf.nav.ResultsRoute
import com.mardev.nearshelf.ui.home.HomeScreen
import com.mardev.nearshelf.ui.libraries.AddLibraryScreen
import com.mardev.nearshelf.ui.libraries.LibrariesScreen
import com.mardev.nearshelf.ui.results.ResultsScreen
import com.mardev.nearshelf.ui.theme.NearshelfTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        setContent { NearshelfTheme { NearshelfRoot() } }
    }
}

private data class TopLevel(val route: Any, @StringRes val label: Int, @DrawableRes val icon: Int, @DrawableRes val selectedIcon: Int)

private val topLevel = listOf(
    TopLevel(HomeRoute, R.string.nav_search, R.drawable.ic_search, R.drawable.ic_search_fill),
    TopLevel(LibrariesRoute, R.string.nav_libraries, R.drawable.ic_library, R.drawable.ic_library_fill),
)

@Composable
private fun NearshelfRoot() {
    val nav = rememberNavController()
    val entry by nav.currentBackStackEntryAsState()
    val dest = entry?.destination
    val showBar = dest == null || topLevel.any { t -> dest.hasRoute(t.route::class) }

    Scaffold(
        bottomBar = {
            if (showBar) NavigationBar {
                topLevel.forEach { t ->
                    val selected = dest?.hasRoute(t.route::class) == true
                    NavigationBarItem(
                        selected = selected,
                        onClick = {
                            nav.navigate(t.route) {
                                popUpTo(nav.graph.findStartDestination().id) { saveState = true }
                                launchSingleTop = true
                                restoreState = true
                            }
                        },
                        icon = { Icon(painterResource(if (selected) t.selectedIcon else t.icon), contentDescription = null) },
                        label = { Text(stringResource(t.label)) },
                    )
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = nav,
            startDestination = HomeRoute,
            modifier = Modifier.padding(bottom = padding.calculateBottomPadding()).consumeWindowInsets(padding),
        ) {
            composable<HomeRoute> {
                HomeScreen(
                    onSearch = { q -> nav.navigate(ResultsRoute(q.title, q.author, q.isbn)) },
                    onManageLibraries = {
                        nav.navigate(LibrariesRoute) {
                            popUpTo(nav.graph.findStartDestination().id) { saveState = true }
                            launchSingleTop = true
                        }
                    },
                    onAddLibrary = { nav.navigate(AddLibraryRoute) },
                )
            }
            composable<LibrariesRoute> { LibrariesScreen(onAddLibrary = { nav.navigate(AddLibraryRoute) }) }
            composable<AddLibraryRoute> { AddLibraryScreen(onBack = { nav.popBackStack() }) }
            composable<ResultsRoute> {
                ResultsScreen(onBack = { nav.popBackStack() }, onAddLibrary = { nav.navigate(AddLibraryRoute) })
            }
        }
    }
}
