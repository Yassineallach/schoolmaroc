package com.mardev.nearshelf.core.net

import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.provider.ProviderException.Kind
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.HttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException

/** GET helper for catalog providers: maps HTTP failures and bot walls to [ProviderException]. */
class ProviderHttp(private val client: OkHttpClient, private val provider: ProviderId) {

    class Response(val code: Int, val body: String, val contentType: String?)

    /** Returns the body of a 2xx answer; throws otherwise. 404 → NOT_FOUND unless [allow404]. */
    suspend fun get(url: HttpUrl, accept: String = "*/*"): String = fetch(url, accept).body

    suspend fun fetch(url: HttpUrl, accept: String = "*/*", allowCodes: Set<Int> = emptySet()): Response =
        withContext(Dispatchers.IO) {
            val req = Request.Builder().url(url).header("Accept", accept).build()
            val r = try {
                client.newCall(req).execute().use { Response(it.code, it.body.string(), it.header("Content-Type")) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: IOException) {
                throw ProviderException(provider, Kind.NETWORK, e.message ?: "Network error", e)
            }
            if (BotWall.isWall(r.code, r.body)) throw ProviderException(provider, Kind.BLOCKED, "Bot check at ${url.host}")
            if (r.code in 200..299 || r.code in allowCodes) return@withContext r
            throw ProviderException(
                provider,
                when (r.code) {
                    404 -> Kind.NOT_FOUND
                    403, 429 -> Kind.RATE_LIMITED
                    else -> Kind.HTTP
                },
                "HTTP ${r.code} from ${url.host}",
            )
        }
}
