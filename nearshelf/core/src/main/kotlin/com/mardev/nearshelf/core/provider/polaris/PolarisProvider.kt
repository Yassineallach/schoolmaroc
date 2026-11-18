package com.mardev.nearshelf.core.provider.polaris

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.match.Isbn
import com.mardev.nearshelf.core.match.MarcNames
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.net.ProviderHttp
import com.mardev.nearshelf.core.provider.CatalogProvider
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import okhttp3.Cookie
import okhttp3.CookieJar
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import org.jsoup.Jsoup
import java.net.URI
import java.net.URLEncoder
import java.time.LocalDate
import java.time.format.DateTimeFormatter

/** Parses Polaris PowerPAC pages. Recorded from Hillsborough County (FL) and Brentwood (TN), 2026-11-18. */
object PolarisParser {
    private val printFormat = Regex("book|print|paperback|hardcover|graphic novel", RegexOption.IGNORE_CASE)
    private val notPrint = Regex("ebook|e-book|audio|cd|dvd|blu-ray|kit|video|music|playaway|magazine", RegexOption.IGNORE_CASE)

    /** components/ajaxResults.aspx: one block per record. Print formats only. */
    fun parseResults(html: String): List<Holding> {
        val doc = Jsoup.parse(html)
        return doc.select("div.content-module--search-result").mapNotNull { block ->
            val format = block.selectFirst("img.c-title-detail-formats__img")?.attr("alt").orEmpty()
            if (!printFormat.containsMatchIn(format) || notPrint.containsMatchIn(format)) return@mapNotNull null
            val titleLink = block.selectFirst(".nsm-brief-primary-title-group a") ?: return@mapNotNull null
            val cn = Regex("[?&]cn=(\\d+)").find(titleLink.attr("href"))?.groupValues?.get(1) ?: return@mapNotNull null
            val author = block.selectFirst(".nsm-brief-primary-author-group")?.text()?.removePrefix("by ")?.trim()
                ?.replace(Regex("\\s+,"), ",")?.trimEnd('.', ',')
            val isbn = block.select("div.gbs-preview-div").firstNotNullOfOrNull { Regex("ISBN:([0-9Xx]{10,13})").find(it.id())?.groupValues?.get(1) }
            val text = block.text()
            val holds = Regex("Current Holds:\\s*(\\d+)").find(text)?.groupValues?.get(1)?.toInt()
            val avail = Regex("System Availability:\\s*(\\d+)\\s*\\(of\\s*(\\d+)\\)").find(text)
            Holding(
                provider = ProviderId.POLARIS,
                format = Format.PHYSICAL,
                title = titleLink.text().trim().replace(Regex("[\\s/:;,.]+$"), ""),
                authors = listOfNotNull(author?.let(MarcNames::display)),
                isbns = setOfNotNull(isbn?.takeIf(Isbn::isValid)?.let(Isbn::normalize)),
                holds = holds,
                available = avail?.groupValues?.get(1)?.toInt(),
                owned = avail?.groupValues?.get(2)?.toInt(),
                isAvailableNow = (avail?.groupValues?.get(1)?.toInt() ?: 0) > 0,
                providerItemId = cn,
                edition = if (format.contains("large", true)) "Large print" else null,
            )
        }
    }

    /**
     * Result position per control number, from each record's Availability link
     * ("ajaxavailability.aspx?…&pos=1&bibid=1803265"). Polaris returns no branches without it.
     */
    fun positions(html: String): Map<String, String> =
        Regex("ajaxavailability\\.aspx\\?[^'\"]*?pos=(\\d+)&(?:amp;)?bibid=(\\d+)").findAll(html)
            .associate { it.groupValues[2] to it.groupValues[1] }

    /** components/ajaxavailability.aspx: a location row per branch, then one row per copy. */
    fun parseAvailability(html: String): List<PhysicalCopy> {
        val copies = mutableListOf<PhysicalCopy>()
        var branch = "?"
        for (row in Jsoup.parse(html).select("table.availability__table tr")) {
            when {
                row.hasClass("location") -> branch = row.selectFirst("a.group")?.text()?.trim() ?: branch
                row.hasClass("piece") -> {
                    val cells = row.select("> td")
                    val statusText = cells.getOrNull(2)?.text()?.trim().orEmpty()
                    val (status, due) = status(statusText)
                    copies += PhysicalCopy(
                        branchName = branch,
                        callNumber = row.selectFirst("td.piecefront")?.text()?.trim()?.takeIf { it.isNotEmpty() },
                        status = status,
                        dueDate = due,
                    )
                }
            }
        }
        return copies
    }

    private val usDate = DateTimeFormatter.ofPattern("M/d/yyyy")

    internal fun status(s: String): Pair<CopyStatus, String?> {
        val t = s.lowercase()
        return when {
            t.startsWith("out") -> CopyStatus.CHECKED_OUT to Regex("Due:\\s*(\\d{1,2}/\\d{1,2}/\\d{4})").find(s)?.groupValues?.get(1)
                ?.let { runCatching { LocalDate.parse(it, usDate).toString() }.getOrNull() }
            t == "in" || t == "checked in" || t == "available" -> CopyStatus.AVAILABLE to null
            "transit" in t || t == "transferred" -> CopyStatus.IN_TRANSIT to null
            "held" in t || "hold shelf" in t -> CopyStatus.ON_HOLD_SHELF to null
            "process" in t || "on order" in t -> CopyStatus.IN_PROCESSING to null
            "missing" in t || "lost" in t || "claim" in t || "withdrawn" in t -> CopyStatus.MISSING to null
            "non-circ" in t || "reference" in t || "library use" in t -> CopyStatus.LIBRARY_USE_ONLY to null
            else -> CopyStatus.UNKNOWN to null
        }
    }

