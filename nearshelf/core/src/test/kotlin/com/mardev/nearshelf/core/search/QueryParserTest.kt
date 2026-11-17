package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.model.BookQuery
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

class QueryParserTest {
    @Test
    fun isbn13WithDashes() = assertEquals(BookQuery(isbn = "9780593135204"), QueryParser.parse("978-0-593-13520-4"))

    @Test
    fun isbn10BecomesIsbn13() = assertEquals(BookQuery(isbn = "9780593135204"), QueryParser.parse("0593135202"))

    @Test
    fun invalidChecksumIsTreatedAsTitle() = assertEquals(BookQuery(title = "9780593135205"), QueryParser.parse("9780593135205"))

    @Test
    fun titleByAuthor() =
        assertEquals(BookQuery(title = "Project Hail Mary", author = "Andy Weir"), QueryParser.parse("  Project Hail Mary by Andy Weir "))

    @Test
    fun plainTitle() = assertEquals(BookQuery(title = "Stand by"), QueryParser.parse("Stand by"))

    @Test
    fun blank() = assertNull(QueryParser.parse("   "))
}
