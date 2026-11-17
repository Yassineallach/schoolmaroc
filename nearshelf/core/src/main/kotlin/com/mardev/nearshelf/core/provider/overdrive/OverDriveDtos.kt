package com.mardev.nearshelf.core.provider.overdrive

import kotlinx.serialization.Serializable

// Shapes recorded from locate.libbyapp.com and thunder.api.overdrive.com (Nov 2026).
// Only fields Nearshelf uses are declared; the Json instance ignores the rest.

@Serializable
internal data class LocateResponse(val branches: List<LocateBranch> = emptyList())

@Serializable
internal data class LocateBranch(
    val id: Long? = null,
    val name: String? = null,
    val city: String? = null,
    val regionCode: String? = null,
    val countryCode: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val systems: List<LocateSystem> = emptyList(),
)

@Serializable
internal data class LocateSystem(
    val id: Long? = null,
    val name: String,
    val type: String? = null,
    val fulfillmentId: String? = null,
    val styling: Styling? = null,
) {
    @Serializable
    data class Styling(val logos: List<Logo> = emptyList())

    @Serializable
    data class Logo(val sourceUrl: String? = null)
}

@Serializable
internal data class MediaResponse(
    val items: List<MediaItem> = emptyList(),
    val totalItems: Int? = null,
)

@Serializable
internal data class MediaItem(
    val id: String,
    val title: String,
    val subtitle: String? = null,
    val type: IdName? = null,
    val creators: List<Creator> = emptyList(),
    val languages: List<IdName> = emptyList(),
    val formats: List<MediaFormat> = emptyList(),
    val isAvailable: Boolean = false,
    val isOwned: Boolean = true,
    val ownedCopies: Int? = null,
    val availableCopies: Int? = null,
    val holdsCount: Int? = null,
    val estimatedWaitDays: Int? = null,
    val availabilityType: String? = null,
    val covers: Map<String, Cover> = emptyMap(),
)

@Serializable
internal data class IdName(val id: String, val name: String? = null)

@Serializable
internal data class Creator(val name: String, val role: String? = null)

@Serializable
internal data class MediaFormat(
    val id: String? = null,
    val isbn: String? = null,
    val identifiers: List<Identifier> = emptyList(),
)

@Serializable
internal data class Identifier(val type: String, val value: String)

@Serializable
internal data class Cover(val href: String? = null, val width: Int? = null)
