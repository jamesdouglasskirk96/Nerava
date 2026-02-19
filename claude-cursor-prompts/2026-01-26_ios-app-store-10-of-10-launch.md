# Cursor Prompt — iOS App Store 10/10 Launch: P0 Blockers + P1 Polish

## Context

The Nerava iOS app (`/Nerava/Nerava/`) is a native SwiftUI shell wrapping the driver web app (`apps/driver/`) in a WKWebView. The native layer is ~2,200 LOC across 19 files and already includes a 7-state SessionEngine, geofencing, Keychain auth, and a validated JavaScript bridge. An audit identified 8 P0 (submission-blocking) and 8 P1 (10/10 polish) issues. This prompt fixes all P0s and the highest-impact P1s.

**Hard constraints:**
- Do NOT refactor SessionEngine, NativeBridge message protocol, or GeofenceManager internals
- Keep changes additive — no breaking changes to the JS bridge API contract
- No new third-party dependencies
- No feature creep — ship what's listed, nothing more

---

## Scope & Priorities

### P0 — Must Ship (Submission Blockers)
1. Launch screen (no white/black flash)
2. Remove unused CloudKit entitlement
3. APS environment = production for release builds
4. Move notification permission to contextual trigger
5. Privacy policy link in web app Account page
6. App icon assets (1024x1024, no alpha)
7. WebView error recovery (provisional failures, retry, pull-to-refresh, process crash)
8. Fix deprecated `onChange` signature for iOS 17+

### P1 — Ship for 10/10 Polish
1. Accessibility labels on all native views
2. Dynamic Type safety on native views
3. Offline overlay with Retry button
4. Keychain-to-web token sync (GET_AUTH_TOKEN bridge action)
5. Haptic feedback at key session moments
6. WKUIDelegate for JS alert/confirm
7. Web app title + favicon fix

---

## Step-by-Step Implementation

---

### P0-1: Launch Screen

**Problem:** App launches to a black/white screen with a spinner. Apple requires a polished launch experience.

**File:** `Nerava/Nerava/Info.plist`

Add the UILaunchScreen key (SwiftUI approach, no storyboard needed):

```xml
<!-- Add BEFORE the closing </dict> in Info.plist -->
<key>UILaunchScreen</key>
<dict>
    <key>UIColorName</key>
    <string>LaunchBackground</string>
    <key>UIImageName</key>
    <string>LaunchLogo</string>
</dict>
```

**File:** `Nerava/Nerava/Assets.xcassets/`

Create two new color/image assets:

1. Create `LaunchBackground.colorset/Contents.json`:
```json
{
  "colors" : [
    {
      "color" : {
        "color-space" : "srgb",
        "components" : { "red" : "1.000", "green" : "1.000", "blue" : "1.000", "alpha" : "1.000" }
      },
      "idiom" : "universal"
    },
    {
      "appearances" : [{ "appearance" : "luminosity", "value" : "dark" }],
      "color" : {
        "color-space" : "srgb",
        "components" : { "red" : "0.020", "green" : "0.020", "blue" : "0.020", "alpha" : "1.000" }
      },
      "idiom" : "universal"
    }
  ],
  "info" : { "author" : "xcode", "version" : 1 }
}
```

2. Add a `LaunchLogo` image set with the Nerava logo (use the existing `apps/driver/public/nerava-logo.png` as source, export at appropriate sizes).

**Also:** Set the `LoadingOverlay` background in `WebViewContainer.swift` to match:

```swift
// In LoadingOverlay, change:
Color.black.opacity(0.3)
// To:
Color(UIColor.systemBackground)
```

This eliminates the visual "flash" between launch screen and loading overlay.

**Verification:**
- `rg "UILaunchScreen" Nerava/Nerava/Info.plist` — confirm key exists
- Build and run: launch screen should show Nerava logo on white/dark background with no flash to a different color

---

### P0-2: Remove Unused CloudKit Entitlement

**Problem:** `Nerava.entitlements` declares CloudKit but it's never used. Apple rejects apps with unused capabilities (Guideline 2.5.9).

**File:** `Nerava/Nerava/Nerava.entitlements`

Current contents:
```xml
<dict>
    <key>aps-environment</key>
    <string>development</string>
    <key>com.apple.developer.icloud-container-identifiers</key>
    <array/>
    <key>com.apple.developer.icloud-services</key>
    <array>
        <string>CloudKit</string>
    </array>
</dict>
```

Replace with:
```xml
<dict>
    <key>aps-environment</key>
    <string>development</string>
</dict>
```

**Also:** In Xcode project settings (Signing & Capabilities tab), remove the iCloud capability if it appears. Search the `.pbxproj` for `com.apple.iCloud` and remove any references.

**Verification:**
- `rg "icloud" Nerava/Nerava/Nerava.entitlements` — should return nothing
- Build succeeds without iCloud capability

---

### P0-3: APS Environment = Production for Release

