package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.CatalogProvider
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope

data class LibrarySearchResult(
    val libraries: List<Library>,
    val failedProviders: Set<ProviderId>,
)

/**
 * Asks every provider for libraries matching [query] in parallel and merges the
 * answers into one [Library] per real-world library (same normalized name and
 * country), so "Toronto Public Library" shows once with Libby and BiblioCommons.
 * The bundled library registry joins here in milestone 5.
 */
class LibrarySearchService(private val providers: List<CatalogProvider>) {

    suspend fun search(query: String): LibrarySearchResult = coroutineScope {
        val answers = providers.map { p ->
            async {
                try {
                    p.id to Result.success(p.findLibraries(query))
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    p.id to Result.failure(e)
                }
            }
        }.awaitAll()
        LibrarySearchResult(
            libraries = merge(answers.flatMap { it.second.getOrDefault(emptyList()) }),
            failedProviders = answers.filter { it.second.isFailure }.map { it.first }.toSet(),
        )
    }

    companion object {
        fun merge(refs: List<LibraryRef>): List<Library> {
            val byId = LinkedHashMap<String, MutableList<LibraryRef>>()
            for (ref in refs) byId.getOrPut(Library.idFor(ref.name, ref.countryCode)) { mutableListOf() } += ref
            return byId.map { (id, group) ->
                val first = group.first()
                Library(
                    id = id,
                    name = first.name,
                    city = group.firstNotNullOfOrNull { it.city },
                    region = group.firstNotNullOfOrNull { it.region },
                    countryCode = first.countryCode,
                    services = group.distinctBy { it.provider to it.key }.sortedBy { it.provider.ordinal },
                )
            }
        }
    }
}
