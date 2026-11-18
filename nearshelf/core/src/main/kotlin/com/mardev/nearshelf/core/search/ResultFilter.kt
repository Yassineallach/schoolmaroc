package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding

/**
 * Filters the reader picks on the results page. Empty [formats] means every format.
 * [availableNow] keeps only what can be borrowed today: a digital copy confirmed
 * available, or a print copy on a shelf. Titles whose availability the service can't
 * confirm (hoopla without a login) are left out, because "available now" is a promise.
 */
data class ResultFilter(
    val formats: Set<Format> = emptySet(),
    val availableNow: Boolean = false,
) {
    val isActive: Boolean get() = formats.isNotEmpty() || availableNow

    fun keeps(m: MatchedHolding): Boolean {
        val h = m.holding
        if (formats.isNotEmpty() && h.format.filterKey() !in formats) return false
        if (availableNow && !h.isBorrowableNow()) return false
        return true
    }

    fun apply(matches: List<MatchedHolding>): List<MatchedHolding> = if (isActive) matches.filter(::keeps) else matches

    fun toggle(format: Format): ResultFilter = copy(formats = if (format in formats) formats - format else formats + format)

    companion object {
        /** "Other" formats are grouped with print, as the results page shows them. */
        fun Format.filterKey(): Format = if (this == Format.OTHER) Format.PHYSICAL else this

        fun Holding.isBorrowableNow(): Boolean = when {
            !availabilityKnown -> false
            format == Format.PHYSICAL || format == Format.OTHER ->
                isAvailableNow || copies.any { it.status == CopyStatus.AVAILABLE }
            else -> isAvailableNow
        }
    }
}
