package com.mardev.nearshelf.core.provider.bibliocommons

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.net.NearshelfHttp
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.provider.koha.KohaProvider
import kotlinx.coroutines.runBlocking
import org.junit.Assume.assumeTrue
import kotlin.test.BeforeTest
import kotlin.test.Test
import kotlin.test.assertTrue

/** Real network; run with -Pnearshelf.live=true. Koha may answer BLOCKED (rate limits): that's reported, not failed. */
class PhysicalLiveTest {
    private val client = NearshelfHttp.client("0.1.0-test")

    @BeforeTest
    fun gate() = assumeTrue(System.getProperty("nearshelf.live") == "true")

    @Test
    fun biblioCommonsSeattle() = runBlocking {
        val ref = LibraryRef(ProviderId.BIBLIOCOMMONS, "https://seattle.bibliocommons.com", "Seattle Public Library")
        val h = BiblioCommonsProvider(client).search(ref, BookQuery(title = "Project Hail Mary", author = "Andy Weir"))
        val bk = h.first { it.copies.isNotEmpty() }
        println("LIVE seattle: ${bk.title} ${bk.edition ?: ""} copies=${bk.copies.size} onShelf=${bk.copies.count { it.status == CopyStatus.AVAILABLE }} branches=${bk.copies.map { it.branchName }.distinct().size}")
        assertTrue(bk.copies.size > 10)
    }

    @Test
    fun kohaPillsbury() = runBlocking {
        val ref = LibraryRef(ProviderId.KOHA, "https://pillsbury.nhais.bywatersolutions.com", "Pillsbury Free Library")
        try {
            val h = KohaProvider(client).search(ref, BookQuery(title = "The Hobbit", author = "J. R. R. Tolkien"))
            println("LIVE pillsbury: ${h.size} records, copies=${h.sumOf { it.copies.size }}")
        } catch (e: ProviderException) {
            println("LIVE pillsbury: ${e.kind} (${e.message})")
            assertTrue(e.kind == ProviderException.Kind.BLOCKED || e.kind == ProviderException.Kind.RATE_LIMITED)
        }
    }
}
