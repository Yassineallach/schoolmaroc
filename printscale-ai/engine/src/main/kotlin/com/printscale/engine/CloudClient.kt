package com.printscale.engine

import java.io.File
import java.io.IOException
import java.net.ConnectException
import java.net.HttpURLConnection
import java.net.SocketTimeoutException
import java.net.URI
import java.net.URL
import java.net.URLDecoder
import java.net.UnknownHostException

/** A server link as printed by the notebook: https://name.trycloudflare.com/?key=SECRET */
data class CloudLink(val baseUrl: String, val key: String) {
    fun asText() = "$baseUrl/?key=$key"

    companion object {
        private val LOCAL_HOSTS = setOf("localhost", "127.0.0.1", "10.0.2.2")

        /** Accepts the full link, with or without a trailing slash or extra path. Null if it is not usable. */
        fun parse(text: String): CloudLink? {
            val raw = text.trim().trim('"', '\'', '<', '>')
            if (raw.startsWith("printscale://")) {
                // deep link from the notebook's QR page: printscale://connect?server=...&key=...
                val q = query(raw.substringAfter('?', ""))
                return q["server"]?.let { s -> q["key"]?.let { k -> parse("$s/?key=$k") } }
            }
            val uri = runCatching { URI(raw) }.getOrNull() ?: return null
            val host = uri.host ?: return null
            val https = uri.scheme.equals("https", true)
            val localHttp = uri.scheme.equals("http", true) && host in LOCAL_HOSTS // testing only
            if (!https && !localHttp) return null
            val key = query(uri.rawQuery ?: "")["key"]?.takeIf { it.length >= 8 } ?: return null
            val port = if (uri.port > 0) ":${uri.port}" else ""
            return CloudLink("${uri.scheme.lowercase()}://$host$port", key)
        }

        private fun query(q: String): Map<String, String> = q.split('&').filter { '=' in it }.associate {
            URLDecoder.decode(it.substringBefore('='), "UTF-8") to URLDecoder.decode(it.substringAfter('='), "UTF-8")
        }
    }
}

data class ServerInfo(val model: String, val device: String, val gpu: String, val maxPixels: Long)

data class CloudJob(val state: String, val done: Long, val total: Long, val error: String?) {
    val finished get() = state == "done"
    val failed get() = state == "failed" || state == "cancelled"
}

class CloudException(message: String, val retryable: Boolean = false) : IOException(message)

/**
 * Talks to the PrintScale AuraSR server running in a Colab or Kaggle notebook. The server only
 * does the AI 4× step; framing, resizing to print size and writing the file stay in the app.
 * Jobs are asynchronous because tunnels drop requests that wait too long for a reply.
 */
class CloudClient(private val link: CloudLink, private val connectTimeoutMs: Int = 15_000, private val readTimeoutMs: Int = 90_000) {

    fun health(): ServerInfo {
        val j = request("GET", "/health").use { it.body() }
        if (!j.contains("\"printscale\"")) throw CloudException("This link is not a PrintScale server.")
        return ServerInfo(
            model = Json.str(j, "model") ?: "AuraSR",
            device = Json.str(j, "device") ?: "?",
            gpu = Json.str(j, "gpu") ?: "",
            maxPixels = Json.long(j, "max_pixels") ?: Long.MAX_VALUE,
        )
    }

    /** Uploads a PNG of the prepared artwork and returns the job id. */
    fun submit(png: File, onProgress: (Long, Long) -> Unit, isCancelled: () -> Boolean): String {
        val c = open("POST", "/jobs")
        c.doOutput = true
        c.setRequestProperty("Content-Type", "image/png")
        c.setFixedLengthStreamingMode(png.length())
        try {
            c.outputStream.use { out ->
                png.inputStream().use { inp ->
                    val buf = ByteArray(1 shl 16)
                    var sent = 0L
                    while (true) {
                        if (isCancelled()) throw UpscaleCancelled()
                        val n = inp.read(buf)
                        if (n < 0) break
                        out.write(buf, 0, n)
                        sent += n
                        onProgress(sent, png.length())
                    }
                }
            }
        } catch (e: IOException) {
            throw wrap(e)
        }
        val body = Response(c).body()
        return Json.str(body, "id") ?: throw CloudException("The server did not return a job id.")
    }

