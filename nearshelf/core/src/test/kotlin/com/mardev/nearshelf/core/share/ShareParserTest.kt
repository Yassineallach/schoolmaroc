package com.mardev.nearshelf.core.share

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.testing.Fixtures
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

/**
 * Share strings follow the shapes each app sends (text + link). Page fixtures are
 * real responses fetched 2026-11-18, trimmed to the parts the parser reads.
 */
class ShareParserTest {
    private val fetched = mutableListOf<String>()
    private val pages = mapOf(
        "https://www.goodreads.com/book/show/54493401-project-hail-mary" to "share/goodreads_54493401.html",
        "https://www.goodreads.com/book/show/54493401" to "share/goodreads_54493401.html",
        "https://a.co/d/7xQ2kPz" to "share/amazon_dp_0593135202.html",
    )
    private val parser = ShareParser { url ->
        fetched += url
        pages[url]?.let {
            val final = if (url.startsWith("https://a.co/")) "https://www.amazon.com/Project-Hail-Mary-Andy-Weir/dp/B08FHBV4ZX" else url
            FetchedPage(final, Fixtures.read(it))
        }
    }

    @Test
    fun `goodreads share reads JSON-LD Book`() = runTest {
        val q = parser.parse("Check out Project Hail Mary by Andy Weir on Goodreads: https://www.goodreads.com/book/show/54493401-project-hail-mary")
        assertEquals(BookQuery(title = "Project Hail Mary", author = "Andy Weir", isbn = "9780593135204", language = "en"), q)
    }

    @Test
    fun `goodreads bare link`() = runTest {
        assertEquals("9780593135204", parser.parse("https://www.goodreads.com/book/show/54493401")?.isbn)
    }

    @Test
    fun `goodreads page unreachable falls back to share text, then slug`() = runTest {
        val q = parser.parse("Project Hail Mary by Andy Weir https://www.goodreads.com/book/show/1-unreachable")
        assertEquals(BookQuery(title = "Project Hail Mary", author = "Andy Weir"), q)
        assertEquals(BookQuery(title = "the slug title"), parser.parse("https://www.goodreads.com/book/show/2-the-slug-title"))
    }

    @Test
    fun `amazon dp link with ISBN-10 ASIN needs no fetch`() = runTest {
        val q = parser.parse("Project Hail Mary: A Novel https://www.amazon.com/dp/0593135202/ref=cm_sw_r_as_gl_api_gl_i_ABC?_encoding=UTF8")
        assertEquals("9780593135204", q?.isbn)
        assertTrue(fetched.isEmpty())
    }

    @Test
    fun `amazon short link with Kindle ASIN reads the page title`() = runTest {
        val q = parser.parse("Project Hail Mary: A Novel https://a.co/d/7xQ2kPz")
        assertEquals(BookQuery(title = "Project Hail Mary: A Novel", author = "Andy Weir", isbn = "9780593135204"), q)
    }

    @Test
    fun `amazon page titles`() {
        assertEquals(
            BookQuery(title = "Project Hail Mary: A Novel", author = "Andy Weir"),
            parser.amazonTitle("Project Hail Mary: A Novel eBook : Weir, Andy: Amazon.com: Kindle Store"),
        )
        assertEquals(
            BookQuery(title = "Klara and the Sun", author = "Kazuo Ishiguro", isbn = "9780571364886"),
            parser.amazonTitle("Klara and the Sun: Ishiguro, Kazuo: 9780571364886: Amazon.co.uk: Books"),
        )
        assertNull(parser.amazonTitle("Amazon.com"))
    }

    @Test
    fun `storygraph is never fetched and uses the share text`() = runTest {
        val q = parser.parse("I'm reading Project Hail Mary by Andy Weir on The StoryGraph https://app.thestorygraph.com/books/0bcd6a35-4b2b-4b1a-9c5b-3c3a8e0b2a11")
        assertEquals(BookQuery(title = "Project Hail Mary", author = "Andy Weir"), q)
        assertTrue(fetched.isEmpty())
    }

    @Test
    fun `ISBN-13 in text wins`() = runTest {
        assertEquals("9780593135204", parser.parse("ISBN 978-0-593-13520-4 please")?.isbn)
        assertEquals("9780593135204", parser.parse("9780593135204")?.isbn)
    }

    @Test
    fun `ISBN-10 counts only when labelled`() = runTest {
        assertEquals("9780593135204", parser.parse("ISBN: 0593135202")?.isbn)
        assertNull(parser.parse("Call me at 0593135202")?.isbn)
    }

    @Test
    fun `plain title text`() = runTest {
        assertEquals(BookQuery(title = "The Left Hand of Darkness"), parser.parse("  The Left Hand of Darkness "))
    }

    @Test
    fun `blank and link-only junk`() = runTest {
        assertNull(parser.parse("   "))
        assertNull(parser.parse("https://example.org/nothing"))
    }
}
