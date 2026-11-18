package com.mardev.nearshelf.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.search.QueryParser
import com.mardev.nearshelf.data.HistoryItem
import com.mardev.nearshelf.data.HistoryRepository
import com.mardev.nearshelf.data.LibraryRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(repo: LibraryRepository, history: HistoryRepository) : ViewModel() {
    val recent: StateFlow<List<HistoryItem>> = history.recent(5).stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val input = MutableStateFlow("")

    val libraries: StateFlow<List<Library>?> =
        repo.libraries.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun parsedQuery(): BookQuery? = QueryParser.parse(input.value)
}
