package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.match.MatchedHolding
import com.mardev.nearshelf.core.model.BookQuery
import com.mardev.nearshelf.core.model.Library
import com.mardev.nearshelf.core.model.LibraryRef
import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.CatalogProvider
import com.mardev.nearshelf.core.provider.ProviderException
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.channelFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit

/** State of one service (e.g. Toronto's Libby) for one search. */
sealed interface ServiceState {
    data object Loading : ServiceState
    data class Done(val matches: List<MatchedHolding>) : ServiceState
    data class Failed(val kind: ProviderException.Kind, val message: String?) : ServiceState
}

data class ServiceUpdate(val libraryId: String, val service: LibraryRef, val state: ServiceState)

/**
 * Searches every service of every library in parallel and emits each result as
 * soon as it lands, so the UI never waits for the slowest catalog. At most
 * [maxConcurrent] requests run at once (politeness cap; per-host rate limits
 * live in the HTTP layer from milestone 8).
 */
class SearchCoordinator(
    providers: Collection<CatalogProvider>,
    private val matcher: BookMatcher = BookMatcher(),
    private val maxConcurrent: Int = 3,
) {
    private val providers: Map<ProviderId, CatalogProvider> = providers.associateBy { it.id }

    fun search(libraries: List<Library>, query: BookQuery): Flow<ServiceUpdate> = channelFlow {
        val gate = Semaphore(maxConcurrent)
        val jobs = libraries.flatMap { lib -> lib.services.map { lib to it } }
            .filter { (_, ref) -> ref.provider in providers }
        jobs.forEach { (lib, ref) -> send(ServiceUpdate(lib.id, ref, ServiceState.Loading)) }
        jobs.forEach { (lib, ref) ->
            launch {
                val state = gate.withPermit { searchOne(ref, query) }
                send(ServiceUpdate(lib.id, ref, state))
            }
        }
    }

    suspend fun searchOne(ref: LibraryRef, query: BookQuery): ServiceState {
        val provider = providers[ref.provider]
            ?: return ServiceState.Failed(ProviderException.Kind.NOT_FOUND, "No provider for ${ref.provider}")
        return try {
            ServiceState.Done(matcher.match(query, provider.search(ref, query)))
        } catch (e: CancellationException) {
            throw e
        } catch (e: ProviderException) {
            ServiceState.Failed(e.kind, e.message)
        } catch (e: Exception) {
            ServiceState.Failed(ProviderException.Kind.NETWORK, e.message)
        }
    }

    fun borrowLink(ref: LibraryRef, matched: MatchedHolding) =
        providers.getValue(ref.provider).borrowLink(ref, matched.holding)
}