**Problem:** Entitlements hardcodes `aps-environment: development`. Release/archive builds need `production`.

**Approach:** Xcode's automatic signing handles this during archive (it substitutes `production` for distribution builds). However, to be explicit and safe:

**Option A (Recommended — let Xcode handle it):**
Verify that in Xcode > Build Settings > Code Signing Entitlements, the release configuration uses the same entitlements file. Xcode's archive + export process will automatically flip `development` → `production` for App Store distribution. **No code change needed if using automatic signing.**

**Option B (If manual signing):**
Create `Nerava/Nerava/NeravaRelease.entitlements` with `aps-environment: production` and set it as the entitlements file for the Release build configuration in Build Settings.

**Verification:**
- Archive the app → Export for App Store → inspect the embedded entitlements: `codesign -d --entitlements - Nerava.app` — should show `aps-environment: production`

---

### P0-4: Move Notification Permission to Contextual Trigger

**Problem:** `NeravaApp.init()` calls `NotificationService.shared.requestPermission()` at launch. Apple rejects apps that prompt for permissions without context (Guideline 5.1.1(iv)).

**File:** `Nerava/Nerava/NeravaApp.swift`

Remove the permission request from init:

```swift
// REMOVE this line from init():
NotificationService.shared.requestPermission()
```

The `init()` should become:
```swift
init() {
    let location = LocationService()
    let geofence = GeofenceManager()
    let api = APIClient()

    _locationService = StateObject(wrappedValue: location)
    _sessionEngine = StateObject(wrappedValue: SessionEngine(
        locationService: location,
        geofenceManager: geofence,
        apiClient: api,
        config: .defaults
    ))
}
```

**File:** `Nerava/Nerava/Services/NotificationService.swift`

Add contextual, idempotent permission request:

```swift
import UserNotifications

final class NotificationService {
    static let shared = NotificationService()
    private init() {}

    private static let hasRequestedKey = "com.nerava.notificationPermissionRequested"

    /// Request permission only once, contextually. Call this at meaningful moments
    /// (e.g., after first exclusive activation or merchant arrival).
    func requestPermissionIfNeeded() {
        guard !UserDefaults.standard.bool(forKey: Self.hasRequestedKey) else { return }
        UserDefaults.standard.set(true, forKey: Self.hasRequestedKey)

        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { granted, error in
            if let error = error {
                Log.session.error("Notification permission error: \(error.localizedDescription)")
            }
            Log.session.info("Notification permission granted: \(granted)")
        }
    }

    func showSessionActiveNotification() {
        let content = UNMutableNotificationContent()
        content.title = "You're all set!"
        content.body = "Head to the merchant to unlock your exclusive deal."
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "session_active",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }

    func showAtMerchantNotification() {
        let content = UNMutableNotificationContent()
        content.title = "You've arrived!"
        content.body = "Show your code to the merchant to redeem your exclusive."
        content.sound = .default

        let request = UNNotificationRequest(
            identifier: "at_merchant",
            content: content,
            trigger: nil
        )
        UNUserNotificationCenter.current().add(request)
    }
}
```

**File:** `Nerava/Nerava/Engine/SessionEngine.swift`

In `webConfirmsExclusiveActivated`, add the contextual trigger right before the notification:

```swift
// In webConfirmsExclusiveActivated, BEFORE the existing notification call:
NotificationService.shared.requestPermissionIfNeeded()
NotificationService.shared.showSessionActiveNotification()
```

Find this line (around line 440):
```swift
NotificationService.shared.showSessionActiveNotification()
```
And change it to:
```swift
NotificationService.shared.requestPermissionIfNeeded()
NotificationService.shared.showSessionActiveNotification()
```

**Verification:**
- Fresh install: no notification prompt on launch
- Activate an exclusive → notification prompt appears (first time only)
- Second activation → no prompt (idempotent)

---

### P0-5: Privacy Policy Link in Web App

**Problem:** No privacy policy link anywhere in the app. Required by Guideline 5.1.1.

**File:** `apps/driver/src/components/Account/AccountPage.tsx`

Add a Privacy Policy button in the Account section. Insert after the Favorites button (around line 115) and before the Logout button:

```tsx
          <button
            onClick={() => setShowFavoritesList(true)}
            className="w-full p-4 bg-gray-50 rounded-xl flex items-center gap-3 hover:bg-gray-100 active:bg-gray-200 transition-colors"
          >
            <Heart className="w-5 h-5 text-red-500" />
            <div className="flex-1 text-left">
              <p className="font-medium">Favorites</p>
              <p className="text-sm text-gray-500">{favorites.size} saved</p>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </button>

          {/* Privacy Policy */}
          <a
            href="https://nerava.network/privacy"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full p-4 bg-gray-50 rounded-xl flex items-center gap-3 hover:bg-gray-100 active:bg-gray-200 transition-colors block"
          >
            <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <div className="flex-1 text-left">
              <p className="font-medium">Privacy Policy</p>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400" />
          </a>

          <button
            onClick={handleLogout}
            className="w-full p-4 bg-red-50 text-red-600 rounded-xl flex items-center gap-3"
          >
```