    internal fun invertName(n: String): String {
        val noRole = n.replace(Regex(",?\\s*(author|editor|illustrator|translator|narrator)\\.?\\s*$", RegexOption.IGNORE_CASE), "").trimEnd(',', '.', ' ')
        val parts = noRole.split(", ", limit = 2)
        return if (parts.size == 2 && parts[1].isNotBlank()) "${parts[1].trimEnd(',', '.')} ${parts[0]}" else noRole
    }
}

/**
 * Polaris PowerPAC. Results and availability are session-bound: a search page sets
 * the session, then components/ajaxResults.aspx returns the records and
 * components/ajaxavailability.aspx (via a process.search redirect) each record's copies.
 * Key = PowerPAC root, e.g. "https://catalog.hcplc.org/polaris". One search at a time per
 * catalog, because results belong to the session's last search.
 */
class PolarisProvider(client: OkHttpClient, private val maxDetail: Int = 3) : CatalogProvider {
    override val id = ProviderId.POLARIS
    private val jar = MemoryCookieJar()
    private val http = ProviderHttp(client.newBuilder().cookieJar(jar).followRedirects(true).build(), id)
    private val matcher = BookMatcher()
    private val sessionLocks = HashMap<String, Mutex>()

    override suspend fun findLibraries(query: String): List<LibraryRef> = emptyList()

    override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> {
        val base = base(library)
        val lock = synchronized(sessionLocks) { sessionLocks.getOrPut(base) { Mutex() } }
        return lock.withLock {
            val text = if (!query.title.isNullOrBlank()) query.searchText() else query.isbn ?: query.searchText()
            http.get(
                "$base/search/searchresults.aspx".toHttpUrl().newBuilder()
                    .addQueryParameter("ctx", "1.1033.0.0.1").addQueryParameter("type", "Keyword")
                    .addQueryParameter("term", text).addQueryParameter("by", "KW")
                    .addQueryParameter("sort", "RELEVANCE").addQueryParameter("page", "0")
                    .build(),
            )
            val resultsHtml = http.get("$base/search/components/ajaxResults.aspx?page=1".toHttpUrl())
            val holdings = PolarisParser.parseResults(resultsHtml)
            val positions = PolarisParser.positions(resultsHtml)
            val wanted = matcher.match(query, holdings).take(maxDetail).map { it.holding.providerItemId }.toSet()
            holdings.map { h ->
                val pos = positions[h.providerItemId]
                if (h.providerItemId !in wanted || pos == null) return@map h
                val url = "$base/search/components/ajaxavailability.aspx".toHttpUrl().newBuilder()
                    .addQueryParameter("fp", "1").addQueryParameter("level", "local").addQueryParameter("morelink", "0")
                    .addQueryParameter("pos", pos).addQueryParameter("bibid", h.providerItemId)
                    .addQueryParameter("displayAeonOnly", "0").build()
                val copies = PolarisParser.parseAvailability(http.get(url))
                if (copies.isEmpty()) h else h.copy(
                    copies = copies,
                    owned = copies.size,
                    available = copies.count { it.status == CopyStatus.AVAILABLE },
                    isAvailableNow = copies.any { it.status == CopyStatus.AVAILABLE },
                )
            }
        }
    }

    /** Polaris's permalink: a control-number search that shows the record with its Request button. */
    override fun borrowLink(library: LibraryRef, holding: Holding): URI {
        require(holding.providerItemId.matches(Regex("\\d+")))
        return URI("${base(library)}/view.aspx?cn=${holding.providerItemId}")
    }

    override fun searchLink(library: LibraryRef, query: BookQuery): URI = URI(
        "${base(library)}/search/searchresults.aspx?ctx=1.1033.0.0.1&type=Keyword&by=KW&term=" +
            URLEncoder.encode(query.searchText(), Charsets.UTF_8),
    )

    private fun base(library: LibraryRef): String {
        val u = URI(library.key)
        require(!u.host.isNullOrBlank()) { "Bad Polaris catalog ${library.key}" }
        return "https://${u.host}${u.rawPath.orEmpty().trimEnd('/')}"
    }
}

/** Per-provider cookies (PowerPAC session); never shared with other hosts' providers. */
internal class MemoryCookieJar : CookieJar {
    private val store = HashMap<String, MutableMap<String, Cookie>>()

    @Synchronized
    override fun saveFromResponse(url: HttpUrl, cookies: List<Cookie>) {
        val m = store.getOrPut(url.host) { HashMap() }
        cookies.forEach { m[it.name] = it }
    }

    @Synchronized
    override fun loadForRequest(url: HttpUrl): List<Cookie> {
        val now = System.currentTimeMillis()
        return store[url.host]?.values?.filter { it.expiresAt > now && it.matches(url) }.orEmpty()
    }
}
