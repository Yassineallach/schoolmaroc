package com.mardev.nearshelf.core.metadata

import com.mardev.nearshelf.core.model.BookQuery
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class ExpandedQuery(val query: BookQuery, val coverUrl: String? = null, val work: WorkInfo? = null)

/**
 * Fills a query in from Open Library before the catalogs are searched: an ISBN gains
 * its title, author, language and every ISBN of the work (so other editions and
 * formats match); a title gains the work's ISBN set. Any failure keeps the query as typed.
 */
class QueryExpander(private val openLibrary: OpenLibrary) {

    suspend fun expand(query: BookQuery): ExpandedQuery = withContext(Dispatchers.IO) {
        val work = when {
            !query.isbn.isNullOrBlank() -> openLibrary.byIsbn(query.isbn)
            !query.title.isNullOrBlank() -> openLibrary.byTitle(query.title, query.author)
            else -> null
        } ?: return@withContext ExpandedQuery(query)

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
