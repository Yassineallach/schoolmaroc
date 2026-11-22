package com.printscale.ai.data

import android.content.Context
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

enum class ThemeChoice { SYSTEM, DARK, LIGHT }

class SettingsRepository(context: Context) {
    private val prefs = context.getSharedPreferences("settings", Context.MODE_PRIVATE)
    private val _theme = MutableStateFlow(
        runCatching { ThemeChoice.valueOf(prefs.getString("theme", ThemeChoice.DARK.name)!!) }.getOrDefault(ThemeChoice.DARK),
    )
    /** Dark by default: a neutral dark surround is the usual setting for judging artwork colour. */
    val theme: StateFlow<ThemeChoice> = _theme

    private val _cloudLink = MutableStateFlow(prefs.getString("cloud_link", null))
    /** The server link from the notebook, as text (see CloudLink.parse). Null when not connected. */
    val cloudLink: StateFlow<String?> = _cloudLink

    fun setCloudLink(link: String?) {
        prefs.edit().apply { if (link == null) remove("cloud_link") else putString("cloud_link", link) }.apply()
        _cloudLink.value = link
    }

    fun setTheme(t: ThemeChoice) {
        prefs.edit().putString("theme", t.name).apply()
        _theme.value = t
    }
}
