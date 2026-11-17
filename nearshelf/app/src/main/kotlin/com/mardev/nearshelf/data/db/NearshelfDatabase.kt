package com.mardev.nearshelf.data.db

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

@Database(entities = [SavedLibraryEntity::class], version = 1, exportSchema = true)
abstract class NearshelfDatabase : RoomDatabase() {
    abstract fun savedLibraries(): SavedLibraryDao
}
