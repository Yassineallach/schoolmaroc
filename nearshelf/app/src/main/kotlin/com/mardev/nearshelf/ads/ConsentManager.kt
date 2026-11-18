package com.mardev.nearshelf.ads

import android.app.Activity
import android.content.Context
import com.google.android.gms.ads.MobileAds
import com.google.android.ump.ConsentInformation
import com.google.android.ump.ConsentRequestParameters
import com.google.android.ump.UserMessagingPlatform
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.util.concurrent.atomic.AtomicBoolean
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Google's User Messaging Platform: checks consent at every launch, shows the form
 * where the law requires it (EU/UK/Switzerland), and only then lets ads load.
 * Following https://developers.google.com/admob/android/privacy.
 */
@Singleton
class ConsentManager @Inject constructor(@ApplicationContext private val context: Context) {
    private val info: ConsentInformation = UserMessagingPlatform.getConsentInformation(context)
    private val adsStarted = AtomicBoolean(false)
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val _canShowAds = MutableStateFlow(info.canRequestAds())
    val canShowAds: StateFlow<Boolean> = _canShowAds.asStateFlow()

    /** Whether Settings must offer "Privacy options" (users in regulated regions). */
    val privacyOptionsRequired: Boolean
        get() = info.privacyOptionsRequirementStatus == ConsentInformation.PrivacyOptionsRequirementStatus.REQUIRED

    fun gather(activity: Activity) {
        info.requestConsentInfoUpdate(
            activity,
            ConsentRequestParameters.Builder().build(),
            {
                UserMessagingPlatform.loadAndShowConsentFormIfRequired(activity) { startAdsIfAllowed() }
            },
            { startAdsIfAllowed() }, // keep any earlier consent; ads stay off if there is none
        )
        startAdsIfAllowed() // consent from a previous session can be used right away
    }

    fun showPrivacyOptions(activity: Activity) {
        UserMessagingPlatform.showPrivacyOptionsForm(activity) { startAdsIfAllowed() }
    }

    private fun startAdsIfAllowed() {
        val allowed = info.canRequestAds()
        _canShowAds.value = allowed
        if (allowed && adsStarted.compareAndSet(false, true)) {
            scope.launch { MobileAds.initialize(context) {} }
        }
    }
}
