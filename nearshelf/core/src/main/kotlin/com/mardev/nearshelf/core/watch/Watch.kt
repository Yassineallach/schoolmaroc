package com.mardev.nearshelf.core.watch

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
    /** Shortest digital wait in days, when nothing is available now. */
    val shortestWaitDays: Int? = null,
    /** Branches with a print copy on the shelf (home branch first). */
    val onShelfAt: List<String> = emptyList(),
    val homeBranchOnShelf: Boolean = false,
)

@Serializable
data class WatchSnapshot(val checkedAt: Long, val libraries: Map<String, LibrarySnapshot>)

sealed interface WatchEvent {
    val libraryName: String

    data class NowAvailable(override val libraryName: String, val service: String) : WatchEvent
    data class OnShelf(override val libraryName: String, val branch: String) : WatchEvent
    data class WaitDropped(override val libraryName: String, val days: Int) : WatchEvent
}

object Watch {

    fun snapshot(checkedAt: Long, results: List<Pair<Library, List<Pair<String, ServiceState>>>>): WatchSnapshot =
        WatchSnapshot(checkedAt, results.associate { (lib, services) ->
            val matches = services.flatMap { (service, st) ->
                (st as? ServiceState.Done)?.matches.orEmpty().filter { !it.otherLanguage }.map { service to it.holding }
            }
            val digital = matches.filter { it.second.format == Format.EBOOK || it.second.format == Format.AUDIOBOOK }
            val physical = matches.filter { it.second.format == Format.PHYSICAL }.flatMap { it.second.copies }
            val shelfBranches = physical.filter { it.status == CopyStatus.AVAILABLE }.map { it.branchName }.distinct()
            val home = lib.homeBranch?.name
            val homeOnShelf = home != null && shelfBranches.any { BranchNames.matches(home, it) }
            lib.id to LibrarySnapshot(
                libraryName = lib.name,
                availableIn = digital.filter { it.second.availabilityKnown && it.second.isAvailableNow }.map { it.first }.distinct(),
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
                    add(WatchEvent.NowAvailable(now.libraryName, now.availableIn.first()))
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
