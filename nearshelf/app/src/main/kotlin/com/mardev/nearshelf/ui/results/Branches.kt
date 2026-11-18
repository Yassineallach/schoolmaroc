package com.mardev.nearshelf.ui.results

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
)

/** Home branch first, then branches with copies on the shelf (most first), then the rest by name. */
fun summarizeBranches(copies: List<PhysicalCopy>, homeBranchName: String?): List<BranchSummary> =
    copies.groupBy { it.branchName }.map { (name, cs) ->
        BranchSummary(
            name = name,
            isHome = homeBranchName != null && BranchNames.same(homeBranchName, name),
            onShelf = cs.count { it.status == CopyStatus.AVAILABLE },
            total = cs.size,
            inTransit = cs.count { it.status == CopyStatus.IN_TRANSIT },
            checkedOut = cs.count { it.status == CopyStatus.CHECKED_OUT },
            libraryUseOnly = cs.count { it.status == CopyStatus.LIBRARY_USE_ONLY },
            nextDue = cs.mapNotNull { it.dueDate }.minOrNull(),
            callNumber = cs.firstNotNullOfOrNull { it.callNumber },
        )
    }.sortedWith(compareBy<BranchSummary>({ !it.isHome }, { -it.onShelf }, { it.name }))
