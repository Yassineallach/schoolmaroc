package com.mardev.nearshelf.core.model

import kotlinx.serialization.Serializable

/**
 * A library the way the user thinks of it ("Toronto Public Library"), with every
 * catalog service it offers: Libby, Hoopla, its physical catalog.
 */
@Serializable
data class Library(
    val id: String,
    val name: String,
    val city: String? = null,
    val region: String? = null,
    val countryCode: String? = null,
    val services: List<LibraryRef>,
    val homeBranchId: String? = null,
) {
    val digitalServices get() = services.filter { it.provider.kind == ProviderId.Kind.DIGITAL }
    val physicalServices get() = services.filter { it.provider.kind == ProviderId.Kind.PHYSICAL }

    companion object {
        /** Stable id from name + country, so the same library found via two providers merges. */
        fun idFor(name: String, countryCode: String?): String =
            (TextKey.libraryKey(name) + "|" + (countryCode ?: "").lowercase())
    }
}

internal object TextKey {
    private val noise = Regex("\\b(the|public|library|libraries|system|district|county|city|of)\\b")

    fun libraryKey(name: String): String =
        com.mardev.nearshelf.core.match.TextNormalizer.basic(name)
            .replace(noise, " ")
            .replace(Regex("\\s+"), " ")
            .trim()
            .ifEmpty { com.mardev.nearshelf.core.match.TextNormalizer.basic(name) }
}