**Verification:**
- Open Account page → "Privacy Policy" link visible between Favorites and Log Out
- Tapping opens `https://nerava.network/privacy` in browser/webview
- URL actually resolves (if not yet live, create a placeholder page)

---

### P0-6: App Icon Assets

**Problem:** `AppIcon.appiconset/Contents.json` has entries but no actual image files. The `filename` key is missing from all entries.

**File:** `Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/Contents.json`

After adding actual icon image files (1024x1024 PNG, no alpha channel), update the JSON:

```json
{
  "images" : [
    {
      "filename" : "AppIcon.png",
      "idiom" : "universal",
      "platform" : "ios",
      "size" : "1024x1024"
    },
    {
      "appearances" : [
        {
          "appearance" : "luminosity",
          "value" : "dark"
        }
      ],
      "filename" : "AppIcon-Dark.png",
      "idiom" : "universal",
      "platform" : "ios",
      "size" : "1024x1024"
    },
    {
      "appearances" : [
        {
          "appearance" : "luminosity",
          "value" : "tinted"
        }
      ],
      "filename" : "AppIcon-Tinted.png",
      "idiom" : "universal",
      "platform" : "ios",
      "size" : "1024x1024"
    }
  ],
  "info" : {
    "author" : "xcode",
    "version" : 1
  }
}
```

**Action required:** Create or source three 1024x1024 PNG files:
- `AppIcon.png` — standard icon (no alpha, no transparency)
- `AppIcon-Dark.png` — dark mode variant (or duplicate of standard)
- `AppIcon-Tinted.png` — tinted variant (or duplicate of standard)

Place all three in `Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/`.

**Verification:**
- Open Xcode → Assets → AppIcon → all three slots filled, no warnings
- Archive builds without "Missing app icon" errors

---

### P0-7: WebView Error Recovery + Pull-to-Refresh

**Problem:** `WebViewContainer.swift` has no `didFailProvisionalNavigation`, no `webViewWebContentProcessDidTerminate`, no retry mechanism, and no pull-to-refresh. Users hit blank screens on network failures with no way out.

**File:** `Nerava/Nerava/Views/WebViewContainer.swift`

Replace the entire file with this enhanced version:

