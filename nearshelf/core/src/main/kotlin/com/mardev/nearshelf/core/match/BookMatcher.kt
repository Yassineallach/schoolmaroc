package com.mardev.nearshelf.core.match

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Holding

data class MatchedHolding(
    val holding: Holding,
    val score: Double,
    val reason: Reason,
    /** True when the edition's language differs from the language of the book searched for. */
    val otherLanguage: Boolean,
) {
    enum class Reason { ISBN, TITLE_AUTHOR, TITLE }
}

/**
 * Decides which catalog records are the book the user asked for.
 *
 * 1. Any ISBN shared with the query's ISBN set → match.
 * 2. Otherwise the main titles must agree on both Jaro-Winkler (≥ [jwThreshold])
 *    and edit-distance ratio (≥ [editThreshold]); JW alone accepts long shared
 *    prefixes ("Harry Potter and the …"). When the query names an author, one
 *    surname must also match.
 * 3. Study aids ("Summary of …", "Study Guide", …) are dropped unless asked for.
 */
class BookMatcher(
    private val jwThreshold: Double = 0.9,
    private val editThreshold: Double = 0.8,
) {
    fun match(query: BookQuery, holdings: List<Holding>): List<MatchedHolding> {
        val queryIsbns = (query.isbns + listOfNotNull(query.isbn)).map(Isbn::normalize).toSet()
        val queryTitle = query.title?.let(TextNormalizer::title)?.takeIf { it.isNotBlank() }
        val querySurnames = query.author?.let(::surnamesOf).orEmpty()
        val wantsStudyAid = query.title?.let { isStudyAid(it) } == true

        val matched = holdings.mapNotNull { h ->
            val holdingIsbns = h.isbns.map(Isbn::normalize).toSet()
            if (queryIsbns.isNotEmpty() && holdingIsbns.any { it in queryIsbns }) {
                return@mapNotNull Candidate(h, 1.0, MatchedHolding.Reason.ISBN)
            }
            if (queryTitle == null) return@mapNotNull null
            if (!wantsStudyAid && isStudyAid(listOfNotNull(h.title, h.subtitle).joinToString(" "))) {
                return@mapNotNull null
            }
            val candidateTitle = TextNormalizer.title(h.title)
            val jw = Similarity.jaroWinkler(queryTitle, candidateTitle)
            val edit = Similarity.levenshteinRatio(queryTitle, candidateTitle)
            if (jw < jwThreshold || edit < editThreshold) return@mapNotNull null

            val authorKnown = querySurnames.isNotEmpty() && h.authors.isNotEmpty()
            if (authorKnown && h.authors.flatMap(::surnamesOf).none { it in querySurnames }) {
                return@mapNotNull null
            }
            val reason = if (authorKnown) MatchedHolding.Reason.TITLE_AUTHOR else MatchedHolding.Reason.TITLE
            Candidate(h, (jw + edit) / 2, reason)
        }

        val primary = query.language ?: primaryLanguage(queryTitle, matched)
        return matched.map {
            val lang = it.holding.language
            MatchedHolding(it.holding, it.score, it.reason, otherLanguage = primary != null && lang != null && lang != primary)
        }
    }

    private data class Candidate(val holding: Holding, val score: Double, val reason: MatchedHolding.Reason)

    /** Language of the edition that best represents the query: ISBN hit first, then an exact title. */
    private fun primaryLanguage(queryTitle: String?, matched: List<Candidate>): String? =
        matched.firstOrNull { it.reason == MatchedHolding.Reason.ISBN }?.holding?.language
            ?: matched.firstOrNull { queryTitle != null && TextNormalizer.title(it.holding.title) == queryTitle }?.holding?.language

    private fun surnamesOf(names: String): List<String> =
        names.split(Regex("\\s*(;|&|\\band\\b)\\s*")).mapNotNull(TextNormalizer::surname)

    companion object {
        private val studyAid = Regex(
            "\\b(summary of|summary and analysis|summary analysis|study guide|workbook|analysis of|" +
                "sparknotes|cliffsnotes|book summary|a summary|key takeaways|conversation starters)\\b",
        )

        /** Same title rule the matcher applies, for callers outside a full match. */
        fun titlesMatch(a: String, b: String, jw: Double = 0.9, edit: Double = 0.8): Boolean {
            val x = TextNormalizer.title(a)
            val y = TextNormalizer.title(b)
            return x.isNotEmpty() && Similarity.jaroWinkler(x, y) >= jw && Similarity.levenshteinRatio(x, y) >= edit
        }

        fun isStudyAid(text: String): Boolean = studyAid.containsMatchIn(TextNormalizer.basic(text))
    }
}

object Isbn {
    /** Digits (and a trailing X) only; ISBN-10s become ISBN-13s so editions compare equal. */
    fun normalize(raw: String): String {
        val s = raw.uppercase().filter { it.isDigit() || it == 'X' }
        return if (s.length == 10) to13(s) else s
    }

    fun to13(isbn10: String): String {
        val core = "978" + isbn10.take(9)
        val sum = core.mapIndexed { i, c -> (c - '0') * if (i % 2 == 0) 1 else 3 }.sum()
        return core + ((10 - sum % 10) % 10)
    }

    /** A scanned EAN-13 is a book only with the 978/979 "Bookland" prefix and a valid checksum. */
    fun fromBarcode(raw: String): String? {
        val digits = raw.trim()
        return digits.takeIf { it.length == 13 && it.all(Char::isDigit) && (it.startsWith("978") || it.startsWith("979")) && isValid(it) }
    }

    fun isValid(raw: String): Boolean {
        val s = raw.uppercase().filter { it.isDigit() || it == 'X' }
        return when (s.length) {
            13 -> s.all(Char::isDigit) &&
                s.mapIndexed { i, c -> (c - '0') * if (i % 2 == 0) 1 else 3 }.sum() % 10 == 0
            10 -> s.take(9).all(Char::isDigit) &&
                s.mapIndexed { i, c -> (if (c == 'X') 10 else c - '0') * (10 - i) }.sum() % 11 == 0
            else -> false
        }
    }
}
