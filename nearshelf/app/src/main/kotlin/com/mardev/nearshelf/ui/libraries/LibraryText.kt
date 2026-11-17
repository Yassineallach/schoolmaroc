package com.mardev.nearshelf.ui.libraries

import androidx.compose.runtime.Composable
import androidx.compose.ui.res.stringResource
import com.mardev.nearshelf.R
import com.mardev.nearshelf.core.model.Library

/** "Toronto, ON, CA" */
fun Library.locationLine(): String = listOfNotNull(city, region, countryCode).joinToString(", ")

/** "Digital: Libby · Physical catalog: BiblioCommons" */
@Composable
fun Library.servicesLine(): String {
    val digital = digitalServices.map { it.provider.displayName }.distinct()
    val physical = physicalServices.map { it.provider.displayName }.distinct()
    val parts = buildList {
        if (digital.isNotEmpty()) add(stringResource(R.string.services_digital, digital.joinToString(", ")))
        if (physical.isNotEmpty()) add(stringResource(R.string.services_physical, physical.joinToString(", ")))
    }
    return parts.joinToString(" · ")
}
