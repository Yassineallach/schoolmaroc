package com.mardev.nearshelf.core.prefs

import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.Format
import kotlinx.serialization.Serializable

/**
 * How results are shown. [languages] are ISO 639-1 codes the reader reads; editions in
 * other languages are flagged, or hidden when [showOtherLanguages] is off.
 */
@Serializable
data class ReadingPrefs(
    val preferredFormat: Format? = null,
    val languages: Set<String> = emptySet(),
    val showOtherLanguages: Boolean = true,
) {
    /** Hides editions in languages the reader doesn't read (when asked to); never hides unknown languages. */
    fun filter(matches: List<MatchedHolding>): List<MatchedHolding> =
        if (showOtherLanguages) matches
        else matches.filter { m ->
            val lang = m.holding.language
            !m.otherLanguage || lang == null || lang in languages
        }

    /** Sort key for formats: the preferred one first, then eBook, audiobook, print. */
    fun formatRank(f: Format): Int = if (f == preferredFormat) -1 else when (f) {
        Format.EBOOK -> 0
        Format.AUDIOBOOK -> 1
        Format.PHYSICAL -> 2
        Format.OTHER -> 3
    }
}
