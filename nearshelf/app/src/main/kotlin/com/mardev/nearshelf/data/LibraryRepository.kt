package com.mardev.nearshelf.data

import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.data.db.SavedLibraryDao
import com.mardev.nearshelf.data.db.SavedLibraryEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LibraryRepository @Inject constructor(private val dao: SavedLibraryDao) {
    private val json = Json { ignoreUnknownKeys = true }

    val libraries: Flow<List<Library>> = dao.observe().map { rows ->
        rows.mapNotNull { runCatching { json.decodeFromString<Library>(it.json) }.getOrNull() }
    }

    /** Adds a library, or merges newly found services (e.g. Hoopla) into one already saved. */
    suspend fun add(library: Library) {
        val current = libraries.first()
        val index = current.indexOfFirst { it.id == library.id }
        val merged = if (index < 0) library else current[index].let { old ->
            old.copy(services = (old.services + library.services).distinctBy { it.provider to it.key }.sortedBy { it.provider.ordinal })
        }
        val position = if (index >= 0) index else dao.maxPosition() + 1
        dao.upsert(SavedLibraryEntity(library.id, position, json.encodeToString(merged)))
    }

    suspend fun remove(id: String) = dao.delete(id)

    /** Moves a library one place up (-1) or down (+1). */
    suspend fun move(id: String, delta: Int) {
        val ids = libraries.first().map { it.id }.toMutableList()
        val from = ids.indexOf(id)
        val to = from + delta
        if (from < 0 || to !in ids.indices) return
        ids.add(to, ids.removeAt(from))
        dao.reorder(ids)
    }
}
