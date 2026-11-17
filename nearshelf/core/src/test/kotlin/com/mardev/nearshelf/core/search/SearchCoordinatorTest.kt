package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.provider.overdrive.OverDriveProvider
import com.mardev.nearshelf.core.testing.FixtureInterceptor
import com.mardev.nearshelf.core.testing.Fixtures
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.runTest
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertIs
import kotlin.test.assertTrue

class SearchCoordinatorTest {
    private val interceptor = FixtureInterceptor { req ->
        when (req.url.pathSegments.getOrNull(2)) {
            "nypl" -> 200 to Fixtures.read("overdrive/media_nypl_project_hail_mary.json")
            "broken" -> 500 to ""
            else -> null
        }
    }
    private val coordinator = SearchCoordinator(listOf(OverDriveProvider(interceptor.client())))

    private fun lib(key: String) = Library(
        id = key, name = key, services = listOf(LibraryRef(ProviderId.OVERDRIVE, key, key)),
    )

    @Test
    fun `emits loading for every service first, then one final state each`() = runTest {
        val updates = coordinator.search(listOf(lib("nypl"), lib("broken")), BookQuery(title = "Project Hail Mary")).toList()
        assertEquals(4, updates.size)
        assertTrue(updates.take(2).all { it.state == ServiceState.Loading })

        val nypl = updates.drop(2).single { it.libraryId == "nypl" }.state
        assertIs<ServiceState.Done>(nypl)
        assertEquals(setOf("5665700", "6268492"), nypl.matches.map { it.holding.providerItemId }.toSet())

        val broken = updates.drop(2).single { it.libraryId == "broken" }.state
        assertIs<ServiceState.Failed>(broken)
        assertEquals(ProviderException.Kind.HTTP, broken.kind)
    }

    @Test
    fun `services without a registered provider are skipped`() = runTest {
        val hooplaOnly = Library("h", "h", services = listOf(LibraryRef(ProviderId.HOOPLA, "1", "h")))
        assertTrue(coordinator.search(listOf(hooplaOnly), BookQuery(title = "x")).toList().isEmpty())
    }
}
