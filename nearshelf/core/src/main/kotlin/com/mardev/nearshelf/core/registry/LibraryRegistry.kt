package com.mardev.nearshelf.core.registry

import com.mardev.nearshelf.core.match.TextNormalizer
import com.mardev.nearshelf.core.model.Branch
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

/** assets/libraries.json, built and validated by tools/registry/build_registry.py. */
@Serializable
data class RegistryFile(
    val version: Int,
    val generatedAt: String,
    val libraries: List<RegistryLibrary>,
)

@Serializable
data class RegistryLibrary(
    val name: String,
    val country: String,
    val region: String? = null,
    val city: String? = null,
    val catalog: RegistryCatalog? = null,
    val overdrive: RegistryOverDrive? = null,
    val hoopla: RegistryHoopla? = null,
    val branches: List<Branch> = emptyList(),
)

@Serializable
data class RegistryCatalog(val provider: ProviderId, val baseUrl: String)

@Serializable
data class RegistryOverDrive(val key: String, val websiteId: Long? = null)

@Serializable
data class RegistryHoopla(val id: String, val borrowLimitPerMonth: Int? = null)

/**
 * Maps a library to its catalog systems. Physical catalogs have no shared directory,
 * so this is Nearshelf's own list: the bundled copy, replaced by a weekly download.
 */
class LibraryRegistry(val file: RegistryFile) {

    val libraries: List<Library> = file.libraries.map(::toLibrary)
    private val byId = libraries.associateBy { it.id }

    fun find(id: String): Library? = byId[id]

    /** Every query word must appear in the name, city or region. */
    fun search(query: String, limit: Int = 20): List<Library> {
        val words = TextNormalizer.basic(query).split(' ').filter { it.isNotBlank() }
        if (words.isEmpty() || query.trim().length < 2) return emptyList()
        return libraries.filter { lib ->
            val hay = TextNormalizer.basic(listOfNotNull(lib.name, lib.city, lib.region).joinToString(" "))
            words.all { w -> hay.split(' ').any { it.startsWith(w) } }
        }.take(limit)
    }

    companion object {
        val json = Json { ignoreUnknownKeys = true }

        fun parse(text: String): LibraryRegistry = LibraryRegistry(json.decodeFromString<RegistryFile>(text))

        fun toLibrary(r: RegistryLibrary): Library {
            val services = buildList {
                r.overdrive?.let {
                    add(LibraryRef(ProviderId.OVERDRIVE, it.key, r.name, r.city, r.region, r.country, "https://libbyapp.com/library/${it.key}"))
                }
                r.hoopla?.let {
                    add(LibraryRef(ProviderId.HOOPLA, it.id, r.name, r.city, r.region, r.country, "https://www.hoopladigital.com", borrowLimitPerMonth = it.borrowLimitPerMonth))
                }
                r.catalog?.let {
                    add(LibraryRef(it.provider, it.baseUrl, r.name, r.city, r.region, r.country, it.baseUrl))
                }
            }
            return Library(
                id = Library.idFor(r.name, r.country),
                name = r.name,
                city = r.city,
                region = r.region,
                countryCode = r.country,
                services = services,
                branches = r.branches,
            )
        }
    }
}
