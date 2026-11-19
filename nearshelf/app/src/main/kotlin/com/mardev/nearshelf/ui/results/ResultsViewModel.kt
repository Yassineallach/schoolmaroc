package com.mardev.nearshelf.ui.results

import com.mardev.nearshelf.widget.WatchlistWidget
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
import com.mardev.nearshelf.core.metadata.ExpandedQuery
import com.mardev.nearshelf.core.metadata.WorkCandidate
import android.content.Context
import com.mardev.nearshelf.core.geo.LatLng
import com.mardev.nearshelf.core.prefs.ReadingPrefs
import com.mardev.nearshelf.core.search.SearchCoordinator
import com.mardev.nearshelf.data.Connectivity
import com.mardev.nearshelf.data.HistoryRepository
import com.mardev.nearshelf.data.PreferencesRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import com.mardev.nearshelf.core.watch.Watch
import com.mardev.nearshelf.core.watch.WatchScope
import com.mardev.nearshelf.data.WatchlistRepository
import com.mardev.nearshelf.location.LocationRepository
import com.mardev.nearshelf.work.WatchlistWorker
import dagger.hilt.android.qualifiers.ApplicationContext
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
    fun rows(prefs: ReadingPrefs = ReadingPrefs()): List<HoldingRowUi> =
        prefs.filter((state as? ServiceState.Done)?.matches.orEmpty())
            .sortedWith(
                compareBy<MatchedHolding> { it.otherLanguage }
                    .thenBy { prefs.formatRank(it.holding.format) }
                    .thenBy { !it.holding.isAvailableNow }
                    .thenBy { it.holding.waitDays ?: Int.MAX_VALUE },
            )
            .groupBy { listOf(it.holding.format, it.holding.language, it.otherLanguage, it.holding.edition) }
            .values.map { HoldingRowUi(it.first(), it.size - 1) }
}

data class HoldingRowUi(val match: MatchedHolding, val moreEditions: Int)

data class LibraryResult(val library: Library, val services: List<ServiceResult>)

enum class Phase { READING_SHARE, LOOKING_UP, CHOOSING, SEARCHING, SHARE_NOT_UNDERSTOOD }

