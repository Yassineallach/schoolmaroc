package com.mardev.nearshelf.core.provider.overdrive

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.net.NearshelfHttp
import kotlinx.coroutines.runBlocking
import org.junit.Assume.assumeTrue
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertTrue

/**
 * Hits the real endpoints. Skipped unless run with `-Pnearshelf.live=true`
 * (e.g. `./gradlew :core:test -Pnearshelf.live=true --tests '*LiveTest'`).
 * Asserts shape, not numbers: availability changes daily.
 */
class OverDriveLiveTest {
    private val provider = OverDriveProvider(NearshelfHttp.client("0.1.0-test"))

    @BeforeTest
    fun gate() = assumeTrue(System.getProperty("nearshelf.live") == "true")

    @Test
    fun liveLookupAndSearch() = runBlocking {
        val nypl = provider.findLibraries("new york public").first { it.key == "nypl" }
        val holdings = provider.search(nypl, BookQuery(title = "project hail mary"))
        val ebook = holdings.first { it.providerItemId == "5665700" }
        println("LIVE nypl ebook: owned=${ebook.owned} available=${ebook.available} holds=${ebook.holds} wait=${ebook.waitDays}")
        println("LIVE link: ${provider.borrowLink(nypl, ebook)}")
        assertTrue(ebook.format == Format.EBOOK && (ebook.owned ?: 0) > 0)
        val toronto = provider.findLibraries("toronto").first { it.key == "toronto" }
        val tpl = provider.search(toronto, BookQuery(isbn = "9780593135211"))
        println("LIVE toronto by ISBN: ${tpl.map { "${it.title}/${it.format}/owned=${it.owned}/holds=${it.holds}" }}")
    }
}
