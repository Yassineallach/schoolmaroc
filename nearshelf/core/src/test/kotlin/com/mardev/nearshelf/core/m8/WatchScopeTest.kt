package com.mardev.nearshelf.core.m8

import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.Branch
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.search.ServiceState
import com.mardev.nearshelf.core.watch.Watch
import com.mardev.nearshelf.core.watch.WatchEvent
import com.mardev.nearshelf.core.watch.WatchScope
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class WatchScopeTest {
    private val seattle = Library("sea", "Seattle Public Library", services = emptyList(), homeBranchId = "b", branches = listOf(Branch("b", "Ballard")))
    private val tacoma = Library("tac", "Tacoma Public Library", services = emptyList())

    private fun digital(format: Format, now: Boolean, wait: Int? = null) = MatchedHolding(
        Holding(ProviderId.OVERDRIVE, format, "Dune", providerItemId = format.name, isAvailableNow = now, waitDays = wait), 1.0, MatchedHolding.Reason.TITLE, false,
    )
    private fun print(onShelf: Boolean) = MatchedHolding(
        Holding(ProviderId.BIBLIOCOMMONS, Format.PHYSICAL, "Dune", providerItemId = "p",
            copies = listOf(PhysicalCopy("Ballard", status = if (onShelf) CopyStatus.AVAILABLE else CopyStatus.CHECKED_OUT))),
        1.0, MatchedHolding.Reason.TITLE, false,
    )

    /** Ebook free and print on the shelf at Seattle; audiobook free at Tacoma. */
    private fun everythingAvailable() = listOf(
        seattle to listOf("Libby" to ServiceState.Done(listOf(digital(Format.EBOOK, true))), "BiblioCommons" to ServiceState.Done(listOf(print(true)))),
        tacoma to listOf("Libby" to ServiceState.Done(listOf(digital(Format.AUDIOBOOK, true)))),
    )
    private fun nothingAvailable() = listOf(
        seattle to listOf("Libby" to ServiceState.Done(listOf(digital(Format.EBOOK, false, 30))), "BiblioCommons" to ServiceState.Done(listOf(print(false)))),
        tacoma to listOf("Libby" to ServiceState.Done(listOf(digital(Format.AUDIOBOOK, false, 20)))),
    )

    @Test fun `everything scope reports every format and library`() {
        val s = Watch.snapshot(1, everythingAvailable())
        assertEquals(setOf("sea", "tac"), s.libraries.keys)
        assertEquals(listOf("Ballard"), s.libraries["sea"]!!.onShelfAt)
    }

    @Test fun `an audiobook watch ignores ebook and print news`() {
        val scope = WatchScope(formats = setOf(Format.AUDIOBOOK))
        val events = Watch.events(Watch.snapshot(1, nothingAvailable(), scope), Watch.snapshot(2, everythingAvailable(), scope))
        assertEquals(listOf(WatchEvent.NowAvailable("Tacoma Public Library", "Libby", Format.AUDIOBOOK)), events)
    }

    @Test fun `a print watch at one library ignores the others`() {
        val scope = WatchScope(formats = setOf(Format.PHYSICAL), libraryIds = setOf("sea"))
        val after = Watch.snapshot(2, everythingAvailable(), scope)
        assertEquals(setOf("sea"), after.libraries.keys)
        assertTrue(after.libraries["sea"]!!.availableIn.isEmpty(), "Seattle's ebook isn't watched")
        val events = Watch.events(Watch.snapshot(1, nothingAvailable(), scope), after)
        assertEquals(listOf(WatchEvent.OnShelf("Seattle Public Library", "Ballard")), events)
    }

    @Test fun `status follows the scope`() {
        val scope = WatchScope(formats = setOf(Format.EBOOK), libraryIds = setOf("tac"))
        assertEquals(Watch.Status.NotYet, Watch.status(Watch.snapshot(1, everythingAvailable(), scope)))
    }
}
