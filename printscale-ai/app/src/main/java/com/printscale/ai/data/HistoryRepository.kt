package com.printscale.ai.data

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import org.json.JSONArray

sealed interface HistoryState {
    data object Loading : HistoryState
    data class Loaded(val items: List<HistoryItem>) : HistoryState
    data class Failed(val message: String) : HistoryState
}

class HistoryRepository(context: Context) {
    private val paths = Paths(context)
    private val mutex = Mutex()
    private val _state = MutableStateFlow<HistoryState>(HistoryState.Loading)
    val state: StateFlow<HistoryState> = _state

    suspend fun load() = withContext(Dispatchers.IO) {
        mutex.withLock {
            _state.value = try {
                HistoryState.Loaded(read())
            } catch (e: Exception) {
                HistoryState.Failed("History could not be read (${e.message}).")
            }
        }
    }

    private fun read(): List<HistoryItem> {
        if (!paths.historyFile.exists()) return emptyList()
        val a = JSONArray(paths.historyFile.readText())
        return (0 until a.length()).map { HistoryItem.fromJson(a.getJSONObject(it)) }.sortedByDescending { it.createdAt }
    }

    private fun write(items: List<HistoryItem>) {
        val a = JSONArray()
        items.forEach { a.put(it.toJson()) }
        val tmp = java.io.File(paths.historyFile.path + ".tmp")
        tmp.writeText(a.toString())
        tmp.renameTo(paths.historyFile)
        _state.value = HistoryState.Loaded(items.sortedByDescending { it.createdAt })
    }

    private suspend fun mutate(f: (List<HistoryItem>) -> List<HistoryItem>) = withContext(Dispatchers.IO) {
        mutex.withLock {
            val current = runCatching { read() }.getOrDefault(emptyList())
            write(f(current))
        }
    }

    suspend fun add(item: HistoryItem) = mutate { it.filterNot { x -> x.id == item.id } + item }

    suspend fun addExport(id: String, record: ExportRecord) =
        mutate { list -> list.map { if (it.id == id) it.copy(exports = it.exports + record) else it } }

    suspend fun get(id: String): HistoryItem? = withContext(Dispatchers.IO) {
        mutex.withLock { runCatching { read() }.getOrDefault(emptyList()).firstOrNull { it.id == id } }
    }

    suspend fun delete(id: String) {
        mutate { it.filterNot { x -> x.id == id } }
        withContext(Dispatchers.IO) { paths.jobDir(id).deleteRecursively() }
    }

    /** Removes every processed file and import copy. Exports already saved to the gallery stay. */
    suspend fun clearAll() {
        mutate { emptyList() }
        withContext(Dispatchers.IO) {
            paths.jobs.listFiles()?.forEach { it.deleteRecursively() }
            paths.imports.listFiles()?.forEach { it.deleteRecursively() }
            paths.exports.listFiles()?.forEach { it.deleteRecursively() }
        }
    }

    suspend fun storageBytes(): Long = withContext(Dispatchers.IO) {
        paths.jobs.sizeRecursive() + paths.imports.sizeRecursive() + paths.exports.sizeRecursive()
    }
}