```swift
import SwiftUI
import WebKit

struct WebViewContainer: View {
    @EnvironmentObject private var locationService: LocationService
    @EnvironmentObject private var sessionEngine: SessionEngine
    @ObservedObject private var networkMonitor = NetworkMonitor.shared
    @State private var isLoading = true
    @State private var loadError: WebViewError? = nil

    var body: some View {
        ZStack {
            WebViewRepresentable(
                locationService: locationService,
                sessionEngine: sessionEngine,
                isLoading: $isLoading,
                loadError: $loadError
            )

            if isLoading && loadError == nil {
                LoadingOverlay()
            }

            if let error = loadError {
                ErrorOverlay(error: error) {
                    loadError = nil
                    isLoading = true
                    NotificationCenter.default.post(name: .neravaWebViewReload, object: nil)
                }
            }

            if !networkMonitor.isConnected && loadError == nil {
                OfflineOverlay {
                    NotificationCenter.default.post(name: .neravaWebViewReload, object: nil)
                }
            }
        }
    }
}

// MARK: - Error Types

enum WebViewError {
    case network(String)
    case serverError
    case sslError
    case processTerminated
    case unknown(String)

    var title: String {
        switch self {
        case .network: return "No Connection"
        case .serverError: return "Server Error"
        case .sslError: return "Security Error"
        case .processTerminated: return "Something Went Wrong"
        case .unknown: return "Something Went Wrong"
        }
    }

    var message: String {
        switch self {
        case .network(let detail): return detail
        case .serverError: return "The server isn't responding. Please try again."
        case .sslError: return "We couldn't establish a secure connection."
        case .processTerminated: return "The page stopped unexpectedly. Tap retry to reload."
        case .unknown(let detail): return detail
        }
    }

    var systemImage: String {
        switch self {
        case .network: return "wifi.slash"
        case .serverError: return "exclamationmark.icloud"
        case .sslError: return "lock.slash"
        case .processTerminated: return "arrow.counterclockwise"
        case .unknown: return "exclamationmark.triangle"
        }
    }
}

// MARK: - Overlays

private struct LoadingOverlay: View {
    var body: some View {
        ZStack {
            Color(UIColor.systemBackground)
            ProgressView()
                .scaleEffect(1.5)
                .tint(.secondary)
        }
        .ignoresSafeArea()
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Loading Nerava")
    }
}

private struct OfflineOverlay: View {
    let onRetry: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: "wifi.slash")
                .font(.system(size: 40))
                .foregroundColor(.gray)
                .accessibilityHidden(true)
            Text("No internet connection")
                .font(.headline)
                .foregroundColor(.primary)
            Text("Check your connection and try again.")
                .font(.subheadline)
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
            Button(action: onRetry) {
                Text("Retry")
                    .font(.body.weight(.medium))
                    .padding(.horizontal, 32)
                    .padding(.vertical, 12)
                    .background(Color(red: 24/255, green: 119/255, blue: 242/255))
                    .foregroundColor(.white)
                    .cornerRadius(12)
            }
            .accessibilityLabel("Retry loading")
            .accessibilityHint("Attempts to reload the page")
        }
        .padding(24)
        .background(.ultraThinMaterial)
        .cornerRadius(16)
    }
}

private struct ErrorOverlay: View {
    let error: WebViewError
    let onRetry: () -> Void

    var body: some View {
        ZStack {
            Color(UIColor.systemBackground)
            VStack(spacing: 16) {
                Image(systemName: error.systemImage)
                    .font(.system(size: 44))
                    .foregroundColor(.gray)
                    .accessibilityHidden(true)
                Text(error.title)
                    .font(.title3.weight(.semibold))
                    .foregroundColor(.primary)
                Text(error.message)
                    .font(.subheadline)
                    .foregroundColor(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
                Button(action: onRetry) {
                    Text("Retry")
                        .font(.body.weight(.medium))
                        .frame(minWidth: 120)
                        .padding(.horizontal, 32)
                        .padding(.vertical, 12)
                        .background(Color(red: 24/255, green: 119/255, blue: 242/255))
                        .foregroundColor(.white)
                        .cornerRadius(12)
                }
                .accessibilityLabel("Retry loading")
                .accessibilityHint("Attempts to reload the page")

                Link("Privacy Policy", destination: URL(string: "https://nerava.network/privacy")!)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .padding(.top, 8)
            }
        }
        .ignoresSafeArea()
    }
}

// MARK: - Notification

extension Notification.Name {
    static let neravaWebViewReload = Notification.Name("neravaWebViewReload")
}

// MARK: - WebView Representable

struct WebViewRepresentable: UIViewRepresentable {
    let locationService: LocationService
    let sessionEngine: SessionEngine
    @Binding var isLoading: Bool
    @Binding var loadError: WebViewError?

    func makeCoordinator() -> Coordinator {
        Coordinator(
            locationService: locationService,
            sessionEngine: sessionEngine,
            isLoading: $isLoading,
            loadError: $loadError
        )
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let controller = WKUserContentController()
        config.userContentController = controller

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.allowsBackForwardNavigationGestures = false
        webView.scrollView.bounces = true

        // Pull-to-refresh
        let refreshControl = UIRefreshControl()
        refreshControl.addTarget(
            context.coordinator,
            action: #selector(Coordinator.handleRefresh(_:)),
            for: .valueChanged
        )
        webView.scrollView.refreshControl = refreshControl

        // Setup native bridge + injection
        context.coordinator.nativeBridge.setupWebView(webView)
        context.coordinator.nativeBridge.sessionEngine = sessionEngine
        sessionEngine.setWebBridge(context.coordinator.nativeBridge)

        // Store reference for reload notifications
        context.coordinator.webView = webView

        // Listen for reload requests
        NotificationCenter.default.addObserver(
            context.coordinator,
            selector: #selector(Coordinator.handleReloadNotification),
            name: .neravaWebViewReload,
            object: nil
        )

        // Load driver app
        let url = URL(string: "https://app.nerava.network")!
        webView.load(URLRequest(url: url))

        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKNavigationDelegate, WKUIDelegate {
        let nativeBridge: NativeBridge
        var isLoading: Binding<Bool>
        var loadError: Binding<WebViewError?>
        weak var webView: WKWebView?

        init(locationService: LocationService, sessionEngine: SessionEngine,
             isLoading: Binding<Bool>, loadError: Binding<WebViewError?>) {
            self.nativeBridge = NativeBridge(locationService: locationService)
            self.isLoading = isLoading
            self.loadError = loadError
            super.init()
        }

        @objc func handleRefresh(_ sender: UIRefreshControl) {
            webView?.reload()
            DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                sender.endRefreshing()
            }
        }

        @objc func handleReloadNotification() {
            let url = URL(string: "https://app.nerava.network")!
            webView?.load(URLRequest(url: url))
        }

        // MARK: - WKNavigationDelegate

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            isLoading.wrappedValue = false
            loadError.wrappedValue = nil
            nativeBridge.didFinishNavigation()
            nativeBridge.sendToWeb(.ready)
        }

        func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
            isLoading.wrappedValue = true
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            isLoading.wrappedValue = false
            loadError.wrappedValue = classifyError(error)
            Log.bridge.error("Navigation failed: \(error.localizedDescription)")
        }

        func webView(_ webView: WKWebView, didFailProvisionalNavigation navigation: WKNavigation!, withError error: Error) {
            isLoading.wrappedValue = false
            loadError.wrappedValue = classifyError(error)
            Log.bridge.error("Provisional navigation failed: \(error.localizedDescription)")
        }

        func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
            isLoading.wrappedValue = false
            loadError.wrappedValue = .processTerminated
            Log.bridge.error("WebView process terminated")
        }

        // MARK: - WKUIDelegate (JS alert/confirm)

        func webView(_ webView: WKWebView,
                      runJavaScriptAlertPanelWithMessage message: String,
                      initiatedByFrame frame: WKFrameInfo,
                      completionHandler: @escaping () -> Void) {
            guard let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                  let root = scene.windows.first?.rootViewController else {
                completionHandler()
                return
            }
            let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler() })
            root.present(alert, animated: true)
        }

        func webView(_ webView: WKWebView,
                      runJavaScriptConfirmPanelWithMessage message: String,
                      initiatedByFrame frame: WKFrameInfo,
                      completionHandler: @escaping (Bool) -> Void) {
            guard let scene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
                  let root = scene.windows.first?.rootViewController else {
                completionHandler(false)
                return
            }
            let alert = UIAlertController(title: nil, message: message, preferredStyle: .alert)
            alert.addAction(UIAlertAction(title: "Cancel", style: .cancel) { _ in completionHandler(false) })
            alert.addAction(UIAlertAction(title: "OK", style: .default) { _ in completionHandler(true) })
            root.present(alert, animated: true)
        }

        // MARK: - Error Classification

        private func classifyError(_ error: Error) -> WebViewError {
            let nsError = error as NSError
            switch nsError.code {
            case NSURLErrorNotConnectedToInternet, NSURLErrorNetworkConnectionLost:
                return .network("You appear to be offline. Check your connection and try again.")
            case NSURLErrorCannotFindHost, NSURLErrorDNSLookupFailed:
                return .network("We couldn't reach the server. Please try again.")
            case NSURLErrorTimedOut:
                return .network("The request timed out. Please try again.")
            case NSURLErrorSecureConnectionFailed, NSURLErrorServerCertificateUntrusted,
                 NSURLErrorServerCertificateHasBadDate, NSURLErrorServerCertificateNotYetValid:
                return .sslError
            case NSURLErrorBadServerResponse:
                return .serverError
            default:
                if nsError.domain == "WebKitErrorDomain" && nsError.code == 102 {
                    // Frame load interrupted — typically not an error the user needs to see
                    return .unknown("The page couldn't finish loading.")
                }
                return .unknown("Something went wrong. Please try again.")
            }
        }
    }
}
```

