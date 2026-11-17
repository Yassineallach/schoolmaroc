package com.mardev.nearshelf.core.match

import java.text.Normalizer

object TextNormalizer {
    private val diacritics = Regex("\\p{Mn}+")
    private val nonWord = Regex("[^\\p{L}\\p{N}]+")
    private val apostrophes = Regex("['’ʼ`]")
    private val leadingArticle = Regex("^(the|a|an|le|la|les|l|el|los|las|der|die|das)\\s+")
    private val bracketed = Regex("[(\\[][^)\\]]*[)\\]]")

    /** Lowercase, strip diacritics and punctuation, collapse spaces. */
    fun basic(s: String): String =
        Normalizer.normalize(s, Normalizer.Form.NFD)
            .replace(diacritics, "")
            .lowercase()
            .replace(apostrophes, "")
            .replace(nonWord, " ")
            .trim()

    /**
     * Comparable main title: drops the subtitle (after ':' or ' - '), bracketed
     * notes like "(Unabridged)" or "[Book 1]", and a leading article.
     */
    fun title(s: String): String {
        val main = s.substringBefore(':').substringBefore(" - ").substringBefore(" — ")
        return basic(main.replace(bracketed, " ")).replace(leadingArticle, "").trim()
    }

    /** Surname from "Andy Weir" or "Weir, Andy". */
    fun surname(name: String): String? {
        val core = if (',' in name) name.substringBefore(',') else name
        return basic(core).split(' ').lastOrNull { it.isNotBlank() }
    }
}
