package com.mardev.nearshelf.core.share

import com.mardev.nearshelf.core.match.Isbn
import com.mardev.nearshelf.core.metadata.LanguageCodes
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.search.QueryParser
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonPrimitive
import org.jsoup.Jsoup
import java.net.URI

/**
 * Turns text shared from Goodreads, Amazon, StoryGraph or a browser into a [BookQuery].
 *
 * 1. An ISBN anywhere in the text, or an ISBN-10 used as an Amazon ASIN in the URL.
 * 2. The linked page: JSON-LD `Book` (Goodreads), Amazon's "Title: Author: ISBN: Amazon…"
 *    page title, or `og:title`. StoryGraph pages sit behind a bot check, so they are
 *    not fetched; their share text is used instead.
 * 3. Otherwise the shared text itself, minus URLs and boilerplate, read as "title by author".
 */
class ShareParser(private val fetcher: PageFetcher) {

    suspend fun parse(shared: String): BookQuery? {
        val text = shared.trim()
        if (text.isEmpty()) return null
        val urls = urlRegex.findAll(text).map { it.value.trimEnd('.', ',', ')', ']', '"', '\'') }.toList()
        val fromText = textQuery(text)

        isbnIn(text.replace(urlRegex, " "))?.let { return BookQuery(isbn = it, title = fromText?.title, author = fromText?.author) }
        urls.firstNotNullOfOrNull(::isbnFromUrl)?.let { return BookQuery(isbn = it) }

        for (url in urls) {
            if (!shouldFetch(url)) continue
            val page = fetcher.fetch(url) ?: continue
            isbnFromUrl(page.finalUrl)?.let { return BookQuery(isbn = it) }
            parsePage(page)?.let { return it }
        }
        return fromText ?: urls.firstNotNullOfOrNull(::titleFromSlug)
    }

    internal fun parsePage(page: FetchedPage): BookQuery? {
        val doc = Jsoup.parse(page.html, page.finalUrl)
        jsonLdBook(doc.select("script[type=application/ld+json]").map { it.data() })?.let { return it }
        val host = hostOf(page.finalUrl)
        if (host != null && "amazon." in host) amazonTitle(doc.title())?.let { return it }
        val og = doc.selectFirst("meta[property=og:title]")?.attr("content")?.trim()
        return og?.takeIf { it.isNotEmpty() }?.let { QueryParser.parse(it) }
    }

    internal fun jsonLdBook(scripts: List<String>): BookQuery? {
        for (s in scripts) {
            val root = runCatching { json.parseToJsonElement(s) }.getOrNull() ?: continue
            val book = flatten(root).firstOrNull { typeOf(it).any { t -> t.equals("Book", true) } } ?: continue
            val name = book.str("name")?.trim()
            val isbn = book.str("isbn")?.let(Isbn::normalize)?.takeIf(Isbn::isValid)
            val author = when (val a = book["author"]) {
                is JsonArray -> a.firstOrNull()?.let { (it as? JsonObject)?.str("name") ?: (it as? JsonPrimitive)?.contentOrNull }
                is JsonObject -> a.str("name")
                is JsonPrimitive -> a.contentOrNull
                else -> null
            }?.trim()
            val lang = LanguageCodes.toIso1(book.str("inLanguage"))
            if (name.isNullOrEmpty() && isbn == null) continue
            return BookQuery(title = name?.ifEmpty { null }, author = author?.ifEmpty { null }, isbn = isbn, language = lang)
        }
        return null
    }

    /** "Project Hail Mary: A Novel: Weir, Andy: 9780593135204: Amazon.com: Books" */
    internal fun amazonTitle(title: String): BookQuery? {
        val parts = title.split(": ", " : ").map { it.trim() }.filter { it.isNotEmpty() }
        val cut = parts.indexOfFirst { it.startsWith("Amazon.", ignoreCase = true) }
        if (cut <= 0) return null
        val head = parts.take(cut).toMutableList()
        val isbn = head.firstOrNull { Isbn.isValid(it) }?.let(Isbn::normalize)
        head.removeAll { Isbn.isValid(it) || it.matches(Regex("[A-Z0-9]{10}")) }
        val authorIdx = head.indexOfLast { Regex("^[^,]+, [^,]+$").matches(it) && head.indexOf(it) > 0 }
        val author = head.getOrNull(authorIdx)?.let { val (last, first) = it.split(", ", limit = 2); "$first $last" }
        if (authorIdx >= 0) head.removeAt(authorIdx)
        val bookTitle = head.joinToString(": ")
            .replace(Regex("\\s+(eBook|Kindle Edition|Audible Audiobook)\\s*$", RegexOption.IGNORE_CASE), "")
            .trim()
        if (bookTitle.isEmpty() && isbn == null) return null
        return BookQuery(title = bookTitle.ifEmpty { null }, author = author, isbn = isbn)
    }

