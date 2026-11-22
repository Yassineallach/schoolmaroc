import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("org.jetbrains.kotlin.jvm")
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

dependencies {
    // The ai.onnxruntime Java API is identical in the desktop jar and the Android AAR.
    // The app module supplies the Android runtime; tests use the desktop runtime.
    compileOnly("com.microsoft.onnxruntime:onnxruntime:1.32.0")
    testImplementation("com.microsoft.onnxruntime:onnxruntime:1.32.0")
    testImplementation("junit:junit:4.13.2")
}

tasks.test {
    maxHeapSize = "3g"
    systemProperty("modelDir", rootProject.file("app/src/main/assets/models").absolutePath)
    // Set PRINTSCALE_TEST_SERVER to a running notebook server link to run the cloud integration tests.
    systemProperty("cloudServer", System.getenv("PRINTSCALE_TEST_SERVER") ?: "")
    systemProperty("outDir", layout.buildDirectory.dir("test-output").get().asFile.absolutePath)
    testLogging { events("passed", "failed", "skipped"); showStandardStreams = true }
}
