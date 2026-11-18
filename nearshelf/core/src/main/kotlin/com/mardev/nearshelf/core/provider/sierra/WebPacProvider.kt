package com.mardev.nearshelf.core.provider.sierra

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.net.ProviderHttp
import com.mardev.nearshelf.core.provider.CatalogProvider
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import org.jsoup.Jsoup
import org.jsoup.nodes.Element
import java.net.URI
import java.net.URLEncoder

/** Parses Sierra's classic WebPAC. Recorded from Cincinnati & Hamilton County's classic catalog, 2026-11-18. */
object WebPacParser {
    private val printFormat = Regex("^(book|large print|paperback|graphic novel|board book)$", RegexOption.IGNORE_CASE)

    fun parseResults(html: String): List<Holding> = Jsoup.parse(html).select("td.briefcitCell").mapNotNull { cell ->
        val bib = Regex("~(b\\d+)").find(cell.html())?.groupValues?.get(1) ?: return@mapNotNull null
        val format = cell.select("img[alt]").map { it.attr("alt") }.firstOrNull { printFormat.matches(it) } ?: return@mapNotNull null
        val title = cell.select("a[href*=frameset]").firstOrNull()?.text()?.trim()?.replace(Regex("[\\s/:;,.]+$"), "")
            ?: return@mapNotNull null
        val text = cell.text()
        val holds = Regex("(\\d+) holds? on").find(text)?.groupValues?.get(1)?.toInt()
        val owned = Regex("of (\\d+) cop(?:y|ies)").find(text)?.groupValues?.get(1)?.toInt()
        val copies = cell.select("table.bibItems tr.bibItemsEntry").map(::copyRow)
        Holding(
            provider = ProviderId.SIERRA_ENCORE,
            format = Format.PHYSICAL,
            title = title,
            holds = holds,
            owned = owned ?: copies.size.takeIf { it > 0 },
            isAvailableNow = copies.any { it.status == CopyStatus.AVAILABLE },
            providerItemId = bib,
            edition = if (format.equals("Large Print", true)) "Large print" else null,
            copies = copies,
        )
    }

    /** The record page's item table (first page of copies). */
    fun parseRecordItems(html: String): List<PhysicalCopy> = Jsoup.parse(html).select("table.bibItems tr.bibItemsEntry").map(::copyRow)

    private fun copyRow(row: Element): PhysicalCopy {
        val cells = row.select("> td").map { it.text().replace(' ', ' ').trim() }
        val (status, due) = status(cells.lastOrNull().orEmpty())
        return PhysicalCopy(
            // A shelf location such as "Anderson Fiction": matched to the Anderson branch later.
            branchName = cells.getOrNull(0).orEmpty().ifEmpty { "?" },
            callNumber = cells.getOrNull(1)?.takeIf { it.isNotEmpty() },
            status = status,
            dueDate = due,
        )
    }

    internal fun status(s: String): Pair<CopyStatus, String?> {
        val t = s.uppercase().trim()
        Regex("^DUE (\\d{2})-(\\d{2})-(\\d{2})").find(t)?.let { m ->
            val (mm, dd, yy) = m.destructured
            return CopyStatus.CHECKED_OUT to "20$yy-$mm-$dd"
        }
        return when {
            t == "AVAILABLE" || t.startsWith("CHECK SHELF") || t.startsWith("CHECK SHELVES") -> CopyStatus.AVAILABLE
            "TRANSIT" in t -> CopyStatus.IN_TRANSIT
            "HOLDSHELF" in t || "ON HOLD" in t -> CopyStatus.ON_HOLD_SHELF
            "LIB USE" in t || "LIBRARY USE" in t || "REFERENCE" in t -> CopyStatus.LIBRARY_USE_ONLY
            "ORDER" in t || "PROCESS" in t || "CATALOG" in t -> CopyStatus.IN_PROCESSING
            "MISSING" in t || "BILLED" in t || "LOST" in t || "WITHDRAWN" in t -> CopyStatus.MISSING
            else -> CopyStatus.UNKNOWN
        } to null
    }
}

/**
 * Sierra classic WebPAC (also reachable on many Encore hosts at /search~S1). Search page
 * gives records with a few copies; the record page lists the first batch of copies.
 */
class WebPacProvider(client: OkHttpClient, private val maxDetail: Int = 3) : CatalogProvider {
    override val id = ProviderId.SIERRA_ENCORE
    private val http = ProviderHttp(client, id)
    private val matcher = BookMatcher()

    override suspend fun findLibraries(query: String): List<LibraryRef> = emptyList()

    override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> = coroutineScope {
        val base = base(library)
        val text = if (!query.title.isNullOrBlank()) query.searchText() else query.isbn ?: query.searchText()
        val url = "$base/search~S1/".toHttpUrl().newBuilder()
            .addQueryParameter("searchtype", "X").addQueryParameter("searcharg", text).addQueryParameter("SORT", "D").build()
        val holdings = WebPacParser.parseResults(http.get(url, "text/html"))
        val wanted = matcher.match(query, holdings).take(maxDetail).map { it.holding.providerItemId }.toSet()
        holdings.map { h ->
            if (h.providerItemId !in wanted) return@map async { h }
            async {
                val copies = WebPacParser.parseRecordItems(http.get("$base/record=${h.providerItemId}~S1".toHttpUrl(), "text/html"))
                if (copies.isEmpty()) h else h.copy(copies = copies, isAvailableNow = copies.any { it.status == CopyStatus.AVAILABLE })
            }
        }.awaitAll()
    }

    override fun borrowLink(library: LibraryRef, holding: Holding): URI {
        require(holding.providerItemId.matches(Regex("b\\d+")))
        return URI("${base(library)}/record=${holding.providerItemId}~S1")
    }

    override fun searchLink(library: LibraryRef, query: BookQuery): URI =
        URI("${base(library)}/search~S1/?searchtype=X&searcharg=${URLEncoder.encode(query.searchText(), Charsets.UTF_8)}")

    private fun base(library: LibraryRef): String {
        val u = URI(library.key)
        require(!u.host.isNullOrBlank()) { "Bad Sierra catalog ${library.key}" }
        return "https://${u.host}"
    }
}
