package com.mardev.nearshelf.ui.watchlist

import com.mardev.nearshelf.widget.WatchlistWidget
import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mardev.nearshelf.data.WatchItem
import com.mardev.nearshelf.data.WatchlistRepository
import com.mardev.nearshelf.work.WatchlistWorker
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class WatchlistViewModel @Inject constructor(
    private val repo: WatchlistRepository,
    @ApplicationContext private val context: Context,
) : ViewModel() {
    val items: StateFlow<List<WatchItem>?> = repo.items.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), null)

    fun remove(item: WatchItem) = viewModelScope.launch {
        repo.remove(item.key)
        if (repo.all().isEmpty()) WatchlistWorker.cancel(context)
        WatchlistWidget.refresh(context)
    }

    fun restore(item: WatchItem) = viewModelScope.launch {
        repo.add(item.query, item.title, item.author, item.coverUrl, item.snapshot)
        WatchlistWorker.schedule(context)
        WatchlistWidget.refresh(context)
    }

    /** One extra check now (still network-constrained and polite). */
    fun checkNow() = WatchlistWorker.checkNow(context)
}