**Verification:**
- Airplane mode → launch app → see ErrorOverlay with "No Connection" + Retry button
- Tap Retry → loading spinner → error again (still offline) or loads (if back online)
- Pull down on webview → refresh control appears → page reloads
- Kill web process (Debug > Safari > Terminate Process) → "Something Went Wrong" overlay appears with Retry

---

### P0-8: Fix Deprecated `onChange` Signature

**Problem:** `ContentView.swift:46` uses the iOS 16 `onChange(of:)` single-parameter closure, which is deprecated on iOS 17+.

**File:** `Nerava/Nerava/Views/ContentView.swift`

Replace the full file:

```swift
import SwiftUI
import CoreLocation

struct ContentView: View {
    @EnvironmentObject private var locationService: LocationService
    @EnvironmentObject private var sessionEngine: SessionEngine

    @State private var showWhenInUseRationale = false
    @State private var showAlwaysRationale = false

    var body: some View {
        ZStack {
            WebViewContainer()
                .environmentObject(locationService)
                .environmentObject(sessionEngine)

            // Rationale overlays (shown BEFORE system prompt)
            if showWhenInUseRationale {
                LocationPermissionView(
                    onContinue: {
                        showWhenInUseRationale = false
                        locationService.requestWhenInUsePermission()
                    },
                    onNotNow: {
                        showWhenInUseRationale = false
                    }
                )
            } else if showAlwaysRationale {
                BackgroundPermissionView(
                    onContinue: {
                        showAlwaysRationale = false
                        locationService.requestAlwaysPermission()
                    },
                    onNotNow: {
                        showAlwaysRationale = false
                    }
                )
            }
        }
        .onAppear {
            // Fresh install: show rationale BEFORE prompting
            if locationService.authorizationStatus == .notDetermined {
                showWhenInUseRationale = true
            }
        }
        .onChange(of: locationService.authorizationStatus) { _, newStatus in
            // If user granted when-in-use, app works. Later the web can trigger Always.
            if newStatus == .authorizedWhenInUse {
                // Do nothing automatically; keep hooks for later UX trigger.
            }
        }
    }
}
```

The only change is line `.onChange(of: locationService.authorizationStatus) { _, newStatus in` — two-parameter closure for iOS 17+.

**Verification:**
- Build with no deprecation warnings related to `onChange`

---

### P1-1/P1-2: Accessibility Labels + Dynamic Type Safety

