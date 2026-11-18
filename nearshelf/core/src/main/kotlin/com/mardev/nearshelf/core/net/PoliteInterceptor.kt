package com.mardev.nearshelf.core.net

import okhttp3.Interceptor
import okhttp3.Response
import java.io.IOException
import java.io.InterruptedIOException
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit

/**
 * Politeness for every request Nearshelf makes: at most [maxConcurrent] in flight
 * overall, and requests to one host spaced at least [minIntervalMillis] apart
 * (~2 per second). Extra requests wait their turn instead of being dropped.
 */
class PoliteInterceptor(
    maxConcurrent: Int = 3,
    private val minIntervalMillis: Long = 500,
    private val clock: () -> Long = System::currentTimeMillis,
    private val sleeper: (Long) -> Unit = Thread::sleep,
) : Interceptor {
    private val permits = Semaphore(maxConcurrent, true)
    private val nextSlot = HashMap<String, Long>()

    override fun intercept(chain: Interceptor.Chain): Response {
        if (!permits.tryAcquire(60, TimeUnit.SECONDS)) throw IOException("Too many requests queued")
        try {
            val wait = reserveSlot(chain.request().url.host)
            if (wait > 0) {
                try {
                    sleeper(wait)
                } catch (e: InterruptedException) {
                    throw InterruptedIOException("Cancelled while waiting for ${chain.request().url.host}")
                }
            }
            return chain.proceed(chain.request())
        } finally {
            permits.release()
        }
    }

    /** Books the next free slot for [host]; returns how long to wait for it. */
    @Synchronized
    internal fun reserveSlot(host: String): Long {
        val now = clock()
        val slot = maxOf(now, nextSlot[host] ?: 0L)
        nextSlot[host] = slot + minIntervalMillis
        return slot - now
    }
}
