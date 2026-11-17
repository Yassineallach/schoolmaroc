package com.mardev.nearshelf.ui.libraries

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.search.LibrarySearchService
import com.mardev.nearshelf.data.LibraryRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed interface LibrarySearchUi {
    data object Idle : LibrarySearchUi
    data object Loading : LibrarySearchUi
    data class Results(
        val query: String,
        val libraries: List<Library>,
        val failed: Set<ProviderId>,
    ) : LibrarySearchUi
}

@OptIn(FlowPreview::class, kotlinx.coroutines.ExperimentalCoroutinesApi::class)
@HiltViewModel
class AddLibraryViewModel @Inject constructor(
    private val search: LibrarySearchService,
    private val repo: LibraryRepository,
) : ViewModel() {

    val query = MutableStateFlow("")

    val results: StateFlow<LibrarySearchUi> = query
        .map { it.trim() }
        .distinctUntilChanged()
        .debounce(350)
        .flatMapLatest { q ->
            flow {
                if (q.length < 2) {
                    emit(LibrarySearchUi.Idle)
                    return@flow
                }
                emit(LibrarySearchUi.Loading)
                val r = search.search(q)
                emit(LibrarySearchUi.Results(q, r.libraries, r.failedProviders))
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), LibrarySearchUi.Idle)

    val savedIds: StateFlow<Set<String>> = repo.libraries
        .map { libs -> libs.map { it.id }.toSet() }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptySet())

    fun add(library: Library) = viewModelScope.launch { repo.add(library) }
    fun remove(id: String) = viewModelScope.launch { repo.remove(id) }
}
