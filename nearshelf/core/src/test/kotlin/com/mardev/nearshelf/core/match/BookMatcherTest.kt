package com.mardev.nearshelf.core.match

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.overdrive.OverDriveParser
import com.mardev.nearshelf.core.testing.Fixtures
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class BookMatcherTest {
    private val matcher = BookMatcher()
    private val nyplPhm = OverDriveParser.parseMedia(Fixtures.read("overdrive/media_nypl_project_hail_mary.json"))

    private fun holding(title: String, authors: List<String> = emptyList(), isbns: Set<String> = emptySet(), lang: String? = "en") =
        Holding(ProviderId.OVERDRIVE, Format.EBOOK, title, authors = authors, isbns = isbns, language = lang, providerItemId = title.hashCode().toString())

    @Test
    fun `NYPL Project Hail Mary keeps ebook and Spanish audiobook, drops summary and unrelated`() {
        val result = matcher.match(BookQuery(title = "Project Hail Mary", author = "Andy Weir"), nyplPhm)
        assertEquals(setOf("5665700", "6268492"), result.map { it.holding.providerItemId }.toSet())

        val ebook = result.single { it.holding.providerItemId == "5665700" }
        assertFalse(ebook.otherLanguage)
        assertEquals(MatchedHolding.Reason.TITLE_AUTHOR, ebook.reason)

        val spanish = result.single { it.holding.providerItemId == "6268492" }
        assertTrue(spanish.otherLanguage, "Spanish edition must be flagged")
        assertEquals("es", spanish.holding.language)
    }

    @Test
    fun `title-only query gives the same matches`() {
        val result = matcher.match(BookQuery(title = "project hail mary"), nyplPhm)
        assertEquals(setOf("5665700", "6268492"), result.map { it.holding.providerItemId }.toSet())
    }

    @Test
    fun `ISBN from the work set matches regardless of title`() {
        val result = matcher.match(BookQuery(isbns = setOf("9780593135211", "9780593135204")), nyplPhm)
        assertEquals(listOf("5665700"), result.map { it.holding.providerItemId })
        assertEquals(MatchedHolding.Reason.ISBN, result.single().reason)
    }

    @Test
    fun `ISBN-10 in the query matches the ISBN-13 edition`() {
        val h = holding("Anything", isbns = setOf("9780593135204"))
        assertEquals(1, matcher.match(BookQuery(isbn = "0593135202"), listOf(h)).size)
    }

    @Test
    fun `summary is kept when the user searches for one`() {
        val result = matcher.match(BookQuery(title = "Summary of Andy Weir's Project Hail Mary"), nyplPhm)
        assertEquals(listOf("6597161"), result.map { it.holding.providerItemId })
    }

    @Test
    fun `study aids are excluded`() {
        val q = BookQuery(title = "Dune")
        for (t in listOf("Study Guide: Dune", "Dune Workbook", "SparkNotes Dune", "Analysis of Dune")) {
            assertTrue(matcher.match(q, listOf(holding(t))).isEmpty(), t)
        }
    }

    @Test
    fun `sequels and shared prefixes are not matches`() {
        assertTrue(matcher.match(BookQuery(title = "Dune"), listOf(holding("Dune Messiah"))).isEmpty())
        assertTrue(
            matcher.match(
                BookQuery(title = "Harry Potter and the Sorcerer's Stone"),
                listOf(holding("Harry Potter and the Chamber of Secrets")),
            ).isEmpty(),
        )
    }

    @Test
    fun `subtitle, leading article, punctuation and diacritics are ignored`() {
        val q = BookQuery(title = "Martian", author = "Weir")
        assertEquals(1, matcher.match(q, listOf(holding("The Martian: A Novel", listOf("Andy Weir")))).size)
        assertEquals(1, matcher.match(BookQuery(title = "Les Misérables"), listOf(holding("Les Miserables (Unabridged)"))).size)
    }

    @Test
    fun `author surname must match when both sides name one`() {
        val q = BookQuery(title = "The Shining", author = "Stephen King")
        assertTrue(matcher.match(q, listOf(holding("The Shining", listOf("Some Imitator")))).isEmpty())
        assertEquals(1, matcher.match(q, listOf(holding("The Shining", listOf("King, Stephen")))).size)
        assertEquals(1, matcher.match(q, listOf(holding("The Shining"))).size, "no authors on record: title decides")
    }

    @Test
    fun `explicit query language drives the other-language flag`() {
        val result = matcher.match(
            BookQuery(title = "Project Hail Mary", language = "es"),
            nyplPhm,
        )
        assertTrue(result.single { it.holding.language == "en" }.otherLanguage)
        assertFalse(result.single { it.holding.language == "es" }.otherLanguage)
    }
}
