package com.mardev.nearshelf.core.provider.overdrive

import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.provider.ProviderException.Kind
import kotlinx.coroutines.CancellationException
import kotlinx.serialization.SerializationException
import okhttp3.OkHttpClient
import okhttp3.ResponseBody
import retrofit2.Response
import retrofit2.Retrofit
import java.io.IOException
import java.net.URI
import java.net.URLEncoder

/**
 * OverDrive / Libby. Library lookup via locate.libbyapp.com; availability via
 * thunder.api.overdrive.com. Borrowing happens in Libby through an App Link.
 */
class OverDriveProvider(
    client: OkHttpClient,
    thunderBaseUrl: String = THUNDER_BASE,
    private val locateBaseUrl: String = LOCATE_BASE,
) : CatalogProvider {

    override val id = ProviderId.OVERDRIVE

    private val api: OverDriveApi = Retrofit.Builder()
        .baseUrl(thunderBaseUrl)
        .client(client)
        .build()
        .create(OverDriveApi::class.java)

    override suspend fun findLibraries(query: String): List<LibraryRef> {
        val q = query.trim()
        if (q.length < 2) return emptyList()
        // locate takes the query as a path segment; encode spaces as %20, not '+'.
        val segment = URLEncoder.encode(q, Charsets.UTF_8).replace("+", "%20")
        val body = call { api.locate("$locateBaseUrl/autocomplete/$segment") }
        return parse { OverDriveParser.parseLibraries(body) }
    }

    override suspend fun search(library: LibraryRef, query: BookQuery): List<Holding> {
        require(library.provider == ProviderId.OVERDRIVE) { "Not an OverDrive library: $library" }
        // An ISBN query is exact and cheap; fall back to text when we have none.
        val text = query.isbn ?: query.searchText()
        val body = call { api.media(library.key, text) }
        return parse { OverDriveParser.parseMedia(body) }
    }

    override fun borrowLink(library: LibraryRef, holding: Holding): URI =
        libbyTitleUri(library.key, holding.providerItemId)

    private suspend fun call(block: suspend () -> Response<ResponseBody>): String {
        val response = try {
            block()
        } catch (e: CancellationException) {
            throw e
        } catch (e: IOException) {
            throw ProviderException(id, Kind.NETWORK, e.message ?: "Network error", e)
        }
        response.use {
            if (!it.isSuccessful) {
                val kind = when (it.code()) {
                    404 -> Kind.NOT_FOUND
                    403, 429 -> Kind.RATE_LIMITED
                    else -> Kind.HTTP
                }
                throw ProviderException(id, kind, "HTTP ${it.code()}")
            }
            return it.body()?.string() ?: throw ProviderException(id, Kind.PARSE, "Empty body")
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
        const val THUNDER_BASE = "https://thunder.api.overdrive.com/"
        const val LOCATE_BASE = "https://locate.libbyapp.com"

        /**
         * Libby's router rewrites `library/{key}/title/{id}` to the title detail
         * page (title-redirect-controller in libbyapp.com/dewey-22.2.1/src/main.js).
         * libbyapp.com's assetlinks.json delegates to com.overdrive.mobile.android.libby,
         * so ACTION_VIEW opens the app when installed and the web app otherwise.
         */
        fun libbyTitleUri(libraryKey: String, titleId: String): URI {
            require(libraryKey.matches(Regex("[A-Za-z0-9_-]+"))) { "Bad library key: $libraryKey" }
            require(titleId.matches(Regex("\\d+"))) { "Bad title id: $titleId" }
            return URI("https://libbyapp.com/library/$libraryKey/title/$titleId")
        }
    }
}

private inline fun <T> Response<ResponseBody>.use(block: (Response<ResponseBody>) -> T): T =
    try { block(this) } finally { errorBody()?.close() }
