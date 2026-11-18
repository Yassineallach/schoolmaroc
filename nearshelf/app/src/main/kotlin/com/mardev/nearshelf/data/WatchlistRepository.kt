package com.mardev.nearshelf.data

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.watch.WatchSnapshot
import com.mardev.nearshelf.data.db.WatchDao
import com.mardev.nearshelf.data.db.WatchItemEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import javax.inject.Inject
import javax.inject.Singleton

data class WatchItem(
    val key: String,
    val query: BookQuery,
    val title: String,
    val author: String?,
    val coverUrl: String?,
    val addedAt: Long,
    val lastCheckedAt: Long?,
    val snapshot: WatchSnapshot?,
)

@Singleton
class WatchlistRepository @Inject constructor(private val dao: WatchDao) {
    private val json = Json { ignoreUnknownKeys = true }

    val items: Flow<List<WatchItem>> = dao.observe().map { rows -> rows.mapNotNull(::toItem) }

    suspend fun all(): List<WatchItem> = dao.all().mapNotNull(::toItem)

    suspend fun isWatched(query: BookQuery) = dao.get(keyOf(query)) != null

    suspend fun add(query: BookQuery, title: String, author: String?, coverUrl: String?, snapshot: WatchSnapshot?) {
        val key = keyOf(query)
        dao.upsert(
            WatchItemEntity(
                key = key,
                queryJson = json.encodeToString(query),
                title = title,
                author = author,
                coverUrl = coverUrl,
                addedAt = dao.get(key)?.addedAt ?: System.currentTimeMillis(),
                lastCheckedAt = snapshot?.checkedAt,
                snapshotJson = snapshot?.let { json.encodeToString(it) },
            ),
        )
    }

    suspend fun remove(key: String) = dao.delete(key)

    suspend fun saveCheck(item: WatchItem, snapshot: WatchSnapshot) {
        dao.get(item.key)?.let { dao.upsert(it.copy(lastCheckedAt = snapshot.checkedAt, snapshotJson = json.encodeToString(snapshot))) }
    }

    private fun toItem(e: WatchItemEntity): WatchItem? = runCatching {
        WatchItem(
            e.key, json.decodeFromString<BookQuery>(e.queryJson), e.title, e.author, e.coverUrl, e.addedAt, e.lastCheckedAt,
            e.snapshotJson?.let { json.decodeFromString<WatchSnapshot>(it) },
        )
    }.getOrNull()

    companion object {
        /** Same book, same key: the ISBN when there is one, else title and author. */
        fun keyOf(q: BookQuery): String =
            q.isbn?.let { "isbn:$it" } ?: "ta:" + listOf(q.title, q.author).joinToString("|") { it?.trim()?.lowercase().orEmpty() }
    }
}
