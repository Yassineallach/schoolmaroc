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
import com.mardev.nearshelf.core.metadata.QueryExpander
import com.mardev.nearshelf.core.search.SearchCoordinator
import com.mardev.nearshelf.core.share.ShareParser
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

data class ServiceResult(val ref: LibraryRef, val state: ServiceState) {
    /**
     * One row per format and language: the best edition (already sorted first) plus how
     * many more editions it stands for. Hoopla often has four editions of one audiobook.
     */
    val rows: List<HoldingRowUi>
        get() = (state as? ServiceState.Done)?.matches.orEmpty()
            .groupBy { listOf(it.holding.format, it.holding.language, it.otherLanguage, it.holding.edition) }
            .values.map { HoldingRowUi(it.first(), it.size - 1) }
}

data class HoldingRowUi(val match: MatchedHolding, val moreEditions: Int)

data class LibraryResult(val library: Library, val services: List<ServiceResult>)

enum class Phase { READING_SHARE, LOOKING_UP, SEARCHING, SHARE_NOT_UNDERSTOOD }

data class ResultsUiState(
    val phase: Phase,
    /** null until a shared link has been read. */
    val query: BookQuery? = null,
    /** Open Library cover, used until a catalog supplies one. */
    val metadataCover: String? = null,
    /** null while the saved libraries load. */
    val libraries: List<LibraryResult>? = null,
    val sharedText: String? = null,
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
                title = best?.title ?: query?.title ?: query?.isbn.orEmpty(),
                authors = best?.authors ?: listOfNotNull(query?.author),
                coverUrl = all.flatMap { (it.state as? ServiceState.Done)?.matches.orEmpty() }
                    .firstNotNullOfOrNull { it.holding.coverUrl } ?: metadataCover,
            )
        }
}

@HiltViewModel
class ResultsViewModel @Inject constructor(
    savedState: SavedStateHandle,
    private val repo: LibraryRepository,
    private val coordinator: SearchCoordinator,
    private val shareParser: ShareParser,
    private val expander: QueryExpander,
) : ViewModel() {

    private val route = savedState.toRoute<ResultsRoute>()
    private var query: BookQuery? = route.toQueryOrNull()

    private val _state = MutableStateFlow(
        ResultsUiState(
            phase = if (route.shared != null) Phase.READING_SHARE else Phase.LOOKING_UP,
            query = query,
            sharedText = route.shared,
        ),
    )
    val state: StateFlow<ResultsUiState> = _state.asStateFlow()

    init {
        viewModelScope.launch {
            val typed = query ?: route.shared?.let { shareParser.parse(it) }
            if (typed == null) {
                _state.update { it.copy(phase = Phase.SHARE_NOT_UNDERSTOOD) }
                return@launch
            }
            _state.update { it.copy(phase = Phase.LOOKING_UP, query = typed) }
            val expanded = expander.expand(typed)
            val q = expanded.query
            query = q
            _state.update { it.copy(phase = Phase.SEARCHING, query = q, metadataCover = expanded.coverUrl) }

            val libraries = repo.libraries.first()
            _state.update { s ->
                s.copy(libraries = libraries.map { lib ->
                    LibraryResult(lib, lib.services.map { ServiceResult(it, ServiceState.Loading) })
                })
            }
            coordinator.search(libraries, q).collect { u -> apply(u.libraryId, u.service, u.state) }
        }
    }

    fun retry(libraryId: String, ref: LibraryRef) {
        val q = query ?: return
        apply(libraryId, ref, ServiceState.Loading)
        viewModelScope.launch { apply(libraryId, ref, coordinator.searchOne(ref, q)) }
    }

    fun borrowLink(ref: LibraryRef, match: MatchedHolding): String =
        coordinator.borrowLink(ref, match).toString()

    fun searchLink(ref: LibraryRef): String? = query?.let { coordinator.searchLink(ref, it)?.toString() }

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

private fun ResultsRoute.toQueryOrNull(): BookQuery? =
    if (title.isNullOrBlank() && isbn.isNullOrBlank()) null else BookQuery(title = title, author = author, isbn = isbn)
