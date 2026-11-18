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

        ExpandedQuery(
            query = query.copy(
                title = query.title ?: work.title.takeIf { it.isNotBlank() },
                author = query.author ?: work.authors.firstOrNull(),
                isbns = query.isbns + work.isbns,
                language = query.language ?: work.language,
            ),
            coverUrl = work.coverUrl,
            work = work,
        )
    }
}
