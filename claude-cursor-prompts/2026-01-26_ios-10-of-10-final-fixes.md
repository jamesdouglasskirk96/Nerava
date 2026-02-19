# Cursor Prompt — Nerava iOS 10/10 Final Fixes

## Scope

Three surgical changes to move from 8.5/10 to 10/10. One P0 blocker (app icon assets), two P1 one-liners.

**Hard constraints:**
- Do NOT modify any file not listed below
- Do NOT refactor, rename, or restructure anything
- Do NOT add dependencies
- Do NOT add features beyond what is listed
- Changes are purely additive or single-line edits

---

## Step 1 — P0: App Icon Assets (DESIGNER HANDOFF)

**Status:** `Contents.json` already references the correct filenames. The PNG files do not exist on disk. App Store Connect will reject the binary without them.

**Directory:** `Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/`

**Current contents:**
- `Contents.json` (correct, no changes needed)

**Required files (must be added manually):**

| Filename | Purpose | Spec |
|---|---|---|
| `AppIcon.png` | Standard (light mode) icon | 1024x1024 PNG, no alpha channel, no transparency, sRGB |
| `AppIcon-Dark.png` | Dark mode variant | 1024x1024 PNG, no alpha channel, sRGB. Dark background version of the logo. |
| `AppIcon-Tinted.png` | Tinted/monochrome variant | 1024x1024 PNG, no alpha channel, sRGB. Single-color silhouette version for iOS 18 tinted mode. |

**Designer instructions:**
1. Export the Nerava logo as a 1024x1024 PNG with **no alpha channel** (flatten to opaque background).
2. For the dark variant, use a dark background (e.g., #0A0A0A) with light logo.
3. For the tinted variant, create a monochrome silhouette — iOS will colorize this automatically, so use a single shade of gray on white/black.
4. Drop all three files into: `Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/`
5. Open Xcode → Assets → AppIcon → confirm all three slots show the icon with no yellow warnings.

**If generating a placeholder programmatically (temporary for build testing only):**
You can use any 1024x1024 solid-color PNG to unblock the build. The real assets must come from the designer before App Store submission.

**Verification:**
- `ls Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/` shows `AppIcon.png`, `AppIcon-Dark.png`, `AppIcon-Tinted.png`, `Contents.json`
- Xcode asset catalog shows no warnings on AppIcon
- Build and install on device → home screen shows the icon (not blank/default)

---

## Step 2 — P1-A: Enable Back Navigation in WKWebView

**Problem:** `target=_blank` links (e.g., Privacy Policy in AccountPage) load in the same webview via the `createWebViewWith` delegate. Without swipe-back, the user gets stuck on the linked page with no way to return. App Review will likely test the Privacy Policy link and hit this dead end.

**File:** `Nerava/Nerava/Views/WebViewContainer.swift`

**Current code (lines 204–207):**
```swift
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.scrollView.alwaysBounceVertical = true
```

**Change:** Add one line after `webView.uiDelegate = context.coordinator` (line 206):

```swift
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator
        webView.uiDelegate = context.coordinator
        webView.allowsBackForwardNavigationGestures = true
        webView.scrollView.alwaysBounceVertical = true
```

**What this does:** Enables the standard iOS edge-swipe gesture to go back/forward in the webview's navigation history. After tapping Privacy Policy (or any `target=_blank` link), the user can swipe from the left edge to return to the app.

**Verification:**
- Load app → Account → tap Privacy Policy → privacy page loads in webview
- Swipe from left edge → returns to the app's Account page
- Confirm pull-to-refresh still works (no gesture conflict)

---

## Step 3 — P1-B: Fix BackgroundPermissionView Icon

**Problem:** `BackgroundPermissionView` uses `bell.badge.fill` (a notification bell), which is the same icon as `NotificationPermissionView`. A user seeing both screens in sequence sees identical bell icons for two completely different permissions (background location vs. notifications), which is confusing.

**File:** `Nerava/Nerava/Views/BackgroundPermissionView.swift`

**Current code (line 10):**
```swift
            Image(systemName: "bell.badge.fill")
```

**Change to:**
```swift
            Image(systemName: "location.fill.viewfinder")
```

**Why `location.fill.viewfinder`:** This SF Symbol shows a location pin inside a viewfinder/scope, which visually communicates "tracking your location in the background." It differentiates clearly from the bell icon used for notifications.

**Verification:**
- Fresh install → grant when-in-use location → trigger the background location rationale
- Confirm the icon is a location viewfinder, not a bell
- Confirm `NotificationPermissionView` still shows `bell.badge.fill` (unchanged)

---

## QA / Verification Checklist

### On-Device (iPhone, Release build)

- [ ] **App icon visible** on home screen (light mode) — not blank/default
- [ ] **App icon visible** in dark mode — dark variant shows
- [ ] **Privacy Policy navigation round-trip:** Account → Privacy Policy → swipe back → Account page visible
- [ ] **Pull-to-refresh still works** after enabling back gestures (no conflict)
- [ ] **Background location rationale** shows location viewfinder icon, not bell
- [ ] **Notification rationale** still shows bell icon (unchanged)
- [ ] **All prior QA still passes:** launch screen, no prompt on launch, error recovery, haptics, token sync

### Build Checks

```bash
# Build succeeds with zero errors
xcodebuild clean build -scheme Nerava -configuration Release -quiet

# App icon files present
ls -la Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/*.png
# Expect: AppIcon.png, AppIcon-Dark.png, AppIcon-Tinted.png

# No regressions — these should still return nothing
rg "icloud" Nerava/Nerava/Nerava.entitlements
rg "requestPermission\(\)" Nerava/Nerava/NeravaApp.swift
```

---

## App Store Submission Checklist (Final)

- [ ] **App icon:** All 3 variants in asset catalog, no Xcode warnings
- [ ] **Launch screen:** Branded, no flash (already done)
- [ ] **No permission prompt at launch:** Verified on fresh install (already done)
- [ ] **Privacy policy in-app:** Account page link works, user can navigate back
- [ ] **Privacy policy URL resolves:** `https://nerava.network/privacy` returns content
- [ ] **Error recovery:** All error paths show retry UI (already done)
- [ ] **Entitlements clean:** Only `aps-environment`, no CloudKit (already done)
- [ ] **aps-environment:** Confirm `production` in archived binary
- [ ] **PrivacyInfo.xcprivacy:** Present and declares location + UserDefaults (already done)
- [ ] **Bundle version:** 1.0.0 in Info.plist (already set)

---

## Guardrails

- Do NOT modify `SessionEngine`, `NativeBridge`, `GeofenceManager`, `APIClient`, or any file not listed above
- Do NOT change the JS bridge injection script or message protocol
- Do NOT add third-party dependencies
- Do NOT add features, screens, or UI beyond what is listed
- The only code changes are: 1 line added to `WebViewContainer.swift`, 1 line changed in `BackgroundPermissionView.swift`
- The icon PNGs are a file-drop, not a code change
