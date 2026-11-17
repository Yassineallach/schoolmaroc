package com.mardev.nearshelf.ui.libraries

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.data.LibraryRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class LibrariesViewModel @Inject constructor(private val repo: LibraryRepository) : ViewModel() {
    /** null until the database answers, so the screen doesn't flash its empty state. */
    val libraries: StateFlow<List<Library>?> =
        repo.libraries.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun moveUp(id: String) = viewModelScope.launch { repo.move(id, -1) }
    fun moveDown(id: String) = viewModelScope.launch { repo.move(id, +1) }
    fun remove(id: String) = viewModelScope.launch { repo.remove(id) }
    fun restore(library: Library) = viewModelScope.launch { repo.add(library) }
}
