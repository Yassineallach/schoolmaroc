package com.mardev.nearshelf.core.model

import kotlinx.serialization.Serializable

/**
 * What the user is looking for. [isbns] holds every known ISBN of the work
 * (filled from Open Library in a later milestone); [isbn] is the one the user gave.
 */
@Serializable
data class BookQuery(
    val title: String? = null,
    val author: String? = null,
    val isbn: String? = null,
    val isbns: Set<String> = emptySet(),
    /** ISO 639-1 language of the book searched for, when known (Open Library). */
    val language: String? = null,
) {
    init {
        require(!title.isNullOrBlank() || !isbn.isNullOrBlank() || isbns.isNotEmpty()) {
            "BookQuery needs a title or an ISBN"
        }
    }

    /** Free-text string for catalogs that only take one search box. */
    fun searchText(): String = when {
        !title.isNullOrBlank() && !author.isNullOrBlank() -> "$title $author"
        !title.isNullOrBlank() -> title
        !isbn.isNullOrBlank() -> isbn
        else -> isbns.first()
    }
}
