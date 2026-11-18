package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.search.Availability.group
import com.mardev.nearshelf.core.search.Availability.isBorrowableNow
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class AvailabilityTest {
    private fun h(format: Format, now: Boolean = false, known: Boolean = true, copies: List<PhysicalCopy> = emptyList()) =
        Holding(ProviderId.OVERDRIVE, format, "T", providerItemId = "x", isAvailableNow = now, availabilityKnown = known, copies = copies)

    @Test fun `other formats group with print`() {
        assertEquals(Format.PHYSICAL, Format.OTHER.group())
        assertEquals(Format.EBOOK, Format.EBOOK.group())
    }

    @Test fun `digital is borrowable only when confirmed available`() {
        assertTrue(h(Format.EBOOK, now = true).isBorrowableNow())
        assertFalse(h(Format.EBOOK).isBorrowableNow())
        assertFalse(h(Format.AUDIOBOOK, now = true, known = false).isBorrowableNow())
    }

    @Test fun `print is borrowable with a copy on a shelf`() {
        assertTrue(h(Format.PHYSICAL, copies = listOf(PhysicalCopy("Main", status = CopyStatus.AVAILABLE))).isBorrowableNow())
        assertFalse(h(Format.PHYSICAL, copies = listOf(PhysicalCopy("Main", status = CopyStatus.CHECKED_OUT))).isBorrowableNow())
        assertTrue(h(Format.OTHER, now = true).isBorrowableNow())
    }
}