**File:** `Nerava/Nerava/Views/LocationPermissionView.swift`

Replace with:

```swift
import SwiftUI

struct LocationPermissionView: View {
    let onContinue: () -> Void
    let onNotNow: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "location.fill")
                .font(.system(size: 36))
                .foregroundColor(Color(red: 24/255, green: 119/255, blue: 242/255))
                .accessibilityHidden(true)

            Text("Enable Location")
                .font(.title2.weight(.bold))
                .accessibilityAddTraits(.isHeader)

            Text("Nerava needs your location to detect when you arrive at an EV charger and unlock nearby merchant exclusives.")
                .font(.body)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
                .fixedSize(horizontal: false, vertical: true)

            HStack(spacing: 12) {
                Button("Not Now") { onNotNow() }
                    .font(.body.weight(.medium))
                    .padding()
                    .frame(maxWidth: .infinity)
                    .accessibilityHint("Dismisses the location request. You can enable it later in Settings.")

                Button("Continue") { onContinue() }
                    .font(.body.weight(.medium))
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color(red: 24/255, green: 119/255, blue: 242/255))
                    .foregroundColor(.white)
                    .cornerRadius(12)
                    .accessibilityHint("Shows the iOS location permission prompt")
            }
            .padding(.horizontal)
        }
        .padding(24)
        .background(.ultraThinMaterial)
        .cornerRadius(20)
        .padding()
    }
}
```

**File:** `Nerava/Nerava/Views/BackgroundPermissionView.swift`

Replace with:

```swift
import SwiftUI

struct BackgroundPermissionView: View {
    let onContinue: () -> Void
    let onNotNow: () -> Void

    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "bell.badge.fill")
                .font(.system(size: 36))
                .foregroundColor(Color(red: 24/255, green: 119/255, blue: 242/255))
                .accessibilityHidden(true)

            Text("Allow Background Location")
                .font(.title2.weight(.bold))
                .accessibilityAddTraits(.isHeader)

            Text("This lets Nerava notify you when you arrive at the merchant while your phone is in your pocket.")
                .font(.body)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
                .fixedSize(horizontal: false, vertical: true)

            HStack(spacing: 12) {
                Button("Not Now") { onNotNow() }
                    .font(.body.weight(.medium))
                    .padding()
                    .frame(maxWidth: .infinity)
                    .accessibilityHint("Dismisses the request. Background notifications will not be available.")

                Button("Continue") { onContinue() }
                    .font(.body.weight(.medium))
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color(red: 24/255, green: 119/255, blue: 242/255))
                    .foregroundColor(.white)
                    .cornerRadius(12)
                    .accessibilityHint("Shows the iOS background location permission prompt")
            }
            .padding(.horizontal)
        }
        .padding(24)
        .background(.ultraThinMaterial)
        .cornerRadius(20)
        .padding()
    }
}
```

