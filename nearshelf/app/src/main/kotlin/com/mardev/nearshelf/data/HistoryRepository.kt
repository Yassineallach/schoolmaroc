package com.mardev.nearshelf.data

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.data.db.HistoryDao
import com.mardev.nearshelf.data.db.HistoryEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import javax.inject.Inject
import javax.inject.Singleton

data class HistoryItem(val key: String, val query: BookQuery, val title: String, val author: String?, val coverUrl: String?, val searchedAt: Long)

/** Recent lookups, kept on the device only (newest 50). */
@Singleton
class HistoryRepository @Inject constructor(private val dao: HistoryDao) {
    private val json = Json { ignoreUnknownKeys = true }

    fun recent(limit: Int = 50): Flow<List<HistoryItem>> = dao.observe(limit).map { rows ->
        rows.mapNotNull { e ->
            runCatching { HistoryItem(e.key, json.decodeFromString<BookQuery>(e.queryJson), e.title, e.author, e.coverUrl, e.searchedAt) }.getOrNull()
        }
    }

    suspend fun record(query: BookQuery, title: String, author: String?, coverUrl: String?) {
        dao.upsert(HistoryEntity(WatchlistRepository.keyOf(query), json.encodeToString(query), title, author, coverUrl, System.currentTimeMillis()))
        dao.trim(KEEP)
    }

    suspend fun remove(key: String) = dao.delete(key)
    suspend fun clear() = dao.clear()

    private companion object {
        const val KEEP = 50
    }
}
