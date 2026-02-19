# iOS Deep-Link Routing Implementation

## Overview
Enable deep-link routing so push notifications can open specific screens.

## URL Scheme
Register `nerava://` scheme in Info.plist:
```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>nerava</string>
    </array>
  </dict>
</array>
```

## Universal Links
Add Associated Domains capability:
- `applinks:app.nerava.network`
- `applinks:nerava.network`

## Route Mapping
| Deep Link | Web Path | Screen |
|-----------|----------|--------|
| `nerava://charger/{id}` | `/charger/{id}` | Charger details |
| `nerava://merchant/{id}` | `/merchant/{id}` | Merchant details |
| `nerava://session/{id}` | `/session/{id}` | Active session |
| `nerava://wallet` | `/wallet` | Wallet screen |

## Implementation
In `AppDelegate.swift`:
```swift
func application(_ app: UIApplication, open url: URL, options: [UIApplication.OpenURLOptionsKey : Any] = [:]) -> Bool {
    guard let components = URLComponents(url: url, resolvingAgainstBaseURL: true),
          let host = components.host else { return false }

    let path = "/\(host)\(components.path)"
    webView?.evaluateJavaScript("window.location.href = '\(path)'")
    return true
}
```

## Testing
1. `xcrun simctl openurl booted "nerava://merchant/abc123"`
2. Verify WebView navigates to `/merchant/abc123`
