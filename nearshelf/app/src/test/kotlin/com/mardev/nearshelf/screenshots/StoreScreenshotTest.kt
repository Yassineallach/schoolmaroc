package com.mardev.nearshelf.screenshots

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onRoot
import com.github.takahirom.roborazzi.captureRoboImage
import com.github.takahirom.roborazzi.captureScreenRoboImage
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.geo.LatLng
import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.metadata.WorkCandidate
import com.mardev.nearshelf.core.metadata.WorkInfo
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Branch
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.prefs.ReadingPrefs
import com.mardev.nearshelf.core.search.ServiceState
import com.mardev.nearshelf.core.watch.LibrarySnapshot
import com.mardev.nearshelf.core.watch.WatchScope
import com.mardev.nearshelf.core.watch.WatchSnapshot
import com.mardev.nearshelf.data.HistoryItem
import com.mardev.nearshelf.data.WatchItem
import com.mardev.nearshelf.ui.components.NavDestinationItem
import com.mardev.nearshelf.ui.components.NearshelfNavBar
import com.mardev.nearshelf.ui.home.HomeContent
import com.mardev.nearshelf.ui.libraries.LibrariesContent
import com.mardev.nearshelf.ui.results.LibraryResult
import com.mardev.nearshelf.ui.results.Phase
import com.mardev.nearshelf.ui.results.ResultsContent
import com.mardev.nearshelf.ui.results.ResultsUiState
import com.mardev.nearshelf.ui.results.ServiceResult
import com.mardev.nearshelf.ui.theme.NearshelfTheme
import com.mardev.nearshelf.ui.watchlist.WatchlistContent
import org.junit.Assume.assumeTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import org.robolectric.shadows.ShadowLog

/**
 * Raw screens for the Play Store listing: fictional libraries, public-domain books, no
 * ad cards (Play doesn't allow test ads in store images). Only runs with
 * -Pnearshelf.store=true; tools/store/make_store_images.py frames the PNGs with captions.
 */
@RunWith(RobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [35], application = android.app.Application::class)
class StoreScreenshotTest {

    @get:Rule val compose = createComposeRule()

    @Before fun onlyWhenAsked() = assumeTrue(System.getProperty("nearshelf.store") == "true")

    private fun shot(name: String, dark: Boolean = false, dialog: Boolean = false, content: @Composable () -> Unit) {
        org.robolectric.RuntimeEnvironment.setQualifiers(if (dark) "w411dp-h800dp-night-xxhdpi" else "w411dp-h800dp-xxhdpi")
        ShadowLog.stream = null
        compose.setContent { NearshelfTheme(darkTheme = dark) { content() } }
        compose.waitForIdle()
        val path = "build/outputs/store/raw/$name.png"
        if (dialog) captureScreenRoboImage(path) else compose.onRoot().captureRoboImage(path)
    }

    private val noAd: @Composable (Modifier) -> Unit = {}

    // --- Demo data: fictional libraries, public-domain books ---

    private val rivLibby = LibraryRef(ProviderId.OVERDRIVE, "riverside", "Riverside Public Library")
    private val rivHoopla = LibraryRef(ProviderId.HOOPLA, "riverside", "Riverside Public Library", borrowLimitPerMonth = 6)
    private val rivCat = LibraryRef(ProviderId.BIBLIOCOMMONS, "riverside", "Riverside Public Library", catalogUrl = "https://example.org")
    private val mapLibby = LibraryRef(ProviderId.OVERDRIVE, "maple", "Maple County Library")
    private val mapCat = LibraryRef(ProviderId.POLARIS, "maple", "Maple County Library", catalogUrl = "https://example.org")
    private val harHoopla = LibraryRef(ProviderId.HOOPLA, "harbor", "Harbor City Library", borrowLimitPerMonth = 4)

    private val riverside = Library(
        "riverside", "Riverside Public Library", "Riverside", "CA", "US", listOf(rivLibby, rivHoopla, rivCat),
        homeBranchId = "central", branches = listOf(Branch("central", "Central Library", latitude = 33.981, longitude = -117.375)),
    )
    private val maple = Library("maple", "Maple County Library", "Maple Grove", "CA", "US", listOf(mapLibby, mapCat),
        branches = listOf(Branch("main", "Main Library")))
    private val harbor = Library("harbor", "Harbor City Library", "Harbor City", "CA", "US", listOf(harHoopla),
        branches = listOf(Branch("main", "Main Library")))
    private val here = LatLng(33.975, -117.37)

