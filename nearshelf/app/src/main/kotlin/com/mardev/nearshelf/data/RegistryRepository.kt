package com.mardev.nearshelf.data

import android.content.Context
import com.mardev.nearshelf.BuildConfig
import com.mardev.nearshelf.core.registry.LibraryRegistry
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.IOException
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The library registry: a downloaded copy (refreshed at most weekly from
 * [BuildConfig.REGISTRY_URL]) with the copy bundled in assets as fallback. A
 * download is used only if it parses and isn't older than the bundled one.
 */
@Singleton
class RegistryRepository @Inject constructor(
    @ApplicationContext private val context: Context,
    private val client: OkHttpClient,
) {
    private val cacheFile get() = File(context.filesDir, "registry/libraries.json")
    private val _registry = MutableStateFlow<LibraryRegistry?>(null)
    val registry: StateFlow<LibraryRegistry?> = _registry.asStateFlow()

    val current: LibraryRegistry? get() = _registry.value

    suspend fun load() = withContext(Dispatchers.IO) {
        val bundled = runCatching {
            LibraryRegistry.parse(context.assets.open("libraries.json").bufferedReader().readText())
        }.getOrNull()
        val cached = runCatching { LibraryRegistry.parse(cacheFile.readText()) }.getOrNull()
        _registry.value = newest(bundled, cached)
    }

    /** Downloads a fresh copy when the cached one is over a week old. Failures keep what we have. */
    suspend fun refreshIfStale(now: Long = System.currentTimeMillis()) = withContext(Dispatchers.IO) {
        val url = BuildConfig.REGISTRY_URL
        if (url.isBlank()) return@withContext
        if (cacheFile.exists() && now - cacheFile.lastModified() < TimeUnit.DAYS.toMillis(7)) return@withContext
        try {
            client.newCall(Request.Builder().url(url).build()).execute().use { r ->
                if (!r.isSuccessful) return@use
                val text = r.body.string()
                val fresh = LibraryRegistry.parse(text) // throws if malformed: keep the old copy
                cacheFile.parentFile?.mkdirs()
                File(cacheFile.parentFile, "libraries.json.tmp").apply { writeText(text) }.renameTo(cacheFile)
                _registry.value = newest(_registry.value, fresh)
            }
        } catch (e: CancellationException) {
            throw e
        } catch (_: IOException) {
        } catch (_: IllegalArgumentException) {
        } catch (_: kotlinx.serialization.SerializationException) {
        }
    }

    private fun newest(a: LibraryRegistry?, b: LibraryRegistry?): LibraryRegistry? = listOfNotNull(a, b).maxByOrNull { it.file.generatedAt }
}
