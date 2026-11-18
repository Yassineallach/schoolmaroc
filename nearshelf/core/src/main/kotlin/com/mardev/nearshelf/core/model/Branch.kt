package com.mardev.nearshelf.core.model

import kotlinx.serialization.Serializable

/** A physical branch, for the home-branch picker and (milestone 8) distance sorting. */
@Serializable
data class Branch(
    val id: String,
    val name: String,
    val address: String? = null,
    val city: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
)