Key changes:
- Added SF Symbol icons
- Added `.accessibilityAddTraits(.isHeader)` to titles
- Added `.accessibilityHint()` to buttons
- Added `.accessibilityHidden(true)` to decorative icons
- Used `.font(.body)` (scales with Dynamic Type) instead of implicit sizes
- Added `.fixedSize(horizontal: false, vertical: true)` to prevent text clipping at large sizes
- Used brand blue (#1877F2) consistently

**Verification:**
- Enable VoiceOver → navigate permission views → all elements announced with labels and hints
- Settings > Accessibility > Display & Text Size > Larger Text → set to max → views don't clip or overlap

---

### P1-4: Keychain-to-Web Token Sync (GET_AUTH_TOKEN)

**Problem:** WKWebView's `localStorage` can be purged by iOS. If that happens, the web app loses `access_token` and the user is silently logged out despite having a valid token in Keychain.

**File:** `Nerava/Nerava/Services/NativeBridge.swift`

Add `GET_AUTH_TOKEN` handling in the `switch actionStr` block (around line 319):

```swift
        case "GET_AUTH_TOKEN":
            if let token = KeychainService.shared.getAccessToken() {
                sendToWeb(.authTokenResponse(requestId: requestId ?? "", token: token))
            } else {
                sendToWeb(.error(requestId: requestId, message: "No token stored"))
            }
```

Add the new message type in `NativeBridgeMessage`:

```swift
enum NativeBridgeMessage {
    case sessionStateChanged(state: SessionState)
    case permissionStatus(status: String, alwaysGranted: Bool)
    case locationResponse(requestId: String, lat: Double, lng: Double, accuracy: Double)
    case authTokenResponse(requestId: String, token: String)  // NEW
    case sessionStartRejected(reason: String)
    case error(requestId: String?, message: String)
    case eventEmissionFailed(event: String, reason: String)
    case authRequired
    case ready
```

Add the action and payload for the new case:

In `var action: String`:
```swift
case .authTokenResponse: return "AUTH_TOKEN_RESPONSE"
```

In `var payload: [String: Any]`:
```swift
case .authTokenResponse(let requestId, let token):
    return ["requestId": requestId, "token": token]
```

Also add `getAuthToken` to the injected JavaScript in `var injectionScript: String`:

Find this block in the injection script:
```javascript
                getPermissionStatus: function() {
                    return this.request('GET_PERMISSION_STATUS', {});
                }
```

Add after it:
```javascript
                getPermissionStatus: function() {
                    return this.request('GET_PERMISSION_STATUS', {});
                },

                getAuthToken: function() {
                    return this.request('GET_AUTH_TOKEN', {});
                }
```

**File:** `apps/driver/src/hooks/useNativeBridge.ts`

Add the `getAuthToken` method to the Window interface and hook:

In the `Window.neravaNative` interface (around line 36):
```typescript
      getPermissionStatus: () => Promise<PermissionStatus>;
      getAuthToken: () => Promise<{ token: string }>;  // NEW
```

Add the callback and return value:
```typescript
  const getAuthToken = useCallback(async (): Promise<string | null> => {
    if (bridgeExists()) {
      try {
        const result = await window.neravaNative!.getAuthToken();
        return result.token;
      } catch {
        return null;
      }
    }
    return null;
  }, []);
```

In the return block, add `getAuthToken`:
```typescript
  return {
    isNative: bridgeReady,
    sessionState,
    setChargerTarget,
    setAuthToken,
    confirmExclusiveActivated,
    confirmVisitVerified,
    endSession,
    requestAlwaysLocation,
    getLocation,
    getPermissionStatus,
    getAuthToken,  // NEW
  };
```

**File:** `apps/driver/src/hooks/useNativeBridge.ts`

In the "Sync initial auth token" `useEffect` (around line 131), add Keychain→web sync:

```typescript
  // Sync initial auth token (once)
  useEffect(() => {
    if (!bridgeReady || initializedRef.current) return;
    initializedRef.current = true;

    const token = localStorage.getItem('access_token');
    if (token) {
      // Web has a token — push it to native Keychain
      window.neravaNative?.setAuthToken(token);
    } else {
      // Web has NO token — try to recover from native Keychain
      window.neravaNative?.getAuthToken().then((result: { token: string }) => {
        if (result?.token) {
          localStorage.setItem('access_token', result.token);
          console.log('[NativeBridge] Restored token from Keychain');
        }
      }).catch(() => {
        // No token in Keychain either — user needs to log in
      });
    }
  }, [bridgeReady]);
```

**Verification:**
- Login via OTP → token stored in both localStorage and Keychain
- Clear WKWebView data (Settings > Safari > Clear) → reopen app → token recovered from Keychain → user stays logged in
- `rg "GET_AUTH_TOKEN" Nerava/Nerava/` — confirm native handler exists

---

### P1-5: Haptic Feedback at Key Moments

**File:** `Nerava/Nerava/Engine/SessionEngine.swift`

Add a haptic helper (import UIKit at top if not already imported):

```swift
import UIKit  // Add at top if not present
```

Add a private method:

```swift
    // MARK: - Haptics

    private func triggerHaptic(_ style: UIImpactFeedbackGenerator.FeedbackStyle) {
        DispatchQueue.main.async {
            let generator = UIImpactFeedbackGenerator(style: style)
            generator.impactOccurred()
        }
    }

    private func triggerNotificationHaptic(_ type: UINotificationFeedbackGenerator.FeedbackType) {
        DispatchQueue.main.async {
            let generator = UINotificationFeedbackGenerator()
            generator.notificationOccurred(type)
        }
    }
```

Add haptic calls at key transition moments in the `transition(to:event:occurredAt:)` method. After the `Log.session.info("Transition:...")` line (around line 595):

```swift
        // Haptic feedback for key moments
        switch newState {
        case .sessionActive:
            triggerNotificationHaptic(.success)
        case .atMerchant:
            triggerNotificationHaptic(.success)
        case .nearCharger:
            triggerHaptic(.light)
        case .sessionEnded:
            triggerHaptic(.medium)
        default:
            break
        }
```

**Verification:**
- Activate exclusive on device → feel success haptic
- Enter merchant geofence → feel success haptic
- Enter charger zone → feel light haptic

---

### P1-7 (Quick Win): Web App Title + Favicon

**File:** `apps/driver/index.html`

Change:
```html
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
```
To:
```html
    <link rel="icon" type="image/png" href="/nerava-logo.png" />
```

Change:
```html
    <title>nerava-ui</title>
```
To:
```html
    <title>Nerava</title>
```

**Verification:**
- Open web app → browser tab shows "Nerava" title and Nerava icon
- iOS app switcher shows "Nerava" as app label

---

### P2-5 (Quick Win): Cache ISO8601DateFormatter

**File:** `Nerava/Nerava/Services/APIClient.swift`

Add a static formatter at the top of the class:

```swift
final class APIClient: APIClientProtocol {
    private static let iso8601Formatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        return formatter
    }()
```

Then replace all `ISO8601DateFormatter().string(from:` with `Self.iso8601Formatter.string(from:`.

There are 4 occurrences (2 in `emitSessionEvent`, 2 in `emitPreSessionEvent`):
- Line 53: `"occurred_at": ISO8601DateFormatter().string(from: occurredAt),`
- Line 54: `"timestamp": ISO8601DateFormatter().string(from: Date()),`
- Line 90: `"occurred_at": ISO8601DateFormatter().string(from: occurredAt),`
- Line 91: `"timestamp": ISO8601DateFormatter().string(from: Date()),`

Replace all with:
```swift
"occurred_at": Self.iso8601Formatter.string(from: occurredAt),
"timestamp": Self.iso8601Formatter.string(from: Date()),
```

---

## QA / Verification Checklist

### On-Device Manual Tests (iPhone, Release build)

- [ ] **Launch:** App opens with branded launch screen → smooth transition to web content (no white/black flash)
- [ ] **No prompt at launch:** Fresh install → no notification permission prompt on first launch
- [ ] **Location rationale:** Fresh install → location rationale overlay shows before iOS prompt → VoiceOver reads all elements
- [ ] **Notification prompt (contextual):** Activate first exclusive → notification prompt appears
- [ ] **Notification prompt (idempotent):** Activate second exclusive → no prompt
- [ ] **Privacy policy:** Account page → "Privacy Policy" link → opens URL
- [ ] **Error recovery (offline):** Airplane mode → launch → error overlay with Retry → turn off airplane mode → tap Retry → loads
- [ ] **Error recovery (mid-session):** Load app → airplane mode → pull-to-refresh → error overlay → reconnect → retry → loads
- [ ] **Process crash recovery:** Load app → Safari Dev Tools → Terminate Web Process → "Something Went Wrong" overlay → Retry → loads
- [ ] **Token sync:** Login → clear Safari/WKWebView data → relaunch → still logged in (recovered from Keychain)
- [ ] **Haptics:** Activate exclusive → feel success vibration; enter charger zone → light vibration
- [ ] **Dynamic Type:** Settings → max text size → permission views don't clip
- [ ] **App icon:** Home screen shows Nerava icon (not blank)
- [ ] **App switcher:** Shows "Nerava" title (not "nerava-ui")

### Build/Archive Checks

- [ ] `xcodebuild clean build -scheme Nerava -configuration Release` — zero errors, zero warnings
- [ ] Archive → Validate App → no entitlement warnings (no CloudKit, no unused capabilities)
- [ ] Archive → embedded entitlements show `aps-environment: production`
- [ ] `rg "icloud" Nerava/Nerava/Nerava.entitlements` — returns nothing
- [ ] `rg "requestPermission()" Nerava/Nerava/NeravaApp.swift` — returns nothing

### Web App Checks

- [ ] `cd apps/driver && npx tsc --noEmit` — zero errors
- [ ] `cd apps/driver && npx vite build` — builds successfully
- [ ] `rg "nerava-ui" apps/driver/index.html` — returns nothing
- [ ] `rg "vite.svg" apps/driver/index.html` — returns nothing
- [ ] Account page shows Privacy Policy link

---

## App Store Submission Checklist

- [ ] **Entitlements clean:** Only `aps-environment` in entitlements (no CloudKit)
- [ ] **Privacy policy:** `https://nerava.network/privacy` resolves and content is accurate
- [ ] **Privacy policy in-app:** Link visible in Account page
- [ ] **App icon:** 1024x1024 PNG, no alpha channel, all three variants in asset catalog
- [ ] **Launch screen:** Configured in Info.plist
- [ ] **No permission prompt at launch:** Verified on fresh install
- [ ] **No blank screens:** All error paths show recovery UI with Retry
- [ ] **PrivacyInfo.xcprivacy:** Already declares location + UserDefaults (verified, no changes needed)
- [ ] **NSLocationWhenInUseUsageDescription:** Already present in Info.plist
- [ ] **NSLocationAlwaysAndWhenInUseUsageDescription:** Already present in Info.plist
- [ ] **UIBackgroundModes:** Already includes `location`
- [ ] **Bundle ID:** `EVcharging.Nerava` — consider changing to `network.nerava.driver` before first submission
- [ ] **Version:** 1.0.0 in Info.plist

---

## Guardrails (DO NOT)

- Do NOT refactor `SessionEngine`, `SessionState`, `SessionEvent`, or `SessionSnapshot`
- Do NOT change the NativeBridge message handler names (except adding `GET_AUTH_TOKEN`)
- Do NOT change the JS injection script's `window.neravaNative` interface shape (only add new methods)
- Do NOT add third-party dependencies
- Do NOT modify `GeofenceManager`, `DwellDetector`, or `BackgroundTimer`
- Do NOT modify `APIClient` retry logic (only cache the formatter)
- Do NOT touch `SessionConfig` defaults
- Do NOT add features not listed in this prompt
