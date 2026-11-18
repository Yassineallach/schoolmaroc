package com.mardev.nearshelf.core.provider.sierra

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.match.Isbn
import com.mardev.nearshelf.core.metadata.LanguageCodes
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.ProviderException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.net.URI

// Shapes recorded from Vega Discover (NYPL na2, Suffolk na), 2026-11-18.

@Serializable
internal data class VegaPage(val data: List<VegaGroup> = emptyList())

@Serializable
internal data class VegaGroup(
    val id: String,
    val title: String,
    val language: String? = null,
    val primaryAgent: VegaAgent? = null,
    val materialTabs: List<VegaTab> = emptyList(),
)

@Serializable
internal data class VegaAgent(val label: String? = null)

@Serializable
internal data class VegaTab(
    val name: String,
    val type: String? = null,
    val callNumber: String? = null,
    val itemCount: Int? = null,
    val identifiedBy: VegaIdentified? = null,
    val locations: List<VegaLocation>? = null,
    val coverUrl: VegaCover? = null,
)

@Serializable
internal data class VegaIdentified(val isbn: List<String> = emptyList())

@Serializable
internal data class VegaLocation(val code: String? = null, val label: String, val availabilityStatus: String? = null, val callNumber: String? = null)

@Serializable
internal data class VegaCover(val medium: String? = null)

@Serializable
internal data class VegaLocations(val available: List<VegaLocation> = emptyList(), val unavailable: List<VegaLocation> = emptyList())

object VegaParser {
    internal val json = Json { ignoreUnknownKeys = true; coerceInputValues = true; explicitNulls = false }
    private val printTabs = setOf("Book", "Large Print", "Board Book", "Graphic Novel", "Paperback")

    /** One holding per print tab of each format group; id = "{formatGroupId}|{tab}". */
    fun parseSearch(body: String): List<Holding> = json.decodeFromString<VegaPage>(body).data.flatMap { g ->
        g.materialTabs.filter { it.type == "physical" && it.name in printTabs }.map { tab ->
            val copies = tab.locations.orEmpty().map(::copyOf)
            Holding(
                provider = ProviderId.SIERRA_VEGA,
                format = Format.PHYSICAL,
                title = g.title.replace(Regex("[\\s/:;,.=]+$"), ""),
                authors = listOfNotNull(g.primaryAgent?.label?.let(::invertName)),
                language = LanguageCodes.toIso1(g.language),
                isbns = tab.identifiedBy?.isbn.orEmpty().filter(Isbn::isValid).map(Isbn::normalize).toSet(),
                owned = tab.itemCount,
                isAvailableNow = copies.any { it.status == CopyStatus.AVAILABLE },
                providerItemId = "${g.id}|${tab.name}",
                coverUrl = tab.coverUrl?.medium,
                edition = if (tab.name == "Large Print") "Large print" else null,
                copies = copies,
                branchLevelOnly = true,
            )
        }
    }

    fun parseLocations(body: String): List<PhysicalCopy> = json.decodeFromString<VegaLocations>(body).let { l ->
        l.available.map { copyOf(it, CopyStatus.AVAILABLE) } + l.unavailable.map { copyOf(it, CopyStatus.UNKNOWN) }
    }

    private fun copyOf(l: VegaLocation, forced: CopyStatus? = null) = PhysicalCopy(
        branchName = l.label,
        branchId = l.code,
        callNumber = l.callNumber,
        status = forced ?: if (l.availabilityStatus == "Available") CopyStatus.AVAILABLE else CopyStatus.UNKNOWN,
    )

    internal fun invertName(n: String): String {
        val parts = n.trimEnd('.').split(", ", limit = 2)
        return if (parts.size == 2 && parts[1].isNotBlank()) "${parts[1]} ${parts[0]}" else n.trimEnd('.')
    }

