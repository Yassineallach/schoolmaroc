package com.mardev.nearshelf.screenshots

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onRoot
import androidx.compose.ui.unit.dp
import com.github.takahirom.roborazzi.captureRoboImage
import com.mardev.nearshelf.core.geo.LatLng
import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.Branch
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.prefs.ReadingPrefs
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.search.ServiceState
import com.mardev.nearshelf.ui.onboarding.OnboardingScreen
import com.mardev.nearshelf.R
import com.mardev.nearshelf.data.HistoryItem
import com.mardev.nearshelf.ui.home.HomeContent
import com.mardev.nearshelf.ui.components.NavDestinationItem
import com.mardev.nearshelf.ui.components.NearshelfNavBar
import androidx.compose.foundation.layout.padding
import com.mardev.nearshelf.ui.results.LibraryResult
import com.mardev.nearshelf.ui.results.Phase
import com.mardev.nearshelf.ui.results.ResultsContent
import com.mardev.nearshelf.ui.results.ResultsUiState
import com.mardev.nearshelf.ui.results.ServiceResult
import com.mardev.nearshelf.ui.settings.AboutScreen
import com.mardev.nearshelf.ui.theme.NearshelfTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.ParameterizedRobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import org.robolectric.shadows.ShadowLog

/**
 * Renders the main screens at the sizes the UX checklist asks for: a small phone,
 * landscape, the largest font scale, and dark mode. Only records PNGs when run with
 * -Pnearshelf.screenshots=true; otherwise it just checks every screen composes.
 */
@RunWith(ParameterizedRobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [35], application = android.app.Application::class)
class ScreenshotTest(private val device: Device) {

    data class Device(val name: String, val qualifiers: String, val fontScale: Float = 1f, val dark: Boolean = false) {
        override fun toString() = name
    }

    companion object {
        @JvmStatic
        @ParameterizedRobolectricTestRunner.Parameters(name = "{0}")
        fun devices() = listOf(
            Device("phone", "w411dp-h891dp-xxhdpi"),
            Device("small", "w360dp-h640dp-xhdpi"),
            Device("landscape", "w891dp-h411dp-land-xxhdpi"),
            Device("font2x", "w411dp-h891dp-xxhdpi", fontScale = 2f),
            Device("dark", "w411dp-h891dp-night-xxhdpi", dark = true),
            Device("tall", "w411dp-h1500dp-xxhdpi"),
        ).map { arrayOf<Any>(it) }
    }

    @get:Rule val compose = createComposeRule()

    private fun shot(screen: String, content: @Composable () -> Unit) {
        org.robolectric.RuntimeEnvironment.setQualifiers(device.qualifiers)
        org.robolectric.RuntimeEnvironment.setFontScale(device.fontScale)
        ShadowLog.stream = null
        compose.setContent { NearshelfTheme(darkTheme = device.dark) { content() } }
        compose.onRoot().captureRoboImage("build/outputs/roborazzi/${screen}_${device.name}.png")
    }

    @Test fun results() = shot("results") {
        ResultsContent(
            state = sampleState(), watched = false, here = LatLng(41.88, -87.63), prefs = ReadingPrefs(),
            offline = false, showLocationCard = false,
            onBack = {}, onPreferences = {}, onAddLibrary = {}, onSearchManually = {}, onWatch = {},
            onRetry = { _, _ -> }, onBorrow = { _, _ -> }, onOpenCatalog = {}, onAllowLocation = {}, onDismissLocation = {},
            adSlot = { FakeAd(it) },
        )
    }

    @Test fun home() = shot("home") { HomeFrame(sampleLibraries(), sampleRecent()) }

    @Test fun homeEmpty() = shot("home_empty") { HomeFrame(emptyList(), emptyList()) }

    @Composable
    private fun HomeFrame(libraries: List<Library>, recent: List<HistoryItem>) {
        androidx.compose.material3.Scaffold(
            bottomBar = {
                NearshelfNavBar(
                    listOf(
                        NavDestinationItem(R.string.nav_search, R.drawable.ic_search, R.drawable.ic_search_fill),
                        NavDestinationItem(R.string.nav_watchlist, R.drawable.ic_watchlist, R.drawable.ic_watchlist_fill),
                        NavDestinationItem(R.string.nav_libraries, R.drawable.ic_library, R.drawable.ic_library_fill),
                    ),
                    selectedIndex = 0, onSelect = {},
                )
            },
        ) { padding ->
            Box(Modifier.padding(padding)) {
                HomeContent(
                    input = "", onInputChange = {}, libraries = libraries, recent = recent, hasCamera = true,
                    onSubmit = {}, onScan = {}, onManageLibraries = {}, onAddLibrary = {}, onOpenHistory = {},
                    onPreferences = {}, onSettings = {},
                )
            }
        }
    }

