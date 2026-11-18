package com.mardev.nearshelf.core.metadata

import com.mardev.nearshelf.core.cache.CacheTtl
import com.mardev.nearshelf.core.cache.KeyValueCache
import com.mardev.nearshelf.core.model.BookQuery
import kotlinx.serialization.json.Json
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class ExpandedQuery(val query: BookQuery, val coverUrl: String? = null, val work: WorkInfo? = null)

/**
 * Fills a query in from Open Library before the catalogs are searched: an ISBN gains
 * its title, author, language and every ISBN of the work (so other editions and
 * formats match); a title gains the work's ISBN set. Any failure keeps the query as typed.
 */
class QueryExpander(
    private val openLibrary: OpenLibrary,
    private val cache: KeyValueCache? = null,
    private val clock: () -> Long = System::currentTimeMillis,
) {
    private val json = Json { ignoreUnknownKeys = true }

    suspend fun expand(query: BookQuery): ExpandedQuery = withContext(Dispatchers.IO) {
        val key = "ol|" + listOf(query.isbn, query.title, query.author).joinToString("|") { it?.trim()?.lowercase().orEmpty() }
        val cached = cache?.get(key)?.takeIf { clock() - it.second < CacheTtl.OPEN_LIBRARY_MILLIS }
            ?.let { runCatching { json.decodeFromString<WorkInfo>(it.first) }.getOrNull() }
        val work = cached ?: when {
            !query.isbn.isNullOrBlank() -> openLibrary.byIsbn(query.isbn)
            !query.title.isNullOrBlank() -> openLibrary.byTitle(query.title, query.author)
            else -> null
        }?.also { cache?.put(key, json.encodeToString(it)) } ?: return@withContext ExpandedQuery(query)
        withWork(query, work)
    }

    /** The query narrowed to one book: its author, every ISBN of the work, its language. */
    fun withWork(query: BookQuery, work: WorkInfo) = ExpandedQuery(
        query = query.copy(
            title = query.title ?: work.title.takeIf { it.isNotBlank() },
            author = query.author ?: work.authors.firstOrNull(),
            isbns = query.isbns + work.isbns,
            language = query.language ?: work.language,
        ),
        coverUrl = work.coverUrl,
        work = work,
    )

    /**
     * When the reader typed only a title, the books it could mean. Asked only when nothing
     * else pins the book down (no ISBN, no author); empty when offline or on any failure.
     */
    suspend fun candidates(query: BookQuery): List<WorkCandidate> = withContext(Dispatchers.IO) {
        val title = query.title?.trim()
        if (title.isNullOrEmpty() || !query.isbn.isNullOrBlank() || query.isbns.isNotEmpty() || !query.author.isNullOrBlank()) {
            return@withContext emptyList()
        }
        val key = "olc|" + title.lowercase()
        cache?.get(key)?.takeIf { clock() - it.second < CacheTtl.OPEN_LIBRARY_MILLIS }
            ?.let { runCatching { json.decodeFromString<List<WorkCandidate>>(it.first) }.getOrNull() }
            ?.let { return@withContext it }
        openLibrary.candidates(title).also { if (it.isNotEmpty()) cache?.put(key, json.encodeToString(it)) }
    }
}
