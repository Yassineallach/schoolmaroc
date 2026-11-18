package com.mardev.nearshelf.core.registry

import com.mardev.nearshelf.core.model.Branch
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.search.LibrarySearchService
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class LibraryRegistryTest {
    private val registry = LibraryRegistry.parse(
        """
        {"version":1,"generatedAt":"2026-11-18T00:00:00Z","libraries":[
          {"name":"Seattle Public Library","country":"US","region":"WA","city":"Seattle",
           "catalog":{"provider":"BIBLIOCOMMONS","baseUrl":"https://seattle.bibliocommons.com"},
           "overdrive":{"key":"spl","websiteId":83},
           "branches":[{"id":"1","name":"Central Library","latitude":47.6,"longitude":-122.3}]},
          {"name":"Toronto Public Library","country":"CA","region":"ON","city":"Toronto",
           "catalog":{"provider":"BIBLIOCOMMONS","baseUrl":"https://tpl.bibliocommons.com"},
           "overdrive":{"key":"toronto"},"futureField":true}
        ]}
        """.trimIndent(),
    )

    @Test
    fun `entries become libraries with every service`() {
        val spl = registry.libraries.first()
        assertEquals(listOf(ProviderId.OVERDRIVE, ProviderId.BIBLIOCOMMONS), spl.services.map { it.provider })
        assertEquals("https://seattle.bibliocommons.com", spl.services.last().key)
        assertEquals(listOf(Branch("1", "Central Library", latitude = 47.6, longitude = -122.3)), spl.branches)
    }

    @Test
    fun `search matches word prefixes in name, city or region`() {
        assertEquals(listOf("Seattle Public Library"), registry.search("seat").map { it.name })
        assertEquals(listOf("Toronto Public Library"), registry.search("public on").map { it.name })
        assertTrue(registry.search("x").isEmpty())
    }

    @Test
    fun `registry entry absorbs the Hoopla service providers found and keeps its branches`() {
        val hoopla = LibraryRef(ProviderId.HOOPLA, "2", "Seattle Public Library", countryCode = "US", borrowLimitPerMonth = 15)
        val other = LibraryRef(ProviderId.OVERDRIVE, "kcls", "King County Library System", countryCode = "US")
        val merged = LibrarySearchService.merge(listOf(hoopla, other), registry.search("seattle"))
        assertEquals(2, merged.size)
        val spl = merged.first()
        assertEquals(listOf(ProviderId.OVERDRIVE, ProviderId.HOOPLA, ProviderId.BIBLIOCOMMONS), spl.services.map { it.provider })
        assertEquals(1, spl.branches.size)
    }
}
