package com.mardev.nearshelf.core.provider.hoopla

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.net.NearshelfHttp
import kotlinx.coroutines.runBlocking
import org.junit.Assume.assumeTrue
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertTrue

/** Real network; run with -Pnearshelf.live=true. */
class HooplaLiveTest {
    private val provider = HooplaProvider(NearshelfHttp.client("0.1.0-test"))

    @BeforeTest
    fun gate() = assumeTrue(System.getProperty("nearshelf.live") == "true")

    @Test
    fun liveLookupAndSearch() = runBlocking {
        val spl = provider.findLibraries("seattle").first { it.name == "Seattle Public Library" }
        println("LIVE hoopla library: $spl")
        val q = BookQuery(title = "The Hobbit", author = "J. R. R. Tolkien")
        val m = BookMatcher().match(q, provider.search(spl, q))
        println("LIVE hoopla hobbit: ${m.map { "${it.holding.format}/${it.holding.language}/${it.holding.providerItemId}" }}")
        assertTrue(m.isNotEmpty())
    }
}
