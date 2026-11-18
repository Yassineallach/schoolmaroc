package com.mardev.nearshelf.core.share

import com.mardev.nearshelf.core.metadata.OpenLibrary
import com.mardev.nearshelf.core.metadata.QueryExpander
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.net.NearshelfHttp
import kotlinx.coroutines.runBlocking
import org.junit.Assume.assumeTrue
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Real network; run with -Pnearshelf.live=true. Uses Nearshelf's own User-Agent. */
class ShareLiveTest {
    private val client = NearshelfHttp.client("0.1.0-test")

    @BeforeTest
    fun gate() = assumeTrue(System.getProperty("nearshelf.live") == "true")

    @Test
    fun goodreadsAndOpenLibrary() = runBlocking {
        val q = ShareParser(OkHttpPageFetcher(client))
            .parse("Check out Project Hail Mary by Andy Weir on Goodreads: https://www.goodreads.com/book/show/54493401-project-hail-mary")
        println("LIVE goodreads share -> $q")
        assertEquals("9780593135204", q?.isbn)

        val e = QueryExpander(OpenLibrary(client)).expand(BookQuery(isbn = "9780593135204"))
        println("LIVE openlibrary -> title=${e.query.title} author=${e.query.author} lang=${e.query.language} isbns=${e.query.isbns.size} cover=${e.coverUrl}")
        assertTrue(e.query.isbns.size > 10)
    }
}
