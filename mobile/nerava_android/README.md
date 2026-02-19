# Nerava Android App

Native Android shell wrapping the Nerava React driver web app (`https://app.nerava.network`).
This is the Android equivalent of the iOS WKWebView wrapper at `Nerava/Nerava/`.

## Prerequisites

- Android Studio Hedgehog (2023.1.1) or later
- JDK 17
- Android SDK 34
- Gradle 8.2+
- A Firebase project with `google-services.json` (for FCM)

## Setup

1. Copy `local.properties.example` to `local.properties` and set your SDK path:
   ```
   sdk.dir=/Users/YOUR_USER/Library/Android/sdk
   ```

2. Place your Firebase `google-services.json` in `app/`:
   ```
   app/google-services.json
   ```
   If you don't have one yet, the app will still build and run — FCM will just fail silently.

3. Open the project in Android Studio or build from CLI.

## Build

```bash
# Debug build (loads http://10.0.2.127:5173 for local dev)
./gradlew assembleDebug

# Release build (loads https://app.nerava.network)
./gradlew assembleRelease

# Staging build
./gradlew assembleStaging

# Run unit tests
./gradlew test

# Run instrumentation tests (requires connected device/emulator)
./gradlew connectedAndroidTest
```

## Build Variants

| Variant | Web App URL | API URL | Debug |
|---------|-------------|---------|-------|
| `debug` | `http://10.0.2.127:5173` | `http://10.0.2.127:8001` | Yes |
| `staging` | `https://staging.nerava.network` | `https://staging-api.nerava.network` | No |
| `release` | `https://app.nerava.network` | `https://api.nerava.network` | No |

To test against a local backend from an emulator, use `10.0.2.2` (Android emulator loopback).

## Architecture

```
app/src/main/java/network/nerava/app/
├── MainActivity.kt          # WebView host, permissions, lifecycle
├── NeravaApplication.kt     # App init, notification channels
├── webview/                  # WebView configuration, error handling
├── bridge/                   # JS ↔ Native bridge (matches iOS NativeBridge.swift)
├── engine/                   # Session state machine (matches iOS SessionEngine.swift)
├── location/                 # FusedLocation + geofencing
├── network/                  # API client for /v1/native/* endpoints
├── auth/                     # EncryptedSharedPreferences token store
├── notifications/            # FCM + local notifications
├── deeplink/                 # Deep link routing
└── debug/                    # Bridge diagnostics (debug builds)
```

## Bridge Parity

The JavaScript bridge is identical in behavior to iOS. Both platforms:
1. Inject `window.neravaNative` at document start
2. Use `window.neravaNativeCallback(action, payload)` for native → web
3. Support the same 6 fire-and-forget commands and 4 request/response queries

The only difference is the transport:
- iOS: `window.webkit.messageHandlers.neravaBridge.postMessage()`
- Android: `AndroidBridge.onMessage()` via `@JavascriptInterface`

See `docs/android-bridge-parity.md` for the full contract.

## Key Differences from iOS

| Feature | iOS | Android |
|---------|-----|---------|
| Token storage | Keychain | EncryptedSharedPreferences |
| Background location | CLLocationManager + significantChanges | FusedLocation + foreground service |
| Geofencing | CLCircularRegion | GeofencingClient |
| Push | APNs (not wired) | FCM (ready for backend) |
| Deep links | Not implemented | Android App Links + nerava:// |
| Wallet | Not implemented | Not implemented (stub) |
| Event source | `ios_native` | `android_native` |

## Signing

For release builds, create a keystore and configure in `app/build.gradle.kts`:

```kotlin
signingConfigs {
    create("release") {
        storeFile = file("path/to/keystore.jks")
        storePassword = "..."
        keyAlias = "nerava"
        keyPassword = "..."
    }
}
```

## Play Store Submission

1. Build release APK/AAB: `./gradlew bundleRelease`
2. Sign with release keystore
3. Upload to Google Play Console
4. Configure App Links verification in Search Console
5. Set up Firebase for production FCM