    /** "https://nypl.na2.iiivega.com" → "https://na2.iiivega.com" (the catalog's config.js API_URL). */
    fun apiBase(catalogHost: String): String = "https://" + catalogHost.substringAfter('.')
}

/**
 * Sierra / Polaris "Vega Discover". Search is a POST to the regional API with the
 * catalog's domain in iii-customer-domain. Availability is per branch, not per copy:
 * the search lists the first few branches, and the locations call lists them all.
 */
class VegaProvider(private val client: OkHttpClient, private val maxDetail: Int = 3) : CatalogProvider {
    override val id = ProviderId.SIERRA_VEGA
    private val matcher = BookMatcher()

    override suspend fun findLibraries(query: String): List<LibraryRef> = emptyList()

    override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> = coroutineScope {
        val host = host(library)
        val text = if (!query.title.isNullOrBlank()) query.searchText() else query.isbn ?: query.searchText()
        val body = buildJsonObject {
            put("searchText", text); put("sorting", "relevance"); put("sortOrder", "asc")
            put("searchType", "everything"); put("pageNum", 0); put("pageSize", 10); put("resourceType", "FormatGroup")
        }.toString()
        val holdings = parse {
            VegaParser.parseSearch(
                call(host, Request.Builder().url("${VegaParser.apiBase(host)}/api/search-result/search/format-groups")
                    .post(body.toRequestBody("application/json".toMediaType())).header("api-version", "2")),
            )
        }
        val wanted = matcher.match(query, holdings).take(maxDetail).map { it.holding.providerItemId }.toSet()
        holdings.map { h ->
            if (h.providerItemId !in wanted) return@map async { h }
            async {
                val (group, tab) = h.providerItemId.split('|', limit = 2)
                val url = okhttp3.HttpUrl.Builder().scheme("https").host(VegaParser.apiBase(host).removePrefix("https://"))
                    .addPathSegments("api/search-result/drawer/format-groups").addPathSegment(group).addPathSegment("locations")
                    .addQueryParameter("tab", tab).build()
                // Keep the search's first few branches if the full list can't be read.
                val copies = try {
                    parse { VegaParser.parseLocations(call(host, Request.Builder().url(url).header("api-version", "1"))) }
                } catch (e: ProviderException) {
                    if (e.kind == ProviderException.Kind.PARSE) h.copies else throw e
                }
                h.copy(copies = copies, isAvailableNow = copies.any { it.status == CopyStatus.AVAILABLE })
            }
        }.awaitAll()
    }

    override fun borrowLink(library: LibraryRef, holding: Holding): URI {
        val group = holding.providerItemId.substringBefore('|')
        require(group.matches(Regex("[0-9a-f-]{36}"))) { "Bad format group $group" }
        return URI("https://${host(library)}/search/card?id=$group&entityType=FormatGroup")
    }

    private suspend fun call(host: String, builder: Request.Builder): String = withContext(Dispatchers.IO) {
        val req = builder.header("iii-customer-domain", host).header("iii-host-domain", host)
            .header("Accept", "application/json").header("Origin", "https://$host").build()
        try {
            client.newCall(req).execute().use { r ->
                if (!r.isSuccessful) {
                    throw ProviderException(id, if (r.code == 429 || r.code == 403) ProviderException.Kind.RATE_LIMITED else ProviderException.Kind.HTTP, "HTTP ${r.code}")
                }
                r.body.string()
            }
        } catch (e: IOException) {
            throw ProviderException(id, ProviderException.Kind.NETWORK, e.message ?: "Network error", e)
        }
    }

    private fun host(library: LibraryRef): String {
        val h = URI(library.key).host?.lowercase()
        require(h != null && h.endsWith(".iiivega.com")) { "Bad Vega catalog ${library.key}" }
        return h
    }

    private inline fun <T> parse(block: () -> T): T = try {
        block()
    } catch (e: SerializationException) {
        throw ProviderException(id, ProviderException.Kind.PARSE, e.message ?: "Unexpected response", e)
    }
}
