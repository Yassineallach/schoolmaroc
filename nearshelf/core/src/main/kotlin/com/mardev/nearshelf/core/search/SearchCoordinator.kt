package com.mardev.nearshelf.core.search

import com.mardev.nearshelf.core.cache.CacheTtl
import com.mardev.nearshelf.core.cache.KeyValueCache
import com.mardev.nearshelf.core.match.BookMatcher
import com.mardev.nearshelf.core.net.ProviderHealth
import kotlinx.serialization.json.Json
import com.mardev.nearshelf.core.match.BranchNames
import com.mardev.nearshelf.core.model.Holding
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

    /**
     * [fetchedAt] is when the catalog answered (epoch millis); [stale] means the catalog
     * couldn't be reached now and this is the last answer we have.
     */
    data class Done(val matches: List<MatchedHolding>, val fetchedAt: Long = 0, val stale: Boolean = false) : ServiceState
    data class Failed(val kind: ProviderException.Kind, val message: String?) : ServiceState

    /** Failed several times in a row; skipped for a while so other catalogs stay fast. */
    data object TemporarilyUnavailable : ServiceState
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
    private val cache: KeyValueCache? = null,
    private val health: ProviderHealth = ProviderHealth(),
    private val clock: () -> Long = System::currentTimeMillis,
) {
    private val json = Json { ignoreUnknownKeys = true }

    private val providers: Map<ProviderId, CatalogProvider> = providers.associateBy { it.id }

    fun search(libraries: List<Library>, query: BookQuery, forceRefresh: Boolean = false): Flow<ServiceUpdate> = channelFlow {
        val gate = Semaphore(maxConcurrent)
        val jobs = libraries.flatMap { lib -> lib.services.map { lib to it } }
            .filter { (_, ref) -> ref.provider in providers }
        jobs.forEach { (lib, ref) -> send(ServiceUpdate(lib.id, ref, ServiceState.Loading)) }
        jobs.forEach { (lib, ref) ->
            launch {
                val state = gate.withPermit { searchOne(ref, query, lib, forceRefresh) }
                send(ServiceUpdate(lib.id, ref, state))
            }
        }
    }

    /**
     * One catalog. A cached answer younger than 6 hours is used unless [forceRefresh];
     * if the catalog fails, an older cached answer is shown as stale rather than an error.
     */
    suspend fun searchOne(ref: LibraryRef, query: BookQuery, library: Library? = null, forceRefresh: Boolean = false): ServiceState {
        val provider = providers[ref.provider]
            ?: return ServiceState.Failed(ProviderException.Kind.NOT_FOUND, "No provider for ${ref.provider}")
        val key = cacheKey(ref, query)
        val cached = cache?.get(key)?.let { (value, at) ->
            runCatching { json.decodeFromString<List<Holding>>(value) }.getOrNull()?.let { it to at }
        }
        fun done(holdings: List<Holding>, at: Long, stale: Boolean) =
            ServiceState.Done(matcher.match(query, holdings.map { h -> library?.let { withBranchLocations(h, it) } ?: h }), at, stale)

        if (cached != null && !forceRefresh && clock() - cached.second < CacheTtl.SEARCH_MILLIS) return done(cached.first, cached.second, false)
        if (forceRefresh) health.reset(ref.provider, ref.key)
        if (health.isDown(ref.provider, ref.key)) {
            return cached?.let { done(it.first, it.second, true) } ?: ServiceState.TemporarilyUnavailable
        }
        return try {
            val holdings = provider.search(ref, query)
            health.recordSuccess(ref.provider, ref.key)
            cache?.put(key, json.encodeToString(holdings))
            done(holdings, clock(), false)
        } catch (e: CancellationException) {
            throw e
        } catch (e: ProviderException) {
            health.recordFailure(ref.provider, ref.key, e.kind)
            if (e.kind != ProviderException.Kind.BLOCKED && cached != null) done(cached.first, cached.second, true)
            else ServiceState.Failed(e.kind, e.message)
        } catch (e: Exception) {
            health.recordFailure(ref.provider, ref.key, ProviderException.Kind.NETWORK)
            cached?.let { done(it.first, it.second, true) } ?: ServiceState.Failed(ProviderException.Kind.NETWORK, e.message)
        }
    }

    /** The query as the catalog sees it; Open Library's ISBN set is part of matching, not of the key. */
    private fun cacheKey(ref: LibraryRef, q: BookQuery) =
        "search|${ref.provider}|${ref.key}|" + listOf(q.title, q.author, q.isbn).joinToString("|") { it?.trim()?.lowercase().orEmpty() }

    fun borrowLink(ref: LibraryRef, matched: MatchedHolding) =
        providers.getValue(ref.provider).borrowLink(ref, matched.holding)

    fun searchLink(ref: LibraryRef, query: BookQuery) = providers[ref.provider]?.searchLink(ref, query)

    /** Catalog copies name their branch; the registry knows where it is. */
    private fun withBranchLocations(h: Holding, library: Library): Holding {
        if (h.copies.isEmpty() || library.branches.isEmpty()) return h
        return h.copy(copies = h.copies.map { c ->
            if (c.latitude != null) return@map c
            val b = library.branches.firstOrNull { BranchNames.matches(it.name, c.branchName) } ?: return@map c
            c.copy(latitude = b.latitude, longitude = b.longitude)
        })
    }
}
