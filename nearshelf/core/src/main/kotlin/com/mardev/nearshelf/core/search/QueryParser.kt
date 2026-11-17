package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.match.Isbn
import com.mardev.nearshelf.core.model.BookQuery

/** Turns what the user typed into a [BookQuery]: an ISBN, "title by author", or a title. */
object QueryParser {
    private val by = Regex("\\s+by\\s+", RegexOption.IGNORE_CASE)

    fun parse(input: String): BookQuery? {
        val text = input.trim()
        if (text.isEmpty()) return null
        val compact = text.replace(Regex("[\\s-]"), "")
        if (compact.matches(Regex("\\d{9}[\\dXx]|\\d{13}")) && Isbn.isValid(compact)) {
            return BookQuery(isbn = Isbn.normalize(compact))
        }
        val parts = text.split(by, limit = 2)
        return if (parts.size == 2 && parts[0].isNotBlank() && parts[1].isNotBlank()) {
            BookQuery(title = parts[0].trim(), author = parts[1].trim())
        } else {
            BookQuery(title = text)
        }
    }
}
