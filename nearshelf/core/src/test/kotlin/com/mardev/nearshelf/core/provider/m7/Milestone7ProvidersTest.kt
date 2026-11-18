package com.mardev.nearshelf.core.provider.m7

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.match.BranchNames
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.provider.aspen.AspenProvider
import com.mardev.nearshelf.core.provider.evergreen.EvergreenParser
import com.mardev.nearshelf.core.provider.evergreen.EvergreenProvider
import com.mardev.nearshelf.core.provider.polaris.PolarisParser
import com.mardev.nearshelf.core.provider.polaris.PolarisProvider
import com.mardev.nearshelf.core.provider.sierra.VegaParser
import com.mardev.nearshelf.core.provider.sierra.VegaProvider
import com.mardev.nearshelf.core.provider.sierra.WebPacParser
import com.mardev.nearshelf.core.provider.sierra.WebPacProvider
import com.mardev.nearshelf.core.testing.FixtureInterceptor
import com.mardev.nearshelf.core.testing.Fixtures
import kotlinx.coroutines.test.runTest
import java.net.URI
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

/** Real pages recorded 2026-11-18: PINES and C/W MARS (Evergreen), Hillsborough and Brentwood (Polaris),
 * NYPL and Suffolk (Vega), Cincinnati classic (Sierra WebPAC). */
class Milestone7ProvidersTest {
    private val phm = BookQuery(title = "Project Hail Mary", author = "Andy Weir", isbns = setOf("9780593135204", "9780593395561"), language = "en")
    private val hobbit = BookQuery(title = "The Hobbit", author = "J. R. R. Tolkien")

    // ---------- Evergreen ----------
    @Test
    fun `Evergreen feed gives records with copies per library`() {
        val h = EvergreenParser.parse(Fixtures.read("evergreen/pines_project_hail_mary_weir.xml"))
        val hc = h.single { it.providerItemId == "6281615" }
        assertEquals("Project Hail Mary : a novel", hc.title)
        assertEquals(listOf("Andy Weir"), hc.authors)
        assertTrue("9780593135204" in hc.isbns)
        // 231 copies in the feed; 10 are hidden from the public catalog or deleted.
        assertEquals(221, hc.copies.size)
        assertEquals(112, hc.copies.count { it.status == CopyStatus.AVAILABLE }) // Available + Reshelving
        assertEquals(75, hc.copies.count { it.status == CopyStatus.CHECKED_OUT })
        assertTrue(hc.copies.any { it.branchName == "Statham Public Library" } || hc.copies.all { it.branchName.isNotBlank() })
        assertTrue(hc.copies.all { it.callNumber != null })
    }

    @Test
    fun `Evergreen second consortium and matching`() = runTest {
        val net = FixtureInterceptor { req ->
            if (req.url.encodedPath == "/opac/extras/opensearch/1.1/-/atom-full/keyword/") 200 to Fixtures.read("evergreen/cwmars_title_the_hobbit_author_tolkien.xml") else null
        }
        val ref = LibraryRef(ProviderId.EVERGREEN, "https://bark.cwmars.org", "C/W MARS")
        val m = BookMatcher().match(hobbit, EvergreenProvider(net.client()).search(ref, hobbit))
        assertTrue(m.isNotEmpty())
        assertTrue(m.all { it.holding.copies.isNotEmpty() })
        assertTrue(m.none { "[" in it.holding.title }) // e-resources and sound recordings dropped
        assertEquals("title:The Hobbit author:tolkien", net.requests.single().url.queryParameter("searchTerms"))
        assertEquals(URI("https://bark.cwmars.org/eg/opac/record/${m.first().holding.providerItemId}"), EvergreenProvider(net.client()).borrowLink(ref, m.first().holding))
    }

    @Test
    fun `plain keyword results are companion books, which the matcher rejects`() {
        val h = EvergreenParser.parse(Fixtures.read("evergreen/cwmars_the_hobbit_tolkien.xml"))
        assertTrue(BookMatcher().match(hobbit, h).isEmpty())
        assertTrue(h.flatMap { it.authors }.none { "CWMARS" in it || "(" in it })
    }

    @Test
    fun `MARC names`() {
        val n = com.mardev.nearshelf.core.match.MarcNames::display
        assertEquals("J. R. R. Tolkien", n("Tolkien, J. R. R.(John Ronald Reuel),1892-1973,author,illustrator.http://id.loc.gov/authorities/names/n79005673(CWMARS)225068"))
        assertEquals("Christopher Tolkien", n("Tolkien, Christopher,writer of foreword.http://id.loc.gov/x(CWMARS)270476"))
        assertEquals("Andy Weir", n("Weir, Andy,author.https://id.oclc.org/worldcat/entity/E39PB(GaAaGPL)13264905"))
        assertEquals("Andy Weir", n("Weir , Andy, author."))
        assertEquals("J. R. R. Tolkien", n("Tolkien, J. R. R."))
        assertEquals("Homer", n("Homer"))
    }

