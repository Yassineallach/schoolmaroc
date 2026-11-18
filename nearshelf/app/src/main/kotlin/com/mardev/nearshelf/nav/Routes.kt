package com.mardev.nearshelf.nav

import kotlinx.serialization.Serializable

@Serializable data object HomeRoute
@Serializable data object LibrariesRoute
@Serializable data object AddLibraryRoute
@Serializable data object ScannerRoute

@Serializable
data class ResultsRoute(
    val title: String? = null,
    val author: String? = null,
    val isbn: String? = null,
    /** Raw text from the share sheet; parsed on the Results screen. */
    val shared: String? = null,
)
