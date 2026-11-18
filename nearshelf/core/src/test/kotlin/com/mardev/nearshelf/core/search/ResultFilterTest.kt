package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class ResultFilterTest {
    private fun m(
        format: Format,
        availableNow: Boolean = false,
        known: Boolean = true,
        copies: List<PhysicalCopy> = emptyList(),
    ) = MatchedHolding(
        Holding(
            provider = ProviderId.OVERDRIVE, format = format, title = "T", providerItemId = format.name,
            isAvailableNow = availableNow, availabilityKnown = known, copies = copies,
        ),
        1.0, MatchedHolding.Reason.ISBN, otherLanguage = false,
    )

    private val ebookNow = m(Format.EBOOK, availableNow = true)
    private val ebookWait = m(Format.EBOOK)
    private val audio = m(Format.AUDIOBOOK, availableNow = true)
    private val hoopla = m(Format.AUDIOBOOK, known = false)
    private val printOnShelf = m(Format.PHYSICAL, copies = listOf(PhysicalCopy("Main", status = CopyStatus.AVAILABLE)))
    private val printOut = m(Format.PHYSICAL, copies = listOf(PhysicalCopy("Main", status = CopyStatus.CHECKED_OUT)))
    private val other = m(Format.OTHER, availableNow = true)
    private val all = listOf(ebookNow, ebookWait, audio, hoopla, printOnShelf, printOut, other)

    @Test fun `no filter keeps everything`() {
        val f = ResultFilter()
        assertFalse(f.isActive)
        assertEquals(all, f.apply(all))
    }

    @Test fun `format filter keeps only chosen formats, other counts as print`() {
        val f = ResultFilter(formats = setOf(Format.PHYSICAL))
        assertEquals(listOf(printOnShelf, printOut, other), f.apply(all))
    }

    @Test fun `several formats combine with or`() {
        val f = ResultFilter(formats = setOf(Format.EBOOK, Format.AUDIOBOOK))
        assertEquals(listOf(ebookNow, ebookWait, audio, hoopla), f.apply(all))
    }

    @Test fun `available now keeps confirmed digital and print on a shelf, not unknown`() {
        val f = ResultFilter(availableNow = true)
        assertEquals(listOf(ebookNow, audio, printOnShelf, other), f.apply(all))
    }

    @Test fun `format and availability combine with and`() {
        val f = ResultFilter(formats = setOf(Format.EBOOK), availableNow = true)
        assertEquals(listOf(ebookNow), f.apply(all))
    }

    @Test fun `toggle adds and removes a format`() {
        val on = ResultFilter().toggle(Format.EBOOK)
        assertTrue(on.isActive)
        assertEquals(setOf(Format.EBOOK), on.formats)
        assertFalse(on.toggle(Format.EBOOK).isActive)
    }
}
