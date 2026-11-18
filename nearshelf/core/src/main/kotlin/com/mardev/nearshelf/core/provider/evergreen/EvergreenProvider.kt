package com.mardev.nearshelf.core.provider.evergreen

import com.mardev.nearshelf.core.match.Isbn
import com.mardev.nearshelf.core.match.MarcNames
import com.mardev.nearshelf.core.match.TextNormalizer
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.CopyStatus
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.PhysicalCopy
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.net.ProviderHttp
import com.mardev.nearshelf.core.provider.CatalogProvider
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import org.jsoup.Jsoup
import org.jsoup.nodes.Element
import org.jsoup.parser.Parser
import java.net.URI
import java.net.URLEncoder

/**
 * Parses Evergreen's OpenSearch "atom-full" feed: each entry carries its holdings
 * (volume = call number, copy = status + circulating library). Recorded from Georgia
 * PINES and C/W MARS, 2026-11-18.
 */
object EvergreenParser {
    fun parse(body: String): List<Holding> {
        val doc = Jsoup.parse(body, "", Parser.xmlParser())
        return doc.getElementsByTag("atom:entry").ifEmpty { doc.getElementsByTag("entry") }.mapNotNull(::entry)
    }

    private fun entry(e: Element): Holding? {
        val id = Regex("urn:tcn:(\\d+)").find(e.getElementsByTag("id").firstOrNull()?.text().orEmpty())?.groupValues?.get(1)
            ?: return null
        val rawTitle = e.getElementsByTag("title").firstOrNull()?.text().orEmpty()
        // MARC "general material designations" mark non-print records: "The hobbit [sound recording] /".
        if (nonPrint.containsMatchIn(rawTitle)) return null
        val title = cleanTitle(rawTitle).takeIf { it.isNotEmpty() } ?: return null
        val authors = e.getElementsByTag("author").mapNotNull { it.getElementsByTag("name").firstOrNull()?.text()?.let(MarcNames::display) }
            .filter { it.isNotEmpty() }.distinct()
        val isbns = e.getElementsByTag("dc:identifier").map { it.text() }
            .mapNotNull { Regex("URN:ISBN:([0-9Xx-]{10,17})").find(it)?.groupValues?.get(1)?.replace("-", "") }
            .filter(Isbn::isValid).map(Isbn::normalize).toSet()
        val copies = e.getElementsByTag("volume").flatMap { vol ->
            val call = vol.attr("label").takeIf { it.isNotBlank() }
            vol.getElementsByTag("copy").filter { it.attr("opac_visible") != "f" && it.attr("deleted") != "t" }.map { c ->
                val circ = c.getElementsByTag("circ_lib").firstOrNull()
                PhysicalCopy(
                    branchName = circ?.attr("name")?.takeIf { it.isNotBlank() } ?: c.getElementsByTag("circlib").text(),
                    branchId = circ?.attr("shortname"),
                    callNumber = call,
                    status = status(c.getElementsByTag("status").firstOrNull()?.attr("ident")?.toIntOrNull()),
                )
            }
        }
        return Holding(
            provider = ProviderId.EVERGREEN,
            format = Format.PHYSICAL,
            title = title,
            authors = authors,
            isbns = isbns,
            owned = copies.size,
            available = copies.count { it.status == CopyStatus.AVAILABLE },
            isAvailableNow = copies.any { it.status == CopyStatus.AVAILABLE },
            providerItemId = id,
            copies = copies,
        )
    }

    private val nonPrint = Regex("\\[(electronic|sound|video|kit|game|music|motion picture|cartographic|computer)[^\\]]*\\]", RegexOption.IGNORE_CASE)

    /** Evergreen's stock config.copy_status ids. */
    internal fun status(ident: Int?): CopyStatus = when (ident) {
        0, 7 -> CopyStatus.AVAILABLE // Available, Reshelving
        1 -> CopyStatus.CHECKED_OUT
        6, 18 -> CopyStatus.IN_TRANSIT
        8, 15 -> CopyStatus.ON_HOLD_SHELF
        5, 9, 11 -> CopyStatus.IN_PROCESSING // In process, On order, Cataloging
        12 -> CopyStatus.LIBRARY_USE_ONLY // Reserves
        3, 4, 13, 14, 16, 17 -> CopyStatus.MISSING // Lost, Missing, Discard, Damaged, Long overdue, Lost and paid
        else -> CopyStatus.UNKNOWN
    }

    /** "Project Hail Mary : a novel /" → "Project Hail Mary : a novel" */
    internal fun cleanTitle(s: String) = s.trim().replace(Regex("[\\s/:;,.=]+$"), "")

    /** "Weir, Andy,author.https://id.oclc.org/…(GaAaGPL)13264905" → "Andy Weir" */
    internal fun cleanAuthor(s: String): String = MarcNames.display(s)
}

/**
 * Evergreen (consortia such as Georgia PINES, C/W MARS). One request: the OpenSearch
 * feed for the whole consortium ("-" = top org unit) with holdings inline.
 */
class EvergreenProvider(client: OkHttpClient, private val count: Int = 6) : CatalogProvider {
    override val id = ProviderId.EVERGREEN
    private val http = ProviderHttp(client, id)

    override suspend fun findLibraries(query: String): List<LibraryRef> = emptyList()

    override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> {
        // Field qualifiers: plain keywords rank companion books ("The art of the Hobbit") above the book.
        val text = when {
            // Surname only: initials ("J. R. R.") push the print record out of the results.
            !query.title.isNullOrBlank() ->
                "title:${query.title}" + (query.author?.let(TextNormalizer::surname)?.let { " author:$it" } ?: "")
            else -> query.isbn ?: query.searchText()
        }
        val url = "${base(library)}/opac/extras/opensearch/1.1/-/atom-full/keyword/".toHttpUrl().newBuilder()
            .addQueryParameter("searchTerms", text)
            .addQueryParameter("count", count.toString())
            .build()
        return EvergreenParser.parse(http.get(url, "application/atom+xml"))
    }

    override fun borrowLink(library: LibraryRef, holding: Holding): URI {
        require(holding.providerItemId.matches(Regex("\\d+")))
        return URI("${base(library)}/eg/opac/record/${holding.providerItemId}")
    }

    override fun searchLink(library: LibraryRef, query: BookQuery): URI =
        URI("${base(library)}/eg/opac/results?query=${URLEncoder.encode(query.searchText(), Charsets.UTF_8)}&qtype=keyword")

    private fun base(library: LibraryRef): String {
        val u = URI(library.key)
        require(!u.host.isNullOrBlank()) { "Bad Evergreen catalog ${library.key}" }
        return "https://${u.host}"
    }
}
