package com.mardev.nearshelf.ui.results

import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.PhysicalCopy
import org.junit.Assert.assertEquals
import org.junit.Test

class BranchesTest {
    private fun c(branch: String, s: CopyStatus, due: String? = null) = PhysicalCopy(branch, status = s, callNumber = "FIC WEIR", dueDate = due)

    @Test
    fun homeFirstThenMostOnShelfThenName() {
        val copies = listOf(
            c("Central Library", CopyStatus.AVAILABLE), c("Central Library", CopyStatus.AVAILABLE),
            c("Ballard Branch", CopyStatus.CHECKED_OUT, "2026-12-09"), c("Ballard Branch", CopyStatus.CHECKED_OUT, "2026-12-02"),
            c("Northgate Branch", CopyStatus.AVAILABLE),
            c("Beacon Hill Branch", CopyStatus.IN_TRANSIT),
        )
        val s = summarizeBranches(copies, homeBranchName = "Ballard") // Libby's name for the branch
        assertEquals(listOf("Ballard Branch", "Central Library", "Northgate Branch", "Beacon Hill Branch"), s.map { it.name })
        assertEquals(true, s[0].isHome)
        assertEquals("2026-12-02", s[0].nextDue)
        assertEquals(2, s[1].onShelf)
        assertEquals(1, s[3].inTransit)
    }
}
