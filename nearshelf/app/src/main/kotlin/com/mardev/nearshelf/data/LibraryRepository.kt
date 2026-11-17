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

    suspend fun add(library: Library) {
        val existing = libraries.first().indexOfFirst { it.id == library.id }
        val position = if (existing >= 0) existing else dao.maxPosition() + 1
        dao.upsert(SavedLibraryEntity(library.id, position, json.encodeToString(library)))
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
