import java.io.FileInputStream
import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

val keystoreProperties = Properties()
val keystorePropertiesFile = rootProject.file("key.properties")
val releaseSigningConfigured = keystorePropertiesFile.exists()

if (releaseSigningConfigured) {
    FileInputStream(keystorePropertiesFile).use { keystoreProperties.load(it) }
}

android {
    namespace = "br.com.lafamigliaplayworks.fitnexuscoach"
    // Google Play requires new submissions/updates to target Android 16 / API 36
    // from 2026-08-31. Keep compile/target explicit so Flutter defaults cannot
    // silently regress the publication contract.
    compileSdk = 36
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        applicationId = "br.com.lafamigliaplayworks.fitnexuscoach"
        // Current Flutter in_app_purchase Android support starts at SDK 24.
        minSdk = maxOf(flutter.minSdkVersion, 24)
        targetSdk = 36
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        if (releaseSigningConfigured) {
            create("release") {
                val storeFileValue = keystoreProperties.getProperty("storeFile")
                    ?: error("Missing storeFile in android/key.properties")
                storeFile = rootProject.file(storeFileValue)
                storePassword = keystoreProperties.getProperty("storePassword")
                    ?: error("Missing storePassword in android/key.properties")
                keyAlias = keystoreProperties.getProperty("keyAlias")
                    ?: error("Missing keyAlias in android/key.properties")
                keyPassword = keystoreProperties.getProperty("keyPassword")
                    ?: error("Missing keyPassword in android/key.properties")
            }
        }
    }

    buildTypes {
        release {
            // CI/repository previews remain unsigned when key.properties is absent.
            // A real upload key is external secret material and must never be committed.
            if (releaseSigningConfigured) {
                signingConfig = signingConfigs.getByName("release")
            }
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
