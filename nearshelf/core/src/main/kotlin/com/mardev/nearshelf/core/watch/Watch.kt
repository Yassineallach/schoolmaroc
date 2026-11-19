package com.mardev.nearshelf.core.watch

import com.mardev.nearshelf.core.search.Availability.group
import com.mardev.nearshelf.core.match.BranchNames
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.search.ServiceState
import kotlinx.serialization.Serializable

/** What one check found for a watched book at one library (same-language editions only). */
@Serializable
data class LibrarySnapshot(
    val libraryName: String,
    /** Digital services with a copy to borrow now, e.g. ["Libby"]. */
    val availableIn: List<String> = emptyList(),
    /** Formats of those copies, in the same order (so a notification can say which). */
    val availableFormats: List<Format> = emptyList(),
    /** Shortest digital wait in days, when nothing is available now. */
    val shortestWaitDays: Int? = null,
    /** Branches with a print copy on the shelf (home branch first). */
    val onShelfAt: List<String> = emptyList(),
    val homeBranchOnShelf: Boolean = false,
)

/**
 * What a watch covers. Empty [formats] or [libraryIds] means all of them, so watches
 * saved before scopes existed keep watching everything.
 */
@Serializable
data class WatchScope(
    val formats: Set<Format> = emptySet(),
    val libraryIds: Set<String> = emptySet(),
    /** Names of [libraryIds], for display only. */
    val libraryNames: List<String> = emptyList(),
) {
    fun covers(format: Format): Boolean = formats.isEmpty() || format.group() in formats
    fun covers(libraryId: String): Boolean = libraryIds.isEmpty() || libraryId in libraryIds
    val isEverything: Boolean get() = formats.isEmpty() && libraryIds.isEmpty()

    companion object {
        val Everything = WatchScope()
    }
}

@Serializable
data class WatchSnapshot(val checkedAt: Long, val libraries: Map<String, LibrarySnapshot>)

sealed interface WatchEvent {
    val libraryName: String

    data class NowAvailable(override val libraryName: String, val service: String, val format: Format? = null) : WatchEvent
    data class OnShelf(override val libraryName: String, val branch: String) : WatchEvent
    data class WaitDropped(override val libraryName: String, val days: Int) : WatchEvent
}

object Watch {

    /**
     * What one check found, limited to the watch's [scope]: libraries outside it are left
     * out and so are formats it doesn't cover, so notifications, the watchlist status and
     * the widget only ever report what the reader asked to watch.
     */
    fun snapshot(
        checkedAt: Long,
        results: List<Pair<Library, List<Pair<String, ServiceState>>>>,
        scope: WatchScope = WatchScope.Everything,
    ): WatchSnapshot =
        WatchSnapshot(checkedAt, results.filter { scope.covers(it.first.id) }.associate { (lib, services) ->
            val matches = services.flatMap { (service, st) ->
                (st as? ServiceState.Done)?.matches.orEmpty()
                    .filter { !it.otherLanguage && scope.covers(it.holding.format) }
                    .map { service to it.holding }
            }
            val digital = matches.filter { it.second.format == Format.EBOOK || it.second.format == Format.AUDIOBOOK }
            val physical = matches.filter { it.second.format.group() == Format.PHYSICAL }.flatMap { it.second.copies }
            val shelfBranches = physical.filter { it.status == CopyStatus.AVAILABLE }.map { it.branchName }.distinct()
            val home = lib.homeBranch?.name
            val homeOnShelf = home != null && shelfBranches.any { BranchNames.matches(home, it) }
            lib.id to LibrarySnapshot(
                libraryName = lib.name,
                availableIn = digital.filter { it.second.availabilityKnown && it.second.isAvailableNow }.map { it.first }.distinct(),
                availableFormats = digital.filter { it.second.availabilityKnown && it.second.isAvailableNow }.map { it.second.format }.distinct(),
                shortestWaitDays = digital.mapNotNull { it.second.waitDays }.minOrNull(),
                onShelfAt = shelfBranches.sortedBy { b -> if (home != null && BranchNames.matches(home, b)) 0 else 1 },
                homeBranchOnShelf = homeOnShelf,
            )
        })

    /**
     * What changed for the better since the last check. The first check (no [old]) only
     * records a baseline. Waits must drop by at least 3 days and 20% to be worth a ping.
     */
    fun events(old: WatchSnapshot?, new: WatchSnapshot): List<WatchEvent> {
        if (old == null) return emptyList()
        return new.libraries.flatMap { (id, now) ->
            val before = old.libraries[id] ?: return@flatMap emptyList()
            buildList {
                if (before.availableIn.isEmpty() && now.availableIn.isNotEmpty()) {
                    add(WatchEvent.NowAvailable(now.libraryName, now.availableIn.first(), now.availableFormats.firstOrNull()))
                }
                val shelfNews = when {
                    now.homeBranchOnShelf && !before.homeBranchOnShelf -> now.onShelfAt.first()
                    before.onShelfAt.isEmpty() && now.onShelfAt.isNotEmpty() -> now.onShelfAt.first()
                    else -> null
                }
                shelfNews?.let { add(WatchEvent.OnShelf(now.libraryName, it)) }
                val w0 = before.shortestWaitDays
                val w1 = now.shortestWaitDays
                if (now.availableIn.isEmpty() && w0 != null && w1 != null && w0 - w1 >= 3 && w1 <= w0 * 0.8) {
                    add(WatchEvent.WaitDropped(now.libraryName, w1))
                }
            }
        }
    }

    /** One-line status for the watchlist and widget, best news first. */
    sealed interface Status {
        data class Available(val library: String, val service: String) : Status
        data class OnShelf(val library: String, val branch: String) : Status
        data class Waiting(val library: String, val days: Int) : Status
        data object NotYet : Status
    }

    fun status(s: WatchSnapshot?): Status? {
        if (s == null) return null
        val libs = s.libraries.values
        libs.firstOrNull { it.availableIn.isNotEmpty() }?.let { return Status.Available(it.libraryName, it.availableIn.first()) }
        (libs.firstOrNull { it.homeBranchOnShelf } ?: libs.firstOrNull { it.onShelfAt.isNotEmpty() })
            ?.let { return Status.OnShelf(it.libraryName, it.onShelfAt.first()) }
        libs.filter { it.shortestWaitDays != null }.minByOrNull { it.shortestWaitDays!! }
            ?.let { return Status.Waiting(it.libraryName, it.shortestWaitDays!!) }
        return Status.NotYet
    }
}
