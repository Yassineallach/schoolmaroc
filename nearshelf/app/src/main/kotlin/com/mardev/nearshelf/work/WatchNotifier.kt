package com.mardev.nearshelf.work

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.mardev.nearshelf.MainActivity
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.watch.WatchEvent
import com.mardev.nearshelf.data.WatchItem
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

/** Watchlist notifications. No ads, no tracking: just the news, opening the book's results. */
@Singleton
class WatchNotifier @Inject constructor(@ApplicationContext private val context: Context) {

    fun ensureChannel() {
        val channel = NotificationChannel(CHANNEL, context.getString(R.string.notif_channel_name), NotificationManager.IMPORTANCE_DEFAULT)
            .apply { description = context.getString(R.string.notif_channel_description) }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
    }

    fun notify(item: WatchItem, event: WatchEvent) {
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) return
        ensureChannel()
        val text = when (event) {
            is WatchEvent.NowAvailable -> context.getString(R.string.notif_now_available, event.libraryName, event.service)
            is WatchEvent.OnShelf -> context.getString(R.string.notif_on_shelf, event.branch, event.libraryName)
            is WatchEvent.WaitDropped -> context.resources.getQuantityString(R.plurals.notif_wait_dropped, event.days, event.days, event.libraryName)
        }
        val open = Intent(context, MainActivity::class.java)
            .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
            .putExtra(MainActivity.EXTRA_WATCH_KEY, item.key)
        val pi = PendingIntent.getActivity(context, item.key.hashCode(), open, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)
        val n = NotificationCompat.Builder(context, CHANNEL)
            .setSmallIcon(R.drawable.ic_books)
            .setContentTitle(item.title)
            .setContentText(text)
            .setStyle(NotificationCompat.BigTextStyle().bigText(text))
            .setContentIntent(pi)
            .setAutoCancel(true)
            .setCategory(NotificationCompat.CATEGORY_RECOMMENDATION)
            .build()
        NotificationManagerCompat.from(context).notify("${item.key}|${event.libraryName}|${event::class.simpleName}".hashCode(), n)
    }

    companion object {
        const val CHANNEL = "watchlist"
    }
}