    internal fun textQuery(text: String): BookQuery? {
        var t = text.replace(urlRegex, " ")
        boilerplate.forEach { t = t.replace(it, " ") }
        t = t.replace(Regex("\\s+"), " ").trim().trim('"', '“', '”', '-', '–', '—', ':', '|', ' ')
        if (t.length < 2) return null
        return QueryParser.parse(t)
    }

    /** 13-digit Bookland ISBNs anywhere; 10-digit ones only after "ISBN" (a random 10-digit number passes the checksum 1 time in 11). */
    private fun isbnIn(text: String): String? =
        isbnRegex.findAll(text).firstNotNullOfOrNull { m ->
            val v = m.value.replace(Regex("[\\s-]"), "")
            val labelled = text.substring(0, m.range.first).trimEnd(' ', ':', '-').endsWith("ISBN", ignoreCase = true) ||
                text.substring(0, m.range.first).trimEnd(' ', ':', '-').endsWith("ISBN-10", ignoreCase = true)
            v.takeIf {
                Isbn.isValid(it) && ((it.length == 13 && (it.startsWith("978") || it.startsWith("979"))) || (it.length == 10 && labelled))
            }
        }?.let(Isbn::normalize)

    internal fun isbnFromUrl(url: String): String? {
        val host = hostOf(url) ?: return null
        val path = runCatching { URI(url).rawPath }.getOrNull().orEmpty()
        if ("amazon." in host) {
            val asin = asinRegex.find(path)?.groupValues?.get(1) ?: return null
            return asin.takeIf { Isbn.isValid(it) }?.let(Isbn::normalize)
        }
        Regex("/isbn/(\\d{9}[\\dXx]|\\d{13})").find(path)?.groupValues?.get(1)?.takeIf(Isbn::isValid)?.let { return Isbn.normalize(it) }
        return null
    }

    /** Goodreads slugs ("/book/show/54493401-project-hail-mary") give a title if all else fails. */
    private fun titleFromSlug(url: String): BookQuery? {
        if (hostOf(url)?.endsWith("goodreads.com") != true) return null
        val slug = Regex("/book/show/\\d+[-.]([\\w-]+)").find(url)?.groupValues?.get(1) ?: return null
        return BookQuery(title = slug.replace('-', ' ').replace('_', ' '))
    }

    private fun shouldFetch(url: String): Boolean {
        val host = hostOf(url) ?: return false
        return !host.endsWith("thestorygraph.com")
    }

    private fun hostOf(url: String): String? = runCatching { URI(url).host?.lowercase() }.getOrNull()

    private fun flatten(e: JsonElement): List<JsonObject> = when (e) {
        is JsonArray -> e.flatMap(::flatten)
        is JsonObject -> listOf(e) + (e["@graph"]?.let(::flatten) ?: emptyList())
        else -> emptyList()
    }

    private fun typeOf(o: JsonObject): List<String> = when (val t = o["@type"]) {
        is JsonPrimitive -> listOfNotNull(t.contentOrNull)
        is JsonArray -> t.mapNotNull { (it as? JsonPrimitive)?.contentOrNull }
        else -> emptyList()
    }

    private fun JsonObject.str(key: String): String? = (this[key] as? JsonPrimitive)?.contentOrNull
        ?: (this[key] as? JsonArray)?.firstOrNull()?.let { runCatching { it.jsonPrimitive.contentOrNull }.getOrNull() }

    private companion object {
        val json = Json { ignoreUnknownKeys = true; isLenient = true }
        val urlRegex = Regex("https?://\\S+")
        val isbnRegex = Regex("(?<![\\d])(?:97[89][\\s-]?)?\\d{1,5}[\\s-]?\\d{1,7}[\\s-]?\\d{1,7}[\\s-]?[\\dXx](?![\\d])")
        val asinRegex = Regex("/(?:dp|gp/product|gp/aw/d|exec/obidos/ASIN)/([A-Z0-9]{10})", RegexOption.IGNORE_CASE)
        val boilerplate = listOf(
            Regex("(?i)\\bcheck out\\b"),
            Regex("(?i)\\bon goodreads\\b[:!.]?"),
            Regex("(?i)\\bon the ?storygraph\\b[:!.]?"),
            Regex("(?i)\\bon amazon(\\.[a-z.]+)?\\b[:!.]?"),
            Regex("(?i)\\bi(?:'|’)m (?:currently )?reading\\b"),
            Regex("(?i)\\bi (?:just )?(?:finished|read|want to read)\\b"),
            Regex("(?i)\\bcheck out this (?:book|product)\\b[:!.]?"),
            Regex("(?i)\\bshared (?:from|via) [\\w ]+$"),
        )
    }
}
