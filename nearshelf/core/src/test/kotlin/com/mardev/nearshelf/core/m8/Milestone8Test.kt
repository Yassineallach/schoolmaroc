package com.mardev.nearshelf.core.m8

import com.mardev.nearshelf.core.cache.MemoryCache
import com.mardev.nearshelf.core.geo.Distance
import com.mardev.nearshelf.core.geo.LatLng
import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Branch
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.net.PoliteInterceptor
import com.mardev.nearshelf.core.net.ProviderHealth
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.search.SearchCoordinator
import com.mardev.nearshelf.core.search.ServiceState
import com.mardev.nearshelf.core.watch.Watch
import com.mardev.nearshelf.core.watch.WatchEvent
import kotlinx.coroutines.test.runTest
import java.net.URI
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue

class Milestone8Test {
    private var now = 1_000_000L

    private class FakeProvider(var fail: ProviderException.Kind? = null) : CatalogProvider {
        override val id = ProviderId.OVERDRIVE
        var calls = 0
        override suspend fun findLibraries(query: String) = emptyList<LibraryRef>()
        override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> {
            calls++
            fail?.let { throw ProviderException(id, it, "down") }
            return listOf(Holding(ProviderId.OVERDRIVE, Format.EBOOK, "Dune", providerItemId = "1", isAvailableNow = true, language = "en"))
        }
        override fun borrowLink(library: LibraryRef, holding: Holding) = URI("https://x")
    }

    private val ref = LibraryRef(ProviderId.OVERDRIVE, "lib", "Lib")
    private val q = BookQuery(title = "Dune")

    @Test
    fun `fresh cache answers without a request, stale cache covers a failure`() = runTest {
        val p = FakeProvider()
        val c = SearchCoordinator(listOf(p), cache = MemoryCache { now }, clock = { now })
        assertIs<ServiceState.Done>(c.searchOne(ref, q))
        assertIs<ServiceState.Done>(c.searchOne(ref, q))
        assertEquals(1, p.calls)
        now += 7L * 60 * 60 * 1000 // past 6 hours
        p.fail = ProviderException.Kind.NETWORK
        val st = c.searchOne(ref, q)
        assertIs<ServiceState.Done>(st)
        assertTrue(st.stale)
        assertEquals(2, p.calls)
    }

    @Test
    fun `three failures in a row mark a catalog temporarily unavailable, retry resets`() = runTest {
        val p = FakeProvider(ProviderException.Kind.HTTP)
        val health = ProviderHealth(clock = { now })
        val c = SearchCoordinator(listOf(p), health = health, clock = { now })
        repeat(3) { assertIs<ServiceState.Failed>(c.searchOne(ref, q)) }
        assertEquals(ServiceState.TemporarilyUnavailable, c.searchOne(ref, q))
        assertEquals(3, p.calls)
        p.fail = null
        assertIs<ServiceState.Done>(c.searchOne(ref, q, forceRefresh = true))
        now += 16 * 60 * 1000
        assertTrue(!health.isDown(ProviderId.OVERDRIVE, "lib"))
    }

    @Test
    fun `bot checks don't count as outages`() {
        val h = ProviderHealth(clock = { now })
        repeat(5) { h.recordFailure(ProviderId.KOHA, "x", ProviderException.Kind.BLOCKED) }
        assertTrue(!h.isDown(ProviderId.KOHA, "x"))
    }

    @Test
    fun `polite limiter spaces requests to one host by 500 ms`() {
        val p = PoliteInterceptor(clock = { now })
        assertEquals(0, p.reserveSlot("a.org"))
        assertEquals(500, p.reserveSlot("a.org"))
        assertEquals(1000, p.reserveSlot("a.org"))
        assertEquals(0, p.reserveSlot("b.org"))
    }

    @Test
    fun distance() {
        val seattleCentral = LatLng(47.6067, -122.3325)
        val ballard = LatLng(47.6699, -122.3844)
        assertTrue(Distance.km(seattleCentral, ballard) in 7.5..8.5)
    }

    // ---------- watchlist ----------
    private val lib = Library("seattle|us", "Seattle Public Library", services = emptyList(), homeBranchId = "b", branches = listOf(Branch("b", "Ballard")))

    private fun ebook(available: Boolean, wait: Int?) = MatchedHolding(
        Holding(ProviderId.OVERDRIVE, Format.EBOOK, "Dune", providerItemId = "1", isAvailableNow = available, waitDays = wait), 1.0, MatchedHolding.Reason.TITLE, false,
    )

    private fun print(vararg shelf: String) = MatchedHolding(
        Holding(
            ProviderId.BIBLIOCOMMONS, Format.PHYSICAL, "Dune", providerItemId = "p",
            copies = shelf.map { PhysicalCopy(it, status = CopyStatus.AVAILABLE) } + PhysicalCopy("Central Library", status = CopyStatus.CHECKED_OUT),
        ),
        1.0, MatchedHolding.Reason.TITLE, false,
    )

    private fun snap(vararg m: MatchedHolding) = Watch.snapshot(now, listOf(lib to listOf("Libby" to ServiceState.Done(m.filter { it.holding.format != Format.PHYSICAL }), "BiblioCommons" to ServiceState.Done(m.filter { it.holding.format == Format.PHYSICAL }))))

    @Test
    fun `first check is a baseline only`() {
        assertTrue(Watch.events(null, snap(ebook(true, null))).isEmpty())
    }

    @Test
    fun `now available, on shelf at home branch, and wait dropped`() {
        val e1 = Watch.events(snap(ebook(false, 30)), snap(ebook(true, null)))
        assertEquals(listOf<WatchEvent>(WatchEvent.NowAvailable("Seattle Public Library", "Libby")), e1)
        val e2 = Watch.events(snap(print("Northgate Branch")), snap(print("Northgate Branch", "Ballard Branch")))
        assertEquals(listOf<WatchEvent>(WatchEvent.OnShelf("Seattle Public Library", "Ballard Branch")), e2)
        val e3 = Watch.events(snap(ebook(false, 40)), snap(ebook(false, 12)))
        assertEquals(listOf<WatchEvent>(WatchEvent.WaitDropped("Seattle Public Library", 12)), e3)
    }

    @Test
    fun `small wait changes and unchanged availability stay quiet`() {
        assertTrue(Watch.events(snap(ebook(false, 14)), snap(ebook(false, 12))).isEmpty())
        assertTrue(Watch.events(snap(ebook(true, null)), snap(ebook(true, null))).isEmpty())
        assertTrue(Watch.events(snap(print("Northgate Branch")), snap(print("Northgate Branch"))).isEmpty())
    }

    @Test
    fun `status line prefers available, then home shelf, then shortest wait`() {
        assertEquals(Watch.Status.Available("Seattle Public Library", "Libby"), Watch.status(snap(ebook(true, null), print("Ballard Branch"))))
        assertEquals(Watch.Status.OnShelf("Seattle Public Library", "Ballard Branch"), Watch.status(snap(ebook(false, 9), print("Northgate Branch", "Ballard Branch"))))
        assertEquals(Watch.Status.Waiting("Seattle Public Library", 9), Watch.status(snap(ebook(false, 9))))
        assertEquals(Watch.Status.NotYet, Watch.status(snap()))
    }
}
