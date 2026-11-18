package com.mardev.nearshelf.core.provider.koha

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.match.Isbn
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
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.SerializationException
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import org.jsoup.Jsoup
import org.jsoup.parser.Parser
import java.net.URI
import java.net.URLEncoder

// Shapes recorded from Koha OPACs (Pillsbury Free Library NH, Portsmouth NH, South Taranaki
// and Horowhenua NZ; 2026-11-18). REST: /api/v1/public (Koha 20.11+, RESTPublicAPI on).

@Serializable
internal data class KohaItem(
    val holding_library_id: String? = null,
    val home_library_id: String? = null,
    val callnumber: String? = null,
    /** Koha's items.onloan: the due date of the current checkout (null when on the shelf). */
    val checked_out_date: String? = null,
    val lost_status: Int = 0,
    val withdrawn: Int = 0,
    val not_for_loan_status: Int = 0,
    val damaged_status: Int = 0,
)

@Serializable
internal data class KohaLibrary(val library_id: String, val name: String)

object KohaParser {
    internal val json = Json { ignoreUnknownKeys = true; coerceInputValues = true; explicitNulls = false }
    private val trailingPunct = Regex("[\\s/:;,.=]+$")

    /** OPAC search as RSS (opac-search.pl?format=rss). Koha's RSS doesn't say format or language. */
    fun parseRss(body: String): List<Holding> {
        val doc = Jsoup.parse(body, "", Parser.xmlParser())
        return doc.select("item").mapNotNull { item ->
            val link = item.selectFirst("link")?.text().orEmpty()
            val id = Regex("biblionumber=(\\d+)").find(link)?.groupValues?.get(1) ?: return@mapNotNull null
            val title = item.selectFirst("title")?.text()?.trim()?.replace(trailingPunct, "")?.takeIf { it.isNotEmpty() }
                ?: return@mapNotNull null
            // Description HTML: "<p> By Tolkien, J. R. R..<br /> New York, Ballantine 1966 .<br /> ...".
            val firstLine = item.selectFirst("description")?.text().orEmpty()
                .split(Regex("<br\\s*/?>", RegexOption.IGNORE_CASE)).firstOrNull().orEmpty()
            val author = Jsoup.parse(firstLine).text().trim()
                .takeIf { it.startsWith("By ") }?.removePrefix("By ")?.let(::tidyAuthor)?.takeIf { it.isNotEmpty() }
            val isbns = item.select("dc|identifier, identifier").map { it.text() }
                .flatMap { Regex("[0-9Xx][0-9Xx -]{8,16}[0-9Xx]").findAll(it).map { m -> m.value } }
                .map { it.replace(Regex("[ -]"), "") }.filter(Isbn::isValid).map(Isbn::normalize).toSet()
            Holding(
                provider = ProviderId.KOHA,
                format = Format.PHYSICAL,
                title = title.substringBefore(" / ").replace(trailingPunct, ""),
                authors = listOfNotNull(author?.let(::invertName)),
                isbns = isbns,
                providerItemId = id,
            )
        }
    }

    fun parseLibraries(body: String): Map<String, String> =
        json.decodeFromString<List<KohaLibrary>>(body).associate { it.library_id to it.name }

    fun parseItems(body: String, libraryNames: Map<String, String>): List<PhysicalCopy> =
        json.decodeFromString<List<KohaItem>>(body).map { item ->
            val branchId = item.holding_library_id ?: item.home_library_id
            PhysicalCopy(
                branchName = branchId?.let { libraryNames[it] ?: it } ?: "?",
                branchId = branchId,
                callNumber = item.callnumber,
                status = status(item),
                dueDate = item.checked_out_date?.take(10),
            )
        }

    internal fun status(i: KohaItem): CopyStatus = when {
        i.lost_status != 0 || i.withdrawn != 0 -> CopyStatus.MISSING
        i.checked_out_date != null -> CopyStatus.CHECKED_OUT
        i.not_for_loan_status != 0 -> CopyStatus.LIBRARY_USE_ONLY
        else -> CopyStatus.AVAILABLE
    }

    /** "Tolkien, J. R. R.." → "Tolkien, J. R. R." (the dot after an initial stays); "Weir, Andy." → "Weir, Andy". */
    internal fun tidyAuthor(s: String): String {
        val t = s.trim().replace(Regex("\\.{2,}$"), ".")
        return if (Regex("\\b\\p{Lu}\\.$").containsMatchIn(t)) t else t.trimEnd('.', ' ')
    }

