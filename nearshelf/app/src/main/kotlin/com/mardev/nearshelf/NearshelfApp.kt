package com.mardev.nearshelf

import android.app.Application
import androidx.hilt.work.HiltWorkerFactory
import androidx.work.Configuration
import com.mardev.nearshelf.data.LibraryRepository
import com.mardev.nearshelf.data.RoomCache
import com.mardev.nearshelf.data.RegistryRepository
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltAndroidApp
class NearshelfApp : Application(), Configuration.Provider {
    @Inject lateinit var registry: RegistryRepository
    @Inject lateinit var libraries: LibraryRepository
    @Inject lateinit var cache: RoomCache
    @Inject lateinit var workerFactory: HiltWorkerFactory

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder().setWorkerFactory(workerFactory).build()

    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        appScope.launch {
            registry.load()
            registry.refreshIfStale()
            registry.current?.let { libraries.syncWithRegistry(it) }
            cache.prune()
        }
    }
}
