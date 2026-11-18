package com.mardev.nearshelf.core.net

import com.mardev.nearshelf.core.model.ProviderId
import com.mardev.nearshelf.core.provider.ProviderException

/**
 * Tracks failures per catalog (provider + library key). After [failureLimit] failures in
 * a row the catalog is "temporarily unavailable" for [coolDownMillis] and is skipped,
 * so a broken catalog doesn't slow every search; the others keep working.
 * Blocked (bot check) and not-found answers don't count: they aren't outages.
 */
class ProviderHealth(
    private val failureLimit: Int = 3,
    private val coolDownMillis: Long = 15 * 60 * 1000,
    private val clock: () -> Long = System::currentTimeMillis,
) {
    private data class State(val failures: Int = 0, val downUntil: Long = 0)
    private val states = HashMap<Pair<ProviderId, String>, State>()

    @Synchronized
    fun isDown(provider: ProviderId, key: String): Boolean = (states[provider to key]?.downUntil ?: 0) > clock()

    @Synchronized
    fun recordSuccess(provider: ProviderId, key: String) {
        states.remove(provider to key)
    }

    @Synchronized
    fun recordFailure(provider: ProviderId, key: String, kind: ProviderException.Kind) {
        if (kind == ProviderException.Kind.BLOCKED || kind == ProviderException.Kind.NOT_FOUND) return
        val s = states[provider to key] ?: State()
        val failures = s.failures + 1
        states[provider to key] = State(failures, if (failures >= failureLimit) clock() + coolDownMillis else s.downUntil)
    }

    /** User pressed Retry: give the catalog another chance right away. */
    @Synchronized
    fun reset(provider: ProviderId, key: String) {
        states.remove(provider to key)
    }
}
