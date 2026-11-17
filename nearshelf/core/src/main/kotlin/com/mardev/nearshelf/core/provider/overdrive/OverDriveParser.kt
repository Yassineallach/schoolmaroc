package com.mardev.nearshelf.core.provider.overdrive

import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import kotlinx.serialization.json.Json

/** Pure JSON → domain mapping, separate from HTTP so fixtures can drive it. */
object OverDriveParser {
    internal val json = Json { ignoreUnknownKeys = true; coerceInputValues = true }

    /** Roles that are not authors; kept out of [Holding.authors]. */
    private val nonAuthorRoles = setOf("Narrator", "Translator", "Illustrator", "Performer", "Reader", "Read by")

    fun parseLibraries(body: String): List<LibraryRef> =
        mapLibraries(json.decodeFromString<LocateResponse>(body))

    fun parseMedia(body: String): List<Holding> =
        json.decodeFromString<MediaResponse>(body).items.map(::toHolding)

    internal fun mapLibraries(response: LocateResponse): List<LibraryRef> {
        // locate returns branches; several branches share one lending system.
        // Keep the first branch's location for each system, in relevance order.
        val bySystem = LinkedHashMap<String, LibraryRef>()
        for (branch in response.branches) {
            for (system in branch.systems) {
                val key = system.fulfillmentId?.takeIf { it.isNotBlank() } ?: continue
                bySystem.getOrPut(key) {
                    LibraryRef(
                        provider = ProviderId.OVERDRIVE,
                        key = key,
                        name = system.name.trim(),
                        city = branch.city,
                        region = branch.regionCode,
                        countryCode = branch.countryCode,
                        catalogUrl = "https://libbyapp.com/library/$key",
                        latitude = branch.latitude,
                        longitude = branch.longitude,
                        logoUrl = system.styling?.logos?.firstOrNull()?.sourceUrl,
                    )
                }
            }
        }
        return bySystem.values.toList()
    }

    internal fun toHolding(item: MediaItem): Holding {
        val isbns = item.formats.flatMap { f ->
            listOfNotNull(f.isbn) + f.identifiers.filter { it.type.equals("ISBN", true) }.map { it.value }
        }.map { it.filter(Char::isLetterOrDigit) }.filter { it.length == 10 || it.length == 13 }.toSet()

        val authors = item.creators
            .filter { c -> c.role == null || c.role !in nonAuthorRoles }
            .map { it.name }
            .distinct()

        return Holding(
            provider = ProviderId.OVERDRIVE,
            format = when (item.type?.id) {
                "ebook" -> Format.EBOOK
                "audiobook" -> Format.AUDIOBOOK
                else -> Format.OTHER
            },
            title = item.title,
            subtitle = item.subtitle,
            authors = authors,
            language = item.languages.firstOrNull()?.id,
            isbns = isbns,
            owned = item.ownedCopies,
            available = item.availableCopies,
            holds = item.holdsCount,
            // OverDrive reports a wait estimate even for titles on the shelf; drop it then.
            waitDays = item.estimatedWaitDays.takeUnless { item.isAvailable },
            isAvailableNow = item.isAvailable,
            providerItemId = item.id,
            coverUrl = item.covers["cover300Wide"]?.href ?: item.covers.values.firstOrNull()?.href,
        )
    }
}
