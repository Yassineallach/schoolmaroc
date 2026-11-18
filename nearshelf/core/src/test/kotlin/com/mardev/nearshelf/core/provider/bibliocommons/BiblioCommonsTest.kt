package com.mardev.nearshelf.core.provider.bibliocommons

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Branch
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.search.SearchCoordinator
import com.mardev.nearshelf.core.search.ServiceState
import com.mardev.nearshelf.core.testing.FixtureInterceptor
import com.mardev.nearshelf.core.testing.Fixtures
import kotlinx.coroutines.test.runTest
import java.net.URI
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Real gateway responses from Seattle and Toronto, 2026-11-18. */
class BiblioCommonsTest {
    private val interceptor = FixtureInterceptor { req ->
        val p = req.url.encodedPath
        when {
            p == "/v2/libraries/seattle/bibs/search" -> 200 to Fixtures.read("bibliocommons/seattle_search_project_hail_mary.json")
            p == "/v2/libraries/seattle/bibs/S246C968971/availability" -> 200 to Fixtures.read("bibliocommons/seattle_availability_S246C968971.json")
            p == "/v2/libraries/tpl/bibs/search" -> 200 to Fixtures.read("bibliocommons/tpl_search_project_hail_mary_weir.json")
            p == "/v2/libraries/tpl/bibs/S234C3970025/availability" -> 200 to Fixtures.read("bibliocommons/tpl_availability_S234C3970025.json")
            p.startsWith("/v2/libraries/walled/") -> 429 to "<title>Attention Required! | Cloudflare</title>"
            p.endsWith("/availability") -> 200 to """{"entities":{"bibItems":{}}}"""
            else -> null
        }
    }
    private val provider = BiblioCommonsProvider(interceptor.client())
    private val seattle = LibraryRef(ProviderId.BIBLIOCOMMONS, "https://seattle.bibliocommons.com", "Seattle Public Library")
    private val tpl = LibraryRef(ProviderId.BIBLIOCOMMONS, "https://tpl.bibliocommons.com", "Toronto Public Library")
    private val q = BookQuery(title = "Project Hail Mary", author = "Andy Weir", isbns = setOf("9780593135204"), language = "en")

    @Test
    fun `search keeps print books only and reads the record summary`() {
        val h = BiblioCommonsParser.parseSearch(Fixtures.read("bibliocommons/seattle_search_project_hail_mary.json"))
        assertTrue(h.all { it.format == Format.PHYSICAL })
        assertEquals(setOf("S246C968971", "S246C1018833", "S246C1054972", "S246C1010617"), h.map { it.providerItemId }.toSet())
        val bk = h.single { it.providerItemId == "S246C968971" }
        assertEquals(listOf("Andy Weir"), bk.authors)
        assertEquals("en", bk.language)
        assertTrue("9780593135204" in bk.isbns)
        assertEquals(165, bk.owned)
        assertEquals("Large print", h.single { it.providerItemId == "S246C1018833" }.edition)
        assertEquals("zh", h.single { it.providerItemId == "S246C1054972" }.language)
    }

    @Test
    fun `copies carry branch, call number and status`() {
        val copies = BiblioCommonsParser.parseCopies(Fixtures.read("bibliocommons/seattle_availability_S246C968971.json"))
        assertEquals(145, copies.size)
        val c = copies.first { it.branchName == "Central Library" && it.status == CopyStatus.AVAILABLE }
        assertEquals("3", c.branchId)
        assertEquals("SCI-FIC WEIR 2021", c.callNumber)
        assertEquals(6, copies.count { it.status == CopyStatus.AVAILABLE })
        assertEquals(100, copies.count { it.status == CopyStatus.CHECKED_OUT })
        assertEquals(16, copies.count { it.status == CopyStatus.ON_HOLD_SHELF })
        assertEquals(11, copies.count { it.status == CopyStatus.IN_TRANSIT })
        assertEquals(3, copies.count { it.status == CopyStatus.MISSING })
        assertEquals(9, copies.count { it.status == CopyStatus.IN_PROCESSING })
    }

    @Test
    fun `provider fetches copies only for records that match the book`() = runTest {
        val h = provider.search(seattle, q)
        val bk = h.single { it.providerItemId == "S246C968971" }
        assertEquals(145, bk.copies.size)
        assertEquals(6, bk.available)
        assertTrue(bk.isAvailableNow)
        val detailCalls = interceptor.requests.filter { it.url.encodedPath.endsWith("/availability") }.map { it.url.encodedPath }
        assertTrue("/v2/libraries/seattle/bibs/S246C968971/availability" in detailCalls)
        assertTrue(detailCalls.size <= 3)
        assertEquals("Project Hail Mary Andy Weir", interceptor.requests.first().url.queryParameter("query"))
    }

    @Test
    fun `Toronto, second library`() = runTest {
        val h = provider.search(tpl, q)
        val bk = h.single { it.providerItemId == "S234C3970025" }
        assertEquals(216, bk.copies.size)
        assertEquals(2, bk.copies.count { it.status == CopyStatus.AVAILABLE })
        assertEquals(1, bk.copies.count { it.status == CopyStatus.LIBRARY_USE_ONLY })
    }

    @Test
    fun `matcher keeps English print and flags the Spanish edition`() = runTest {
        val m = BookMatcher().match(q, provider.search(seattle, q))
        assertEquals(setOf("S246C968971", "S246C1018833"), m.filter { !it.otherLanguage }.map { it.holding.providerItemId }.toSet())
        assertEquals(setOf("es"), m.filter { it.otherLanguage }.mapNotNull { it.holding.language }.toSet())
    }

    @Test
    fun `Chinese edition ("Wan jiu ji hua") matches only through its ISBN, then is flagged`() = runTest {
        val withChinese = q.copy(isbns = q.isbns + "9787544787352")
        val zh = BookMatcher().match(withChinese, provider.search(seattle, withChinese)).single { it.holding.providerItemId == "S246C1054972" }
        assertTrue(zh.otherLanguage)
        assertEquals("zh", zh.holding.language)
    }

    @Test
    fun `coordinator places copies at registry branch coordinates`() = runTest {
        val lib = Library(
            "seattle|us", "Seattle Public Library", services = listOf(seattle),
            branches = listOf(Branch("od:1", "Central", latitude = 47.6067, longitude = -122.3325)),
        )
        val state = SearchCoordinator(listOf(provider)).searchOne(seattle, q, lib)
        assertIs<ServiceState.Done>(state)
        val central = state.matches.first { it.holding.providerItemId == "S246C968971" }.holding.copies.first { it.branchName == "Central Library" }
        assertEquals(47.6067, central.latitude)
        assertNull(state.matches.first().holding.copies.firstOrNull { it.branchName == "Northgate Branch" }?.latitude)
    }

    @Test
    fun `links and bot walls`() = runTest {
        val bk = BiblioCommonsParser.parseSearch(Fixtures.read("bibliocommons/seattle_search_project_hail_mary.json")).first { it.providerItemId == "S246C968971" }
        assertEquals(URI("https://seattle.bibliocommons.com/v2/record/S246C968971"), provider.borrowLink(seattle, bk))
        assertEquals(
            URI("https://seattle.bibliocommons.com/v2/search?query=Project%20Hail%20Mary%20Andy%20Weir&searchType=smart"),
            provider.searchLink(seattle, q),
        )
        val walled = seattle.copy(key = "https://walled.bibliocommons.com")
        assertEquals(ProviderException.Kind.BLOCKED, assertFailsWith<ProviderException> { provider.search(walled, q) }.kind)
    }
}
