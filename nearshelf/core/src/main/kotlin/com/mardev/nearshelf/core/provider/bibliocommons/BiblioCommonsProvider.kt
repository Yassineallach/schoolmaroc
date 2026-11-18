package com.mardev.nearshelf.core.provider.bibliocommons

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
import com.mardev.nearshelf.core.net.ProviderHttp
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.ProviderException
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.serialization.SerializationException
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import java.net.URI
import java.net.URLEncoder

// Shapes recorded from gateway.bibliocommons.com (Seattle, Toronto; 2026-11-18).

@Serializable
internal data class BcSearch(val entities: BcEntities = BcEntities())

@Serializable
internal data class BcEntities(
    val bibs: Map<String, BcBib> = emptyMap(),
    val bibItems: Map<String, BcItem> = emptyMap(),
)

@Serializable
internal data class BcBib(val id: String, val briefInfo: BcBrief, val availability: BcAvailability? = null)

@Serializable
internal data class BcBrief(
    val title: String,
    val subtitle: String? = null,
    val format: String? = null,
    val superFormats: List<String> = emptyList(),
    val authors: List<String> = emptyList(),
    val isbns: List<String> = emptyList(),
    val primaryLanguage: String? = null,
    val jacket: BcJacket? = null,
)

@Serializable
internal data class BcJacket(val medium: String? = null, val large: String? = null)

@Serializable
internal data class BcAvailability(
    val availableCopies: Int? = null,
    val totalCopies: Int? = null,
    val heldCopies: Int? = null,
)

@Serializable
internal data class BcItem(
    val callNumber: String? = null,
    val collection: String? = null,
    val branch: BcBranch? = null,
    val branchName: String? = null,
    val availability: BcItemAvailability? = null,
)

@Serializable
internal data class BcBranch(val name: String? = null, val code: String? = null)

@Serializable
internal data class BcItemAvailability(val status: String? = null, val libraryStatus: String? = null)

object BiblioCommonsParser {
    internal val json = Json { ignoreUnknownKeys = true; coerceInputValues = true; explicitNulls = false }

    /** Print books only: e-books and e-audiobooks here are OverDrive/Hoopla records Nearshelf already shows. */
    fun parseSearch(body: String): List<Holding> =
        json.decodeFromString<BcSearch>(body).entities.bibs.values.mapNotNull { bib ->
            val b = bib.briefInfo
            if ("BOOKS" !in b.superFormats || "ELECTRONIC_FORMATS" in b.superFormats) return@mapNotNull null
            val a = bib.availability
            Holding(
                provider = ProviderId.BIBLIOCOMMONS,
                format = Format.PHYSICAL,
                title = b.title,
                subtitle = b.subtitle?.takeIf { it.isNotBlank() },
                authors = b.authors.map(::invertName),
                language = LanguageCodes.toIso1(b.primaryLanguage),
                isbns = b.isbns.filter(Isbn::isValid).map(Isbn::normalize).toSet(),
                owned = a?.totalCopies,
                available = a?.availableCopies,
                holds = a?.heldCopies,
                isAvailableNow = (a?.availableCopies ?: 0) > 0,
                providerItemId = bib.id,
                coverUrl = b.jacket?.medium ?: b.jacket?.large,
                edition = if (b.format == "LPRINT") "Large print" else null,
            )
        }

    fun parseCopies(body: String): List<PhysicalCopy> =
        json.decodeFromString<BcSearch>(body).entities.bibItems.values.map { item ->
            PhysicalCopy(
                branchName = item.branch?.name ?: item.branchName ?: "?",
                branchId = item.branch?.code,
                callNumber = item.callNumber,
                status = status(item.availability),
            )
        }