    /** "Tolkien, J. R. R." → "J. R. R. Tolkien" */
    internal fun invertName(n: String): String {
        val parts = n.split(", ", limit = 2)
        return if (parts.size == 2 && parts[1].isNotBlank()) "${parts[1]} ${parts[0]}" else n
    }
}

/**
 * Koha (common in Europe, Africa, the Arab world, Oceania). Key = OPAC root URL.
 * Search uses the OPAC's RSS output; copies come from the public REST API.
 *
 * Many Koha hosts now put bot checks in front of the OPAC (Cloudflare rate limits at
 * Bywater, a JavaScript challenge at Catalyst). Those surface as Kind.BLOCKED and the
 * app offers [searchLink] instead. When the REST API is switched off, holdings are
 * returned without copies (availability unknown) rather than failing.
 */
class KohaProvider(
    client: OkHttpClient,
    private val maxDetail: Int = 3,
) : CatalogProvider {
    override val id = ProviderId.KOHA
    private val http = ProviderHttp(client, id)
    private val matcher = BookMatcher()
    private val libraryNames = HashMap<String, Map<String, String>>()
    private val namesLock = Mutex()

    override suspend fun findLibraries(query: String): List<LibraryRef> = emptyList()

    override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> = coroutineScope {
        val base = baseOf(library)
        val text = if (!query.title.isNullOrBlank()) query.searchText() else query.isbn ?: query.searchText()
        val url = "$base/cgi-bin/koha/opac-search.pl".toHttpUrl().newBuilder()
            .addQueryParameter("q", text)
            .addQueryParameter("format", "rss")
            .build()
        val rss = http.fetch(url, "application/rss+xml, application/xml, text/xml")
        if (rss.contentType?.contains("html", true) == true) {
            throw ProviderException(id, ProviderException.Kind.PARSE, "OPAC at ${url.host} returned HTML instead of RSS")
        }
        val holdings = KohaParser.parseRss(rss.body)
        val wanted = matcher.match(query, holdings).take(maxDetail).map { it.holding.providerItemId }.toSet()
        if (wanted.isEmpty()) return@coroutineScope holdings
        val names = names(base)
        holdings.map { h ->
            if (h.providerItemId !in wanted) return@map async { h }
            async {
                val r = http.fetch("$base/api/v1/public/biblios/${h.providerItemId}/items".toHttpUrl(), "application/json", setOf(401, 403, 404))
                if (r.code != 200) return@async h.copy(availabilityKnown = false)
                val copies = parse { KohaParser.parseItems(r.body, names) }
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
        require(holding.providerItemId.matches(Regex("\\d+"))) { "Bad biblionumber ${holding.providerItemId}" }
        return URI("${baseOf(library)}/cgi-bin/koha/opac-detail.pl?biblionumber=${holding.providerItemId}")
    }

    override fun searchLink(library: LibraryRef, query: BookQuery): URI =
        URI("${baseOf(library)}/cgi-bin/koha/opac-search.pl?q=${URLEncoder.encode(query.searchText(), Charsets.UTF_8)}")

    /** Branch codes → names, once per catalog; an empty map if the API is off. */
    private suspend fun names(base: String): Map<String, String> = namesLock.withLock {
        libraryNames[base] ?: try {
            val r = http.fetch("$base/api/v1/public/libraries?_per_page=500".toHttpUrl(), "application/json", setOf(401, 403, 404))
            if (r.code == 200) KohaParser.parseLibraries(r.body) else emptyMap()
        } catch (_: ProviderException) {
            emptyMap()
        } catch (_: SerializationException) {
            emptyMap()
        }.also { libraryNames[base] = it }
    }

    private fun baseOf(library: LibraryRef): String {
        val u = URI(library.key)
        require(u.scheme == "https" && !u.host.isNullOrBlank()) { "Bad Koha catalog: ${library.key}" }
        return "https://${u.host}"
    }

    private inline fun <T> parse(block: () -> T): T = try {
        block()
    } catch (e: SerializationException) {
        throw ProviderException(id, ProviderException.Kind.PARSE, e.message ?: "Unexpected response", e)
    }
}
