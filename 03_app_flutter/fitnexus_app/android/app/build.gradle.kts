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
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // Canonical FitNexus Android identity selected in the repository.
        // Play Console uniqueness/ownership remains an external publication gate.
        applicationId = "br.com.lafamigliaplayworks.fitnexuscoach"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
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
