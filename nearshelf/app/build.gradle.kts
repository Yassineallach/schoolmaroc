import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.room)
}

room {
    schemaDirectory("$projectDir/schemas")
}

// Real AdMob IDs live in local.properties (never committed):
//   admob.appId=ca-app-pub-XXXXXXXXXXXXXXXX~YYYYYYYYYY
//   admob.nativeUnitId=ca-app-pub-XXXXXXXXXXXXXXXX/ZZZZZZZZZZ
// Without them, Google's published test IDs are used (safe to click, no revenue).
val localProps = Properties().apply {
    rootProject.file("local.properties").takeIf { it.exists() }?.inputStream()?.use { load(it) }
}
val admobAppId = localProps.getProperty("admob.appId") ?: "ca-app-pub-3940256099942544~3347511713"
val admobNativeUnit = localProps.getProperty("admob.nativeUnitId") ?: "ca-app-pub-3940256099942544/2247696110"
if (admobAppId.startsWith("ca-app-pub-3940256099942544")) {
    logger.lifecycle("Nearshelf: using AdMob TEST ids (set admob.appId / admob.nativeUnitId in local.properties for release)")
}

android {
    namespace = "com.mardev.nearshelf"
    compileSdk = 37

    defaultConfig {
        applicationId = "com.mardev.nearshelf"
        minSdk = 26
        targetSdk = 37
        versionCode = 1
        versionName = "0.1.0"

        // Weekly library-registry download (a raw file in your public registry repo).
        // Empty = bundled copy only. Set nearshelf.registryUrl in gradle.properties.
        manifestPlaceholders["admobAppId"] = admobAppId
        buildConfigField("String", "ADMOB_NATIVE_UNIT", "\"$admobNativeUnit\"")
        buildConfigField(
            "String",
            "REGISTRY_URL",
            "\"${(project.findProperty("nearshelf.registryUrl") as String?).orEmpty()}\"",
        )
    }

    buildTypes {
        release {
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
}
