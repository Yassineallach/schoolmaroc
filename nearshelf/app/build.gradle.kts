import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.room)
    alias(libs.plugins.baselineprofile)
}

room {
    schemaDirectory("$projectDir/schemas")
}

// AdMob IDs. The real ones are below; local.properties can override them:
//   admob.appId=…  admob.nativeUnitId=…
//   admob.testAds=true   (release builds show Google's test ads as well)
val localProps = Properties().apply {
    rootProject.file("local.properties").takeIf { it.exists() }?.inputStream()?.use { load(it) }
}
// Google's published test IDs: safe to tap, no revenue.
val testAdmobAppId = "ca-app-pub-3940256099942544~3347511713"
val testAdmobNativeUnit = "ca-app-pub-3940256099942544/2247696110"
// Nearshelf's own AdMob app and native ad unit.
val realAdmobAppId = "ca-app-pub-4106840885730797~7503768574"
val realAdmobNativeUnit = "ca-app-pub-4106840885730797/4354861051"
// Real IDs are used by RELEASE builds only. Debug builds always show test ads, so testing
// on your own phone can never tap your live ads (AdMob suspends accounts for that).
// The on/off switch for test ads in release builds: admob.testAds=true in local.properties.
val forceTestAds = localProps.getProperty("admob.testAds")?.trim().equals("true", ignoreCase = true)
val admobAppId = if (forceTestAds) testAdmobAppId else localProps.getProperty("admob.appId")?.trim()?.takeIf { it.isNotEmpty() } ?: realAdmobAppId
val admobNativeUnit = if (forceTestAds) testAdmobNativeUnit else localProps.getProperty("admob.nativeUnitId")?.trim()?.takeIf { it.isNotEmpty() } ?: realAdmobNativeUnit
// Catch the classic mix-up (unit ID where the app ID goes, or the reverse) at build time.
require(Regex("""ca-app-pub-\d{16}~\d{10}""").matches(admobAppId)) {
    "admob.appId in local.properties should look like ca-app-pub-0000000000000000~0000000000 (with ~), got: $admobAppId"
}
require(Regex("""ca-app-pub-\d{16}/\d{10}""").matches(admobNativeUnit)) {
    "admob.nativeUnitId in local.properties should look like ca-app-pub-0000000000000000/0000000000 (with /), got: $admobNativeUnit"
}
if (admobAppId == testAdmobAppId) {
    logger.lifecycle("Nearshelf: release uses AdMob TEST ids (admob.testAds=true in local.properties)")
}

android {
    namespace = "com.mardev.nearshelf"
    testOptions.unitTests.isIncludeAndroidResources = true
    compileSdk = 37

    defaultConfig {
        applicationId = "com.mardev.nearshelf"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "1.0.0"

        // Weekly library-registry download (a raw file in your public registry repo).
        // Empty = bundled copy only. Set nearshelf.registryUrl in gradle.properties.
        // Test ads by default (debug); the release block below switches to the real IDs.
        manifestPlaceholders["admobAppId"] = testAdmobAppId
        buildConfigField("String", "ADMOB_NATIVE_UNIT", "\"$testAdmobNativeUnit\"")
        buildConfigField(
            "String",
            "REGISTRY_URL",
            "\"${(project.findProperty("nearshelf.registryUrl") as String?).orEmpty()}\"",
        )
    }

    // Upload key from local.properties (never committed):
    //   release.storeFile=/path/to/upload-keystore.jks
    //   release.storePassword=…  release.keyAlias=upload  release.keyPassword=…
    // Without it, release builds are unsigned (fine for checks, not for Play).
    val hasUploadKey = listOf("release.storeFile", "release.storePassword", "release.keyAlias", "release.keyPassword")
        .all { !localProps.getProperty(it).isNullOrBlank() }
    signingConfigs {
        if (hasUploadKey) {
            create("upload") {
                storeFile = file(localProps.getProperty("release.storeFile"))
                storePassword = localProps.getProperty("release.storePassword")
                keyAlias = localProps.getProperty("release.keyAlias")
                keyPassword = localProps.getProperty("release.keyPassword")
            }
        }
    }

    buildTypes {
        release {
            if (hasUploadKey) signingConfig = signingConfigs.getByName("upload")
            manifestPlaceholders["admobAppId"] = admobAppId
            buildConfigField("String", "ADMOB_NATIVE_UNIT", "\"$admobNativeUnit\"")
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
}

dependencies {
    implementation(project(":core"))
    implementation(libs.profileinstaller)
    baselineProfile(project(":baselineprofile"))

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.hilt.navigation.compose)
    implementation(libs.kotlinx.coroutines.android)

    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.material3)
    implementation(libs.compose.ui.tooling.preview)
    debugImplementation(libs.compose.ui.tooling)

    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)

    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)

    implementation(libs.coil.compose)
    implementation(libs.coil.network.okhttp)

    implementation(libs.camera.core)
    implementation(libs.camera.camera2)
    implementation(libs.camera.lifecycle)
    implementation(libs.camera.compose)
    implementation(libs.work.runtime)
    implementation(libs.hilt.work)
    ksp(libs.hilt.androidx.compiler)
    implementation(libs.play.location)
    implementation(libs.datastore.preferences)
    implementation(libs.glance.appwidget)
    implementation(libs.glance.material3)
    implementation(libs.play.ads)
    implementation(libs.ump)
    implementation(libs.kotlinx.coroutines.play.services)

    // Bundled model: works offline and without Google Play services.
    implementation(libs.mlkit.barcode)

    testImplementation(libs.junit)
    // Screenshot tests (Robolectric renders the screens on the JVM, no device needed).
    // Record: ./gradlew :app:testDebugUnitTest -Pnearshelf.screenshots=true (PNGs in app/build/outputs/roborazzi)
    testImplementation(libs.roborazzi)
    testImplementation(libs.roborazzi.compose)
    testImplementation(libs.robolectric)
    testImplementation(platform(libs.compose.bom))
    testImplementation(libs.compose.ui.test.junit4)
    debugImplementation(libs.compose.ui.test.manifest)
}

tasks.withType<Test>().configureEach {
    if (providers.gradleProperty("nearshelf.screenshots").orNull == "true") {
        systemProperty("roborazzi.test.record", "true")
    }
    // Play Store images: ./gradlew :app:testDebugUnitTest --tests '*StoreScreenshotTest*' -Pnearshelf.store=true
    if (providers.gradleProperty("nearshelf.store").orNull == "true") {
        systemProperty("roborazzi.test.record", "true")
        systemProperty("nearshelf.store", "true")
    }
}
