package com.mardev.nearshelf.ui.results

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.toRoute
import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Format
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.search.SearchCoordinator
import com.mardev.nearshelf.core.search.ServiceState
import com.mardev.nearshelf.data.LibraryRepository
import com.mardev.nearshelf.nav.ResultsRoute
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class BookHeader(val title: String, val authors: List<String>, val coverUrl: String?)

data class ServiceResult(val ref: LibraryRef, val state: ServiceState)

data class LibraryResult(val library: Library, val services: List<ServiceResult>)

data class ResultsUiState(
    val query: BookQuery,
    /** null while the saved libraries load. */
    val libraries: List<LibraryResult>? = null,
) {
    private val all get() = libraries.orEmpty().flatMap { it.services }
    val total: Int get() = all.size
    val finished: Int get() = all.count { it.state !is ServiceState.Loading }
    val progress: Float get() = if (total == 0) 1f else finished.toFloat() / total

    /** Best same-language match across every library, for the book header. */
    val header: BookHeader
        get() {
            val best = all.mapNotNull { it.state as? ServiceState.Done }
                .flatMap { it.matches }
                .filter { !it.otherLanguage }
                .maxByOrNull { it.score }
                ?.holding
            return BookHeader(
                title = best?.title ?: query.title ?: query.isbn.orEmpty(),
                authors = best?.authors ?: listOfNotNull(query.author),
                coverUrl = all.flatMap { (it.state as? ServiceState.Done)?.matches.orEmpty() }
                    .firstNotNullOfOrNull { it.holding.coverUrl },
            )
        }
}

@HiltViewModel
class ResultsViewModel @Inject constructor(
    savedState: SavedStateHandle,
    private val repo: LibraryRepository,
    private val coordinator: SearchCoordinator,
) : ViewModel() {

    private val route = savedState.toRoute<ResultsRoute>()
    private val query = BookQuery(title = route.title, author = route.author, isbn = route.isbn)

    private val _state = MutableStateFlow(ResultsUiState(query))
    val state: StateFlow<ResultsUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            val libraries = repo.libraries.first()
            _state.update { s ->
                s.copy(libraries = libraries.map { lib ->
                    LibraryResult(lib, lib.services.map { ServiceResult(it, ServiceState.Loading) })
                })
            }
            coordinator.search(libraries, query).collect { u -> apply(u.libraryId, u.service, u.state) }
        }
    }

    fun retry(libraryId: String, ref: LibraryRef) {
        apply(libraryId, ref, ServiceState.Loading)
        viewModelScope.launch { apply(libraryId, ref, coordinator.searchOne(ref, query)) }
    }

    fun borrowLink(ref: LibraryRef, match: MatchedHolding): String =
        coordinator.borrowLink(ref, match).toString()

    private fun apply(libraryId: String, ref: LibraryRef, state: ServiceState) = _state.update { s ->
        s.copy(libraries = s.libraries?.map { lr ->
            if (lr.library.id != libraryId) lr else lr.copy(services = lr.services.map {
                if (it.ref == ref) ServiceResult(ref, state.sorted()) else it
            })
        })
    }

    /** Same language first, then ebook before audiobook, then on-shelf first, then shortest wait. */
    private fun ServiceState.sorted(): ServiceState = if (this !is ServiceState.Done) this else copy(
        matches = matches.sortedWith(
            compareBy<MatchedHolding> { it.otherLanguage }
                .thenBy { formatRank(it.holding.format) }
                .thenBy { !it.holding.isAvailableNow }
                .thenBy { it.holding.waitDays ?: Int.MAX_VALUE },
        ),
    )

    private fun formatRank(f: Format) = when (f) {
        Format.EBOOK -> 0
        Format.AUDIOBOOK -> 1
        Format.PHYSICAL -> 2
        Format.OTHER -> 3
    }
}
