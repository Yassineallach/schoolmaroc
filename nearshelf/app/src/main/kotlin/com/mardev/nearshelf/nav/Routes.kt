package com.mardev.nearshelf.nav

import kotlinx.serialization.Serializable

@Serializable data object HomeRoute
@Serializable data object LibrariesRoute
@Serializable data object AddLibraryRoute
@Serializable data object ScannerRoute
@Serializable data object WatchlistRoute
@Serializable data object HistoryRoute
@Serializable data object PreferencesRoute
@Serializable data object SettingsRoute
@Serializable data object AboutRoute
@Serializable data object PrivacyRoute
@Serializable data object LicencesRoute

@Serializable
data class ResultsRoute(
    val title: String? = null,
    val author: String? = null,
    val isbn: String? = null,
    /** Raw text from the share sheet; parsed on the Results screen. */
    val shared: String? = null,
    /** Opened from the watchlist or a notification. */
    val watchKey: String? = null,
    /** Opened from history: the stored, already-expanded query as JSON. */
    val queryJson: String? = null,
)
