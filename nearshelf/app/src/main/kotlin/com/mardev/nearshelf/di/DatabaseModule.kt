package com.mardev.nearshelf.di

import android.content.Context
import androidx.room.Room
import com.mardev.nearshelf.data.db.NearshelfDatabase
import com.mardev.nearshelf.data.db.SavedLibraryDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton
    fun database(@ApplicationContext context: Context): NearshelfDatabase =
        Room.databaseBuilder(context, NearshelfDatabase::class.java, "nearshelf.db").build()

    @Provides
    fun savedLibraries(db: NearshelfDatabase): SavedLibraryDao = db.savedLibraries()
}
