# Nerava iOS App Store Launch Fixes - Change Review Pack

Date: 2026-01-27
Scope: P0 blockers + selected P1/P2 polish per ios_app_store_launch_fixes_451ce9bf.plan.md

## Summary of What Changed
- Removed CloudKit entitlements.
- Added UILaunchScreen config + LaunchBackground/LaunchLogo assets; loading overlay now matches.
- Moved notification permission to a contextual rationale screen.
- Implemented WebView error recovery (provisional failures, process terminations), pull-to-refresh, and WKUIDelegate for JS alert/confirm and target=_blank.
- Added in-app Privacy Policy link and native fallback links on error/offline overlays.
- Fixed iOS 17 onChange signature warning.
- Added accessibility labels + Dynamic Type fixes for permission views.
- Added haptic feedback at key session states.
- Added Keychain -> Web token recovery via GET_AUTH_TOKEN bridge.
- Cached ISO8601DateFormatter.
- Updated web app title + favicon.
- Added AppIcon filename entries (PNG files still required).

## Files Modified / Added

### iOS Native
- Nerava/Nerava/Nerava.entitlements
- Nerava/Nerava/Info.plist
- Nerava/Nerava/Views/ContentView.swift
- Nerava/Nerava/NeravaApp.swift
- Nerava/Nerava/Services/NotificationService.swift
- Nerava/Nerava/Engine/SessionEngine.swift
- Nerava/Nerava/Views/WebViewContainer.swift
- Nerava/Nerava/Views/LocationPermissionView.swift
- Nerava/Nerava/Views/BackgroundPermissionView.swift
- Nerava/Nerava/Views/NotificationPermissionView.swift (new)
- Nerava/Nerava/Services/NativeBridge.swift
- Nerava/Nerava/Services/APIClient.swift
- Nerava/Nerava/Assets.xcassets/LaunchBackground.colorset/Contents.json (new)
- Nerava/Nerava/Assets.xcassets/LaunchLogo.imageset/Contents.json (new)
- Nerava/Nerava/Assets.xcassets/LaunchLogo.imageset/nerava-logo.png (new)
- Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/Contents.json

### Web App (Driver)
- apps/driver/index.html
- apps/driver/src/components/Account/AccountPage.tsx
- apps/driver/src/hooks/useNativeBridge.ts

## Highlights (What to Validate)

### P0-1 Launch Screen
- Added UILaunchScreen dictionary in Info.plist pointing to LaunchBackground and LaunchLogo.
- LoadingOverlay now uses Color("LaunchBackground") to avoid flash.

### P0-2 CloudKit Entitlements
- Removed com.apple.developer.icloud-container-identifiers and com.apple.developer.icloud-services.

### P0-4 Notification Permission (Contextual)
- Removed request at launch.
- Added NotificationPermissionView shown when exclusive activated / arrived at merchant.
- Uses UserDefaults flags to ensure one-time prompt.

### P0-5 Privacy Policy Link
- Added Privacy Policy link in Account page.
- Added native fallback link in OfflineOverlay and ErrorOverlay.

### P0-7 WebView Recovery
- Added loadError state + WebViewError enum.
- Implemented didFailProvisionalNavigation/didFail/webViewWebContentProcessDidTerminate.
- Added pull-to-refresh via UIRefreshControl.
- Implemented WKUIDelegate alert/confirm + target=_blank handling.

### P1-4 Token Sync
- NativeBridge GET_AUTH_TOKEN action responds with token (if any).
- useNativeBridge retrieves token from native when localStorage empty.

### P1-5 Haptics
- Added haptic triggers on sessionActive/atMerchant/nearCharger/sessionEnded.

### P2-5 ISO8601 Formatter
- Cached static ISO8601DateFormatter in APIClient.

## Manual Steps Required
- Add AppIcon PNGs (1024x1024, no alpha):
  - Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/AppIcon.png
  - Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/AppIcon-Dark.png
  - Nerava/Nerava/Assets.xcassets/AppIcon.appiconset/AppIcon-Tinted.png

## QA Checklist
- Launch screen shows logo with no flash on cold start.
- No notification prompt on fresh install launch.
- Notification prompt appears on first exclusive activation / arrival at merchant (rationale first).
- Offline and error overlays show with Retry + Privacy Policy link.
- Pull-to-refresh works and ends refreshing.
- JS alert/confirm dialogs display.
- GET_AUTH_TOKEN populates localStorage when WKWebView storage is empty.
- Haptics fire at key transitions.
- VoiceOver and Dynamic Type on permission views.

## Open Questions / Risks
- aps-environment in entitlements still "development"; confirm Release archive uses production entitlement or separate entitlements file.
- Account page uses target=_blank; WKUIDelegate createWebViewWith now routes to same webview.
- AppIcon appiconset assumes “Single Size” usage; confirm asset catalog settings in Xcode.

## Quick Diff Pointers
- WebView recovery and overlays: Nerava/Nerava/Views/WebViewContainer.swift
- Notification rationale and permission gating: Nerava/Nerava/Services/NotificationService.swift, Nerava/Nerava/Engine/SessionEngine.swift, Nerava/Nerava/Views/NotificationPermissionView.swift, Nerava/Nerava/Views/ContentView.swift
- Token sync bridge: Nerava/Nerava/Services/NativeBridge.swift, apps/driver/src/hooks/useNativeBridge.ts
- Launch screen assets: Nerava/Nerava/Info.plist, Nerava/Nerava/Assets.xcassets/LaunchBackground.colorset/Contents.json, Nerava/Nerava/Assets.xcassets/LaunchLogo.imageset/Contents.json
