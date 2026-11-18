package com.mardev.nearshelf.widget

import android.content.Context
import android.content.Intent
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.glance.GlanceId
import androidx.glance.GlanceModifier
import androidx.glance.GlanceTheme
import androidx.glance.action.clickable
import androidx.glance.appwidget.GlanceAppWidget
import androidx.glance.appwidget.GlanceAppWidgetReceiver
import androidx.glance.appwidget.action.actionStartActivity
import androidx.glance.appwidget.cornerRadius
import androidx.glance.appwidget.lazy.LazyColumn
import androidx.glance.appwidget.lazy.items
import androidx.glance.appwidget.provideContent
import androidx.glance.appwidget.updateAll
import androidx.glance.background
import androidx.glance.layout.Column
import androidx.glance.layout.Spacer
import androidx.glance.layout.fillMaxSize
import androidx.glance.layout.fillMaxWidth
import androidx.glance.layout.height
import androidx.glance.layout.padding
import androidx.glance.material3.ColorProviders
import androidx.glance.text.FontWeight
import androidx.glance.text.Text
import androidx.glance.text.TextStyle
import com.mardev.nearshelf.MainActivity
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.watch.Watch
import com.mardev.nearshelf.data.WatchlistRepository
import com.mardev.nearshelf.ui.theme.Dark
import com.mardev.nearshelf.ui.theme.Light
import dagger.hilt.EntryPoint
import dagger.hilt.InstallIn
import dagger.hilt.android.EntryPointAccessors
import dagger.hilt.components.SingletonComponent
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

@EntryPoint
@InstallIn(SingletonComponent::class)
interface WidgetEntryPoint {
    fun watchlist(): WatchlistRepository
}

private data class Row(val key: String, val title: String, val status: String, val good: Boolean)

/** Home-screen widget: the watchlist at a glance, read from the local database (works offline). */
class WatchlistWidget : GlanceAppWidget() {
    override suspend fun provideGlance(context: Context, id: GlanceId) {
        val items = EntryPointAccessors.fromApplication(context, WidgetEntryPoint::class.java).watchlist().all().take(5)
        val rows = items.map { item ->
            val status = Watch.status(item.snapshot)
            Row(
                item.key,
                item.title,
                when (status) {
                    is Watch.Status.Available -> context.getString(R.string.watch_status_available, status.service, status.library)
                    is Watch.Status.OnShelf -> context.getString(R.string.watch_status_on_shelf, status.branch)
                    is Watch.Status.Waiting -> context.resources.getQuantityString(R.plurals.watch_status_waiting, status.days, status.days, status.library)
                    Watch.Status.NotYet -> context.getString(R.string.watch_status_not_yet)
                    null -> context.getString(R.string.watchlist_not_checked)
                },
                status is Watch.Status.Available || status is Watch.Status.OnShelf,
            )
        }
        provideContent {
            GlanceTheme(colors = ColorProviders(light = Light, dark = Dark)) { Content(context, rows) }
        }
    }

    @Composable
    private fun Content(context: Context, rows: List<Row>) {
        val openApp = actionStartActivity(Intent(context, MainActivity::class.java))
        Column(
            GlanceModifier.fillMaxSize().background(GlanceTheme.colors.surface).cornerRadius(20.dp).padding(14.dp),
        ) {
            Text(
                context.getString(R.string.widget_title),
                style = TextStyle(color = GlanceTheme.colors.primary, fontWeight = FontWeight.Bold, fontSize = 16.sp),
                modifier = GlanceModifier.clickable(openApp),
            )
            Spacer(GlanceModifier.height(6.dp))
            if (rows.isEmpty()) {
                Text(
                    context.getString(R.string.widget_empty),
                    style = TextStyle(color = GlanceTheme.colors.onSurfaceVariant, fontSize = 14.sp),
                    modifier = GlanceModifier.clickable(openApp),
                )
            } else {
                LazyColumn {
                    items(rows, itemId = { it.key.hashCode().toLong() }) { r ->
                        val open = actionStartActivity(
                            Intent(context, MainActivity::class.java)
                                .setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
                                .putExtra(MainActivity.EXTRA_WATCH_KEY, r.key),
                        )
                        Column(GlanceModifier.fillMaxWidth().padding(vertical = 5.dp).clickable(open)) {
                            Text(r.title, maxLines = 1, style = TextStyle(color = GlanceTheme.colors.onSurface, fontWeight = FontWeight.Medium, fontSize = 15.sp))
                            Text(
                                r.status,
                                maxLines = 1,
                                style = TextStyle(color = if (r.good) GlanceTheme.colors.tertiary else GlanceTheme.colors.onSurfaceVariant, fontSize = 13.sp),
                            )
                        }
                    }
                }
            }
        }
    }

    companion object {
        private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

        /** Redraw every placed widget (after a check, or when the watchlist changes). */
        fun refresh(context: Context) {
            scope.launch { runCatching { WatchlistWidget().updateAll(context.applicationContext) } }
        }
    }
}

class WatchlistWidgetReceiver : GlanceAppWidgetReceiver() {
    override val glanceAppWidget: GlanceAppWidget = WatchlistWidget()
}
