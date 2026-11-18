package com.mardev.nearshelf.core.provider.koha

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.testing.FixtureInterceptor
import com.mardev.nearshelf.core.testing.Fixtures
import kotlinx.coroutines.test.runTest
import java.net.URI
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Real Koha responses (Pillsbury NH, Portsmouth NH, South Taranaki and Horowhenua NZ), 2026-11-18. */
class KohaTest {
    private val pillsbury = LibraryRef(ProviderId.KOHA, "https://pillsbury.nhais.bywatersolutions.com", "Pillsbury Free Library")
    private val q = BookQuery(title = "The Hobbit", author = "J. R. R. Tolkien")

    private fun provider(routes: (okhttp3.Request) -> Pair<Int, String>?) = FixtureInterceptor(routes).let { it to KohaProvider(it.client()) }

    private val normal: (okhttp3.Request) -> Pair<Int, String>? = { req ->
        val p = req.url.encodedPath
        when {
            p == "/cgi-bin/koha/opac-search.pl" -> 200 to Fixtures.read("koha/pillsbury_rss_the_hobbit_tolkien.xml")
            p == "/api/v1/public/libraries" -> 200 to Fixtures.read("koha/pillsbury_libraries.json")
            p == "/api/v1/public/biblios/132614/items" -> 200 to Fixtures.read("koha/pillsbury_items_132614.json")
            p == "/api/v1/public/biblios/140246/items" -> 200 to Fixtures.read("koha/pillsbury_items_140246.json")
            p.endsWith("/items") -> 200 to "[]"
            else -> null
        }
    }

    @Test
    fun `RSS gives records with biblionumbers, clean titles and inverted authors`() {
        val h = KohaParser.parseRss(Fixtures.read("koha/pillsbury_rss_the_hobbit_tolkien.xml"))
        assertTrue(h.size >= 3)
        assertTrue(h.any { it.providerItemId == "132614" })
        val t = h.first { it.providerItemId == "140892" }
        assertEquals("The Hobbit; or, There and back again", t.title)
        assertEquals(listOf("J. R. R. Tolkien"), t.authors)
        assertTrue(h.none { it.title.endsWith("/") || it.title.endsWith(",") })
    }

    @Test
    fun `items become copies with branch names from the libraries endpoint`() {
        val names = KohaParser.parseLibraries(Fixtures.read("koha/pillsbury_libraries.json"))
        val copies = KohaParser.parseItems(Fixtures.read("koha/pillsbury_items_132614.json"), names)
        val c = copies.single()
        assertEquals("Pillsbury Free Library", c.branchName)
        assertEquals("HSG9", c.branchId)
        assertEquals("FIC TOL", c.callNumber)
        assertEquals(CopyStatus.AVAILABLE, c.status)
    }

    @Test
    fun `item statuses, including a checked-out copy's due date`() {
        val json = """[
          {"holding_library_id":"A","checked_out_date":"2026-12-02","lost_status":0,"withdrawn":0,"not_for_loan_status":0},
          {"holding_library_id":"A","checked_out_date":null,"lost_status":1,"withdrawn":0,"not_for_loan_status":0},
          {"holding_library_id":"A","checked_out_date":null,"lost_status":0,"withdrawn":0,"not_for_loan_status":1}]"""
        val c = KohaParser.parseItems(json, mapOf("A" to "Main"))
        assertEquals(listOf(CopyStatus.CHECKED_OUT, CopyStatus.MISSING, CopyStatus.LIBRARY_USE_ONLY), c.map { it.status })
        assertEquals("2026-12-02", c[0].dueDate)
    }

    @Test
    fun `other libraries' branch lists parse`() {
        assertEquals(11, KohaParser.parseLibraries(Fixtures.read("koha/southtaranaki_libraries.json")).size)
        assertTrue("Foxton" in KohaParser.parseLibraries(Fixtures.read("koha/horowhenua_libraries.json")).values)
        assertTrue("Little Harbour" in KohaParser.parseLibraries(Fixtures.read("koha/portsmouth_libraries.json")).values)
    }

    @Test
    fun `provider searches RSS, then fetches copies for matching records only`() = runTest {
        val (net, provider) = provider(normal)
        val h = provider.search(pillsbury, q)
        val m = BookMatcher().match(q, h)
        assertTrue(m.isNotEmpty())
        val withCopies = h.filter { it.copies.isNotEmpty() }
        assertTrue(withCopies.all { c -> c.copies.all { it.branchName == "Pillsbury Free Library" } })
        assertEquals("rss", net.requests.first().url.queryParameter("format"))
        assertTrue(net.requests.count { it.url.encodedPath.endsWith("/items") } <= 3)
        assertEquals(1, net.requests.count { it.url.encodedPath == "/api/v1/public/libraries" })
    }

    @Test
    fun `REST API switched off leaves availability unknown instead of failing`() = runTest {
        val (_, provider) = provider { req ->
            if (req.url.encodedPath == "/cgi-bin/koha/opac-search.pl") 200 to Fixtures.read("koha/pillsbury_rss_the_hobbit_tolkien.xml") else 404 to "{}"
        }
        val matched = BookMatcher().match(q, provider.search(pillsbury, q)).map { it.holding }
        assertTrue(matched.isNotEmpty())
        assertTrue(matched.take(3).all { !it.availabilityKnown && it.copies.isEmpty() })
    }

    @Test
    fun `Cloudflare 429 and the JavaScript challenge are reported as BLOCKED`() = runTest {
        for (page in listOf("koha/portsmouth_search_cloudflare_429.html" to 429, "koha/southtaranaki_search_bot_challenge.html" to 200)) {
            val (_, provider) = provider { page.second to Fixtures.read(page.first) }
            val e = assertFailsWith<ProviderException> { provider.search(pillsbury, q) }
            assertEquals(ProviderException.Kind.BLOCKED, e.kind, page.first)
        }
    }

    @Test
    fun `links`() {
        val (_, provider) = provider(normal)
        val h = KohaParser.parseRss(Fixtures.read("koha/pillsbury_rss_the_hobbit_tolkien.xml")).first()
        assertEquals(
            URI("https://pillsbury.nhais.bywatersolutions.com/cgi-bin/koha/opac-detail.pl?biblionumber=${h.providerItemId}"),
            provider.borrowLink(pillsbury, h),
        )
        assertFalse(provider.searchLink(pillsbury, q).toString().contains(" "))
    }
}