    private fun sampleLibraries(): List<Library> {
        val od = LibraryRef(ProviderId.OVERDRIVE, "chipublib", "Chicago Public Library")
        val ho = LibraryRef(ProviderId.HOOPLA, "chicago", "Chicago Public Library")
        val bc = LibraryRef(ProviderId.BIBLIOCOMMONS, "chipublib", "Chicago Public Library")
        val ev = LibraryRef(ProviderId.POLARIS, "evanston", "Evanston Public Library")
        val evOd = LibraryRef(ProviderId.OVERDRIVE, "evanston", "Evanston Public Library")
        val sk = LibraryRef(ProviderId.OVERDRIVE, "skokie", "Skokie Public Library")
        val ar = LibraryRef(ProviderId.SIERRA_VEGA, "arlington", "Arlington Heights Memorial Library")
        val arHo = LibraryRef(ProviderId.HOOPLA, "arlington", "Arlington Heights Memorial Library")
        return listOf(
            Library("chicago", "Chicago Public Library", "Chicago", "IL", "US", listOf(od, ho, bc)),
            Library("evanston", "Evanston Public Library", "Evanston", "IL", "US", listOf(evOd, ev)),
            Library("arlington", "Arlington Heights Memorial Library and Reading Room of the Northwest Suburbs", "Arlington Heights", "IL", "US", listOf(sk, arHo, ar, ev)),
            Library("skokie", "Skokie Public Library", "Skokie", "IL", "US", listOf(sk)),
        )
    }

    private fun sampleRecent(): List<HistoryItem> {
        val now = System.currentTimeMillis()
        return listOf(
            HistoryItem("a", BookQuery(title = "Piranesi"), "Piranesi", "Susanna Clarke", null, now - 3_600_000),
            HistoryItem("b", BookQuery(title = "The Overstory"), "The Overstory", "Richard Powers", null, now - 86_400_000),
            HistoryItem("c", BookQuery(title = "The Left Hand of Darkness"), "The Left Hand of Darkness: 50th Anniversary Edition", "Ursula K. Le Guin", null, now - 3 * 86_400_000),
        )
    }

    @Test fun noLibraries() = shot("no_libraries") {
        ResultsContent(
            state = ResultsUiState(Phase.SEARCHING, query = BookQuery(title = "Piranesi"), libraries = emptyList()),
            watched = false, here = null, prefs = ReadingPrefs(), offline = false, showLocationCard = false,
            onBack = {}, onPreferences = {}, onAddLibrary = {}, onSearchManually = {}, onWatch = {},
            onRetry = { _, _ -> }, onBorrow = { _, _ -> }, onOpenCatalog = {}, onAllowLocation = {}, onDismissLocation = {},
            adSlot = { FakeAd(it) },
        )
    }

    @Test fun onboarding() = shot("onboarding") { OnboardingScreen(onAddLibrary = {}, onDone = {}) }

    @Test fun about() = shot("about") { AboutScreen(onBack = {}) }

    @Composable
    private fun FakeAd(modifier: Modifier) = Surface(
        modifier.fillMaxWidth().height(260.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
        shape = MaterialTheme.shapes.medium,
    ) { Box(contentAlignment = Alignment.Center) { Text("Native ad slot") } }

    private fun sampleState(): ResultsUiState {
        val overdrive = LibraryRef(ProviderId.OVERDRIVE, "chipublib", "Chicago Public Library")
        val hoopla = LibraryRef(ProviderId.HOOPLA, "chicago", "Chicago Public Library", borrowLimitPerMonth = 4)
        val catalog = LibraryRef(ProviderId.BIBLIOCOMMONS, "chipublib", "Chicago Public Library", catalogUrl = "https://chipublib.bibliocommons.com")
        fun m(h: Holding) = MatchedHolding(h, 1.0, MatchedHolding.Reason.ISBN, otherLanguage = false)
        val title = "Tomorrow, and Tomorrow, and Tomorrow"
        val authors = listOf("Gabrielle Zevin")
        val chicago = LibraryResult(
            Library(
                "chicago", "Chicago Public Library", "Chicago", "IL", "US", listOf(overdrive, hoopla, catalog),
                homeBranchId = "hp", branches = listOf(Branch("hp", "Harold Washington Library Center", latitude = 41.876, longitude = -87.628)),
            ),
            listOf(
                ServiceResult(overdrive, ServiceState.Done(listOf(
                    m(Holding(ProviderId.OVERDRIVE, Format.EBOOK, title, providerItemId = "1", authors = authors, owned = 120, available = 0, holds = 310, waitDays = 42)),
                    m(Holding(ProviderId.OVERDRIVE, Format.AUDIOBOOK, title, providerItemId = "2", authors = authors, owned = 60, available = 2, holds = 0, isAvailableNow = true)),
                ))),
                ServiceResult(hoopla, ServiceState.Done(emptyList())),
                ServiceResult(catalog, ServiceState.Done(listOf(
                    m(Holding(
                        ProviderId.BIBLIOCOMMONS, Format.PHYSICAL, title, providerItemId = "3", authors = authors,
                        copies = listOf(
                            PhysicalCopy("Harold Washington Library Center", "hp", "FIC ZEVIN", CopyStatus.AVAILABLE, latitude = 41.876, longitude = -87.628),
                            PhysicalCopy("Lincoln Park", null, "FIC ZEVIN", CopyStatus.CHECKED_OUT, dueDate = "2026-12-02", latitude = 41.92, longitude = -87.65),
                            PhysicalCopy("Bezazian", null, "FIC ZEVIN", CopyStatus.IN_TRANSIT),
                        ),
                    )),
                ))),
            ),
        )
        val evanstonRef = LibraryRef(ProviderId.POLARIS, "evanston", "Evanston Public Library", catalogUrl = "https://evanston.polarislibrary.com")
        val evanston = LibraryResult(
            Library("evanston", "Evanston Public Library", "Evanston", "IL", "US", listOf(evanstonRef)),
            listOf(ServiceResult(evanstonRef, ServiceState.Failed(ProviderException.Kind.NETWORK, "timeout"))),
        )
        return ResultsUiState(Phase.SEARCHING, query = BookQuery(title = title, author = "Zevin"), libraries = listOf(chicago, evanston))
    }
}
