package com.mardev.nearshelf.ui.libraries

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.data.LibraryRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import com.mardev.nearshelf.data.RegistryRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class LibrariesViewModel @Inject constructor(
    private val repo: LibraryRepository,
    registry: RegistryRepository,
) : ViewModel() {
    /**
     * Saved libraries, with branch lists filled in from the registry for entries
     * saved before it knew them. null until the database answers.
     */
    val libraries: StateFlow<List<Library>?> = combine(repo.libraries, registry.registry) { libs, reg ->
        libs.map { lib -> if (lib.branches.isNotEmpty() || reg == null) lib else reg.find(lib.id)?.let { lib.copy(branches = it.branches) } ?: lib }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun setHomeBranch(library: Library, branchId: String?) =
        viewModelScope.launch { repo.setHomeBranch(library.id, branchId, library.branches) }

    fun moveUp(id: String) = viewModelScope.launch { repo.move(id, -1) }
    fun moveDown(id: String) = viewModelScope.launch { repo.move(id, +1) }
    fun remove(id: String) = viewModelScope.launch { repo.remove(id) }
    fun restore(library: Library) = viewModelScope.launch { repo.add(library) }
}
