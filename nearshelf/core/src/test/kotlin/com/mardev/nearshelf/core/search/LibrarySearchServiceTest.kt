package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.ProviderException
import kotlinx.coroutines.test.runTest
import java.net.URI
import kotlin.test.Test
import kotlin.test.assertEquals

class LibrarySearchServiceTest {

    private class FakeProvider(override val id: ProviderId, val libs: List<LibraryRef>, val fail: Boolean = false) : CatalogProvider {
        override suspend fun findLibraries(query: String): List<LibraryRef> =
            if (fail) throw ProviderException(id, ProviderException.Kind.NETWORK, "down") else libs
        override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> = emptyList()
        override fun borrowLink(library: LibraryRef, holding: Holding) = URI("https://example.org")
    }

    @Test
    fun `same library from two providers merges into one with both services`() = runTest {
        val od = LibraryRef(ProviderId.OVERDRIVE, "toronto", "Toronto Public Library", city = "Toronto", countryCode = "CA")
        val bc = LibraryRef(ProviderId.BIBLIOCOMMONS, "tpl", "Toronto Public Library", countryCode = "CA")
        val other = LibraryRef(ProviderId.OVERDRIVE, "ottawa", "Ottawa Public Library", countryCode = "CA")
        val service = LibrarySearchService(
            listOf(FakeProvider(ProviderId.OVERDRIVE, listOf(od, other)), FakeProvider(ProviderId.BIBLIOCOMMONS, listOf(bc))),
        )
        val result = service.search("toronto")
        assertEquals(2, result.libraries.size)
        val tpl = result.libraries.first()
        assertEquals("Toronto Public Library", tpl.name)
        assertEquals("Toronto", tpl.city)
        assertEquals(listOf(ProviderId.OVERDRIVE, ProviderId.BIBLIOCOMMONS), tpl.services.map { it.provider })
    }

    @Test
    fun `a failing provider is reported and the others still answer`() = runTest {
        val od = LibraryRef(ProviderId.OVERDRIVE, "nypl", "New York Public Library", countryCode = "US")
        val service = LibrarySearchService(
            listOf(FakeProvider(ProviderId.OVERDRIVE, listOf(od)), FakeProvider(ProviderId.HOOPLA, emptyList(), fail = true)),
        )
        val result = service.search("new york")
        assertEquals(listOf("New York Public Library"), result.libraries.map { it.name })
        assertEquals(setOf(ProviderId.HOOPLA), result.failedProviders)
    }

    @Test
    fun `same name in different countries stays separate`() {
        val merged = LibrarySearchService.merge(
            listOf(
                LibraryRef(ProviderId.OVERDRIVE, "a", "Richmond Public Library", countryCode = "US"),
                LibraryRef(ProviderId.OVERDRIVE, "b", "Richmond Public Library", countryCode = "CA"),
            ),
        )
        assertEquals(2, merged.size)
    }
}
