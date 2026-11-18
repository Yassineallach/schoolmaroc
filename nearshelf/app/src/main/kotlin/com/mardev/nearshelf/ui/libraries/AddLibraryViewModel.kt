package com.mardev.nearshelf.ui.libraries

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.registry.CatalogDetector
import com.mardev.nearshelf.core.share.PageFetcher
import com.mardev.nearshelf.data.RegistryRepository
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

    /** The user typed a catalog address. [library] is null when the software wasn't recognised. */
    data class Detected(val input: String, val library: Library?, val provider: ProviderId?) : LibrarySearchUi
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
    private val fetcher: PageFetcher,
    private val registry: RegistryRepository,
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
                if (CatalogDetector.looksLikeUrl(q)) {
                    emit(detect(q))
                    return@flow
                }
                val r = search.search(q)
                emit(LibrarySearchUi.Results(q, r.libraries, r.failedProviders))
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), LibrarySearchUi.Idle)

    /** Saved services per library id, so a search that finds a new service offers to add it. */
    val saved: StateFlow<Map<String, Set<Pair<ProviderId, String>>>> = repo.libraries
        .map { libs -> libs.associate { lib -> lib.id to lib.services.map { it.provider to it.key }.toSet() } }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyMap())

    private suspend fun detect(input: String): LibrarySearchUi.Detected {
        val d = CatalogDetector.detect(input, fetcher) ?: return LibrarySearchUi.Detected(input, null, null)
        // A registry entry with the same catalog gives the real name, Libby, Hoopla and branches.
        registry.current?.libraries?.firstOrNull { lib -> lib.services.any { it.key == d.baseUrl } }
            ?.let { return LibrarySearchUi.Detected(input, it, d.provider) }
        val host = java.net.URI(d.baseUrl).host.removePrefix("www.")
        val name = d.pageTitle?.takeIf { it.isNotBlank() } ?: host
        val ref = LibraryRef(d.provider, d.baseUrl, name, catalogUrl = d.baseUrl)
        return LibrarySearchUi.Detected(input, Library(Library.idFor(name, null), name, services = listOf(ref)), d.provider)
    }

    fun add(library: Library) = viewModelScope.launch { repo.add(library) }
    fun remove(id: String) = viewModelScope.launch { repo.remove(id) }
}
