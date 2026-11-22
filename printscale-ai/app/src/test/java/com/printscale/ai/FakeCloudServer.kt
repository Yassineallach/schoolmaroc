package com.printscale.ai

import com.printscale.engine.PngStreamReader
import com.printscale.engine.PngStreamWriter
import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.DataInputStream
import java.io.OutputStream
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import kotlin.concurrent.thread

/**
 * Same HTTP API as notebooks/printscale_server.py, with nearest-neighbour 4x instead of AuraSR,
 * so the app's cloud path can be tested without a GPU or Python.
 */
class FakeCloudServer(private val key: String = "fake-key-12345", val failJobs: Boolean = false) : AutoCloseable {
    private val socket = ServerSocket(0, 50, InetAddress.getByName("127.0.0.1"))
    private val results = ConcurrentHashMap<String, ByteArray>()
    @Volatile var lastUpload: Triple<Int, Int, Boolean>? = null
    val deleted = java.util.Collections.synchronizedList(mutableListOf<String>())
    val link get() = "http://127.0.0.1:${socket.localPort}/?key=$key"

    /** Minimal HTTP/1.1: one request per connection (Connection: close). */
    private class Exchange(val method: String, val path: String, val headers: Map<String, String>, val body: ByteArray, val out: OutputStream)

    init {
        thread(isDaemon = true) {
            while (!socket.isClosed) {
                val s = runCatching { socket.accept() }.getOrNull() ?: break
                thread(isDaemon = true) { s.use { serve(it) } }
            }
        }
    }

    private fun serve(s: Socket) {
        val inp = DataInputStream(s.getInputStream().buffered())
        fun line(): String {
            val b = StringBuilder()
            while (true) { val c = inp.read(); if (c < 0 || c == '\n'.code) break; if (c != '\r'.code) b.append(c.toChar()) }
            return b.toString()
        }
        val req = line().split(" ")
        if (req.size < 2) return
        val headers = mutableMapOf<String, String>()
        while (true) { val l = line(); if (l.isEmpty()) break; headers[l.substringBefore(':').trim().lowercase()] = l.substringAfter(':').trim() }
        val body = ByteArray(headers["content-length"]?.toInt() ?: 0).also { inp.readFully(it) }
        handle(Exchange(req[0], req[1].substringBefore('?'), headers, body, s.getOutputStream()))
    }

    private fun send(ex: Exchange, code: Int, body: ByteArray, type: String = "application/json") {
        val head = "HTTP/1.1 $code X\r\nContent-Type: $type\r\nContent-Length: ${body.size}\r\nConnection: close\r\n\r\n"
        ex.out.write(head.toByteArray()); ex.out.write(body); ex.out.flush()
    }

    private fun json(ex: Exchange, code: Int, s: String) = send(ex, code, s.toByteArray())

    private fun handle(ex: Exchange) {
        if (ex.headers["x-printscale-key"] != key) return json(ex, 401, """{"error":"Wrong key."}""")
        val path = ex.path
        when {
            path == "/health" -> json(ex, 200, """{"printscale": 1, "model": "AuraSR v2", "device": "cuda", "gpu": "Fake T4", "max_pixels": 16777216}""")
            path == "/jobs" && ex.method == "POST" -> {
                val bytes = ex.body
                val id = UUID.randomUUID().toString().replace("-", "")
                PngStreamReader(ByteArrayInputStream(bytes)).use { r ->
                    lastUpload = Triple(r.width, r.height, r.hasAlpha)
                    val out = ByteArrayOutputStream()
                    val w = PngStreamWriter(out, r.width * 4, r.height * 4, r.hasAlpha, null, null)
                    val row = IntArray(r.width); val big = IntArray(r.width * 4)
                    var y = 0
                    for (sy in 0 until r.height) {
                        r.readRow(row)
                        for (x in big.indices) big[x] = row[x / 4]
                        repeat(4) { w.writeRow(y++, big) }
                    }
                    w.finish()
                    results[id] = out.toByteArray()
                }
                json(ex, 200, """{"id": "$id"}""")
            }
            path.matches(Regex("/jobs/[0-9a-f]{32}")) && ex.method == "DELETE" -> {
                deleted += path.substringAfterLast('/'); results.remove(path.substringAfterLast('/')); json(ex, 200, """{"ok": true}""")
            }
            path.matches(Regex("/jobs/[0-9a-f]{32}")) -> {
                val id = path.substringAfterLast('/')
                if (!results.containsKey(id)) json(ex, 404, """{"error": "No such job."}""")
                else if (failJobs) json(ex, 200, """{"id": "$id", "state": "failed", "done": 0, "total": 4, "error": "OutOfMemoryError: CUDA out of memory"}""")
                else json(ex, 200, """{"id": "$id", "state": "done", "done": 4, "total": 4, "error": null}""")
            }
            path.matches(Regex("/jobs/[0-9a-f]{32}/result")) -> {
                val bytes = results[path.split('/')[2]] ?: return json(ex, 404, """{"error": "No such job."}""")
                send(ex, 200, bytes, "image/png")
            }
            else -> json(ex, 404, """{"error": "Unknown path."}""")
        }
    }

    override fun close() = socket.close()
}
