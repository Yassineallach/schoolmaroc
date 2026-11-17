package com.mardev.nearshelf.ui.debug

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Holding
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.provider.ProviderException
import com.mardev.nearshelf.core.provider.overdrive.OverDriveProvider
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DebugState(
    val libraryQuery: String = "",
    val libraries: List<LibraryRef> = emptyList(),
    val selected: LibraryRef? = null,
    val bookQuery: String = "",
    val holdings: List<Holding>? = null,
    val loading: Boolean = false,
    val error: String? = null,
)

@OptIn(FlowPreview::class)
@HiltViewModel
class ProviderDebugViewModel @Inject constructor(
    private val overDrive: OverDriveProvider,
) : ViewModel() {

    private val _state = MutableStateFlow(DebugState())
    val state: StateFlow<DebugState> = _state.asStateFlow()
    private var searchJob: Job? = null

    init {
        viewModelScope.launch {
            _state.map { it.libraryQuery.trim() }
                .distinctUntilChanged()
                .debounce(350)
                .collect { q -> lookUpLibraries(q) }
        }
    }

    fun onLibraryQuery(q: String) = _state.update { it.copy(libraryQuery = q) }
    fun onBookQuery(q: String) = _state.update { it.copy(bookQuery = q) }
    fun select(lib: LibraryRef?) = _state.update { it.copy(selected = lib, holdings = null, error = null) }

    fun search() {
        val s = _state.value
        val lib = s.selected ?: return
        val text = s.bookQuery.trim().ifEmpty { return }
        val digits = text.filter(Char::isDigit)
        val query = if (digits.length == 13 || digits.length == 10) BookQuery(isbn = digits) else BookQuery(title = text)
        searchJob?.cancel()
        searchJob = viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null) }
            runProvider { overDrive.search(lib, query) }
                .onSuccess { h -> _state.update { it.copy(holdings = h, loading = false) } }
                .onFailure { e -> _state.update { it.copy(error = e.message, loading = false) } }
        }
    }

    fun libbyLink(holding: Holding): String? =
        _state.value.selected?.let { overDrive.borrowLink(it, holding).toString() }

    private suspend fun lookUpLibraries(q: String) {
        if (q.length < 2) {
            _state.update { it.copy(libraries = emptyList()) }
            return
        }
        runProvider { overDrive.findLibraries(q) }
            .onSuccess { libs -> _state.update { it.copy(libraries = libs, error = null) } }
            .onFailure { e -> _state.update { it.copy(error = e.message) } }
    }

    private suspend fun <T> runProvider(block: suspend () -> T): Result<T> = try {
        Result.success(block())
    } catch (e: CancellationException) {
        throw e
    } catch (e: ProviderException) {
        Result.failure(Exception("${e.provider.displayName} ${e.kind.name.lowercase()}: ${e.message}"))
    }
}
