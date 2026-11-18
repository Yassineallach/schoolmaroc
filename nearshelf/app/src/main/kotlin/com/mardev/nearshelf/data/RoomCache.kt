package com.mardev.nearshelf.data

import com.mardev.nearshelf.core.cache.CacheTtl
import com.mardev.nearshelf.core.cache.KeyValueCache
import com.mardev.nearshelf.data.db.CacheDao
import com.mardev.nearshelf.data.db.CacheEntryEntity
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class RoomCache @Inject constructor(private val dao: CacheDao) : KeyValueCache {
    override suspend fun get(key: String) = dao.get(key)?.let { it.value to it.savedAt }
    override suspend fun put(key: String, value: String) = dao.put(CacheEntryEntity(key, value, System.currentTimeMillis()))

    /** Nothing is kept past the longest lifetime (Open Library, 30 days). */
    suspend fun prune() = dao.deleteOlderThan(System.currentTimeMillis() - CacheTtl.OPEN_LIBRARY_MILLIS)
}
