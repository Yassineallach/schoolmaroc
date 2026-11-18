package com.mardev.nearshelf.ui.results

import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.prefs.ReadingPrefs
import com.mardev.nearshelf.core.search.Availability.group
import com.mardev.nearshelf.core.search.Availability.isBorrowableNow
import com.mardev.nearshelf.core.search.ServiceState

/*
 * Results are organised around the reader's question, "how do I get this book, in the
 * format I want, soonest?", not around where the data came from. So: one section per
 * format (shown as tabs), and inside it every option from every library and service,
 * ranked fastest first. What isn't a result (not found, failures, catalogs
 * still answering) is collected separately for the end of the page.
 */

/** One way to get the book: an edition at one library through one service. */
data class OptionUi(
    val library: Library,
    val ref: LibraryRef,
    val match: MatchedHolding,
    /** More editions of the same format and language this option stands for. */
    val moreEditions: Int,
    /** Saved result shown because the service couldn't be reached; the time it was fetched. */
    val staleSince: Long? = null,
) {
    val holding get() = match.holding
    val isPrint get() = holding.format.group() == Format.PHYSICAL
}

/** The format's answer in a few words: on its tab, and above its options when there is a choice. */
sealed interface Verdict {
    /** Can be borrowed now (digital) at [via]. */
    data class AvailableNow(val via: OptionUi) : Verdict
    /** On a service that only confirms when opened (hoopla). */
    data class OnService(val service: String) : Verdict
    data class ShortestWait(val days: Int) : Verdict
    data object Waitlist : Verdict
    /** A print copy is on a shelf; [via] is the best option (home or nearest branch first). */
    data class OnShelf(val via: OptionUi) : Verdict
    data object AllCheckedOut : Verdict
    data object Unknown : Verdict
}

data class FormatSection(
    val format: Format,
    val verdict: Verdict,
    /** Same-language options, fastest first. */
    val options: List<OptionUi>,
    /** Editions in other languages, collapsed under one line. */
    val otherLanguages: List<OptionUi>,
)

/** A service that produced no result to show, and why. */
data class ServiceNote(val library: Library, val ref: LibraryRef, val state: ServiceState, val reason: Reason) {
    enum class Reason { NOT_FOUND, FAILED, UNAVAILABLE, LOADING, HIDDEN_BY_LANGUAGE }
}

data class OrganizedResults(
    val sections: List<FormatSection>,
    val notes: List<ServiceNote>,
) {
    val loading get() = notes.count { it.reason == ServiceNote.Reason.LOADING }
    fun section(format: Format) = sections.firstOrNull { it.format == format }

    /**
     * The tab to open on: the preferred format when a library has it, otherwise the format
     * the reader can get soonest (available now, on a shelf, on hoopla, shortest wait…).
     */
    fun bestFormat(prefs: ReadingPrefs): Format? {
        val withOptions = sections.filter { it.options.isNotEmpty() }
        withOptions.firstOrNull { it.format == prefs.preferredFormat }?.let { return it.format }
        return withOptions.minWithOrNull(compareBy({ score(it.verdict) }, { prefs.formatRank(it.format) }))?.format
    }

    private fun score(v: Verdict): Double = when (v) {
        is Verdict.AvailableNow -> 0.0
        is Verdict.OnShelf -> 1.0
        is Verdict.OnService -> 2.0
        is Verdict.ShortestWait -> 3.0 + v.days / 100_000.0
        Verdict.Waitlist -> 4.0
        Verdict.AllCheckedOut -> 5.0
        Verdict.Unknown -> 6.0
    }
}

/** Ranking within a section: lower sorts first. Library order (the reader's own) breaks ties. */
internal fun rank(o: OptionUi): Long {
    val h = o.holding
    return when {
        o.isPrint -> if (h.isBorrowableNow()) 0L else if (!h.availabilityKnown) 1L else 2L
        // Available now: more copies free first.
        h.availabilityKnown && h.isAvailableNow -> 0L * 1_000_000 + (999 - (h.available ?: 1).coerceIn(0, 999))
        // Can't confirm (hoopla): likely instant, so before any wait.
        !h.availabilityKnown -> 1_000_000L
        // Waits, shortest first; a waitlist with no estimate goes last.
        else -> 2_000_000L + (h.waitDays ?: 999_999)
    } * 10 + (if (o.staleSince != null) 1 else 0)
}

fun organizeResults(
    libraries: List<LibraryResult>,
    prefs: ReadingPrefs,
): OrganizedResults {
    val options = mutableListOf<Pair<Int, OptionUi>>() // library index for stable ties
    val notes = mutableListOf<ServiceNote>()
    libraries.forEachIndexed { li, lr ->
        lr.services.forEach { svc ->
            when (val st = svc.state) {
                ServiceState.Loading -> notes += ServiceNote(lr.library, svc.ref, st, ServiceNote.Reason.LOADING)
                is ServiceState.Failed -> notes += ServiceNote(lr.library, svc.ref, st, ServiceNote.Reason.FAILED)
                ServiceState.TemporarilyUnavailable -> notes += ServiceNote(lr.library, svc.ref, st, ServiceNote.Reason.UNAVAILABLE)
                is ServiceState.Done -> {
                    val rows = svc.rows(prefs)
                    when {
                        st.matches.isEmpty() -> notes += ServiceNote(lr.library, svc.ref, st, ServiceNote.Reason.NOT_FOUND)
                        rows.isEmpty() -> notes += ServiceNote(lr.library, svc.ref, st, ServiceNote.Reason.HIDDEN_BY_LANGUAGE)
                    }
                    rows.forEach { row ->
                        options += li to OptionUi(lr.library, svc.ref, row.match, row.moreEditions, st.fetchedAt.takeIf { st.stale })
                    }
                }
            }
        }
    }
    val sections = options
        .groupBy { it.second.holding.format.group() }
        .map { (format, group) ->
            val sorted = group.sortedWith(compareBy({ rank(it.second) }, { it.first })).map { it.second }
            val (same, other) = sorted.partition { !it.match.otherLanguage }
            FormatSection(format, verdict(format, same), same, other)
        }
        // Sections with something in the reader's languages first, then by preference.
        .sortedWith(compareBy({ it.options.isEmpty() }, { prefs.formatRank(it.format) }))
    return OrganizedResults(sections, notes)
}

private fun verdict(format: Format, options: List<OptionUi>): Verdict {
    if (options.isEmpty()) return Verdict.Unknown
    if (format == Format.PHYSICAL) {
        val best = options.first()
        return when {
            best.holding.isBorrowableNow() -> Verdict.OnShelf(best)
            options.all { !it.holding.availabilityKnown } -> Verdict.Unknown
            else -> Verdict.AllCheckedOut
        }
    }
    val best = options.first()
    val h = best.holding
    return when {
        h.availabilityKnown && h.isAvailableNow -> Verdict.AvailableNow(best)
        !h.availabilityKnown -> Verdict.OnService(best.ref.provider.displayName)
        options.mapNotNull { it.holding.waitDays }.minOrNull() != null ->
            Verdict.ShortestWait(options.mapNotNull { it.holding.waitDays }.min())
        else -> Verdict.Waitlist
    }
}

/** The physical catalog's provider is never a "service" the reader picks, so it reads as the library's catalog. */
fun LibraryRef.isCatalog() = provider.kind == ProviderId.Kind.PHYSICAL
