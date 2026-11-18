package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding

/** How results are grouped and what "available now" means, shared by the results page and its tests. */
object Availability {
    /** "Other" formats are grouped with print, as the results page shows them. */
    fun Format.group(): Format = if (this == Format.OTHER) Format.PHYSICAL else this

    /**
     * Can be borrowed today: a digital copy confirmed available, or a print copy on a shelf.
     * False when the service can't confirm (hoopla without a login): "available now" is a promise.
     */
    fun Holding.isBorrowableNow(): Boolean = when {
        !availabilityKnown -> false
        format == Format.PHYSICAL || format == Format.OTHER -> isAvailableNow || copies.any { it.status == CopyStatus.AVAILABLE }
        else -> isAvailableNow
    }
}