    fun status(id: String): CloudJob {
        val j = request("GET", "/jobs/$id").use { it.body() }
        return CloudJob(Json.str(j, "state") ?: "unknown", Json.long(j, "done") ?: 0, Json.long(j, "total") ?: 0, Json.str(j, "error"))
    }

    fun download(id: String, dst: File, onProgress: (Long, Long) -> Unit, isCancelled: () -> Boolean) {
        val r = request("GET", "/jobs/$id/result")
        r.use {
            val total = it.conn.contentLengthLong
            try {
                it.conn.inputStream.use { inp ->
                    dst.outputStream().buffered(1 shl 20).use { out ->
                        val buf = ByteArray(1 shl 16)
                        var got = 0L
                        while (true) {
                            if (isCancelled()) throw UpscaleCancelled()
                            val n = inp.read(buf)
                            if (n < 0) break
                            out.write(buf, 0, n)
                            got += n
                            onProgress(got, total)
                        }
                        if (total > 0 && got != total) throw CloudException("The download was cut off. Try again.", retryable = true)
                    }
                }
            } catch (e: IOException) {
                throw wrap(e)
            }
        }
    }

    /** Best effort: frees the GPU and deletes files on the server. */
    fun cancel(id: String) {
        runCatching { request("DELETE", "/jobs/$id").use { it.body() } }
    }

    private fun open(method: String, path: String): HttpURLConnection {
        val c = URL(link.baseUrl + path).openConnection() as HttpURLConnection
        c.requestMethod = method
        c.connectTimeout = connectTimeoutMs
        c.readTimeout = readTimeoutMs
        c.setRequestProperty("X-PrintScale-Key", link.key)
        c.setRequestProperty("User-Agent", "PrintScale-Android")
        return c
    }

    private fun request(method: String, path: String): Response {
        val c = open(method, path)
        try {
            c.connect()
        } catch (e: IOException) {
            throw wrap(e)
        }
        return Response(c)
    }

    private inner class Response(val conn: HttpURLConnection) : AutoCloseable {
        init {
            val code = try { conn.responseCode } catch (e: IOException) { throw wrap(e) }
            if (code !in 200..299) {
                val msg = runCatching { conn.errorStream?.bufferedReader()?.readText() }.getOrNull()
                val detail = msg?.let { Json.str(it, "error") }
                conn.disconnect()
                throw when (code) {
                    401, 403 -> CloudException("The server rejected the key. Copy the whole link from the notebook again.")
                    404 -> CloudException(detail ?: "Not found on the server. The notebook may have restarted; start the job again.")
                    413 -> CloudException(detail ?: "The image is too large for the server.")
                    502, 503, 504, 530 -> CloudException("The server is not responding. Check that the notebook is still running.", retryable = true)
                    else -> CloudException(detail ?: "Server error ($code).", retryable = code >= 500)
                }
            }
        }

        fun body(): String = conn.inputStream.bufferedReader().use { it.readText() }
        override fun close() = conn.disconnect()
    }

    private fun wrap(e: IOException): IOException = when (e) {
        is CloudException -> e
        is UnknownHostException -> CloudException("Server address not found. The notebook link changes each time it starts; paste the new one.")
        is ConnectException -> CloudException("Can't reach the server. Check that the notebook is still running.", retryable = true)
        is SocketTimeoutException -> CloudException("The server took too long to answer.", retryable = true)
        else -> CloudException("Connection problem: ${e.message ?: e.javaClass.simpleName}", retryable = true)
    }
}

/** Just enough JSON for the server's flat replies. */
internal object Json {
    fun str(json: String, key: String): String? =
        Regex("\"" + Regex.escape(key) + "\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"").find(json)?.groupValues?.get(1)
            ?.replace("\\\"", "\"")?.replace("\\n", "\n")?.replace("\\\\", "\\")

    fun long(json: String, key: String): Long? =
        Regex("\"" + Regex.escape(key) + "\"\\s*:\\s*(-?\\d+)").find(json)?.groupValues?.get(1)?.toLongOrNull()
}