    @Test
    fun `Evergreen status codes`() {
        assertEquals(CopyStatus.AVAILABLE, EvergreenParser.status(7))
        assertEquals(CopyStatus.ON_HOLD_SHELF, EvergreenParser.status(8))
        assertEquals(CopyStatus.MISSING, EvergreenParser.status(16))
        assertEquals("Andy Weir", EvergreenParser.cleanAuthor("Weir, Andy,author.https://id.oclc.org/worldcat/entity/E39PB(GaAaGPL)13264905"))
    }

    // ---------- Polaris ----------
    @Test
    fun `Polaris results keep print records with holds and system counts`() {
        val h = PolarisParser.parseResults(Fixtures.read("polaris/hcplc_results_project_hail_mary_weir.html"))
        val hc = h.single { it.providerItemId == "1803265" }
        assertEquals(listOf("Andy Weir"), hc.authors)
        assertEquals(5, hc.holds)
        assertEquals(13, hc.available)
        assertEquals(63, hc.owned)
        assertTrue("9780593135204" in hc.isbns)
        assertEquals("Large print", h.single { it.providerItemId == "1810590" }.edition)
        val brentwood = PolarisParser.parseResults(Fixtures.read("polaris/brentwood_results_the_hobbit_tolkien.html"))
        assertEquals(5, brentwood.size) // the five "Book" records; DVDs, Blu-ray and e-books dropped
    }

    @Test
    fun `Polaris availability gives branches, call numbers and due dates`() {
        val c = PolarisParser.parseAvailability(Fixtures.read("polaris/hcplc_availability_1803265.html"))
        assertTrue(c.size >= 60)
        val held = c.first { it.branchName == "78th Street Community Library" }
        assertEquals(CopyStatus.ON_HOLD_SHELF, held.status)
        assertEquals("FIC WEIR 2021", held.callNumber)
        assertTrue(c.any { it.status == CopyStatus.CHECKED_OUT && it.dueDate == "2026-11-23" })
        assertTrue(c.any { it.status == CopyStatus.IN_TRANSIT })
        assertEquals(13, c.count { it.status == CopyStatus.AVAILABLE })
        assertEquals(CopyStatus.AVAILABLE, PolarisParser.parseAvailability(Fixtures.read("polaris/brentwood_availability_155960.html")).single().status)
    }

    @Test
    fun `Polaris provider runs the session flow and fetches copies for matches only`() = runTest {
        val net = FixtureInterceptor { req ->
            val p = req.url.encodedPath
            when {
                p.endsWith("/search/searchresults.aspx") -> 200 to "<html></html>"
                p.endsWith("/components/ajaxResults.aspx") -> 200 to Fixtures.read("polaris/hcplc_results_project_hail_mary_weir.html")
                p.endsWith("/components/ajaxavailability.aspx") && req.url.queryParameter("bibid") == "1803265" ->
                    200 to Fixtures.read("polaris/hcplc_availability_1803265.html")
                p.endsWith("/components/ajaxavailability.aspx") -> 200 to "<table class='availability__table'></table>"
                else -> null
            }
        }
        val ref = LibraryRef(ProviderId.POLARIS, "https://catalog.hcplc.org/polaris", "Hillsborough")
        val provider = PolarisProvider(net.client())
        val h = provider.search(ref, phm)
        assertTrue(h.single { it.providerItemId == "1803265" }.copies.size >= 60)
        val avail = net.requests.filter { it.url.encodedPath.endsWith("ajaxavailability.aspx") }
        assertTrue(avail.size in 1..3)
        assertEquals("1", avail.single { it.url.queryParameter("bibid") == "1803265" }.url.queryParameter("pos"))
        assertEquals("1", PolarisParser.positions(Fixtures.read("polaris/hcplc_results_project_hail_mary_weir.html"))["1803265"])
        assertEquals(URI("https://catalog.hcplc.org/polaris/view.aspx?cn=1803265"), provider.borrowLink(ref, h.first { it.providerItemId == "1803265" }))
    }

    // ---------- Vega ----------
    @Test
    fun `Vega format groups become print holdings with branch-level availability`() {
        val h = VegaParser.parseSearch(Fixtures.read("vega/nypl_format_groups_project_hail_mary_weir.json"))
        val book = h.single { it.providerItemId == "e3e605be-c7af-5a58-bc32-73b63d5b9f3d|Book" }
        assertEquals("en", book.language)
        assertEquals(listOf("Andy Weir"), book.authors)
        assertTrue(book.branchLevelOnly)
        assertEquals(357, book.owned)
        assertTrue("9780593135204" in book.isbns)
        assertEquals("Large print", h.single { it.providerItemId.endsWith("|Large Print") && it.providerItemId.startsWith("e3e605be") }.edition)
        assertTrue(h.any { it.language == "es" } && h.any { it.language == "ko" })
        assertTrue(h.none { it.providerItemId.endsWith("|DVD") || it.providerItemId.endsWith("|eBook") })
        assertTrue(VegaParser.parseSearch(Fixtures.read("vega/suffolk_format_groups_the_hobbit_tolkien.json")).isNotEmpty())
    }

