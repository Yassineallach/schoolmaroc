package com.mardev.aleatro.pgs;

import android.app.Activity;
import android.util.Log;

import androidx.annotation.NonNull;

import com.android.billingclient.api.AcknowledgePurchaseParams;
import com.android.billingclient.api.BillingClient;
import com.android.billingclient.api.BillingClientStateListener;
import com.android.billingclient.api.BillingFlowParams;
import com.android.billingclient.api.BillingResult;
import com.android.billingclient.api.PendingPurchasesParams;
import com.android.billingclient.api.ProductDetails;
import com.android.billingclient.api.Purchase;
import com.android.billingclient.api.QueryProductDetailsParams;
import com.android.billingclient.api.QueryPurchasesParams;
import com.google.android.gms.ads.AdError;
import com.google.android.gms.ads.AdRequest;
import com.google.android.gms.ads.FullScreenContentCallback;
import com.google.android.gms.ads.LoadAdError;
import com.google.android.gms.ads.MobileAds;
import com.google.android.gms.ads.interstitial.InterstitialAd;
import com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback;
import com.google.android.gms.ads.rewarded.RewardedAd;
import com.google.android.gms.ads.rewarded.RewardedAdLoadCallback;
import com.google.android.ump.ConsentInformation;
import com.google.android.ump.ConsentRequestParameters;
import com.google.android.ump.UserMessagingPlatform;

