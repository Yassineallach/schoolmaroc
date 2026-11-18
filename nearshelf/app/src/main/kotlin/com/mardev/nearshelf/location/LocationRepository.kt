package com.mardev.nearshelf.location

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import com.mardev.nearshelf.core.geo.LatLng
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withTimeoutOrNull
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Coarse location, used on the device only to sort branches by distance. It is never
 * sent anywhere: no catalog query includes it.
 */
@Singleton
class LocationRepository @Inject constructor(@ApplicationContext private val context: Context) {

    fun hasPermission() =
        ContextCompat.checkSelfPermission(context, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED

    @SuppressLint("MissingPermission")
    suspend fun current(): LatLng? {
        if (!hasPermission()) return null
        val client = LocationServices.getFusedLocationProviderClient(context)
        return runCatching {
            val last = client.lastLocation.await()
            val loc = last ?: withTimeoutOrNull(8_000) {
                client.getCurrentLocation(Priority.PRIORITY_BALANCED_POWER_ACCURACY, CancellationTokenSource().token).await()
            }
            loc?.let { LatLng(it.latitude, it.longitude) }
        }.getOrNull()
    }
}