    internal fun status(a: BcItemAvailability?): CopyStatus = when (a?.status) {
        "AVAILABLE" -> CopyStatus.AVAILABLE
        "LIBRARY_USE_ONLY" -> CopyStatus.LIBRARY_USE_ONLY
        "CHECKED_OUT" -> CopyStatus.CHECKED_OUT
        "IN_TRANSIT" -> CopyStatus.IN_TRANSIT
        "ON_HOLD" -> CopyStatus.ON_HOLD_SHELF
        "UNAVAILABLE" -> when {
            a.libraryStatus?.contains("missing", true) == true || a.libraryStatus?.contains("lost", true) == true -> CopyStatus.MISSING
            a.libraryStatus?.contains("shelved", true) == true || a.libraryStatus?.contains("process", true) == true -> CopyStatus.IN_PROCESSING
            else -> CopyStatus.UNKNOWN
        }
        else -> CopyStatus.UNKNOWN
    }

    /** "Weir, Andy" → "Andy Weir". */
    internal fun invertName(n: String): String {
        val parts = n.split(", ", limit = 2)
        return if (parts.size == 2 && parts[1].isNotBlank()) "${parts[1].trimEnd('.')} ${parts[0]}" else n
    }
}

/**
 * BiblioCommons (many large US/Canadian libraries). The library key is the catalog
 * root, e.g. "https://seattle.bibliocommons.com"; its subdomain is the gateway's
 * library code. One search, then per-copy availability for the few records that
 * match the book (at most [maxDetail]).
 */
class BiblioCommonsProvider(
    client: OkHttpClient,
    private val gateway: String = "https://gateway.bibliocommons.com",
    private val maxDetail: Int = 3,
) : CatalogProvider {
    override val id = ProviderId.BIBLIOCOMMONS
    private val http = ProviderHttp(client, id)
    private val matcher = BookMatcher()

    /** Libraries come from the registry; BiblioCommons has no public directory. */
    override suspend fun findLibraries(query: String): List<LibraryRef> = emptyList()

    override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> = coroutineScope {
        val code = codeOf(library)
        // Toronto's gateway finds nothing for an ISBN, so search words; the matcher checks ISBNs.
        val text = if (!query.title.isNullOrBlank()) query.searchText() else query.isbn ?: query.searchText()
        val url = "$gateway/v2/libraries/$code/bibs/search".toHttpUrl().newBuilder()
            .addQueryParameter("query", text)
            .addQueryParameter("searchType", "smart")
            .build()
        val holdings = parse { BiblioCommonsParser.parseSearch(http.get(url, "application/json")) }
        val wanted = matcher.match(query, holdings).take(maxDetail).map { it.holding.providerItemId }.toSet()
        holdings.map { h ->
            if (h.providerItemId !in wanted) return@map async { h }
            async {
                val copies = parse {
                    BiblioCommonsParser.parseCopies(
                        http.get("$gateway/v2/libraries/$code/bibs/${h.providerItemId}/availability".toHttpUrl(), "application/json"),
                    )
                }
                // Item-level counts are fresher than the search summary.
                h.copy(
                    copies = copies,
                    owned = copies.size,
                    available = copies.count { it.status == CopyStatus.AVAILABLE },
                    isAvailableNow = copies.any { it.status == CopyStatus.AVAILABLE },
                )
            }
        }.awaitAll()
    }

    override fun borrowLink(library: LibraryRef, holding: Holding): URI {
        require(holding.providerItemId.matches(Regex("[A-Za-z0-9]+"))) { "Bad record id ${holding.providerItemId}" }
        return URI("https://${codeOf(library)}.bibliocommons.com/v2/record/${holding.providerItemId}")
    }

    override fun searchLink(library: LibraryRef, query: BookQuery): URI =
        URI("https://${codeOf(library)}.bibliocommons.com/v2/search?query=${enc(query.searchText())}&searchType=smart")

    private fun codeOf(library: LibraryRef): String {
        val host = runCatching { URI(library.key).host }.getOrNull() ?: library.key
        val code = host.removeSuffix(".bibliocommons.com")
        require(code.matches(Regex("[a-z0-9-]+"))) { "Bad BiblioCommons library: ${library.key}" }
        return code
    }

    private fun enc(s: String) = URLEncoder.encode(s, Charsets.UTF_8).replace("+", "%20")

    private inline fun <T> parse(block: () -> T): T = try {
        block()
    } catch (e: SerializationException) {
        throw ProviderException(id, ProviderException.Kind.PARSE, e.message ?: "Unexpected response", e)
    }
}