    private fun m(h: Holding) = MatchedHolding(h, 1.0, MatchedHolding.Reason.ISBN, otherLanguage = false)

    private fun resultsState(): ResultsUiState {
        val t = "Pride and Prejudice"; val a = listOf("Jane Austen")
        return ResultsUiState(Phase.SEARCHING, query = BookQuery(title = t, author = "Austen"), libraries = listOf(
            LibraryResult(riverside, listOf(
                ServiceResult(rivLibby, ServiceState.Done(listOf(
                    m(Holding(ProviderId.OVERDRIVE, Format.EBOOK, t, authors = a, providerItemId = "r1", owned = 12, available = 0, holds = 9, waitDays = 14)),
                    m(Holding(ProviderId.OVERDRIVE, Format.AUDIOBOOK, t, authors = a, providerItemId = "r2", owned = 6, available = 2, holds = 0, isAvailableNow = true)),
                ))),
                ServiceResult(rivHoopla, ServiceState.Done(listOf(
                    m(Holding(ProviderId.HOOPLA, Format.AUDIOBOOK, t, authors = a, providerItemId = "r3", availabilityKnown = false)),
                ))),
                ServiceResult(rivCat, ServiceState.Done(listOf(
                    m(Holding(ProviderId.BIBLIOCOMMONS, Format.PHYSICAL, t, authors = a, providerItemId = "r4", copies = listOf(
                        PhysicalCopy("Central Library", "central", "FIC AUSTEN", CopyStatus.AVAILABLE, latitude = 33.981, longitude = -117.375),
                        PhysicalCopy("Arlington Branch", null, "FIC AUSTEN", CopyStatus.AVAILABLE, latitude = 33.93, longitude = -117.40),
                        PhysicalCopy("Marcy Branch", null, "FIC AUSTEN", CopyStatus.CHECKED_OUT, dueDate = "2026-12-09", latitude = 33.95, longitude = -117.33),
                        PhysicalCopy("La Sierra Branch", null, "FIC AUSTEN", CopyStatus.IN_TRANSIT, latitude = 33.91, longitude = -117.48),
                    ))),
                ))),
            )),
            LibraryResult(maple, listOf(
                ServiceResult(mapLibby, ServiceState.Done(listOf(
                    m(Holding(ProviderId.OVERDRIVE, Format.EBOOK, t, authors = a, providerItemId = "m1", owned = 8, available = 1, holds = 0, isAvailableNow = true)),
                    m(Holding(ProviderId.OVERDRIVE, Format.AUDIOBOOK, t, authors = a, providerItemId = "m2", owned = 3, available = 0, holds = 5, waitDays = 21)),
                ))),
                ServiceResult(mapCat, ServiceState.Done(listOf(
                    m(Holding(ProviderId.POLARIS, Format.PHYSICAL, t, authors = a, providerItemId = "m3", copies = listOf(
                        PhysicalCopy("Main Library", "main", "FIC AUS", CopyStatus.AVAILABLE, latitude = 34.05, longitude = -117.29),
                    ))),
                ))),
            )),
            LibraryResult(harbor, listOf(
                ServiceResult(harHoopla, ServiceState.Done(listOf(
                    m(Holding(ProviderId.HOOPLA, Format.EBOOK, t, authors = a, providerItemId = "h1", availabilityKnown = false)),
                ))),
            )),
        ))
    }

    @Composable
    private fun results(tab: Format, watchDialog: Boolean = false, scope: WatchScope? = null) = ResultsContent(
        state = resultsState(), watched = scope != null, here = here, prefs = ReadingPrefs(),
        offline = false, showLocationCard = false,
        onBack = {}, onPreferences = {}, onAddLibrary = {}, onSearchManually = {},
        onRetry = { _, _ -> }, onBorrow = { _, _ -> }, onOpenCatalog = {}, onAllowLocation = {}, onDismissLocation = {},
        adSlot = noAd, initialTab = tab, initialWatchDialog = watchDialog, watchScope = scope,
    )

    @Composable
    private fun TabFrame(selected: Int, content: @Composable () -> Unit) {
        Scaffold(
            bottomBar = {
                NearshelfNavBar(
                    listOf(
                        NavDestinationItem(R.string.nav_search, R.drawable.ic_search, R.drawable.ic_search_fill),
                        NavDestinationItem(R.string.nav_watchlist, R.drawable.ic_watchlist, R.drawable.ic_watchlist_fill),
                        NavDestinationItem(R.string.nav_libraries, R.drawable.ic_library, R.drawable.ic_library_fill),
                    ),
                    selectedIndex = selected, onSelect = {},
                )
            },
        ) { padding -> Box(Modifier.padding(padding)) { content() } }
    }

