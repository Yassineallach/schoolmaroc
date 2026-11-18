package com.mardev.nearshelf

import android.app.Application
import com.mardev.nearshelf.data.RegistryRepository
import dagger.hilt.android.HiltAndroidApp
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltAndroidApp
class NearshelfApp : Application() {
    @Inject lateinit var registry: RegistryRepository

    private val appScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    override fun onCreate() {
        super.onCreate()
        appScope.launch {
            registry.load()
            registry.refreshIfStale()
        }
    }
}
