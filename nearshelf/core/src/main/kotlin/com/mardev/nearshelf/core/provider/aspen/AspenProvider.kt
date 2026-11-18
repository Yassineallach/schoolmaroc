package com.mardev.nearshelf.core.provider.aspen

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.ProviderException
import java.net.URI
import java.net.URLEncoder

/**
 * Aspen Discovery, link only. Checked 2026-11-18: the API accepts only approved IP
 * addresses ("API requests from … are forbidden"), 4 of 5 catalogs answer automated
 * requests with a Cloudflare challenge, and the fifth (OWWL) puts its search behind a
 * JavaScript challenge. Nearshelf makes no requests and offers the catalog's own
 * search page instead.
 */
class AspenProvider : CatalogProvider {
    override val id = ProviderId.ASPEN

    override suspend fun findLibraries(query: String): List<LibraryRef> = emptyList()

    override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> =
        throw ProviderException(id, ProviderException.Kind.BLOCKED, "Aspen catalogs only answer searches made in a browser")

    override fun borrowLink(library: LibraryRef, holding: Holding): URI = searchLink(library, BookQuery(title = holding.title))

    override fun searchLink(library: LibraryRef, query: BookQuery): URI {
        val host = URI(library.key).host
        require(!host.isNullOrBlank()) { "Bad Aspen catalog ${library.key}" }
        return URI("https://$host/Search/Results?lookfor=${URLEncoder.encode(query.searchText(), Charsets.UTF_8)}&searchIndex=Keyword")
    }
}
