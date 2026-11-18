package com.mardev.nearshelf.core.net

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit

object NearshelfHttp {
    /** One limiter for the whole app: every client built here shares it. */
    private val polite = PoliteInterceptor()

    const val PROJECT_URL = "https://github.com/yassineallach/nearshelf"

    fun userAgent(appVersion: String): String = "Nearshelf/$appVersion (Android; +$PROJECT_URL)"

    /**
     * Base client shared by every provider. Rate limiting and the shared
     * concurrency cap arrive in milestone 8 as further interceptors here.
     */
    fun client(appVersion: String, extra: List<Interceptor> = emptyList()): OkHttpClient =
        OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(20, TimeUnit.SECONDS)
            .callTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(UserAgentInterceptor(userAgent(appVersion)))
            .addInterceptor(polite)
            .apply { extra.forEach { addInterceptor(it) } }
            .build()
}

class UserAgentInterceptor(private val userAgent: String) : Interceptor {
    override fun intercept(chain: Interceptor.Chain) =
        chain.proceed(chain.request().newBuilder().header("User-Agent", userAgent).build())
}
