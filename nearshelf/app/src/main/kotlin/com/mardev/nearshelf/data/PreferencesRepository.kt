package com.mardev.nearshelf.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.mardev.nearshelf.core.prefs.ReadingPrefs
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import java.util.Locale
import javax.inject.Inject
import javax.inject.Singleton

private val Context.dataStore by preferencesDataStore("nearshelf_prefs")

@Singleton
class PreferencesRepository @Inject constructor(@ApplicationContext private val context: Context) {
    private val key = stringPreferencesKey("reading_prefs")
    private val json = Json { ignoreUnknownKeys = true }

    /** Defaults: the phone's language plus English; other languages shown but flagged. */
    private fun defaults() = ReadingPrefs(languages = setOf(Locale.getDefault().language, "en").filter { it.isNotBlank() }.toSet())

    val prefs: Flow<ReadingPrefs> = context.dataStore.data.map { p ->
        p[key]?.let { runCatching { json.decodeFromString<ReadingPrefs>(it) }.getOrNull() } ?: defaults()
    }

    private val onboardedKey = androidx.datastore.preferences.core.booleanPreferencesKey("onboarded")

    /** null while loading, so the first screen doesn't flash. */
    val onboarded: Flow<Boolean> = context.dataStore.data.map { it[onboardedKey] ?: false }

    suspend fun setOnboarded() {
        context.dataStore.edit { it[onboardedKey] = true }
    }

    suspend fun update(transform: (ReadingPrefs) -> ReadingPrefs) {
        context.dataStore.edit { p ->
            val current = p[key]?.let { runCatching { json.decodeFromString<ReadingPrefs>(it) }.getOrNull() } ?: defaults()
            p[key] = json.encodeToString(transform(current))
        }
    }
}
