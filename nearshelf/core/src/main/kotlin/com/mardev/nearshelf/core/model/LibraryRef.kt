package com.mardev.nearshelf.core.model

import kotlinx.serialization.Serializable

/**
 * A library as one provider knows it. [key] is the provider's own identifier
 * (OverDrive: the Libby `fulfillmentId`, e.g. "nypl"; Koha: the OPAC base URL).
 */
@Serializable
data class LibraryRef(
    val provider: ProviderId,
    val key: String,
    val name: String,
    val city: String? = null,
    val region: String? = null,
    val countryCode: String? = null,
    val catalogUrl: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val logoUrl: String? = null,
)
