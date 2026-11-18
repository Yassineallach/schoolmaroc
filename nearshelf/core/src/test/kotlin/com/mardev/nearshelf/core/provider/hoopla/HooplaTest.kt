package com.mardev.nearshelf.core.provider.hoopla

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.search.LibrarySearchService
import com.mardev.nearshelf.core.testing.FixtureInterceptor
import com.mardev.nearshelf.core.testing.Fixtures
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.test.runTest
import okio.Buffer
import java.net.URI
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class HooplaTest {
    private fun bodyOf(req: okhttp3.Request) = Buffer().also { req.body?.writeTo(it) }.readUtf8()

    private val interceptor = FixtureInterceptor { req ->
        val u = req.url
        when {
            u.encodedPath == "/core/libraries/autocomplete" ->
                200 to Fixtures.read("hoopla/libraries_${u.queryParameter("query")!!.replace(' ', '_')}.json")
            u.encodedPath == "/graphql" -> {
                val b = bodyOf(req)
                when {
                    "Hail Mary" in b -> 200 to Fixtures.read("hoopla/search_project_hail_mary_andy_weir.json")
                    "Martian" in b -> 200 to Fixtures.read("hoopla/search_the_martian_andy_weir.json")
                    "Hobbit" in b -> 200 to Fixtures.read("hoopla/search_the_hobbit_tolkien.json")
                    "broken" in b -> 200 to """{"errors":[{"message":"boom"}]}"""
                    else -> 500 to ""
                }
            }
            else -> null
        }
    }
    private val provider = HooplaProvider(interceptor.client())
    private val lapl = LibraryRef(ProviderId.HOOPLA, "9", "Los Angeles Public Library")
    private val matcher = BookMatcher()

    @Test
    fun `libraries drop the state suffix and keep the monthly limit`() = runTest {
        val libs = provider.findLibraries("los angeles")
        val la = libs.first { it.key == "9" }
        assertEquals("Los Angeles Public Library", la.name)
        assertEquals("CA", la.region)
        assertEquals(15, la.borrowLimitPerMonth)
        assertTrue(interceptor.requests.all { it.header("app") == "WWW" && it.header("ws-api") == "2.1" })
    }

    @Test
    fun `Hoopla and Libby entries for the same library merge`() = runTest {
        val hoopla = provider.findLibraries("seattle").first { it.name == "Seattle Public Library" }
        val libby = LibraryRef(ProviderId.OVERDRIVE, "spl", "Seattle Public Library", countryCode = "US")
        val merged = LibrarySearchService.merge(listOf(libby, hoopla))
        assertEquals(1, merged.size)
        assertEquals(listOf(ProviderId.OVERDRIVE, ProviderId.HOOPLA), merged.single().services.map { it.provider })
    }

    @Test
    fun `search keeps books only and marks availability unknown`() = runTest {
        val h = provider.search(lapl, BookQuery(title = "The Hobbit", author = "J. R. R. Tolkien"))
        assertTrue(h.isNotEmpty())
        assertTrue(h.all { it.format in setOf(Format.EBOOK, Format.AUDIOBOOK, Format.OTHER) })
        assertTrue(h.none { it.availabilityKnown })
        val ebook = h.first { it.providerItemId == "14818633" }
        assertEquals(Format.EBOOK, ebook.format)
        assertEquals("en", ebook.language)
        assertEquals(setOf("9780547951973"), ebook.isbns)
        assertTrue(ebook.coverUrl!!.matches(Regex("https://cover\\.hoopladigital\\.com/[A-Za-z0-9_]+_270\\.jpeg")), ebook.coverUrl)
    }

    @Test
    fun `Hobbit matches Tolkien editions, drops the craft book and the French summary`() = runTest {
        val q = BookQuery(title = "The Hobbit", author = "J. R. R. Tolkien")
        val m = matcher.match(q, provider.search(lapl, q))
        val ids = m.map { it.holding.providerItemId }.toSet()
        assertTrue("14818633" in ids && "13496436" in ids)
        assertFalse("14383657" in ids, "Story Grid book by Shawn Coyne")
        assertFalse("12920034" in ids, "French summary")
        assertTrue(m.all { it.holding.authors.any { a -> "Tolkien" in a } })
    }

    @Test
    fun `Project Hail Mary on Hoopla is the Italian audiobook, flagged`() = runTest {
        val q = BookQuery(title = "Project Hail Mary", author = "Andy Weir", language = "en")
        val m = matcher.match(q, provider.search(lapl, q))
        val audio = m.single { it.holding.providerItemId == "19370874" }
        assertEquals("it", audio.holding.language)
        assertTrue(audio.otherLanguage)
        assertTrue(m.none { "Summary" in it.holding.title })
    }

    @Test
    fun `The Martian on Hoopla is only study aids, so nothing matches`() = runTest {
        val q = BookQuery(title = "The Martian", author = "Andy Weir")
        assertTrue(matcher.match(q, provider.search(lapl, q)).isEmpty())
    }

    @Test
    fun `one request serves every Hoopla library`() = runTest {
        val q = BookQuery(title = "The Hobbit", author = "J. R. R. Tolkien")
        val libs = (1..4).map { LibraryRef(ProviderId.HOOPLA, "$it", "Lib $it") }
        val results = libs.map { async { provider.search(it, q) } }.awaitAll()
        assertTrue(results.all { it == results.first() })
        assertEquals(1, interceptor.requests.count { it.url.encodedPath == "/graphql" })
    }

    @Test
    fun `GraphQL errors and HTTP errors become ProviderExceptions, and are not cached`() = runTest {
        assertEquals(
            ProviderException.Kind.PARSE,
            assertFailsWith<ProviderException> { provider.search(lapl, BookQuery(title = "broken")) }.kind,
        )
        assertEquals(
            ProviderException.Kind.HTTP,
            assertFailsWith<ProviderException> { provider.search(lapl, BookQuery(title = "nothing")) }.kind,
        )
        assertFailsWith<ProviderException> { provider.search(lapl, BookQuery(title = "nothing")) }
        assertEquals(3, interceptor.requests.size)
    }

    @Test
    fun `all-caps cities are tidied`() {
        assertEquals("Seattle", HooplaParser.tidyCase("SEATTLE"))
        assertEquals("New York Mills", HooplaParser.tidyCase("NEW YORK MILLS"))
        assertEquals("McAllen", HooplaParser.tidyCase("McAllen"))
    }

    @Test
    fun `deep link`() {
        assertEquals(URI("https://www.hoopladigital.com/title/19370874"), HooplaProvider.titleUri("19370874"))
        assertFailsWith<IllegalArgumentException> { HooplaProvider.titleUri("../x") }
    }
}
