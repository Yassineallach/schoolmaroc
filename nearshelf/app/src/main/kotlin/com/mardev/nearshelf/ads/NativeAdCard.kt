package com.mardev.nearshelf.ads

import android.view.LayoutInflater
import android.view.View
import android.widget.Button
import android.widget.ImageView
import android.widget.TextView
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.google.android.gms.ads.AdListener
import com.google.android.gms.ads.AdLoader
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.nativead.MediaView
import com.google.android.gms.ads.nativead.NativeAd
import com.google.android.gms.ads.nativead.NativeAdOptions
import com.google.android.gms.ads.nativead.NativeAdView
import com.mardev.nearshelf.BuildConfig
import com.mardev.nearshelf.R
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class AdsViewModel @Inject constructor(consent: ConsentManager) : ViewModel() {
    val canShowAds = consent.canShowAds
}

/**
 * One native ad, laid out inside the content like Nearshelf's own cards. Renders
 * nothing until an ad has loaded, and nothing at all without consent or on failure,
 * so it never leaves an empty gap. The SDK handles clicks; no custom click handlers.
 */
@Composable
fun NativeAdCard(modifier: Modifier = Modifier, ads: AdsViewModel = hiltViewModel()) {
    val allowed by ads.canShowAds.collectAsStateWithLifecycle()
    if (!allowed) return
    val context = LocalContext.current
    var ad by remember { mutableStateOf<NativeAd?>(null) }

    DisposableEffect(Unit) {
        var disposed = false
        val loader = AdLoader.Builder(context, BuildConfig.ADMOB_NATIVE_UNIT)
            .forNativeAd { loaded -> if (disposed) loaded.destroy() else ad = loaded }
            .withAdListener(object : AdListener() {
                override fun onAdFailedToLoad(error: LoadAdError) { ad = null }
            })
            .withNativeAdOptions(
                NativeAdOptions.Builder()
                    .setAdChoicesPlacement(NativeAdOptions.ADCHOICES_TOP_RIGHT)
                    .setMediaAspectRatio(NativeAdOptions.NATIVE_MEDIA_ASPECT_RATIO_LANDSCAPE)
                    .build(),
            )
            .build()
        loader.loadAd(AdRequest.Builder().build())
        onDispose {
            disposed = true
            ad?.destroy()
            ad = null
        }
    }

    val current = ad ?: return
    AndroidView(
        modifier = modifier.fillMaxWidth(),
        factory = { ctx -> LayoutInflater.from(ctx).inflate(R.layout.native_ad_card, null) as NativeAdView },
        update = { view -> bind(view, current) },
    )
}

private fun bind(view: NativeAdView, ad: NativeAd) {
    val headline = view.findViewById<TextView>(R.id.ad_headline)
    val body = view.findViewById<TextView>(R.id.ad_body)
    val icon = view.findViewById<ImageView>(R.id.ad_icon)
    val advertiser = view.findViewById<TextView>(R.id.ad_advertiser)
    val cta = view.findViewById<Button>(R.id.ad_call_to_action)
    val media = view.findViewById<MediaView>(R.id.ad_media)

    headline.text = ad.headline
    view.headlineView = headline
    view.mediaView = media // set before setNativeAd, per Google's guide
    ad.mediaContent?.let { media.mediaContent = it }
    media.visibility = if (ad.mediaContent != null) View.VISIBLE else View.GONE

    body.text = ad.body
    body.visibility = if (ad.body.isNullOrBlank()) View.GONE else View.VISIBLE
    view.bodyView = body

    ad.icon?.drawable?.let { icon.setImageDrawable(it) }
    icon.visibility = if (ad.icon == null) View.GONE else View.VISIBLE
    view.iconView = icon

    advertiser.text = ad.advertiser
    advertiser.visibility = if (ad.advertiser.isNullOrBlank()) View.GONE else View.VISIBLE
    view.advertiserView = advertiser

    cta.text = ad.callToAction
    cta.visibility = if (ad.callToAction.isNullOrBlank()) View.GONE else View.VISIBLE
    view.callToActionView = cta

    view.setNativeAd(ad)
}
