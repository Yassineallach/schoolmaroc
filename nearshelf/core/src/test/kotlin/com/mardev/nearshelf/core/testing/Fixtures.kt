package com.mardev.nearshelf.core.testing

import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Protocol
import okhttp3.Request
import okhttp3.Response
import okhttp3.ResponseBody.Companion.toResponseBody

object Fixtures {
    fun read(path: String): String =
        requireNotNull(javaClass.classLoader.getResource("fixtures/$path")) { "Missing fixture $path" }
            .readText()
}

/** Serves canned responses by URL; records every request it sees. */
class FixtureInterceptor(private val routes: (Request) -> Pair<Int, String>?) : Interceptor {
    val requests = mutableListOf<Request>()

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        requests += request
        val (code, body) = routes(request) ?: (404 to "{}")
        return Response.Builder()
            .request(request)
            .protocol(Protocol.HTTP_1_1)
            .code(code)
            .message("fixture")
            .body(body.toResponseBody("application/json".toMediaType()))
            .build()
    }

    fun client(): OkHttpClient = OkHttpClient.Builder().addInterceptor(this).build()
}
