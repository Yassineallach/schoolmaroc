package com.mardev.nearshelf.core.registry

import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.share.PageFetcher
import java.net.URI

data class Detection(
    val provider: ProviderId,
    /** Catalog root to build search URLs from, e.g. "https://catalog.hcplc.org/polaris". */
    val baseUrl: String,
    /** The page's own name for the library, when it has one. */
    val pageTitle: String? = null,
)

/**
 * Recognises a library catalog's software from its address and, when that isn't
 * enough, its HTML. URL rules come first because pages mention other products:
 * Chicago's BiblioCommons page says "polaris", Brentwood's Polaris page says "Vega".
 * Every rule was checked against live catalogs on 2026-11-18 (fixtures/detect).
 */
object CatalogDetector {

    fun fromUrl(url: String): Detection? {
        val uri = parse(url) ?: return null
        val host = uri.host.lowercase()
        val path = uri.rawPath.orEmpty()
        val origin = "https://$host"
        return when {
            host.endsWith(".bibliocommons.com") -> Detection(ProviderId.BIBLIOCOMMONS, origin)
            host.endsWith(".iiivega.com") -> Detection(ProviderId.SIERRA_VEGA, origin)
            "/cgi-bin/koha/" in path -> Detection(ProviderId.KOHA, origin)
            path.startsWith("/eg/opac") || path.startsWith("/eg2/") -> Detection(ProviderId.EVERGREEN, origin)
            "/iii/encore" in path -> Detection(ProviderId.SIERRA_ENCORE, origin)
            Regex("^/search~S\\d*").containsMatchIn(path) -> Detection(ProviderId.SIERRA_ENCORE, origin)
            path.startsWith("/polaris/", ignoreCase = true) || path.equals("/polaris", true) ->
                Detection(ProviderId.POLARIS, "$origin/polaris")
            host.endsWith(".polarislibrary.com") -> Detection(ProviderId.POLARIS, origin)
            else -> null
        }
    }

    /**
     * [finalUrl] is where redirects ended (OWWL's /eg/opac/ address now lands on Aspen,
     * so the redirect target decides). HTML markers settle what the URL can't.
     */
    fun fromPage(finalUrl: String, html: String): Detection? {
        val title = Regex("<title[^>]*>(.*?)</title>", setOf(RegexOption.DOT_MATCHES_ALL, RegexOption.IGNORE_CASE))
            .find(html)?.groupValues?.get(1)?.let(::cleanTitle)
        val origin = parse(finalUrl)?.let { "https://${it.host.lowercase()}" } ?: return null
        // Aspen pages can sit on Evergreen/Koha-looking paths, so check its marker first.
        if ("Aspen Discovery" in html) return Detection(ProviderId.ASPEN, origin, title)
        fromUrl(finalUrl)?.let { return it.copy(pageTitle = title) }
        return when {
            Regex("<meta name=\"generator\" content=\"Koha", RegexOption.IGNORE_CASE).containsMatchIn(html) ||
                "/cgi-bin/koha/opac-search.pl" in html -> Detection(ProviderId.KOHA, origin, title)
            "Vega Discover" in html -> Detection(ProviderId.SIERRA_VEGA, origin, title)
            // PowerPAC pages load assets from /polaris/ and declare a POLARIS.PAC OpenSearch feed.
            "POLARIS.PAC" in html || Regex("(src|href)=\"[^\"]*/polaris/", RegexOption.IGNORE_CASE).containsMatchIn(html) ->
                Detection(ProviderId.POLARIS, if ("$origin/polaris/" in html || "\"/polaris/" in html) "$origin/polaris" else origin, title)
            Regex("(src|href)=\"(https?://[^\"/]+)?/(eg/opac/|eg2/)").containsMatchIn(html) -> Detection(ProviderId.EVERGREEN, origin, title)
            // Classic Sierra catalog footer: "WebPAC PRO © 2025 Clarivate".
            "WebPAC PRO" in html -> Detection(ProviderId.SIERRA_ENCORE, origin, title)
            else -> null
        }
    }

    /** Fetches [input] (a URL or bare host) and detects its catalog; null when unrecognised or unreachable. */
    suspend fun detect(input: String, fetcher: PageFetcher): Detection? {
        val url = normalizeInput(input) ?: return null
        val page = fetcher.fetch(url) ?: return fromUrl(url)
        return fromPage(page.finalUrl, page.html) ?: fromUrl(url)
    }

    /** "catalog.example.org" → "https://catalog.example.org"; null when it can't be a web address. */
    fun normalizeInput(input: String): String? {
        val t = input.trim()
        if (t.isEmpty() || ' ' in t || '.' !in t) return null
        val withScheme = if (Regex("^https?://", RegexOption.IGNORE_CASE).containsMatchIn(t)) t else "https://$t"
        return parse(withScheme)?.let { withScheme }
    }

    fun looksLikeUrl(input: String): Boolean = normalizeInput(input) != null &&
        Regex("^(https?://)?[\\w-]+(\\.[\\w-]+)+(/\\S*)?$", RegexOption.IGNORE_CASE).matches(input.trim())

    private fun parse(url: String): URI? = runCatching { URI(url) }.getOrNull()?.takeIf { !it.host.isNullOrBlank() }

    /** "Recent Activity | The Seattle Public Library | BiblioCommons" → "The Seattle Public Library" */
    private fun cleanTitle(raw: String): String? {
        val parts = raw.replace(Regex("\\s+"), " ").trim().split(" | ", " - ", " – ").map { it.trim() }
        val generic = Regex("(?i)^(recent activity|home|catalog home|catalog|search|bibliocommons|vega discover|evergreen|polaris|powerpac|koha( online catalog)?|welcome.*)$")
        return parts.filterNot { it.isEmpty() || generic.matches(it) }.maxByOrNull { if ("librar" in it.lowercase()) 1000 + it.length else it.length }
    }
}
