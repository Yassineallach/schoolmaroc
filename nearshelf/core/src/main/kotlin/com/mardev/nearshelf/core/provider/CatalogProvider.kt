package com.mardev.nearshelf.core.provider

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import java.net.URI

/**
 * One catalog source. Implementations do their own HTTP and parsing and never
 * touch UI code. They throw [ProviderException] on failure; callers decide how
 * to surface it.
 *
 * [borrowLink] returns a java.net.URI (not android.net.Uri) so the module stays
 * pure JVM and deep-link building is unit-testable; the app converts it.
 */
interface CatalogProvider {
    val id: ProviderId
    suspend fun findLibraries(query: String): List<LibraryRef>
    suspend fun search(library: LibraryRef, query: BookQuery): List<Holding>
    fun borrowLink(library: LibraryRef, holding: Holding): URI

    /** The catalog's own search page for [query], for when automated search is blocked. */
    fun searchLink(library: LibraryRef, query: BookQuery): URI? = null
}

class ProviderException(
    val provider: ProviderId,
    val kind: Kind,
    message: String,
    cause: Throwable? = null,
) : Exception(message, cause) {
    enum class Kind {
        NETWORK, HTTP, RATE_LIMITED, NOT_FOUND, PARSE,

        /** The site answers automated requests with a bot check (Cloudflare 429/403, JS challenge). */
        BLOCKED,
    }
}
