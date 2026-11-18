package com.mardev.nearshelf.core.registry

import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.share.FetchedPage
import com.mardev.nearshelf.core.testing.Fixtures
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Pages are excerpts of live catalogs fetched 2026-11-18 (fixtures/detect/index.json). */
class CatalogDetectorTest {
    private fun page(name: String, url: String) = CatalogDetector.fromPage(url, Fixtures.read("detect/$name.html"))

    private val expected = mapOf(
        "bibliocommons_seattle" to ProviderId.BIBLIOCOMMONS,
        "bibliocommons_toronto" to ProviderId.BIBLIOCOMMONS,
        "bibliocommons_chicago" to ProviderId.BIBLIOCOMMONS, // page also says "polaris"
        "evergreen_pines" to ProviderId.EVERGREEN,
        "evergreen_cwmars" to ProviderId.EVERGREEN,
        "evergreen_pines_eg2" to ProviderId.EVERGREEN,
        "aspen_owwl" to ProviderId.ASPEN,
        "polaris_hillsborough" to ProviderId.POLARIS,
        "polaris_brentwood" to ProviderId.POLARIS, // page also says "Vega"
        "vega_nypl" to ProviderId.SIERRA_VEGA,
        "vega_suffolk" to ProviderId.SIERRA_VEGA,
        "koha_portsmouth" to ProviderId.KOHA,
        "koha_pillsbury" to ProviderId.KOHA,
        "sierra_webpac_cincinnati" to ProviderId.SIERRA_ENCORE,
        "sierra_webpac_cincinnati_search" to ProviderId.SIERRA_ENCORE,
    )

    @Test
    fun `every recorded catalog is recognised`() {
        val index = kotlinx.serialization.json.Json.decodeFromString<Map<String, String>>(Fixtures.read("detect/index.json"))
        assertEquals(expected.keys, index.keys)
        for ((name, url) in index) {
            assertEquals(expected[name], page(name, url)?.provider, name)
        }
    }

    @Test
    fun `HTML alone recognises Koha, Vega, Polaris, Evergreen and Sierra on neutral addresses`() {
        val neutral = "https://catalog.example.org/"
        for (name in listOf("koha_portsmouth", "vega_nypl", "polaris_hillsborough", "evergreen_pines", "sierra_webpac_cincinnati", "aspen_owwl")) {
            assertEquals(expected[name], page(name, neutral)?.provider, name)
        }
    }

    @Test
    fun `base URLs and titles`() {
        val polaris = page("polaris_hillsborough", "https://catalog.hcplc.org/polaris/")!!
        assertEquals("https://catalog.hcplc.org/polaris", polaris.baseUrl)
        val seattle = page("bibliocommons_seattle", "https://seattle.bibliocommons.com/")!!
        assertEquals("https://seattle.bibliocommons.com", seattle.baseUrl)
        assertEquals("The Seattle Public Library", seattle.pageTitle)
    }

    @Test
    fun `URL rules`() {
        assertEquals(ProviderId.KOHA, CatalogDetector.fromUrl("https://x.org/cgi-bin/koha/opac-detail.pl?biblionumber=1")?.provider)
        assertEquals(ProviderId.EVERGREEN, CatalogDetector.fromUrl("https://x.org/eg2/en-US/catalog")?.provider)
        assertEquals(ProviderId.SIERRA_ENCORE, CatalogDetector.fromUrl("https://x.org/iii/encore/search")?.provider)
        assertEquals(ProviderId.SIERRA_ENCORE, CatalogDetector.fromUrl("https://x.org/search~S3?/thobbit")?.provider)
        assertEquals(ProviderId.POLARIS, CatalogDetector.fromUrl("https://mybcls.polarislibrary.com/")?.provider)
        assertEquals(ProviderId.SIERRA_VEGA, CatalogDetector.fromUrl("https://nypl.na2.iiivega.com/search?query=x")?.provider)
        assertNull(CatalogDetector.fromUrl("https://www.example.org/search/results"))
    }

    @Test
    fun `OWWL's Evergreen address redirects to Aspen, and the redirect wins`() = runTest {
        val d = CatalogDetector.detect("https://evergreen.owwl.org/eg/opac/home") { _ ->
            FetchedPage("https://search.owwl.org/", Fixtures.read("detect/aspen_owwl.html"))
        }
        assertEquals(ProviderId.ASPEN, d?.provider)
        assertEquals("https://search.owwl.org", d?.baseUrl)
    }

    @Test
    fun `unreachable page falls back to the URL rule`() = runTest {
        assertEquals(ProviderId.KOHA, CatalogDetector.detect("x.org/cgi-bin/koha/opac-main.pl") { null }?.provider)
        assertNull(CatalogDetector.detect("www.example.org") { null })
    }

    @Test
    fun `input that looks like a URL`() {
        assertTrue(CatalogDetector.looksLikeUrl("seattle.bibliocommons.com"))
        assertTrue(CatalogDetector.looksLikeUrl("https://catalog.hcplc.org/polaris/"))
        assertFalse(CatalogDetector.looksLikeUrl("Seattle Public Library"))
        assertFalse(CatalogDetector.looksLikeUrl("toronto"))
    }
}
