package com.mardev.nearshelf.ui.results

import com.mardev.nearshelf.core.geo.Distance
import com.mardev.nearshelf.core.geo.LatLng
import com.mardev.nearshelf.core.match.BranchNames
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.PhysicalCopy

/** Copies of one edition at one branch, summarised for a results row. */
data class BranchSummary(
    val name: String,
    val isHome: Boolean,
    val onShelf: Int,
    val total: Int,
    val inTransit: Int,
    val checkedOut: Int,
    val libraryUseOnly: Int,
    /** Earliest due date (yyyy-MM-dd) among checked-out copies, when the catalog gives one. */
    val nextDue: String?,
    val callNumber: String?,
    val location: com.mardev.nearshelf.core.geo.LatLng? = null,
    /** Kilometres from the user, when both locations are known. */
    val distanceKm: Double? = null,
)

/**
 * Home branch first, then branches with copies on the shelf, then the rest. Within each
 * group: nearest first when [here] is known, otherwise most copies on the shelf, then name.
 */
fun summarizeBranches(copies: List<PhysicalCopy>, homeBranchName: String?, here: LatLng? = null): List<BranchSummary> =
    copies.groupBy { it.branchName }.map { (name, cs) ->
        val loc = cs.firstOrNull { it.latitude != null && it.longitude != null }?.let { LatLng(it.latitude!!, it.longitude!!) }
        BranchSummary(
            name = name,
            isHome = homeBranchName != null && BranchNames.matches(homeBranchName, name),
            onShelf = cs.count { it.status == CopyStatus.AVAILABLE },
            total = cs.size,
            inTransit = cs.count { it.status == CopyStatus.IN_TRANSIT },
            checkedOut = cs.count { it.status == CopyStatus.CHECKED_OUT },
            libraryUseOnly = cs.count { it.status == CopyStatus.LIBRARY_USE_ONLY },
            nextDue = cs.mapNotNull { it.dueDate }.minOrNull(),
            callNumber = cs.firstNotNullOfOrNull { it.callNumber },
            location = loc,
            distanceKm = if (here != null && loc != null) Distance.km(here, loc) else null,
        )
    }.sortedWith(
        compareBy<BranchSummary>({ !it.isHome }, { it.onShelf == 0 }, { it.distanceKm ?: Double.MAX_VALUE }, { -it.onShelf }, { it.name }),
    )
