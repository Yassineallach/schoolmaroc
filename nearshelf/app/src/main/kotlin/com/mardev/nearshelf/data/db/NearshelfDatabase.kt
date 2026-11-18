package com.mardev.nearshelf.data.db

import androidx.room.AutoMigration
import androidx.room.ColumnInfo
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.Query
import androidx.room.RoomDatabase
import androidx.room.Transaction
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

/** A library the user added. [json] is a serialized core `Library` (with all its services). */
@Entity(tableName = "saved_library")
data class SavedLibraryEntity(
    @PrimaryKey val id: String,
    val position: Int,
    val json: String,
)

@Dao
interface SavedLibraryDao {
    @Query("SELECT * FROM saved_library ORDER BY position")
    fun observe(): Flow<List<SavedLibraryEntity>>

    @Query("SELECT COALESCE(MAX(position), -1) FROM saved_library")
    suspend fun maxPosition(): Int

    @Upsert
    suspend fun upsert(entity: SavedLibraryEntity)

    @Query("DELETE FROM saved_library WHERE id = :id")
    suspend fun delete(id: String)

    @Query("UPDATE saved_library SET position = :position WHERE id = :id")
    suspend fun setPosition(id: String, position: Int)

    @Transaction
    suspend fun reorder(idsInOrder: List<String>) {
        idsInOrder.forEachIndexed { i, id -> setPosition(id, i) }
    }
}

/** Search results (6 h) and Open Library data (30 days), as JSON. */
@Entity(tableName = "cache_entry")
data class CacheEntryEntity(@PrimaryKey val key: String, val value: String, val savedAt: Long)

@Dao
interface CacheDao {
    @Query("SELECT * FROM cache_entry WHERE `key` = :key")
    suspend fun get(key: String): CacheEntryEntity?

    @Upsert
    suspend fun put(entry: CacheEntryEntity)

    @Query("DELETE FROM cache_entry WHERE savedAt < :before")
    suspend fun deleteOlderThan(before: Long)
}

/** A watched book. [queryJson] is the core BookQuery; [snapshotJson] the last check's WatchSnapshot. */
@Entity(tableName = "watch_item")
data class WatchItemEntity(
    @PrimaryKey val key: String,
    val queryJson: String,
    val title: String,
    val author: String?,
    val coverUrl: String?,
    val addedAt: Long,
    val lastCheckedAt: Long? = null,
    val snapshotJson: String? = null,
    /** WatchScope as JSON; empty (rows from before v4) means everything. */
    @ColumnInfo(defaultValue = "") val scopeJson: String = "",
)

@Dao
interface WatchDao {
    @Query("SELECT * FROM watch_item ORDER BY addedAt DESC")
    fun observe(): Flow<List<WatchItemEntity>>

    @Query("SELECT * FROM watch_item ORDER BY addedAt DESC")
    suspend fun all(): List<WatchItemEntity>

    @Query("SELECT * FROM watch_item WHERE `key` = :key")
    suspend fun get(key: String): WatchItemEntity?

    @Upsert
    suspend fun upsert(item: WatchItemEntity)

    @Query("DELETE FROM watch_item WHERE `key` = :key")
    suspend fun delete(key: String)
}

/** A recent lookup (the expanded query), newest first. */
@Entity(tableName = "search_history")
data class HistoryEntity(
    @PrimaryKey val key: String,
    val queryJson: String,
    val title: String,
    val author: String?,
    val coverUrl: String?,
    val searchedAt: Long,
)

@Dao
interface HistoryDao {
    @Query("SELECT * FROM search_history ORDER BY searchedAt DESC LIMIT :limit")
    fun observe(limit: Int): Flow<List<HistoryEntity>>

    @Upsert
    suspend fun upsert(e: HistoryEntity)

    @Query("DELETE FROM search_history WHERE `key` = :key")
    suspend fun delete(key: String)

    @Query("DELETE FROM search_history")
    suspend fun clear()

    /** Keeps the newest [keep] entries. */
    @Query("DELETE FROM search_history WHERE `key` NOT IN (SELECT `key` FROM search_history ORDER BY searchedAt DESC LIMIT :keep)")
    suspend fun trim(keep: Int)
}

@Database(
    entities = [SavedLibraryEntity::class, CacheEntryEntity::class, WatchItemEntity::class, HistoryEntity::class],
    version = 4,
    exportSchema = true,
    autoMigrations = [AutoMigration(from = 1, to = 2), AutoMigration(from = 2, to = 3), AutoMigration(from = 3, to = 4)],
)
abstract class NearshelfDatabase : RoomDatabase() {
    abstract fun savedLibraries(): SavedLibraryDao
    abstract fun cache(): CacheDao
    abstract fun watch(): WatchDao
    abstract fun history(): HistoryDao
}