    @Composable
    private fun home() = TabFrame(0) {
        val now = System.currentTimeMillis()
        HomeContent(
            input = "", onInputChange = {}, libraries = listOf(riverside, maple, harbor),
            recent = listOf(
                HistoryItem("a", BookQuery(title = "Middlemarch"), "Middlemarch", "George Eliot", null, now - 3_600_000),
                HistoryItem("b", BookQuery(title = "Frankenstein"), "Frankenstein", "Mary Shelley", null, now - 86_400_000),
                HistoryItem("c", BookQuery(title = "Jane Eyre"), "Jane Eyre", "Charlotte Brontë", null, now - 2 * 86_400_000),
                HistoryItem("d", BookQuery(title = "Moby-Dick"), "Moby-Dick", "Herman Melville", null, now - 3 * 86_400_000),
            ),
            hasCamera = true, onSubmit = {}, onScan = {}, onManageLibraries = {}, onAddLibrary = {}, onOpenHistory = {},
            onPreferences = {}, onSettings = {},
        )
    }

    @Test fun s1Home() = shot("01_home") { home() }

    @Test fun s2Digital() = shot("02_results_ebook") { results(Format.EBOOK) }

    @Test fun s3Print() = shot("03_results_print") { results(Format.PHYSICAL) }

    @Test fun s4Choose() = shot("04_choose_book") {
        fun c(t: String, a: String, y: Int, e: Int) = WorkCandidate(WorkInfo("/works/$a", t, listOf(a), emptySet()), y, e)
        ResultsContent(
            state = ResultsUiState(Phase.CHOOSING, query = BookQuery(title = "The Outsider"), candidates = listOf(
                c("The Outsider", "Stephen King", 2018, 31), c("The Outsider", "Richard Wright", 1953, 20),
                c("The Outsider", "Colin Wilson", 1956, 11), c("The Outsider", "Barbara Delinsky", 1992, 10),
                c("The Outsiders", "S. E. Hinton", 1967, 77),
            )),
            watched = false, here = null, prefs = ReadingPrefs(), offline = false, showLocationCard = false,
            onBack = {}, onPreferences = {}, onAddLibrary = {}, onSearchManually = {},
            onRetry = { _, _ -> }, onBorrow = { _, _ -> }, onOpenCatalog = {}, onAllowLocation = {}, onDismissLocation = {},
        )
    }

    @Test fun s5Watch() = shot("05_watch_dialog", dialog = true) { results(Format.AUDIOBOOK, watchDialog = true) }

    @Test fun s6Watchlist() = shot("06_watchlist") {
        val now = System.currentTimeMillis()
        fun snap(l: LibrarySnapshot) = WatchSnapshot(now - 3_600_000, mapOf("x" to l))
        TabFrame(1) {
            WatchlistContent(
                items = listOf(
                    WatchItem("a", BookQuery(title = "Middlemarch"), "Middlemarch", "George Eliot", null, now, now - 3_600_000,
                        snap(LibrarySnapshot("Maple County Library", availableIn = listOf("Libby")))),
                    WatchItem("b", BookQuery(title = "Jane Eyre"), "Jane Eyre", "Charlotte Brontë", null, now, now - 7_200_000,
                        snap(LibrarySnapshot("Riverside Public Library", shortestWaitDays = 12)),
                        WatchScope(setOf(Format.AUDIOBOOK), setOf("riverside"), listOf("Riverside Public Library"))),
                    WatchItem("c", BookQuery(title = "Little Women"), "Little Women", "Louisa May Alcott", null, now, now - 10_800_000,
                        snap(LibrarySnapshot("Riverside Public Library", onShelfAt = listOf("Central Library", "Arlington Branch"), homeBranchOnShelf = true)),
                        WatchScope(setOf(Format.PHYSICAL), setOf("riverside"), listOf("Riverside Public Library"))),
                ),
                snackbar = SnackbarHostState(),
                onOpen = {}, onSearch = {}, onCheckNow = {}, onRemove = {}, adSlot = noAd,
            )
        }
    }

    @Test fun s7Libraries() = shot("07_libraries") {
        TabFrame(2) { LibrariesContent(listOf(riverside, maple, harbor), SnackbarHostState(), {}, {}, {}, {}, {}) }
    }

    @Test fun s8HomeDark() = shot("08_home_dark", dark = true) { home() }
}
