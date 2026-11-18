package com.mardev.nearshelf.core.provider.hoopla

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.provider.ProviderException.Kind
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonObject
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.net.URI

/**
 * Hoopla. Anonymous search covers Hoopla's whole catalog, not one library's, so a
 * search is made once per query and shared by every Hoopla library the user has
 * (cached for [cacheMillis], concurrent callers wait for the same request).
 * Whether a library lends a title, and whether it's Instant or Flex, is only known
 * after login: holdings carry `availabilityKnown = false`.
 */
class HooplaProvider(
    private val client: OkHttpClient,
    private val baseUrl: String = "https://patron-api-gateway.hoopladigital.com",
    private val cacheMillis: Long = 10 * 60 * 1000,
    private val now: () -> Long = System::currentTimeMillis,
) : CatalogProvider {

    override val id = ProviderId.HOOPLA

    private val lock = Mutex()
    private val cache = HashMap<String, Pair<Long, CompletableDeferred<List<Holding>>>>()

    override suspend fun findLibraries(query: String): List<LibraryRef> {
        val q = query.trim()
        if (q.length < 2) return emptyList()
        val url = "$baseUrl/core/libraries/autocomplete".toHttpUrl().newBuilder().addQueryParameter("query", q).build()
        val body = execute(Request.Builder().url(url).get())
        return parse { HooplaParser.parseLibraries(body) }
    }

    override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> {
        require(library.provider == ProviderId.HOOPLA) { "Not a Hoopla library: $library" }
        // Free-text search; an ISBN alone matches digits in unrelated titles, so prefer words.
        val text = if (!query.title.isNullOrBlank()) query.searchText() else query.isbn ?: query.searchText()
        val key = text.lowercase().trim()

        val (owner, deferred) = lock.withLock {
            val hit = cache[key]?.takeIf { now() - it.first < cacheMillis && !it.second.isCancelled }
            if (hit != null) false to hit.second
            else true to CompletableDeferred<List<Holding>>().also { cache[key] = now() to it }
        }
        if (owner) {
            try {
                deferred.complete(fetch(text))
            } catch (e: Throwable) {
                lock.withLock { cache.remove(key) }
                deferred.completeExceptionally(e)
            }
        }
        return deferred.await()
    }

    override fun borrowLink(library: LibraryRef, holding: Holding): URI = titleUri(holding.providerItemId)

    private suspend fun fetch(text: String): List<Holding> {
        val payload = buildJsonObject {
            put("query", SEARCH_QUERY)
            putJsonObject("variables") {
                putJsonObject("criteria") {
                    put("q", text.take(100)) // the web app caps queries at 100 characters
                    putJsonObject("pagination") { put("page", 1); put("pageSize", 24) }
                }
            }
        }.toString()
        val body = execute(
            Request.Builder().url("$baseUrl/graphql").post(payload.toRequestBody("application/json".toMediaType())),
        )
        return parse { HooplaParser.parseSearch(body) }
    }

    private suspend fun execute(builder: Request.Builder): String = withContext(Dispatchers.IO) {
        val request = builder.header("app", "WWW").header("ws-api", "2.1").header("Accept", "application/json").build()
        try {
            client.newCall(request).execute().use { r ->
                if (!r.isSuccessful) {
                    throw ProviderException(
                        id,
                        when (r.code) {
                            404 -> Kind.NOT_FOUND
                            403, 429 -> Kind.RATE_LIMITED
                            else -> Kind.HTTP
                        },
                        "HTTP ${r.code}",
                    )
                }
                r.body.string()
            }
        } catch (e: CancellationException) {
            throw e
        } catch (e: IOException) {
            throw ProviderException(id, Kind.NETWORK, e.message ?: "Network error", e)
        }
    }

    private inline fun <T> parse(block: () -> T): T = try {
        block()
    } catch (e: SerializationException) {
        throw ProviderException(id, Kind.PARSE, e.message ?: "Unexpected response", e)
    } catch (e: IllegalArgumentException) {
        throw ProviderException(id, Kind.PARSE, e.message ?: "Unexpected response", e)
    }

    companion object {
        internal const val SEARCH_QUERY =
            "query NearshelfSearch(\$criteria: SearchCriteria!) { search(criteria: \$criteria) { found hits " +
                "{ id title subtitle isbn language { name } kind { name } authors { name } artKey } } }"

        /** hoopladigital.com's assetlinks.json hands every URL to com.hoopladigital.android. */
        fun titleUri(titleId: String): URI {
            require(titleId.matches(Regex("\\d+"))) { "Bad Hoopla title id: $titleId" }
            return URI("https://www.hoopladigital.com/title/$titleId")
        }
    }
}