    @Test
    fun `Vega locations and API host`() {
        val c = VegaParser.parseLocations(Fixtures.read("vega/nypl_locations_e3e605be_book.json"))
        assertEquals(87, c.size)
        assertEquals(50, c.count { it.status == CopyStatus.AVAILABLE })
        assertEquals("https://na2.iiivega.com", VegaParser.apiBase("nypl.na2.iiivega.com"))
        assertTrue("var API_URL = 'https://na2.iiivega.com';" in Fixtures.read("vega/nypl_config.js"))
        assertEquals("https://na.iiivega.com", VegaParser.apiBase("livebrarykids-suffc.na.iiivega.com"))
    }

    @Test
    fun `Vega provider posts the search with the customer domain`() = runTest {
        val net = FixtureInterceptor { req ->
            when {
                req.url.encodedPath == "/api/search-result/search/format-groups" -> 200 to Fixtures.read("vega/nypl_format_groups_project_hail_mary_weir.json")
                req.url.encodedPath.endsWith("/e3e605be-c7af-5a58-bc32-73b63d5b9f3d/locations") -> 200 to Fixtures.read("vega/nypl_locations_e3e605be_book.json")
                req.url.encodedPath.endsWith("/locations") -> 200 to """{"available":[],"unavailable":[]}"""
                else -> null
            }
        }
        val ref = LibraryRef(ProviderId.SIERRA_VEGA, "https://nypl.na2.iiivega.com", "NYPL")
        val provider = VegaProvider(net.client())
        val h = provider.search(ref, phm)
        val first = net.requests.first()
        assertEquals("na2.iiivega.com", first.url.host)
        assertEquals("nypl.na2.iiivega.com", first.header("iii-customer-domain"))
        assertEquals("POST", first.method)
        assertEquals(87, h.single { it.providerItemId == "e3e605be-c7af-5a58-bc32-73b63d5b9f3d|Book" }.copies.size)
        assertEquals(
            URI("https://nypl.na2.iiivega.com/search/card?id=e3e605be-c7af-5a58-bc32-73b63d5b9f3d&entityType=FormatGroup"),
            provider.borrowLink(ref, h.first { it.providerItemId.startsWith("e3e605be") }),
        )
    }

    // ---------- Sierra WebPAC ----------
    @Test
    fun `WebPAC results keep print records, drop DVD and audio`() {
        val h = WebPacParser.parseResults(Fixtures.read("webpac/cincinnati_results_project_hail_mary_weir.html"))
        assertEquals(setOf("b3597618", "b3599719", "b3615041"), h.map { it.providerItemId }.toSet())
        assertEquals("Large print", h.single { it.providerItemId == "b3599719" }.edition)
    }

    @Test
    fun `WebPAC record page copies, due dates and shelf locations`() {
        val c = WebPacParser.parseRecordItems(Fixtures.read("webpac/cincinnati_record_b3597618.html"))
        assertEquals(10, c.size)
        assertTrue(c.any { it.status == CopyStatus.CHECKED_OUT && it.dueDate == "2026-11-27" })
        assertEquals(3, c.count { it.status == CopyStatus.IN_TRANSIT })
        assertEquals(2, c.count { it.status == CopyStatus.AVAILABLE }) // CHECK SHELVES
        assertTrue(BranchNames.matches("Anderson", c.first().branchName))
    }

    @Test
    fun `WebPAC links`() {
        val ref = LibraryRef(ProviderId.SIERRA_ENCORE, "https://classic.cincinnatilibrary.org", "Cincinnati")
        val p = WebPacProvider(FixtureInterceptor { null }.client())
        val h = WebPacParser.parseResults(Fixtures.read("webpac/cincinnati_results_project_hail_mary_weir.html")).first()
        assertEquals(URI("https://classic.cincinnatilibrary.org/record=${h.providerItemId}~S1"), p.borrowLink(ref, h))
    }

    // ---------- Aspen ----------
    @Test
    fun `Aspen never searches and offers the catalog's own search`() = runTest {
        val ref = LibraryRef(ProviderId.ASPEN, "https://catalog.akronlibrary.org", "Akron")
        val e = assertFailsWith<ProviderException> { AspenProvider().search(ref, hobbit) }
        assertEquals(ProviderException.Kind.BLOCKED, e.kind)
        assertEquals(
            URI("https://catalog.akronlibrary.org/Search/Results?lookfor=The+Hobbit+J.+R.+R.+Tolkien&searchIndex=Keyword"),
            AspenProvider().searchLink(ref, hobbit),
        )
    }
}
