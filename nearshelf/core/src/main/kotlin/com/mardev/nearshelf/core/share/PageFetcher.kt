package com.mardev.nearshelf.core.share

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.IOException

data class FetchedPage(val finalUrl: String, val html: String)

fun interface PageFetcher {
    /** Follows redirects; returns null on any failure. */
    suspend fun fetch(url: String): FetchedPage?
}

class OkHttpPageFetcher(
    private val client: OkHttpClient,
    private val maxBytes: Long = 2_000_000,
) : PageFetcher {
    override suspend fun fetch(url: String): FetchedPage? = withContext(Dispatchers.IO) {
        try {
            client.newCall(Request.Builder().url(url).header("Accept", "text/html").build()).execute().use { r ->
                if (!r.isSuccessful) return@use null
                val source = r.body.source()
                source.request(maxBytes)
                val bytes = source.buffer.let { buf -> buf.readByteArray(minOf(buf.size, maxBytes)) }
                FetchedPage(r.request.url.toString(), String(bytes, Charsets.UTF_8))
            }
        } catch (e: CancellationException) {
            throw e
        } catch (_: IOException) {
            null
        } catch (_: IllegalArgumentException) {
            null
        }
    }
}