import org.godotengine.godot.Godot;
import org.godotengine.godot.plugin.GodotPlugin;
import org.godotengine.godot.plugin.SignalInfo;
import org.godotengine.godot.plugin.UsedByGodot;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * AdMob (interstitial and rewarded), Google's UMP consent form, and Play
 * Billing for the one-time "remove ads" purchase. Reached from GDScript as
 * Engine.get_singleton("AleatroAds"); every call returns at once and results
 * come back as signals. Ad units are passed in from GDScript (res://ads/ads.cfg);
 * the AdMob app ID goes into the manifest at export (addons/aleatro_pgs).
 */
public class AleatroAds extends GodotPlugin {
    private static final String TAG = "AleatroAds";

    private static final SignalInfo CONSENT = new SignalInfo("consent_finished", Boolean.class, Boolean.class);
    private static final SignalInfo READY = new SignalInfo("ads_ready");
    private static final SignalInfo LOADED = new SignalInfo("ad_loaded", String.class);
    private static final SignalInfo FAILED = new SignalInfo("ad_failed", String.class, String.class);
    private static final SignalInfo CLOSED = new SignalInfo("ad_closed", String.class);
    private static final SignalInfo REWARD = new SignalInfo("reward_earned", String.class);
    private static final SignalInfo PAID = new SignalInfo("ad_paid", String.class, Double.class, String.class);
    private static final SignalInfo OWNED = new SignalInfo("owned", String.class);
    private static final SignalInfo PRICE = new SignalInfo("price", String.class, String.class);
    private static final SignalInfo BOUGHT = new SignalInfo("purchase_done", String.class);
    private static final SignalInfo BUY_FAILED = new SignalInfo("purchase_failed", String.class, String.class);

    private final Map<String, InterstitialAd> interstitials = new HashMap<>();
    private final Map<String, RewardedAd> rewardeds = new HashMap<>();
    private final Set<String> loading = new HashSet<>();
    private ConsentInformation consent;
    private boolean adsStarted = false;
    private BillingClient billing;

    public AleatroAds(Godot godot) {
        super(godot);
    }

    @NonNull
    @Override
    public String getPluginName() {
        return "AleatroAds";
    }

    @NonNull
    @Override
    public Set<SignalInfo> getPluginSignals() {
        Set<SignalInfo> s = new HashSet<>();
        Collections.addAll(s, CONSENT, READY, LOADED, FAILED, CLOSED, REWARD, PAID, OWNED, PRICE, BOUGHT, BUY_FAILED);
        return s;
    }

    // ------------------------------------------------------------ consent + start

    /** Asks for consent where the law needs it (UMP), then starts the Ads SDK. */
    @UsedByGodot
    public void start() {
        Activity a = getActivity();
        if (a == null) return;
        a.runOnUiThread(() -> {
            consent = UserMessagingPlatform.getConsentInformation(a);
            ConsentRequestParameters params = new ConsentRequestParameters.Builder().build();
            consent.requestConsentInfoUpdate(a, params,
                    () -> UserMessagingPlatform.loadAndShowConsentFormIfRequired(a, err -> {
                        if (err != null) Log.w(TAG, "consent form: " + err.getMessage());
                        afterConsent();
                    }),
                    err -> {
                        Log.w(TAG, "consent info: " + err.getMessage());
                        afterConsent();
                    });
            // a returning player who already answered can start straight away
            if (consent.canRequestAds()) afterConsent();
        });
    }

    private void afterConsent() {
        boolean can = consent != null && consent.canRequestAds();
        boolean privacy = consent != null && consent.getPrivacyOptionsRequirementStatus()
                == ConsentInformation.PrivacyOptionsRequirementStatus.REQUIRED;
        emitSignal(CONSENT.getName(), can, privacy);
        if (can && !adsStarted) {
            adsStarted = true;
            Activity a = getActivity();
            if (a == null) return;
            new Thread(() -> MobileAds.initialize(a, status -> emitSignal(READY.getName()))).start();
        }
    }

    /** The "Privacy choices" form, for players who want to change their consent. */
    @UsedByGodot
    public void show_privacy_options() {
        Activity a = getActivity();
        if (a == null) return;
        a.runOnUiThread(() -> UserMessagingPlatform.showPrivacyOptionsForm(a, err -> afterConsent()));
    }

    // ------------------------------------------------------------ ads

    @UsedByGodot
    public void load_interstitial(String unit) {
        Activity a = getActivity();
        if (a == null || !adsStarted || interstitials.containsKey(unit) || !loading.add(unit)) return;
        a.runOnUiThread(() -> InterstitialAd.load(a, unit, new AdRequest.Builder().build(), new InterstitialAdLoadCallback() {
            @Override
            public void onAdLoaded(@NonNull InterstitialAd ad) {
                loading.remove(unit);
                ad.setOnPaidEventListener(v -> emitSignal(PAID.getName(), unit, v.getValueMicros() / 1e6, v.getCurrencyCode()));
                interstitials.put(unit, ad);
                emitSignal(LOADED.getName(), unit);
            }

            @Override
            public void onAdFailedToLoad(@NonNull LoadAdError e) {
                loading.remove(unit);
                emitSignal(FAILED.getName(), unit, "load: " + e.getMessage());
            }
        }));
    }

    @UsedByGodot
    public void load_rewarded(String unit) {
        Activity a = getActivity();
        if (a == null || !adsStarted || rewardeds.containsKey(unit) || !loading.add(unit)) return;
        a.runOnUiThread(() -> RewardedAd.load(a, unit, new AdRequest.Builder().build(), new RewardedAdLoadCallback() {
            @Override
            public void onAdLoaded(@NonNull RewardedAd ad) {
                loading.remove(unit);
                ad.setOnPaidEventListener(v -> emitSignal(PAID.getName(), unit, v.getValueMicros() / 1e6, v.getCurrencyCode()));
                rewardeds.put(unit, ad);
                emitSignal(LOADED.getName(), unit);
            }

            @Override
            public void onAdFailedToLoad(@NonNull LoadAdError e) {
                loading.remove(unit);
                emitSignal(FAILED.getName(), unit, "load: " + e.getMessage());
            }
        }));
    }

    @UsedByGodot
    public boolean is_loaded(String unit) {
        return interstitials.containsKey(unit) || rewardeds.containsKey(unit);
    }

    @UsedByGodot
    public void show_interstitial(String unit) {
        Activity a = getActivity();
        InterstitialAd ad = interstitials.remove(unit);
        if (a == null || ad == null) {
            emitSignal(FAILED.getName(), unit, "show: not loaded");
            return;
        }
        ad.setFullScreenContentCallback(closer(unit));
        a.runOnUiThread(() -> ad.show(a));
    }

    @UsedByGodot
    public void show_rewarded(String unit) {
        Activity a = getActivity();
        RewardedAd ad = rewardeds.remove(unit);
        if (a == null || ad == null) {
            emitSignal(FAILED.getName(), unit, "show: not loaded");
            return;
        }
        ad.setFullScreenContentCallback(closer(unit));
        a.runOnUiThread(() -> ad.show(a, item -> emitSignal(REWARD.getName(), unit)));
    }

    private FullScreenContentCallback closer(String unit) {
        return new FullScreenContentCallback() {
            @Override
            public void onAdDismissedFullScreenContent() {
                emitSignal(CLOSED.getName(), unit);
            }

            @Override
            public void onAdFailedToShowFullScreenContent(@NonNull AdError e) {
                emitSignal(FAILED.getName(), unit, "show: " + e.getMessage());
            }
        };
    }

    // ------------------------------------------------------------ billing

    /** Connects to Play Billing, reports what is already owned and the product's price. */
    @UsedByGodot
    public void start_billing(String sku) {
        Activity a = getActivity();
        if (a == null || billing != null) return;
        billing = BillingClient.newBuilder(a)
                .setListener(this::onPurchases)
                .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().build())
                .build();
        billing.startConnection(new BillingClientStateListener() {
            @Override
            public void onBillingSetupFinished(@NonNull BillingResult r) {
                if (r.getResponseCode() != BillingClient.BillingResponseCode.OK) return;
                refresh_owned();
                withProduct(sku, d -> {
                    ProductDetails.OneTimePurchaseOfferDetails o = d.getOneTimePurchaseOfferDetails();
                    if (o != null) emitSignal(PRICE.getName(), sku, o.getFormattedPrice());
                });
            }

            @Override
            public void onBillingServiceDisconnected() {
                billing = null;  // reconnects on the next start_billing
            }
        });
    }

    @UsedByGodot
    public void refresh_owned() {
        if (billing == null) return;
        billing.queryPurchasesAsync(QueryPurchasesParams.newBuilder()
                .setProductType(BillingClient.ProductType.INAPP).build(), (r, list) -> {
            List<String> owned = new ArrayList<>();
            for (Purchase p : list) {
                if (p.getPurchaseState() != Purchase.PurchaseState.PURCHASED) continue;
                acknowledge(p);
                owned.addAll(p.getProducts());
            }
            emitSignal(OWNED.getName(), String.join(",", owned));
        });
    }

    @UsedByGodot
    public void purchase(String sku) {
        Activity a = getActivity();
        if (a == null || billing == null) {
            emitSignal(BUY_FAILED.getName(), sku, "billing unavailable");
            return;
        }
        withProduct(sku, d -> {
            BillingFlowParams flow = BillingFlowParams.newBuilder()
                    .setProductDetailsParamsList(Collections.singletonList(
                            BillingFlowParams.ProductDetailsParams.newBuilder().setProductDetails(d).build()))
                    .build();
            a.runOnUiThread(() -> billing.launchBillingFlow(a, flow));
        });
    }

    private interface DetailsCallback {
        void on(ProductDetails d);
    }

    private void withProduct(String sku, DetailsCallback cb) {
        QueryProductDetailsParams params = QueryProductDetailsParams.newBuilder()
                .setProductList(Collections.singletonList(QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(sku).setProductType(BillingClient.ProductType.INAPP).build()))
                .build();
        billing.queryProductDetailsAsync(params, (r, result) -> {
            List<ProductDetails> list = result.getProductDetailsList();
            if (r.getResponseCode() == BillingClient.BillingResponseCode.OK && !list.isEmpty()) {
                cb.on(list.get(0));
            } else {
                emitSignal(BUY_FAILED.getName(), sku, "product not found: " + r.getDebugMessage());
            }
        });
    }

    private void onPurchases(@NonNull BillingResult r, List<Purchase> purchases) {
        int code = r.getResponseCode();
        if (code == BillingClient.BillingResponseCode.OK && purchases != null) {
            for (Purchase p : purchases) {
                if (p.getPurchaseState() != Purchase.PurchaseState.PURCHASED) continue;
                acknowledge(p);
                for (String sku : p.getProducts()) emitSignal(BOUGHT.getName(), sku);
            }
        } else if (code == BillingClient.BillingResponseCode.ITEM_ALREADY_OWNED) {
            refresh_owned();
        } else {
            emitSignal(BUY_FAILED.getName(), "", code == BillingClient.BillingResponseCode.USER_CANCELED
                    ? "cancelled" : r.getDebugMessage());
        }
    }

    private void acknowledge(Purchase p) {
        if (p.isAcknowledged() || billing == null) return;
        billing.acknowledgePurchase(AcknowledgePurchaseParams.newBuilder()
                .setPurchaseToken(p.getPurchaseToken()).build(), r -> { });
    }
}
