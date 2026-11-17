package com.mardev.nearshelf.core.provider.overdrive

import com.mardev.nearshelf.core.model.BookQuery
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
import kotlin.test.assertTrue

class OverDriveProviderTest {

    private val nypl = LibraryRef(ProviderId.OVERDRIVE, "nypl", "The New York Public Library")

    private val interceptor = FixtureInterceptor { req ->
        val url = req.url
        when {
            url.host == "locate.libbyapp.com" && url.encodedPath == "/autocomplete/new%20york%20public" ->
                200 to Fixtures.read("overdrive/locate_new_york_public.json")
            url.host == "thunder.api.overdrive.com" && url.encodedPath == "/v2/libraries/nypl/media" &&
                url.queryParameter("query") == "9780593135211" ->
                200 to Fixtures.read("overdrive/media_nypl_isbn_9780593135211.json")
            url.host == "thunder.api.overdrive.com" && url.encodedPath == "/v2/libraries/nypl/media" ->
                200 to Fixtures.read("overdrive/media_nypl_project_hail_mary.json")
            url.encodedPath.startsWith("/v2/libraries/ratelimited") -> 429 to ""
            else -> null
        }
    }
    private val provider = OverDriveProvider(interceptor.client())

    @Test
    fun `findLibraries encodes spaces as percent-20 in the path`() = runTest {
        val libs = provider.findLibraries("new york public")
        assertTrue(libs.any { it.key == "nypl" })
        assertEquals("/autocomplete/new%20york%20public", interceptor.requests.single().url.encodedPath)
    }

    @Test
    fun `findLibraries ignores one-letter queries without a request`() = runTest {
        assertTrue(provider.findLibraries("n").isEmpty())
        assertTrue(interceptor.requests.isEmpty())
    }

    @Test
    fun `search by title sends title and author as one query`() = runTest {
        val holdings = provider.search(nypl, BookQuery(title = "Project Hail Mary", author = "Andy Weir"))
        assertEquals(14, holdings.size)
        val url = interceptor.requests.single().url
        assertEquals("Project Hail Mary Andy Weir", url.queryParameter("query"))
        assertEquals("24", url.queryParameter("perPage"))
    }

    @Test
    fun `search by ISBN uses the ISBN`() = runTest {
        val holdings = provider.search(nypl, BookQuery(isbn = "9780593135211"))
        assertEquals("5665700", holdings.single().providerItemId)
    }

    @Test
    fun `unknown library key maps to NOT_FOUND`() = runTest {
        val e = assertFailsWith<ProviderException> {
            provider.search(nypl.copy(key = "doesnotexist"), BookQuery(title = "x"))
        }
        assertEquals(ProviderException.Kind.NOT_FOUND, e.kind)
    }

    @Test
    fun `429 maps to RATE_LIMITED`() = runTest {
        val e = assertFailsWith<ProviderException> {
            provider.search(nypl.copy(key = "ratelimited"), BookQuery(title = "x"))
        }
        assertEquals(ProviderException.Kind.RATE_LIMITED, e.kind)
    }

    @Test
    fun `borrow link opens the Libby title page`() {
        val holding = OverDriveParser.parseMedia(Fixtures.read("overdrive/media_nypl_isbn_9780593135211.json")).single()
        assertEquals(URI("https://libbyapp.com/library/nypl/title/5665700"), provider.borrowLink(nypl, holding))
    }

    @Test
    fun `borrow link rejects keys that would break the path`() {
        assertFailsWith<IllegalArgumentException> { OverDriveProvider.libbyTitleUri("ny/pl", "1") }
        assertFailsWith<IllegalArgumentException> { OverDriveProvider.libbyTitleUri("nypl", "abc") }
    }
}
