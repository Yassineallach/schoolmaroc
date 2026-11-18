package com.mardev.nearshelf.core.match

/**
 * Library catalogs show MARC personal names: "Tolkien, J. R. R.(John Ronald Reuel),1892-1973,
 * author,illustrator.http://id.loc.gov/…(CWMARS)225068". Keep "J. R. R. Tolkien".
 */
object MarcNames {
    private val relator = Regex(
        "^(author|editor|illustrator|translator|narrator|writer.*|compiler|contributor|creator|performer|" +
            "photographer|adapter|ed\\.?|trans\\.?|joint author)\\.?$",
        RegexOption.IGNORE_CASE,
    )
    private val dates = Regex("^(b\\.|d\\.|fl\\.|ca\\.)?\\s*\\d{3,4}\\??-?(\\d{3,4})?\\??\\.?$")

    fun display(raw: String): String {
        val noLinks = raw.substringBefore("http").replace(Regex("\\([^)]*\\)\\d*"), " ")
        val parts = noLinks.split(',').map { it.trim().trimEnd('.').trim() }.filter { it.isNotEmpty() }
        if (parts.isEmpty()) return raw.trim()
        val surname = parts[0]
        val given = parts.getOrNull(1)?.takeUnless { dates.matches(it) || relator.matches(it) }
            ?.let { g -> if (Regex("(^|\\s)\\p{Lu}$").containsMatchIn(g)) "$g." else g } // keep the dot after a final initial
        return if (given != null) "$given $surname" else surname
    }
}