data class ResultsUiState(
    val phase: Phase,
    /** null until a shared link has been read. */
    val query: BookQuery? = null,
    /** Open Library cover, used until a catalog supplies one. */
    val metadataCover: String? = null,
    /** null while the saved libraries load. */
    val libraries: List<LibraryResult>? = null,
    val sharedText: String? = null,
    /** Books a bare title could mean; shown for the reader to pick when there are several. */
    val candidates: List<WorkCandidate> = emptyList(),
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
    private val watchlist: WatchlistRepository,
    private val location: LocationRepository,
    private val history: HistoryRepository,
    preferences: PreferencesRepository,
    private val connectivity: Connectivity,
    @ApplicationContext private val context: Context,
) : ViewModel() {

    val prefs: StateFlow<ReadingPrefs> = preferences.prefs.stateIn(viewModelScope, SharingStarted.Eagerly, ReadingPrefs())

    /** No connection when the search started: results come from what's saved on the phone. */
    private val _offline = MutableStateFlow(false)
    val offline: StateFlow<Boolean> = _offline.asStateFlow()

    private val _watched = MutableStateFlow(false)
    val watched: StateFlow<Boolean> = _watched.asStateFlow()

    /** Coarse location for branch distances; null without permission. Never leaves the device. */
    private val _here = MutableStateFlow<LatLng?>(null)
    val here: StateFlow<LatLng?> = _here.asStateFlow()

    val hasLocationPermission get() = location.hasPermission()

    fun refreshLocation() = viewModelScope.launch { _here.value = location.current() }

    /** What this book's watch covers; null when it isn't watched. */
    private val _watchScope = MutableStateFlow<WatchScope?>(null)
    val watchScope: StateFlow<WatchScope?> = _watchScope.asStateFlow()

    /**
     * Watch (or re-scope the watch) for [scope]. The current results, limited to that
     * scope, become the baseline, so the first notification is real news.
     */
    fun watch(scope: WatchScope) = viewModelScope.launch {
        val q = query ?: return@launch
        val s = _state.value
        val header = s.header
        val snapshot = s.libraries?.let { libs ->
            if (s.finished < s.total) null
            else Watch.snapshot(System.currentTimeMillis(), libs.map { lr -> lr.library to lr.services.map { it.ref.provider.displayName to it.state } }, scope)
        }
        watchlist.add(q, header.title, header.authors.firstOrNull(), header.coverUrl, snapshot, scope)
        WatchlistWorker.schedule(context)
        _watched.value = true
        _watchScope.value = scope
        WatchlistWidget.refresh(context)
    }

    fun unwatch() = viewModelScope.launch {
        val q = query ?: return@launch
        watchlist.remove(WatchlistRepository.keyOf(q))
        if (watchlist.all().isEmpty()) WatchlistWorker.cancel(context)
        _watched.value = false
        _watchScope.value = null
        WatchlistWidget.refresh(context)
    }

    private val route = savedState.toRoute<ResultsRoute>()
    private var query: BookQuery? = route.toQueryOrNull()

    private val _state = MutableStateFlow(
        ResultsUiState(
            phase = if (route.shared != null && route.watchKey == null && route.queryJson == null) Phase.READING_SHARE else Phase.LOOKING_UP,
            query = query,
            sharedText = route.shared,
        ),
    )
    val state: StateFlow<ResultsUiState> = _state.asStateFlow()

    /** The reader's answer to "Which book?"; declared before init, which waits on it. */
    private val choice = kotlinx.coroutines.CompletableDeferred<WorkCandidate?>()

    /** The reader picked a book ([c]), or chose to search every book with the title (null). */
    fun choose(c: WorkCandidate?) { choice.complete(c) }

    init {
        if (location.hasPermission()) refreshLocation()
        viewModelScope.launch {
            val fromWatch = route.watchKey?.let { key -> watchlist.all().firstOrNull { it.key == key }?.query }
                ?: route.queryJson?.let { runCatching { kotlinx.serialization.json.Json.decodeFromString<BookQuery>(it) }.getOrNull() }
            val typed = fromWatch ?: query ?: route.shared?.let { shareParser.parse(it) }
            if (typed == null) {
                _state.update { it.copy(phase = Phase.SHARE_NOT_UNDERSTOOD) }
                return@launch
            }
            _state.update { it.copy(phase = Phase.LOOKING_UP, query = typed) }
            // A bare title can mean several books (King's and Wright's "The Outsider"):
            // ask which one rather than pick the most popular or mix them.
            val candidates = expander.candidates(typed)
            val expanded = when {
                candidates.size >= 2 -> {
                    _state.update { it.copy(phase = Phase.CHOOSING, candidates = candidates) }
                    val picked = choice.await()
                    _state.update { it.copy(phase = Phase.LOOKING_UP, candidates = emptyList()) }
                    // null: the reader wants every book with this title.
                    picked?.let { expander.withWork(typed, it.work) } ?: ExpandedQuery(typed)
                }
                candidates.size == 1 -> expander.withWork(typed, candidates.first().work)
                else -> expander.expand(typed)
            }
            val q = expanded.query
            query = q
            _state.update { it.copy(phase = Phase.SEARCHING, query = q, metadataCover = expanded.coverUrl) }
            watchlist.get(q).let {
                _watched.value = it != null
                _watchScope.value = it?.scope
            }
            history.record(q, q.title ?: q.isbn.orEmpty(), q.author, expanded.coverUrl)
            _offline.value = !connectivity.isOnline()

            val libraries = repo.libraries.first()
            _state.update { s ->
                s.copy(libraries = libraries.map { lib ->
                    LibraryResult(lib, lib.services.map { ServiceResult(it, ServiceState.Loading) })
                })
            }
            coordinator.search(libraries, q, offline = _offline.value).collect { u -> apply(u.libraryId, u.service, u.state) }
        }
    }

    fun retry(libraryId: String, ref: LibraryRef) {
        val q = query ?: return
        val lib = _state.value.libraries?.firstOrNull { it.library.id == libraryId }?.library
        apply(libraryId, ref, ServiceState.Loading)
        viewModelScope.launch { apply(libraryId, ref, coordinator.searchOne(ref, q, lib, forceRefresh = true)) }
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

private fun ResultsRoute.toQueryOrNull(): BookQuery? = if (watchKey != null || queryJson != null) null else
    if (title.isNullOrBlank() && isbn.isNullOrBlank()) null else BookQuery(title = title, author = author, isbn = isbn)
