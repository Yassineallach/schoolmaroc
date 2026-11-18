package com.mardev.nearshelf

import android.content.Intent
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
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.mardev.nearshelf.nav.AddLibraryRoute
import com.mardev.nearshelf.nav.HomeRoute
import com.mardev.nearshelf.nav.LibrariesRoute
import com.mardev.nearshelf.nav.ResultsRoute
import com.mardev.nearshelf.nav.ScannerRoute
import com.mardev.nearshelf.nav.WatchlistRoute
import com.mardev.nearshelf.nav.HistoryRoute
import com.mardev.nearshelf.nav.PreferencesRoute
import com.mardev.nearshelf.ui.history.HistoryScreen
import com.mardev.nearshelf.ui.prefs.PreferencesScreen
import com.mardev.nearshelf.ui.watchlist.WatchlistScreen
import com.mardev.nearshelf.ui.home.HomeScreen
import com.mardev.nearshelf.ui.libraries.AddLibraryScreen
import com.mardev.nearshelf.ui.libraries.LibrariesScreen
import com.mardev.nearshelf.ui.results.ResultsScreen
import com.mardev.nearshelf.ui.scanner.ScannerScreen
import com.mardev.nearshelf.ui.theme.NearshelfTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    /** Text from the share sheet, consumed once by the nav host. */
    private val pendingShare = mutableStateOf<String?>(null)

    /** A watchlist notification's book, consumed once by the nav host. */
    private val pendingWatch = mutableStateOf<String?>(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        enableEdgeToEdge()
        super.onCreate(savedInstanceState)
        if (savedInstanceState == null) {
            pendingShare.value = intent.sharedText()
            pendingWatch.value = intent.getStringExtra(EXTRA_WATCH_KEY)
        }
        setContent {
            NearshelfTheme {
                NearshelfRoot(
                    pendingShare = pendingShare.value,
                    onShareConsumed = { pendingShare.value = null },
                    pendingWatch = pendingWatch.value,
                    onWatchConsumed = { pendingWatch.value = null },
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        intent.sharedText()?.let { pendingShare.value = it }
        intent.getStringExtra(EXTRA_WATCH_KEY)?.let { pendingWatch.value = it }
    }

    companion object {
        const val EXTRA_WATCH_KEY = "com.mardev.nearshelf.WATCH_KEY"
    }

    private fun Intent.sharedText(): String? =
        if (action == Intent.ACTION_SEND && type == "text/plain") {
            listOfNotNull(getStringExtra(Intent.EXTRA_SUBJECT), getStringExtra(Intent.EXTRA_TEXT))
                .distinct().joinToString(" ").trim().takeIf { it.isNotEmpty() }?.take(2_000)
        } else {
            null
        }
}

private const val PREFILL_KEY = "prefill"

/** Returns to Search with the box pre-filled, e.g. after a share Nearshelf couldn't read. */
private fun backToHomeWith(nav: NavHostController, text: String) {
    nav.popBackStack(HomeRoute, inclusive = false)
    nav.currentBackStackEntry?.savedStateHandle?.set(PREFILL_KEY, text)
}

private data class TopLevel(val route: Any, @StringRes val label: Int, @DrawableRes val icon: Int, @DrawableRes val selectedIcon: Int)

private val topLevel = listOf(
    TopLevel(HomeRoute, R.string.nav_search, R.drawable.ic_search, R.drawable.ic_search_fill),
    TopLevel(WatchlistRoute, R.string.nav_watchlist, R.drawable.ic_watchlist, R.drawable.ic_watchlist_fill),
    TopLevel(LibrariesRoute, R.string.nav_libraries, R.drawable.ic_library, R.drawable.ic_library_fill),
)

@Composable
private fun NearshelfRoot(pendingShare: String?, onShareConsumed: () -> Unit, pendingWatch: String?, onWatchConsumed: () -> Unit) {
    val nav = rememberNavController()
    LaunchedEffect(pendingWatch) {
        if (pendingWatch != null) {
            nav.navigate(ResultsRoute(watchKey = pendingWatch))
            onWatchConsumed()
        }
    }
    LaunchedEffect(pendingShare) {
        if (pendingShare != null) {
            nav.navigate(ResultsRoute(shared = pendingShare)) { launchSingleTop = false }
            onShareConsumed()
        }
    }
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
            composable<HomeRoute> { entry ->
                val prefill = entry.savedStateHandle.get<String>(PREFILL_KEY)
                HomeScreen(
                    prefill = prefill,
                    onPrefillConsumed = { entry.savedStateHandle.remove<String>(PREFILL_KEY) },
                    onScan = { nav.navigate(ScannerRoute) },
                    onSearch = { q -> nav.navigate(ResultsRoute(q.title, q.author, q.isbn)) },
                    onManageLibraries = {
                        nav.navigate(LibrariesRoute) {
                            popUpTo(nav.graph.findStartDestination().id) { saveState = true }
                            launchSingleTop = true
                        }
                    },
                    onAddLibrary = { nav.navigate(AddLibraryRoute) },
                    onOpenHistory = { h ->
                        if (h == null) nav.navigate(HistoryRoute)
                        else nav.navigate(ResultsRoute(queryJson = kotlinx.serialization.json.Json.encodeToString(h.query)))
                    },
                    onPreferences = { nav.navigate(PreferencesRoute) },
                )
            }
            composable<HistoryRoute> {
                HistoryScreen(
                    onBack = { nav.popBackStack() },
                    onOpen = { h -> nav.navigate(ResultsRoute(queryJson = kotlinx.serialization.json.Json.encodeToString(h.query))) },
                )
            }
            composable<PreferencesRoute> { PreferencesScreen(onBack = { nav.popBackStack() }) }
            composable<WatchlistRoute> {
                WatchlistScreen(
                    onOpen = { item -> nav.navigate(ResultsRoute(watchKey = item.key)) },
                    onSearch = { nav.navigate(HomeRoute) { popUpTo(nav.graph.findStartDestination().id); launchSingleTop = true } },
                )
            }
            composable<LibrariesRoute> { LibrariesScreen(onAddLibrary = { nav.navigate(AddLibraryRoute) }) }
            composable<AddLibraryRoute> { AddLibraryScreen(onBack = { nav.popBackStack() }) }
            composable<ResultsRoute> {
                ResultsScreen(
                    onBack = { nav.popBackStack() },
                    onAddLibrary = { nav.navigate(AddLibraryRoute) },
                    onSearchManually = { text -> backToHomeWith(nav, text) },
                    onPreferences = { nav.navigate(PreferencesRoute) },
                )
            }
            composable<ScannerRoute> {
                ScannerScreen(
                    onBack = { nav.popBackStack() },
                    onIsbn = { isbn ->
                        nav.navigate(ResultsRoute(isbn = isbn)) { popUpTo<ScannerRoute> { inclusive = true } }
                    },
                    onTypeInstead = { nav.popBackStack() },
                )
            }
        }
    }
}
