package com.mardev.nearshelf.work

import android.content.Context
import androidx.hilt.work.HiltWorker
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.mardev.nearshelf.core.metadata.QueryExpander
import com.mardev.nearshelf.core.search.SearchCoordinator
import com.mardev.nearshelf.core.search.ServiceState
import com.mardev.nearshelf.core.watch.Watch
import com.mardev.nearshelf.data.LibraryRepository
import com.mardev.nearshelf.data.WatchlistRepository
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.toList
import java.util.concurrent.TimeUnit

/**
 * Checks every watched book at every library, at most once a day, on a network
 * connection. Books are checked one after another (politeness); notifications go out
 * only for news since the previous check. Retries with exponential backoff when
 * nothing could be reached (offline, rate limits).
 */
@HiltWorker
class WatchlistWorker @AssistedInject constructor(
    @Assisted context: Context,
    @Assisted params: WorkerParameters,
    private val watchlist: WatchlistRepository,
    private val libraries: LibraryRepository,
    private val expander: QueryExpander,
    private val coordinator: SearchCoordinator,
    private val notifier: WatchNotifier,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val items = watchlist.all()
        val libs = libraries.libraries.first()
        if (items.isEmpty() || libs.isEmpty()) return Result.success()
        var reachedAny = false
        for (item in items) {
            val query = expander.expand(item.query).query
            val updates = coordinator.search(libs, query, forceRefresh = true).toList()
                .filter { it.state !is ServiceState.Loading }
            if (updates.any { it.state is ServiceState.Done && !(it.state as ServiceState.Done).stale }) reachedAny = true
            val byLibrary = libs.map { lib ->
                lib to updates.filter { it.libraryId == lib.id }.map { it.service.provider.displayName to it.state }
            }
            val snapshot = Watch.snapshot(System.currentTimeMillis(), byLibrary)
            Watch.events(item.snapshot, snapshot).forEach { notifier.notify(item, it) }
            watchlist.saveCheck(item, snapshot)
        }
        return if (reachedAny) Result.success() else Result.retry()
    }

    companion object {
        private const val PERIODIC = "watchlist-daily"
        private const val NOW = "watchlist-now"
        private val network = Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()

        fun schedule(context: Context) {
            val request = PeriodicWorkRequestBuilder<WatchlistWorker>(24, TimeUnit.HOURS)
                .setConstraints(network)
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.MINUTES)
                .setInitialDelay(1, TimeUnit.HOURS)
                .build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(PERIODIC, ExistingPeriodicWorkPolicy.KEEP, request)
        }

        fun checkNow(context: Context) {
            val request = OneTimeWorkRequestBuilder<WatchlistWorker>().setConstraints(network)
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.MINUTES).build()
            WorkManager.getInstance(context).enqueueUniqueWork(NOW, ExistingWorkPolicy.KEEP, request)
        }

        fun cancel(context: Context) = WorkManager.getInstance(context).cancelUniqueWork(PERIODIC)
    }
}
