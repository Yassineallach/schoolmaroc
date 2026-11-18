package com.mardev.nearshelf.core.cache

/** A small persistent cache (Room in the app, a map in tests). Values are JSON. */
interface KeyValueCache {
    /** Value and the time it was stored (epoch millis), or null. */
    suspend fun get(key: String): Pair<String, Long>?
    suspend fun put(key: String, value: String)
}

class MemoryCache(private val clock: () -> Long = System::currentTimeMillis) : KeyValueCache {
    private val map = HashMap<String, Pair<String, Long>>()
    override suspend fun get(key: String) = synchronized(map) { map[key] }
    override suspend fun put(key: String, value: String) = synchronized(map) { map[key] = value to clock() }
}

object CacheTtl {
    const val SEARCH_MILLIS = 6L * 60 * 60 * 1000
    const val OPEN_LIBRARY_MILLIS = 30L * 24 * 60 * 60 * 1000
}
