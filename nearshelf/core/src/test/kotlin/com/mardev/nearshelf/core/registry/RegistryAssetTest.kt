package com.mardev.nearshelf.core.registry

import com.mardev.nearshelf.core.model.ProviderId
import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

/** Validates the bundled app/src/main/assets/libraries.json (same rules as tools/registry/validate_registry.py). */
class RegistryAssetTest {
    private val file = File("../app/src/main/assets/libraries.json")
    private val registry by lazy { LibraryRegistry.parse(file.readText()) }

    @Test
    fun `bundled registry parses and meets the seed target`() {
        assertTrue(file.exists(), "run tools/registry/build_registry.py")
        assertEquals(1, registry.file.version)
        assertTrue(registry.libraries.size >= 100, "only ${registry.libraries.size} libraries")
    }

    @Test
    fun `entries are unique, have a service, and use valid URLs, keys and coordinates`() {
        assertEquals(registry.libraries.size, registry.libraries.map { it.id }.toSet().size, "duplicate library")
        for (lib in registry.libraries) {
            assertTrue(lib.services.isNotEmpty(), "${lib.name}: no service")
            lib.services.filter { it.provider.kind == ProviderId.Kind.PHYSICAL }.forEach { ref ->
                assertTrue(ref.key.startsWith("https://"), "${lib.name}: ${ref.key}")
                // The URL alone must point at the same software, or the HTML marker settled it.
                CatalogDetector.fromUrl(ref.key)?.let { assertEquals(ref.provider, it.provider, "${lib.name}: ${ref.key}") }
            }
            lib.services.filter { it.provider == ProviderId.OVERDRIVE }.forEach {
                assertTrue(it.key.matches(Regex("[A-Za-z0-9_-]+")), "${lib.name}: Libby key ${it.key}")
            }
            assertEquals(lib.branches.size, lib.branches.map { it.id }.toSet().size, "${lib.name}: duplicate branch id")
            lib.branches.forEach { b ->
                assertTrue(b.name.isNotBlank(), "${lib.name}: blank branch")
                assertEquals(b.latitude == null, b.longitude == null, "${lib.name}/${b.name}: half a coordinate")
                b.latitude?.let { assertTrue(it in -90.0..90.0 && b.longitude!! in -180.0..180.0, "${lib.name}/${b.name}") }
            }
        }
    }
}
