package com.mardev.nearshelf.core.provider.hoopla

import com.mardev.nearshelf.core.match.Isbn
import com.mardev.nearshelf.core.metadata.LanguageCodes
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json

// Shapes recorded from patron-api-gateway.hoopladigital.com (2026-11-18). Only the
// fields Nearshelf reads are declared. The single-library endpoint is never used:
// it returns credential-like fields (see docs/providers/hoopla.md).

@Serializable
internal data class HooplaLibrary(
    val id: Long,
    val name: String,
    val enabled: Boolean = true,
    val city: String? = null,
    val state: String? = null,
    val country: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val circsPerPatronMonth: Int? = null,
    val hideFromChooser: Boolean = false,
)

@Serializable
internal data class GqlResponse(val data: GqlData? = null, val errors: List<GqlError>? = null)

@Serializable
internal data class GqlError(val message: String? = null)

@Serializable
internal data class GqlData(val search: GqlSearch? = null)

@Serializable
internal data class GqlSearch(val found: Int = 0, val hits: List<GqlTitle> = emptyList())

@Serializable
internal data class GqlTitle(
    val id: String,
    val title: String,
    val subtitle: String? = null,
    val isbn: String? = null,
    val language: Named? = null,
    val kind: Named? = null,
    val authors: List<Named> = emptyList(),
    val artKey: String? = null,
)

@Serializable
internal data class Named(val name: String? = null)

object HooplaParser {
    internal val json = Json { ignoreUnknownKeys = true; coerceInputValues = true; explicitNulls = false }
    private val trailingRegion = Regex("\\s*\\(([A-Za-z .]{2,20})\\)\\s*$")

    fun parseLibraries(body: String): List<LibraryRef> =
        json.decodeFromString<List<HooplaLibrary>>(body)
            .filter { it.enabled && !it.hideFromChooser }
            .map { lib ->
                LibraryRef(
                    provider = ProviderId.HOOPLA,
                    key = lib.id.toString(),
                    // "Seattle Public Library (WA)" → "Seattle Public Library", so it merges with Libby's entry.
                    name = lib.name.replace(trailingRegion, "").trim(),
                    city = lib.city?.let(::tidyCase),
                    region = lib.state,
                    countryCode = lib.country,
                    catalogUrl = "https://www.hoopladigital.com",
                    latitude = lib.latitude,
                    longitude = lib.longitude,
                    borrowLimitPerMonth = lib.circsPerPatronMonth,
                )
            }

    /** "SEATTLE" → "Seattle"; mixed-case names are left alone. */
    internal fun tidyCase(s: String): String =
        if (s != s.uppercase()) s else s.lowercase().split(' ').joinToString(" ") { w -> w.replaceFirstChar { it.titlecase() } }

    /** Books only: music, film and TV are out of scope. Comics count as OTHER. */
    fun parseSearch(body: String): List<Holding> {
        val r = json.decodeFromString<GqlResponse>(body)
        if (r.data?.search == null && !r.errors.isNullOrEmpty()) {
            throw IllegalArgumentException(r.errors.joinToString { it.message.orEmpty() })
        }
        return r.data?.search?.hits.orEmpty().mapNotNull { t ->
            val format = when (t.kind?.name) {
                "EBOOK" -> Format.EBOOK
                "AUDIOBOOK" -> Format.AUDIOBOOK
                "COMIC" -> Format.OTHER
                else -> return@mapNotNull null
            }
            Holding(
                provider = ProviderId.HOOPLA,
                format = format,
                title = t.title,
                subtitle = t.subtitle,
                authors = t.authors.mapNotNull { it.name },
                language = LanguageCodes.toIso1(t.language?.name),
                isbns = setOfNotNull(t.isbn?.takeIf { Isbn.isValid(it) }?.let(Isbn::normalize)),
                isAvailableNow = false,
                availabilityKnown = false,
                providerItemId = t.id,
                coverUrl = t.artKey?.takeIf { it.isNotBlank() }?.let { "https://cover.hoopladigital.com/${it}_270.jpeg" },
            )
        }
    }
}
