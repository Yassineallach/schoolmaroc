package com.mardev.nearshelf.core.metadata

import com.mardev.nearshelf.core.match.Isbn
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.testing.FixtureInterceptor
import com.mardev.nearshelf.core.testing.Fixtures
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue

class OpenLibraryTest {
    private val interceptor = FixtureInterceptor { req ->
        val u = req.url
        when {
            u.encodedPath == "/isbn/9780593135204.json" -> 200 to Fixtures.read("openlibrary/isbn_9780593135204.json")
            u.encodedPath == "/isbn/9788418037016.json" -> 200 to Fixtures.read("openlibrary/isbn_9788418037016_spanish.json")
            u.encodedPath == "/search.json" && u.queryParameter("isbn") != null ->
                200 to Fixtures.read("openlibrary/search_isbn_9780593135204.json")
            u.encodedPath == "/search.json" && u.queryParameter("title") == "The Outsider" ->
                200 to Fixtures.read("openlibrary/search_title_the_outsider.json")
            u.encodedPath == "/search.json" && u.queryParameter("title") != null ->
                200 to Fixtures.read("openlibrary/search_title_project_hail_mary.json")
            else -> 404 to ""
        }
    }
    private val ol = OpenLibrary(interceptor.client())

    @Test
    fun `ISBN lookup returns the whole work`() = runTest {
        val w = ol.byIsbn("0593135202")!!
        assertEquals("/works/OL21745884W", w.workKey)
        assertEquals("Project Hail Mary", w.title)
        assertEquals(listOf("Andy Weir"), w.authors)
        assertEquals("en", w.language)
        assertTrue("9780593135211" in w.isbns, "ebook ISBN OverDrive uses")
        assertEquals(28, w.isbns.size, "55 raw ISBNs collapse to 28 once ISBN-10s become ISBN-13s")
        assertTrue(w.isbns.all { it.length == 13 })
        assertTrue(w.coverUrl!!.startsWith("https://covers.openlibrary.org/b/id/"))
    }

    @Test
    fun `Spanish edition keeps its own language and title`() = runTest {
        val w = ol.byIsbn("9788418037016")!!
        assertEquals("es", w.language)
        assertEquals("Proyecto Hail Mary", w.title)
    }

    @Test
    fun `title lookup skips the omnibus that matches loosely`() = runTest {
        val w = ol.byTitle("Project Hail Mary", "Andy Weir")!!
        assertEquals("/works/OL21745884W", w.workKey)
    }

    @Test
    fun `a shared title lists each book once, exact titles first`() = runTest {
        val c = ol.candidates("The Outsider")
        val authors = c.map { it.work.authors.first() }
        assertTrue(c.size >= 4, "several books are called The Outsider: $authors")
        assertEquals("Stephen King", authors.first(), "exact title, most published first")
        assertTrue("Richard Wright" in authors && "Barbara Delinsky" in authors)
        assertTrue(c.none { it.work.title.contains("Standing", ignoreCase = true) || it.work.title.contains("Darkness", ignoreCase = true) }, "loose title matches are left out")
        assertEquals(authors.size, authors.distinct().size, "one entry per book")
        assertTrue(c.first().firstPublished != null && c.first().editions > 0)
    }

    @Test
    fun `candidates are only asked for a bare title`() = runTest {
        val ex = QueryExpander(ol)
        assertTrue(ex.candidates(BookQuery(title = "The Outsider", author = "King")).isEmpty())
        assertTrue(ex.candidates(BookQuery(isbn = "9780593135204")).isEmpty())
        assertTrue(ex.candidates(BookQuery(title = "The Outsider")).size >= 4)
        val picked = ex.withWork(BookQuery(title = "The Outsider"), ex.candidates(BookQuery(title = "The Outsider")).first().work)
        assertEquals("Stephen King", picked.query.author)
        assertTrue(picked.query.isbns.isNotEmpty())
    }

    @Test
    fun `unknown ISBN and network failure give null`() = runTest {
        val down = OpenLibrary(FixtureInterceptor { null }.client())
        assertNull(down.byIsbn("9780000000002"))
    }

    @Test
    fun `expander fills an ISBN-only query`() = runTest {
        val e = QueryExpander(ol).expand(BookQuery(isbn = "9780593135204"))
        assertEquals("Project Hail Mary", e.query.title)
        assertEquals("Andy Weir", e.query.author)
        assertEquals("en", e.query.language)
        assertTrue("9780593135211" in e.query.isbns)
    }

    @Test
    fun `expander keeps what the user typed`() = runTest {
        val e = QueryExpander(ol).expand(BookQuery(title = "project hail mary", author = "weir"))
        assertEquals("project hail mary", e.query.title)
        assertEquals("weir", e.query.author)
        assertTrue(e.query.isbns.isNotEmpty())
    }

    @Test
    fun `scanned hardcover ISBN finds the ebook and flags the Spanish audiobook at NYPL`() = runTest {
        val expanded = QueryExpander(ol).expand(BookQuery(isbn = "9780593135204")).query
        val nypl = com.mardev.nearshelf.core.provider.overdrive.OverDriveParser
            .parseMedia(Fixtures.read("overdrive/media_nypl_project_hail_mary.json"))
        val matches = com.mardev.nearshelf.core.match.BookMatcher().match(expanded, nypl)
        assertEquals(setOf("5665700", "6268492"), matches.map { it.holding.providerItemId }.toSet())
        assertTrue(matches.single { it.holding.providerItemId == "6268492" }.otherLanguage)
    }

    @Test
    fun languageCodes() {
        assertEquals("en", LanguageCodes.toIso1("/languages/eng"))
        assertEquals("fr", LanguageCodes.toIso1("fre"))
        assertEquals("fr", LanguageCodes.toIso1("fra"))
        assertEquals("ar", LanguageCodes.toIso1("ara"))
        assertEquals("en", LanguageCodes.toIso1("English"))
        assertNull(LanguageCodes.toIso1(""))
    }

    @Test
    fun barcodes() {
        assertEquals("9780593135204", Isbn.fromBarcode("9780593135204"))
        assertNull(Isbn.fromBarcode("5012345678900"), "grocery EAN")
        assertNull(Isbn.fromBarcode("9780593135205"), "bad checksum")
    }
}
