package com.mardev.nearshelf.core.model

import kotlinx.serialization.Serializable

/**
 * One title in one format at one library. Digital holdings leave [physical] null;
 * physical holdings carry one [PhysicalCopy] per item (branch-level availability).
 */
@Serializable
data class Holding(
    val provider: ProviderId,
    val format: Format,
    val title: String,
    val subtitle: String? = null,
    val authors: List<String> = emptyList(),
    /** ISO 639-1 code when known, e.g. "en", "es". */
    val language: String? = null,
    val isbns: Set<String> = emptySet(),
    val owned: Int? = null,
    val available: Int? = null,
    val holds: Int? = null,
    val waitDays: Int? = null,
    val isAvailableNow: Boolean = false,
    /**
     * False when the provider can't say whether this library can lend the title right now
     * (Hoopla without a login): show it as "on the service" rather than available or waitlisted.
     */
    val availabilityKnown: Boolean = true,
    val providerItemId: String,
    val coverUrl: String? = null,
    val copies: List<PhysicalCopy> = emptyList(),
)

@Serializable
data class PhysicalCopy(
    val branchName: String,
    val branchId: String? = null,
    val callNumber: String? = null,
    val status: CopyStatus,
    /** ISO-8601 date (yyyy-MM-dd) when the copy is due back. */
    val dueDate: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
)

@Serializable
enum class CopyStatus { AVAILABLE, CHECKED_OUT, IN_TRANSIT, ON_HOLD_SHELF, IN_PROCESSING, MISSING, UNKNOWN }
