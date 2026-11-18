package com.mardev.nearshelf.ui.results

import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.prefs.ReadingPrefs
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.search.ResultFilter
import com.mardev.nearshelf.core.search.ServiceState
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ResultsOrganizerTest {
    private val libby = LibraryRef(ProviderId.OVERDRIVE, "tpl", "Toronto")
    private val hoopla = LibraryRef(ProviderId.HOOPLA, "tpl", "Toronto")
    private val catalog = LibraryRef(ProviderId.BIBLIOCOMMONS, "tpl", "Toronto")
    private val libby2 = LibraryRef(ProviderId.OVERDRIVE, "ept", "Evanston")
    private val tpl = Library("tpl", "Toronto Public Library", services = listOf(libby, hoopla, catalog))
    private val ept = Library("ept", "Evanston Public Library", services = listOf(libby2))

    private fun h(
        format: Format, id: String, now: Boolean = false, wait: Int? = null, known: Boolean = true,
        lang: String? = null, other: Boolean = false, copies: List<PhysicalCopy> = emptyList(), available: Int? = null,
    ) = MatchedHolding(
        Holding(ProviderId.OVERDRIVE, format, "Red Rising", providerItemId = id, isAvailableNow = now, waitDays = wait,
            availabilityKnown = known, language = lang, copies = copies, available = available),
        1.0, MatchedHolding.Reason.ISBN, otherLanguage = other,
    )

    private fun sample() = listOf(
        LibraryResult(tpl, listOf(
            ServiceResult(libby, ServiceState.Done(listOf(h(Format.EBOOK, "e1", wait = 80), h(Format.AUDIOBOOK, "a1", wait = 28)))),
            ServiceResult(hoopla, ServiceState.Done(listOf(h(Format.AUDIOBOOK, "h1", known = false), h(Format.AUDIOBOOK, "h2", known = false, lang = "de", other = true)))),
            ServiceResult(catalog, ServiceState.Done(listOf(h(Format.PHYSICAL, "p1", copies = listOf(PhysicalCopy("Main", status = CopyStatus.AVAILABLE)))))),
        )),
        LibraryResult(ept, listOf(
            ServiceResult(libby2, ServiceState.Done(listOf(h(Format.EBOOK, "e2", now = true, available = 2)))),
        )),
    )

    @Test fun `one section per format, options from every library ranked fastest first`() {
        val r = organizeResults(sample(), ReadingPrefs())
        assertEquals(listOf(Format.EBOOK, Format.AUDIOBOOK, Format.PHYSICAL), r.sections.map { it.format })
        val ebook = r.sections[0]
        // Evanston's copy available now beats Toronto's 80-day wait, though Toronto is listed first.
        assertEquals(listOf("e2", "e1"), ebook.options.map { it.holding.providerItemId })
        assertTrue(ebook.verdict is Verdict.AvailableNow)
    }

    @Test fun `hoopla ranks before a wait and becomes the verdict, other languages are set apart`() {
        val audio = organizeResults(sample(), ReadingPrefs()).sections.first { it.format == Format.AUDIOBOOK }
        assertEquals(listOf("h1", "a1"), audio.options.map { it.holding.providerItemId })
        assertEquals(Verdict.OnService("Hoopla"), audio.verdict)
        assertEquals(listOf("h2"), audio.otherLanguages.map { it.holding.providerItemId })
    }

    @Test fun `preferred format comes first`() {
        val r = organizeResults(sample(), ReadingPrefs(preferredFormat = Format.PHYSICAL))
        assertEquals(Format.PHYSICAL, r.sections.first().format)
        assertTrue(r.sections.first().verdict is Verdict.OnShelf)
    }

    @Test fun `shortest wait verdict when nothing is available`() {
        val only = listOf(LibraryResult(tpl, listOf(ServiceResult(libby, ServiceState.Done(listOf(h(Format.EBOOK, "x", wait = 80), h(Format.EBOOK, "y", wait = 30, lang = "fr")))))))
        val s = organizeResults(only, ReadingPrefs()).sections.single()
        assertEquals(Verdict.ShortestWait(30), s.verdict)
    }

    @Test fun `non-results become notes`() {
        val libs = listOf(LibraryResult(tpl, listOf(
            ServiceResult(libby, ServiceState.Done(emptyList())),
            ServiceResult(hoopla, ServiceState.Failed(ProviderException.Kind.NETWORK, null)),
            ServiceResult(catalog, ServiceState.Loading),
        )))
        val r = organizeResults(libs, ReadingPrefs())
        assertTrue(r.sections.isEmpty())
        assertEquals(listOf(ServiceNote.Reason.NOT_FOUND, ServiceNote.Reason.FAILED, ServiceNote.Reason.LOADING), r.notes.map { it.reason })
        assertEquals(1, r.loading)
    }

    @Test fun `filter removes options and leaves a filtered-out note`() {
        val r = organizeResults(sample(), ReadingPrefs(), ResultFilter(availableNow = true))
        assertEquals(listOf(Format.EBOOK, Format.PHYSICAL), r.sections.map { it.format })
        assertTrue(r.filteredOut)
    }
}
