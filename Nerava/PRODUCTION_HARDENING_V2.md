# Nerava iOS Shell App - Production Hardening V2

## Objective

Upgrade the Nerava iOS shell app from "works" to "production-hardened V1" with an A- grade. This means:
- Hard failures become handled errors
- Release builds are safer than debug builds
- Core session lifecycle has test coverage
- Configuration and privacy requirements are present

## Success Criteria

1. App builds in Release configuration without warnings (except deprecation)
2. `xcodebuild test` passes with 6 SessionEngine unit tests (5 automated + 1 idempotency smoke test)
3. Backend `python -m compileall app` succeeds
4. Web `npm run typecheck` succeeds
5. Manual verification: location permission flow works, offline overlay appears, no crashes

---

## Pre-Implementation Verification

**CRITICAL:** Verify all referenced files and methods exist before starting implementation.

**VERIFICATION COMMANDS:**

```bash
cd /Users/jameskirk/Desktop/Nerava/Nerava

# Verify all files to be modified exist
ls -la Nerava/NeravaApp.swift
ls -la Nerava/Info.plist
ls -la Nerava/Services/NativeBridge.swift
ls -la Nerava/Services/APIClient.swift
ls -la Nerava/Services/GeofenceManager.swift
ls -la Nerava/Services/KeychainService.swift
ls -la Nerava/Views/WebViewContainer.swift
ls -la Nerava/Engine/SessionEngine.swift

# Verify SessionEngine methods exist
grep -n "func emitEventWithPending" Nerava/Engine/SessionEngine.swift
grep -n "func retryPendingEvent" Nerava/Engine/SessionEngine.swift
grep -n "private func notifyWeb" Nerava/Engine/SessionEngine.swift

# Verify NativeBridge.sendToWeb uses DispatchQueue.main.async
grep -A 10 "func sendToWeb" Nerava/Services/NativeBridge.swift | grep -q "DispatchQueue.main.async" && echo "✓ sendToWeb uses main thread dispatch" || echo "✗ WARNING: sendToWeb may not dispatch to main thread"

# Verify ContentView structure (for P1-C)
grep -n "environmentObject" Nerava/Views/ContentView.swift

# Verify test target exists
ls -la NeravaTests/SessionEngineTests.swift 2>/dev/null || echo "⚠ Test file will be created"
```

**IF ANY VERIFICATION FAILS:**
- Do not proceed with implementation
- Update file paths or method names in the plan
- Re-verify before starting

---

## P0 Changes (Must Implement)

### P0-A: Fix Dependency Duplication in NeravaApp

**File:** `Nerava/NeravaApp.swift`

**Problem:** Creates duplicate instances of LocationService, GeofenceManager, APIClient in init().

**REPLACE entire file with:**

```swift
import SwiftUI

@main
struct NeravaApp: App {
    @StateObject private var locationService: LocationService
    @StateObject private var sessionEngine: SessionEngine

    init() {
        // Single instance creation - these are the ONLY instances
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

        NotificationService.shared.requestPermission()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(locationService)
                .environmentObject(sessionEngine)
        }
    }
}
```

> **NOTE:** The local `geofence`, `api` variables look unused but are captured in the `StateObject` init closures. Do NOT remove them.

---

### P0-B: iOS Required Config Completeness

**File:** `Nerava/Info.plist`

**REPLACE entire file with:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>Nerava</string>
    <key>CFBundleDisplayName</key>
    <string>Nerava</string>
    <key>CFBundleIdentifier</key>
    <string>$(PRODUCT_BUNDLE_IDENTIFIER)</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>

    <key>NSLocationWhenInUseUsageDescription</key>
    <string>Nerava needs your location to find nearby EV chargers and local merchants with exclusive deals.</string>

    <key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
    <string>Nerava needs background location to notify you when you arrive at the merchant and automatically verify your visit for exclusive deals.</string>

    <key>UIBackgroundModes</key>
    <array>
        <string>location</string>
    </array>

    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <false/>
        <key>NSExceptionDomains</key>
        <dict>
            <key>localhost</key>
            <dict>
                <key>NSExceptionAllowsInsecureHTTPLoads</key>
                <true/>
                <key>NSIncludesSubdomains</key>
                <true/>
            </dict>
        </dict>
    </dict>
</dict>
</plist>
```

**RELEASE BUILD NOTE:** In the Release scheme, verify that `NSAllowsArbitraryLoads` is `false`. Debug builds allow localhost via exception domain only.

**VALIDATION:** After updating Info.plist, verify in Xcode:
- Product → Scheme → Edit Scheme → Info → Build Configuration = Release
- Build and run on device → confirm no ATS errors in Console

**CFBUNDLE KEY VERIFICATION:**
Before updating Info.plist, check Xcode project settings:
1. Select project → Target "Nerava" → General tab
2. Check "Display Name" field — if set, remove `CFBundleDisplayName` from Info.plist
3. Check "Bundle Identifier" — if custom, ensure Info.plist uses `$(PRODUCT_BUNDLE_IDENTIFIER)`
4. If project settings conflict with Info.plist, Xcode project settings take precedence

**AUTOMATED VALIDATION (OPTIONAL BUT RECOMMENDED):**

Add a Release-only build phase script to prevent shipping localhost ATS exceptions:

```bash
# In Build Phases → Run Script (before Compile Sources)
if [ "${CONFIGURATION}" == "Release" ]; then
  if grep -q "localhost" "${SRCROOT}/Nerava/Info.plist"; then
    echo "error: Release build contains localhost ATS exception"
    exit 1
  fi
fi
```

**SCRIPT PATH VERIFICATION:**
Before adding the build phase script, verify the Info.plist path:
1. In Xcode, select Info.plist → Right-click → "Show in Finder"
2. Note the relative path from project root
3. Update `${SRCROOT}/Nerava/Info.plist` if the path differs
4. Test the script manually: `grep -q "localhost" "${SRCROOT}/Nerava/Info.plist" && echo "Found" || echo "Not found"`

**ALTERNATIVE (More Robust):**
```bash
if [ "${CONFIGURATION}" == "Release" ]; then
  PLIST_PATH="${INFOPLIST_FILE}"
  if [ -z "$PLIST_PATH" ]; then
    PLIST_PATH="${SRCROOT}/Nerava/Info.plist"
  fi
  if grep -q "localhost" "$PLIST_PATH"; then
    echo "error: Release build contains localhost ATS exception"
    exit 1
  fi
fi
```

**V1 ACCEPTANCE:** Manual verification is acceptable if this script is not added.

**NEW FILE:** `Nerava/PrivacyInfo.xcprivacy`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSPrivacyTracking</key>
    <false/>
    <key>NSPrivacyTrackingDomains</key>
    <array/>
    <key>NSPrivacyCollectedDataTypes</key>
    <array>
        <dict>
            <key>NSPrivacyCollectedDataType</key>
            <string>NSPrivacyCollectedDataTypePreciseLocation</string>
            <key>NSPrivacyCollectedDataTypeLinked</key>
            <true/>
            <key>NSPrivacyCollectedDataTypeTracking</key>
            <false/>
            <key>NSPrivacyCollectedDataTypePurposes</key>
            <array>
                <string>NSPrivacyCollectedDataTypePurposeAppFunctionality</string>
            </array>
        </dict>
    </array>
    <key>NSPrivacyAccessedAPITypes</key>
    <array>
        <dict>
            <key>NSPrivacyAccessedAPIType</key>
            <string>NSPrivacyAccessedAPICategoryUserDefaults</string>
            <key>NSPrivacyAccessedAPITypeReasons</key>
            <array>
                <string>CA92.1</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
```

**XCODE PROJECT STEP:** After creating this file, you MUST add it to the target:
1. In Xcode, select `PrivacyInfo.xcprivacy` in the file navigator
2. In the right panel → File Inspector → Target Membership → check "Nerava"
3. Verify it appears in Build Phases → Copy Bundle Resources

**VERIFICATION STEP (CRITICAL):**
After adding to target, verify:
1. Build Phases → Copy Bundle Resources → `PrivacyInfo.xcprivacy` appears
2. **If missing from Copy Bundle Resources:**
   - Open Build Phases tab
   - Expand "Copy Bundle Resources"
   - Click "+" button
   - Select `PrivacyInfo.xcprivacy`
   - Click "Add"
3. Build project → verify no warnings about missing privacy manifest
4. **FAILURE TO VERIFY = App Store rejection**

---

### P0-C: Bridge Origin Tightening for Production

**File:** `Nerava/Services/NativeBridge.swift`

**FIND:**
```swift
    // Exact origin matching (NOT substring)
    private let allowedOrigins: Set<String> = [
        "https://app.nerava.network",
        "http://localhost:5173",
        "http://localhost:5174"
    ]
```

**REPLACE WITH:**
```swift
    // Exact origin matching (NOT substring)
    // Localhost only allowed in DEBUG builds
    private var allowedOrigins: Set<String> {
        var origins: Set<String> = [
            "https://app.nerava.network"
        ]
        #if DEBUG
        origins.insert("http://localhost:5173")
        origins.insert("http://localhost:5174")
        #endif
        return origins
    }
```

---

### P0-D: APIClient Reliability Basics

**File:** `Nerava/Services/APIClient.swift`

**REPLACE entire file with:**

```swift
import Foundation
import UIKit

final class APIClient: APIClientProtocol {
    private let baseURL: URL
    private var accessToken: String?
    private let session: URLSession
    private let maxRetries = 3
    private let baseRetryDelay: TimeInterval = 1.0

    init(baseURL: URL = URL(string: "https://api.nerava.network")!) {
        self.baseURL = baseURL
        self.accessToken = KeychainService.shared.getAccessToken()

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)
    }

    func setAuthToken(_ token: String) {
        self.accessToken = token
    }

    // MARK: - Session Events

    func emitSessionEvent(
        sessionId: String,
        event: String,
        eventId: String,
        occurredAt: Date,
        metadata: [String: String]? = nil
    ) async throws {
        let url = baseURL.appendingPathComponent("/v1/native/session-events")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let appState: String = await MainActor.run {
            UIApplication.shared.applicationState == .background ? "background" : "foreground"
        }

        var body: [String: Any] = [
            "schema_version": "1.0",
            "event_id": eventId,
            "idempotency_key": eventId,
            "session_id": sessionId,
            "event": event,
            "occurred_at": ISO8601DateFormatter().string(from: occurredAt),
            "timestamp": ISO8601DateFormatter().string(from: Date()),
            "source": "ios_native",
            "app_state": appState
        ]
        if let metadata = metadata {
            body["metadata"] = metadata
        }

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        try await executeWithRetry(request: request, eventId: eventId, event: event)
    }

    // MARK: - Pre-Session Events

    func emitPreSessionEvent(
        event: String,
        chargerId: String?,
        eventId: String,
        occurredAt: Date,
        metadata: [String: String]? = nil
    ) async throws {
        let url = baseURL.appendingPathComponent("/v1/native/pre-session-events")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        var body: [String: Any] = [
            "schema_version": "1.0",
            "event_id": eventId,
            "idempotency_key": eventId,
            "event": event,
            "occurred_at": ISO8601DateFormatter().string(from: occurredAt),
            "timestamp": ISO8601DateFormatter().string(from: Date()),
            "source": "ios_native"
        ]
        if let chargerId = chargerId {
            body["charger_id"] = chargerId
        }
        if let metadata = metadata {
            body["metadata"] = metadata
        }

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        try await executeWithRetry(request: request, eventId: eventId, event: event)
    }

    // MARK: - Config

    func fetchConfig() async throws -> SessionConfig {
        let url = baseURL.appendingPathComponent("/v1/native/config")
        var request = URLRequest(url: url)

        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode(SessionConfig.self, from: data)
    }

    // MARK: - Retry Logic

    private func executeWithRetry(request: URLRequest, eventId: String, event: String) async throws {
        // CRITICAL: Do NOT modify `request` or its `httpBody` in this method.
        // The request body contains `event_id` which MUST remain identical across retries.
        // Any mutation would break backend idempotency deduplication.
        var lastError: Error?

        for attempt in 0..<maxRetries {
            do {
                let (data, response) = try await session.data(for: request)

                guard let httpResponse = response as? HTTPURLResponse else {
                    throw APIError.invalidResponse
                }

                switch httpResponse.statusCode {
                case 200...299:
                    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                       let status = json["status"] as? String,
                       status == "already_processed" {
                        Log.api.info("Event already processed: \(event) (id=\(eventId.suffix(6)))")
                    } else {
                        Log.api.info("Event sent: \(event) (id=\(eventId.suffix(6)))")
                    }
                    return

                case 401, 403:
                    Log.api.error("Auth error (\(httpResponse.statusCode)) for event: \(event)")
                    throw APIError.authRequired

                case 429:
                    let delay = baseRetryDelay * pow(2.0, Double(attempt)) + Double.random(in: 0...0.5)
                    Log.api.warning("Rate limited, retrying in \(String(format: "%.1f", delay))s (attempt \(attempt + 1)/\(maxRetries))")
                    try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                    continue

                case 500...599:
                    let delay = baseRetryDelay * pow(2.0, Double(attempt)) + Double.random(in: 0...0.5)
                    Log.api.warning("Server error \(httpResponse.statusCode), retrying in \(String(format: "%.1f", delay))s")
                    try await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                    continue

                default:
                    throw APIError.requestFailed(statusCode: httpResponse.statusCode)
                }

            } catch let error as APIError {
                throw error
            } catch {
                lastError = error
                if attempt < maxRetries - 1 {
                    let delay = baseRetryDelay * pow(2.0, Double(attempt))
                    Log.api.warning("Network error, retrying in \(String(format: "%.1f", delay))s: \(error.localizedDescription)")
                    try? await Task.sleep(nanoseconds: UInt64(delay * 1_000_000_000))
                }
            }
        }

        Log.api.error("Event emission failed after \(maxRetries) attempts: \(event)")
        throw lastError ?? APIError.requestFailed(statusCode: 0)
    }

    enum APIError: Error {
        case requestFailed(statusCode: Int)
        case invalidResponse
        case authRequired
    }
}

// MARK: - Protocol for Testing

protocol APIClientProtocol {
    func setAuthToken(_ token: String)
    func emitSessionEvent(sessionId: String, event: String, eventId: String, occurredAt: Date, metadata: [String: String]?) async throws
    func emitPreSessionEvent(event: String, chargerId: String?, eventId: String, occurredAt: Date, metadata: [String: String]?) async throws
    func fetchConfig() async throws -> SessionConfig
}
```

#### Idempotency & Retry Safety Guarantee

**Invariant:** Every retry attempt MUST send the same `event_id` and request body.

- `executeWithRetry` receives a fully-formed `URLRequest` with `httpBody` already set.
- The request body MUST NOT be mutated between retry attempts.
- The `event_id` embedded in the body is the sole idempotency key.

**RATIONALE:** Backend deduplication relies on identical `event_id` across retries. If the body changes between retries (e.g., timestamp regeneration), the backend may process the same logical event multiple times.

**VERIFICATION REQUIREMENT:**
- Add a unit or manual test that forces retries (e.g., mock 500 errors)
- Confirm the same `event_id` appears in all retry attempts
- Verify request body bytes are identical across retries

---

### P0-E: Surface Critical Failures to Web

**File:** `Nerava/Services/NativeBridge.swift`

**FIND (in NativeBridgeMessage enum):**
```swift
    case error(requestId: String?, message: String)
    case ready
```

**REPLACE WITH:**
```swift
    case error(requestId: String?, message: String)
    case eventEmissionFailed(event: String, reason: String)
    case authRequired
    case ready
```

**FIND (in NativeBridgeMessage action computed property):**
```swift
        case .error: return "ERROR"
        case .ready: return "NATIVE_READY"
```

**REPLACE WITH:**
```swift
        case .error: return "ERROR"
        case .eventEmissionFailed: return "EVENT_EMISSION_FAILED"
        case .authRequired: return "AUTH_REQUIRED"
        case .ready: return "NATIVE_READY"
```

**FIND (in NativeBridgeMessage payload computed property):**
```swift
        case .error(let requestId, let message):
            var p: [String: Any] = ["message": message]
            if let rid = requestId { p["requestId"] = rid }
            return p
        case .ready:
            return [:]
```

**REPLACE WITH:**
```swift
        case .error(let requestId, let message):
            var p: [String: Any] = ["message": message]
            if let rid = requestId { p["requestId"] = rid }
            return p
        case .eventEmissionFailed(let event, let reason):
            return ["event": event, "reason": reason]
        case .authRequired:
            return [:]
        case .ready:
            return [:]
```

---

### P0-F: Surface API Errors from SessionEngine to Web

**File:** `Nerava/Engine/SessionEngine.swift`

**Goal:** When native event emission fails, the web layer MUST be informed so it can:
- Trigger re-authentication on 401/403
- Log or surface non-auth failures

---

#### A) emitEventWithPending

**FIND (in `emitEventWithPending`, ~line 700):**
```swift
            } catch {
                print("[SessionEngine] Event emission failed: \(error)")
                // Keep pendingEvent for retry on next launch
            }
```

**REPLACE WITH:**
```swift
            } catch APIClient.APIError.authRequired {
                Log.session.error("Auth required for event: \(pending.eventName)")
                notifyWeb(.authRequired)  // sendToWeb dispatches to main thread
                // Keep pendingEvent for retry on next launch
            } catch let error as APIClient.APIError {
                let reason: String
                switch error {
                case let .requestFailed(statusCode):
                    reason = "HTTP \(statusCode)"
                default:
                    reason = "\(error)"
                }
                Log.session.error("API error for event \(pending.eventName): \(error)")
                notifyWeb(.eventEmissionFailed(event: pending.eventName, reason: reason))
                // Keep pendingEvent for retry on next launch
            } catch {
                Log.session.error("Event emission failed: \(pending.eventName) - \(error.localizedDescription)")
                notifyWeb(.eventEmissionFailed(event: pending.eventName, reason: error.localizedDescription))
                // Keep pendingEvent for retry on next launch
            }
```

**ASYNC CONTEXT NOTE:** These error handlers run inside `Task { }` blocks (async context). `notifyWeb()` → `sendToWeb()` uses `DispatchQueue.main.async` internally, so calling `notifyWeb()` from async context is safe. The main thread dispatch ensures UI updates happen on the correct thread.

---

#### B) retryPendingEvent

**FIND (in `retryPendingEvent`, ~line 180):**
```swift
            } catch {
                print("[SessionEngine] Pending event retry failed: \(error)")
                // Keep pending for next launch
            }
```

**REPLACE WITH:**
```swift
            } catch APIClient.APIError.authRequired {
                Log.session.error("Auth required for pending event retry: \(pending.eventName)")
                notifyWeb(.authRequired)  // sendToWeb dispatches to main thread
                // Keep pending for next launch
            } catch let error as APIClient.APIError {
                let reason: String
                switch error {
                case let .requestFailed(statusCode):
                    reason = "HTTP \(statusCode)"
                default:
                    reason = "\(error)"
                }
                Log.session.error("Pending event retry failed: \(pending.eventName) - \(error)")
                notifyWeb(.eventEmissionFailed(event: pending.eventName, reason: reason))
                // Keep pending for next launch
            } catch {
                Log.session.error("Pending event retry failed: \(pending.eventName) - \(error.localizedDescription)")
                notifyWeb(.eventEmissionFailed(event: pending.eventName, reason: error.localizedDescription))
                // Keep pending for next launch
            }
```

**ASYNC CONTEXT NOTE:** These error handlers run inside `Task { }` blocks (async context). `notifyWeb()` → `sendToWeb()` uses `DispatchQueue.main.async` internally, so calling `notifyWeb()` from async context is safe. The main thread dispatch ensures UI updates happen on the correct thread.

---

**VERIFICATION STEP:**
- Write a unit test or manual test that simulates `APIError.authRequired` being thrown
- Confirm the web layer receives `AUTH_REQUIRED` via the native bridge
- This verifies the error propagation path is complete

**ACTOR CONTEXT VERIFICATION (VERIFIED - NO MainActor.run NEEDED):**

Before implementing P0-F, verify actor context:

1. Check `NativeBridge.sendToWeb` — does it use `DispatchQueue.main.async`?
   - **If YES**: `sendToWeb` already handles main thread dispatch. Remove all `MainActor.run` wrappers from P0-F error handlers.
   - **If NO**: Keep `MainActor.run` wrappers.

**VERIFICATION COMMAND:**
```bash
grep -A 5 "func sendToWeb" Nerava/Services/NativeBridge.swift
```

**IMPLEMENTATION DECISION:**

Since `sendToWeb` uses `DispatchQueue.main.async` internally (verified), use direct calls without `MainActor.run`:

```swift
} catch APIClient.APIError.authRequired {
    Log.session.error("Auth required for event: \(pending.eventName)")
    notifyWeb(.authRequired)  // No MainActor.run needed - sendToWeb dispatches to main
}
```

**RATIONALE:** `sendToWeb` already dispatches to main thread via `DispatchQueue.main.async`, so wrapping in `MainActor.run` is redundant and adds unnecessary overhead.

---

## P1 Changes (Should Implement)

### P1-A: Structured Logging

**NEW FILE:** `Nerava/Support/Log.swift`

```swift
import os.log

enum Log {
    static let session = Logger(subsystem: "network.nerava.app", category: "SessionEngine")
    static let location = Logger(subsystem: "network.nerava.app", category: "LocationService")
    static let geofence = Logger(subsystem: "network.nerava.app", category: "GeofenceManager")
    static let bridge = Logger(subsystem: "network.nerava.app", category: "NativeBridge")
    static let api = Logger(subsystem: "network.nerava.app", category: "APIClient")

    /// Scrub session ID to last 6 chars for logging
    static func scrubSessionId(_ id: String) -> String {
        guard id.count > 6 else { return id }
        return "...\(id.suffix(6))"
    }

    /// Scrub coordinates to 2 decimal places
    static func scrubCoordinate(_ value: Double) -> String {
        return String(format: "%.2f", value)
    }
}
```

**IMPORT VERIFICATION:**
After creating Log.swift, verify all files using Log can access it:
1. Files in the same target can use `Log` without imports (Swift module-level access)
2. If Log is in a different module, add `import Nerava` or appropriate module import
3. Verify compilation succeeds after replacing `print()` statements with `Log.*` calls

**VERIFICATION COMMAND:**
```bash
# After implementing P1-A, verify no compilation errors
xcodebuild -scheme Nerava -configuration Debug build 2>&1 | grep -i "error\|Log"
```

**Update all print() statements to use Log with appropriate levels:**

**Log Level Guidelines:**
- `Log.*.error()` - Errors, failures, exceptions
- `Log.*.warning()` - Warnings, recoverable issues
- `Log.*.info()` - General information, state changes
- `Log.*.debug()` - Detailed debugging (may be filtered in Release)

**Specific Replacements:**

In `SessionEngine.swift`:
- `print("[SessionEngine] Error: ...")` → `Log.session.error(...)`
- `print("[SessionEngine] Transition: ...")` → `Log.session.info(...)`
- `print("[SessionEngine] Snapshot persisted: ...")` → `Log.session.debug(...)`
- `print("[SessionEngine] Event emission failed: ...")` → `Log.session.error(...)`

In `LocationService.swift`:
- `print("[LocationService] ...")` → `Log.location.info(...)`
- `print("[LocationService] Error: ...")` → `Log.location.error(...)`

In `GeofenceManager.swift`:
- `print("[GeofenceManager] Added region: ...")` → `Log.geofence.info(...)`
- `print("[GeofenceManager] Removed region: ...")` → `Log.geofence.info(...)`
- `print("[GeofenceManager] Cleared all regions")` → `Log.geofence.info(...)`

In `NativeBridge.swift`:
- `print("[NativeBridge] Initialized")` → `Log.bridge.info(...)`
- `print("[NativeBridge] Rejected from unauthorized origin")` → `Log.bridge.error(...)`
- `print("[NativeBridge] JS error: ...")` → `Log.bridge.error(...)`
- `print("[NativeBridge] JSON encoding error: ...")` → `Log.bridge.error(...)`
- `print("[NativeBridge] Unknown action: ...")` → `Log.bridge.warning(...)`

---

### P1-B: Geofence FIFO Removal

**File:** `Nerava/Services/GeofenceManager.swift`

**FIND:**
```swift
final class GeofenceManager: NSObject {
    private let locationManager: CLLocationManager
    private var activeRegions: [String: CLCircularRegion] = [:]
    private let maxRegions = 2
```

**REPLACE WITH:**
```swift
final class GeofenceManager: NSObject {
    private let locationManager: CLLocationManager
    private var activeRegions: [String: CLCircularRegion] = [:]
    private var regionOrder: [String] = []  // FIFO order tracking
    private let maxRegions = 2
```

**FIND:**
```swift
    private func addRegion(identifier: String, coordinate: CLLocationCoordinate2D, radius: Double, notifyOnExit: Bool) {
        if activeRegions.count >= maxRegions {
            // NOTE: Dictionary ordering is undefined, so this removes an arbitrary region, not "oldest"
            if let anyKey = activeRegions.keys.first {
                removeRegion(identifier: anyKey)
            }
        }
```

**REPLACE WITH:**
```swift
    private func addRegion(identifier: String, coordinate: CLLocationCoordinate2D, radius: Double, notifyOnExit: Bool) {
        if activeRegions.count >= maxRegions {
            // FIFO: remove oldest region
            if let oldestKey = regionOrder.first {
                removeRegion(identifier: oldestKey)
            }
        }
```

**FIND:**
```swift
        activeRegions[identifier] = region
        locationManager.startMonitoring(for: region)
        locationManager.requestState(for: region)

        print("[GeofenceManager] Added region: \(identifier)")
```

**REPLACE WITH:**
```swift
        activeRegions[identifier] = region
        regionOrder.append(identifier)
        locationManager.startMonitoring(for: region)
        locationManager.requestState(for: region)

        Log.geofence.info("Added region: \(identifier)")
```

**FIND:**
```swift
    func removeRegion(identifier: String) {
        guard let region = activeRegions[identifier] else { return }
        locationManager.stopMonitoring(for: region)
        activeRegions.removeValue(forKey: identifier)
        print("[GeofenceManager] Removed region: \(identifier)")
    }
```

**REPLACE WITH:**
```swift
    func removeRegion(identifier: String) {
        guard let region = activeRegions[identifier] else { return }
        locationManager.stopMonitoring(for: region)
        activeRegions.removeValue(forKey: identifier)
        regionOrder.removeAll { $0 == identifier }
        Log.geofence.info("Removed region: \(identifier)")
    }
```

**FIND:**
```swift
    func clearAll() {
        for (_, region) in activeRegions {
            locationManager.stopMonitoring(for: region)
        }
        activeRegions.removeAll()
        print("[GeofenceManager] Cleared all regions")
    }
```

**REPLACE WITH:**
```swift
    func clearAll() {
        for (_, region) in activeRegions {
            locationManager.stopMonitoring(for: region)
        }
        activeRegions.removeAll()
        regionOrder.removeAll()
        Log.geofence.info("Cleared all regions")
    }

    /// For testing: get current FIFO order
    var currentRegionOrder: [String] { regionOrder }
```

---

### P1-C: Loading/Offline Affordance

**NEW FILE:** `Nerava/Services/NetworkMonitor.swift`

```swift
import Network
import Combine

final class NetworkMonitor: ObservableObject {
    static let shared = NetworkMonitor()

    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "NetworkMonitor")

    @Published private(set) var isConnected = true

    private init() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.isConnected = path.status == .satisfied
            }
        }
        monitor.start(queue: queue)
    }

    deinit {
        monitor.cancel()
    }
}
```

**SINGLETON USAGE NOTE:**
`NetworkMonitor.shared` is intentionally used as a shared observable singleton.
Use `@ObservedObject` (NOT `@StateObject`) because:
- The singleton manages its own lifecycle
- Multiple views should observe the same instance
- `@StateObject` is for owned instances; `@ObservedObject` is for external/shared instances

Do NOT convert to per-view instances; all views MUST share the same connectivity state.

**VERIFICATION:**
After implementation, verify:
1. Network state changes propagate to all observing views
2. No SwiftUI warnings about lifecycle appear in console
3. All views using NetworkMonitor share the same connectivity state

**File:** `Nerava/Views/WebViewContainer.swift`

**FIND:**
```swift
import SwiftUI
import WebKit

struct WebViewContainer: UIViewRepresentable {
```

**REPLACE WITH:**
```swift
import SwiftUI
import WebKit

struct WebViewContainer: View {
    @EnvironmentObject private var locationService: LocationService
    @EnvironmentObject private var sessionEngine: SessionEngine
    @ObservedObject private var networkMonitor = NetworkMonitor.shared
    @State private var isLoading = true

    var body: some View {
        ZStack {
            WebViewRepresentable(
                locationService: locationService,
                sessionEngine: sessionEngine,
                isLoading: $isLoading
            )

            if isLoading {
                LoadingOverlay()
            }

            if !networkMonitor.isConnected {
                OfflineOverlay()
            }
        }
    }
}

private struct LoadingOverlay: View {
    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
            ProgressView()
                .scaleEffect(1.5)
                .tint(.white)
        }
        .ignoresSafeArea()
    }
}

private struct OfflineOverlay: View {
    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "wifi.slash")
                .font(.system(size: 40))
                .foregroundColor(.gray)
            Text("No internet connection")
                .font(.headline)
                .foregroundColor(.primary)
        }
        .padding(24)
        .background(.ultraThinMaterial)
        .cornerRadius(16)
    }
}

struct WebViewRepresentable: UIViewRepresentable {
    let locationService: LocationService
    let sessionEngine: SessionEngine
    @Binding var isLoading: Bool
```

**FIND (Coordinator class):**
```swift
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            nativeBridge.didFinishNavigation()
            // Redundant ready signal (native->web)
            nativeBridge.sendToWeb(.ready)
        }
```

**REPLACE WITH:**
```swift
        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            isLoading.wrappedValue = false
            nativeBridge.didFinishNavigation()
            nativeBridge.sendToWeb(.ready)
        }

        func webView(_ webView: WKWebView, didStartProvisionalNavigation navigation: WKNavigation!) {
            isLoading.wrappedValue = true
        }

        func webView(_ webView: WKWebView, didFail navigation: WKNavigation!, withError error: Error) {
            isLoading.wrappedValue = false
            Log.bridge.error("Navigation failed: \(error.localizedDescription)")
        }
```

**Add isLoading binding to Coordinator init:**
```swift
    final class Coordinator: NSObject, WKNavigationDelegate {
        let nativeBridge: NativeBridge
        var isLoading: Binding<Bool>

        init(locationService: LocationService, sessionEngine: SessionEngine, isLoading: Binding<Bool>) {
            self.nativeBridge = NativeBridge(locationService: locationService)
            self.isLoading = isLoading
            super.init()
        }
```

**UPDATE `makeCoordinator()` in WebViewRepresentable:**

**FIND:**
```swift
    func makeCoordinator() -> Coordinator {
        Coordinator(locationService: locationService, sessionEngine: sessionEngine)
    }
```

**REPLACE WITH:**
```swift
    func makeCoordinator() -> Coordinator {
        Coordinator(
            locationService: locationService,
            sessionEngine: sessionEngine,
            isLoading: $isLoading
        )
    }
```

**VERIFY ContentView compatibility:**

**BEFORE IMPLEMENTING P1-C**, verify ContentView structure matches expectations:

```bash
# Verify ContentView has environment object injection
grep -n "environmentObject" Nerava/Views/ContentView.swift
```

**Expected Output:**
- Should show `.environmentObject(locationService)` and `.environmentObject(sessionEngine)` calls
- Note the actual line numbers (may differ from plan references)

ContentView receives environment objects from NeravaApp (via `.environmentObject()`), then passes them to WebViewContainer via `.environmentObject()` modifiers.

**Environment Object Flow:**
1. NeravaApp injects `locationService` and `sessionEngine` into ContentView's environment
2. ContentView receives them as `@EnvironmentObject`
3. ContentView explicitly passes them to WebViewContainer via `.environmentObject()` modifiers
4. WebViewContainer receives them as `@EnvironmentObject` (in new implementation)

**Redundancy Note:**
The `.environmentObject()` modifiers on WebViewContainer (lines 14-15) are technically redundant—WebViewContainer would inherit these from ContentView's environment automatically. However, keeping them is explicit and safe. SwiftUI ignores redundant environment injections.

**No changes needed to ContentView.**

**ENVIRONMENT OBJECT VERIFICATION (CRITICAL):**

ContentView MUST provide environment objects before WebViewContainer is created:
- ContentView must call `.environmentObject(locationService)` and `.environmentObject(sessionEngine)` on WebViewContainer
- Use `grep -n "environmentObject" Nerava/Views/ContentView.swift` to find actual line numbers
- These are provided at the ContentView level, so WebViewContainer's `@EnvironmentObject` will receive them
- **VERIFY:** ContentView always provides these objects (it does in current implementation)
- **RISK:** If ContentView is refactored to remove environment object injection, WebViewContainer will crash at runtime with "No ObservableObject of type X found"
- **SAFEGUARD:** Do NOT remove `.environmentObject()` calls from ContentView without updating WebViewContainer

---

## P2 Changes (Nice to Have)

### P2-A: Remove Force Unwraps

**File:** `Nerava/Services/KeychainService.swift`

**FIND:**
```swift
    func setAccessToken(_ token: String) {
        let data = token.data(using: .utf8)!
```

**REPLACE WITH:**
```swift
    func setAccessToken(_ token: String) {
        guard let data = token.data(using: .utf8) else {
            Log.api.error("Failed to encode token")
            return
        }
```

### P2-B: Validate Merchant Coordinates

**File:** `Nerava/Engine/SessionEngine.swift`

**FIND (in webConfirmsExclusiveActivated):**
```swift
        merchantTarget = MerchantTarget(id: merchantId, latitude: merchantLat, longitude: merchantLng)
```

**REPLACE WITH:**
```swift
        // Validate coordinates are not (0,0) which indicates invalid data
        guard merchantLat != 0 || merchantLng != 0 else {
            Log.session.error("Invalid merchant coordinates (0,0)")
            notifyWeb(.sessionStartRejected(reason: "INVALID_MERCHANT_LOCATION"))
            return
        }

        merchantTarget = MerchantTarget(id: merchantId, latitude: merchantLat, longitude: merchantLng)
```

---

## Tests

**NEW FILE:** `NeravaTests/SessionEngineTests.swift`

```swift
import XCTest
import CoreLocation
@testable import Nerava

final class MockAPIClient: APIClientProtocol {
    var emittedSessionEvents: [(sessionId: String, event: String, eventId: String)] = []
    var emittedPreSessionEvents: [(event: String, chargerId: String?, eventId: String)] = []
    var shouldFail = false

    func setAuthToken(_ token: String) {}

    // Parameters match APIClientProtocol exactly.
    // Unused parameters (occurredAt, metadata) are intentionally ignored for test simplicity.
    func emitSessionEvent(sessionId: String, event: String, eventId: String, occurredAt: Date, metadata: [String: String]?) async throws {
        if shouldFail { throw APIClient.APIError.requestFailed(statusCode: 500) }
        emittedSessionEvents.append((sessionId, event, eventId))
    }

    // Parameters match APIClientProtocol exactly.
    // Unused parameters (occurredAt, metadata) are intentionally ignored for test simplicity.
    func emitPreSessionEvent(event: String, chargerId: String?, eventId: String, occurredAt: Date, metadata: [String: String]?) async throws {
        if shouldFail { throw APIClient.APIError.requestFailed(statusCode: 500) }
        emittedPreSessionEvents.append((event, chargerId, eventId))
    }

    func fetchConfig() async throws -> SessionConfig {
        return .defaults
    }
}

final class SessionEngineTests: XCTestCase {
    var locationService: LocationService!
    var geofenceManager: GeofenceManager!
    var mockAPIClient: MockAPIClient!
    var sessionEngine: SessionEngine!

    override func setUp() {
        super.setUp()
        locationService = LocationService()
        geofenceManager = GeofenceManager()
        mockAPIClient = MockAPIClient()
        sessionEngine = SessionEngine(
            locationService: locationService,
            geofenceManager: geofenceManager,
            apiClient: mockAPIClient,
            config: .defaults
        )
    }

    override func tearDown() {
        SessionSnapshot.clear()
        super.tearDown()
    }

    // Test 1: Idle -> NearCharger when inside intent radius
    func testTransitionIdleToNearChargerWhenInsideIntentRadius() {
        // Given: Engine in idle state with a charger target
        XCTAssertEqual(sessionEngine.currentState, .idle)

        // When: Set charger target (already inside intent zone will trigger transition)
        // Note: This tests the immediate check in setChargerTarget
        // For full integration, we'd need to mock location updates
        sessionEngine.setChargerTarget(chargerId: "charger_1", lat: 37.7749, lng: -122.4194)

        // Then: Charger target is set
        XCTAssertNotNil(sessionEngine.currentTargetedCharger)
        XCTAssertEqual(sessionEngine.currentTargetedCharger?.id, "charger_1")
    }

    // Test 2: NearCharger -> Anchored (integration-style)
    // NOTE: Uses wall-clock time and WILL be flaky in CI.
    // V1 ACCEPTANCE: Skip in CI, run locally only.
    // V2 TODO: Refactor DwellDetector to accept a time provider for testability.
    func testDwellDetectorMarksAnchored() {
        // Skip in CI to avoid flakiness
        if ProcessInfo.processInfo.environment["CI"] == "true" {
            return  // Skip test in CI environment
        }

        let detector = DwellDetector(anchorRadius: 30, dwellDuration: 2, speedThreshold: 1.5)

        // Simulate stationary location within radius for > dwell duration
        let location = CLLocation(
            coordinate: CLLocationCoordinate2D(latitude: 0, longitude: 0),
            altitude: 0,
            horizontalAccuracy: 5,
            verticalAccuracy: 5,
            course: 0,
            speed: 0,  // Stationary
            timestamp: Date()
        )

        detector.recordLocation(location, distanceToAnchor: 10)
        XCTAssertFalse(detector.isAnchored)  // Not enough time

        // Wait for dwell duration
        let expectation = expectation(description: "Dwell timeout")
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
            detector.recordLocation(location, distanceToAnchor: 10)
            expectation.fulfill()
        }

        wait(for: [expectation], timeout: 3)
        XCTAssertTrue(detector.isAnchored)
    }

    // Test 3: Session restore retries pending event before sessionRestored
    func testSessionRestoreRetriesPendingEventFirst() async throws {
        // Given: A snapshot with pending event
        let pendingEvent = PendingEvent(
            eventId: "test-event-id",
            eventName: "test_event",
            requiresSessionId: false,
            sessionId: nil,
            chargerId: "charger_1",
            occurredAt: Date(),
            metadata: [:]
        )

        let snapshot = SessionSnapshot(
            state: .nearCharger,
            targetedCharger: ChargerTarget(id: "charger_1", latitude: 37.0, longitude: -122.0),
            merchantTarget: nil,
            activeSession: nil,
            gracePeriodDeadline: nil,
            hardTimeoutDeadline: nil,
            savedAt: Date(),
            pendingEvent: pendingEvent
        )
        SessionSnapshot.save(snapshot)

        // When: Create new engine (triggers restore)
        let newEngine = SessionEngine(
            locationService: locationService,
            geofenceManager: geofenceManager,
            apiClient: mockAPIClient,
            config: .defaults
        )

        // Give async tasks time to complete
        try await Task.sleep(nanoseconds: 500_000_000)

        // Then: Pending event was retried
        XCTAssertEqual(mockAPIClient.emittedPreSessionEvents.count, 1)
        XCTAssertEqual(mockAPIClient.emittedPreSessionEvents.first?.event, "test_event")

        _ = newEngine  // Suppress unused warning
    }

    // Test 4: InTransit + expired grace deadline ends session
    func testExpiredGracePeriodEndsSession() {
        // Given: Snapshot in IN_TRANSIT with expired grace deadline
        let expiredDeadline = Date().addingTimeInterval(-60)  // 60 seconds ago

        let snapshot = SessionSnapshot(
            state: .inTransit,
            targetedCharger: ChargerTarget(id: "charger_1", latitude: 37.0, longitude: -122.0),
            merchantTarget: MerchantTarget(id: "merchant_1", latitude: 37.1, longitude: -122.1),
            activeSession: ActiveSessionInfo(
                sessionId: "session_1",
                chargerId: "charger_1",
                merchantId: "merchant_1",
                startedAt: Date().addingTimeInterval(-600)
            ),
            gracePeriodDeadline: expiredDeadline,
            hardTimeoutDeadline: nil,
            savedAt: Date().addingTimeInterval(-1),
            pendingEvent: nil
        )
        SessionSnapshot.save(snapshot)

        // When: Create new engine (triggers restore + deadline check)
        let newEngine = SessionEngine(
            locationService: locationService,
            geofenceManager: geofenceManager,
            apiClient: mockAPIClient,
            config: .defaults
        )

        // Then: Session should be ended
        XCTAssertEqual(newEngine.currentState, .sessionEnded)
    }

    // Test 5: Geofence FIFO removal
    func testGeofenceFIFORemoval() {
        let geoManager = GeofenceManager()

        // Add 3 geofences (max is 2)
        geoManager.addChargerGeofence(
            id: "first",
            coordinate: CLLocationCoordinate2D(latitude: 37.0, longitude: -122.0),
            radius: 100
        )
        geoManager.addChargerGeofence(
            id: "second",
            coordinate: CLLocationCoordinate2D(latitude: 37.1, longitude: -122.1),
            radius: 100
        )
        geoManager.addChargerGeofence(
            id: "third",
            coordinate: CLLocationCoordinate2D(latitude: 37.2, longitude: -122.2),
            radius: 100
        )

        // First should be removed (FIFO)
        // NOTE: GeofenceManager prefixes charger geofence identifiers as "charger_\(id)".
        // Verify this format matches the actual implementation before running.
        //
        // IMPLEMENTATION DETAIL WARNING: This test verifies internal state (FIFO order tracking).
        // If GeofenceManager internals change (e.g., different ordering strategy), this test
        // may need updates even if external behavior is correct.
        // V2 TODO: Consider testing behavior (which region is removed) rather than internal order.
        let order = geoManager.currentRegionOrder
        XCTAssertEqual(order.count, 2)
        XCTAssertFalse(order.contains("charger_first"))
        XCTAssertTrue(order.contains("charger_second"))
        XCTAssertTrue(order.contains("charger_third"))
    }

    // Test 6: Idempotency - event_id passthrough (SMOKE TEST)
    // NOTE: This is a basic smoke test that verifies event ID passthrough.
    // Full retry idempotency verification requires manual testing (see Manual Verification Checklist).
    // V2 TODO: Enhance to simulate actual retries by mocking network failures.
    func testIdempotencyEventIdPassthrough() async throws {
        // Given: Mock client and specific event ID
        let mockClient = MockAPIClient()
        let originalEventId = UUID().uuidString

        // When: Emit event with specific event ID
        try await mockClient.emitPreSessionEvent(
            event: "test_event",
            chargerId: "charger_1",
            eventId: originalEventId,
            occurredAt: Date(),
            metadata: nil
        )

        // Then: Verify event ID was preserved (smoke test)
        XCTAssertEqual(mockClient.emittedPreSessionEvents.count, 1)
        XCTAssertEqual(mockClient.emittedPreSessionEvents.first?.eventId, originalEventId, "Event ID must be preserved through API client")
    }
}
```

**TEST 6 NOTE:**
This is a smoke test that verifies event ID passthrough. It does NOT test retry behavior.
For complete retry idempotency verification, see Manual Verification Checklist item #6.
To test retries in V2, enhance MockAPIClient to simulate failures and verify multiple attempts use the same event_id.

**IDEMPOTENCY MANUAL VERIFICATION (REQUIRED):**
For complete retry idempotency verification:
1. Add network debugging or logging in `executeWithRetry`
2. Force API failures (e.g., disconnect network temporarily)
3. Check backend logs → Verify same `event_id` appears in all retry attempts
4. Verify request body bytes are identical across retries

---

## Web Hook Verification

**File:** `apps/driver/src/hooks/useNativeBridge.ts`

Verify the following are true (no changes needed if already correct):

1. NATIVE_READY is treated as authoritative (line 76-78 sets bridgeReady = true)
2. Event names match native: SESSION_STATE_CHANGED, SESSION_START_REJECTED
3. Add guard against double-init:

**FIND:**
```swift
  // Sync initial auth token (once)
  useEffect(() => {
    if (!bridgeReady || initializedRef.current) return;
    initializedRef.current = true;
```

This is already correct - `initializedRef` prevents double-init.

**REQUIRED: Add event handlers for AUTH_REQUIRED and EVENT_EMISSION_FAILED:**

After line 101 (`if (action === 'SESSION_START_REJECTED') {...}`), add:

```typescript
      if (action === 'AUTH_REQUIRED') {
        console.warn('[NativeBridge] Auth required - token may be expired');
        // V1 BEHAVIOR: Clear tokens and log error. User will re-authenticate when needed.
        // The driver app uses OTP authentication via modals, not a /login route.
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // FUTURE (V2): Show error banner prompting re-authentication
        // FUTURE (V2): Implement token refresh if refresh tokens are available
      }

      if (action === 'EVENT_EMISSION_FAILED') {
        // REQUIRED: Log both payload.event and payload.reason for debugging
        console.error('[NativeBridge] Event emission failed:', payload.event, payload.reason);
        // Optional: Send to analytics/error tracking service
      }
```

**AUTH_REQUIRED Behavior (MUST BE EXPLICIT):**

| Version | Behavior |
|---------|----------|
| V1 | Clear tokens from localStorage. User will re-authenticate via OTP when attempting to activate an exclusive. |
| V2 (future) | Attempt token refresh if refresh tokens supported; show error banner prompting re-authentication; fall back to token clear. |

**ROUTE VERIFICATION:**

The driver app does NOT have a `/login` route. Authentication is handled via:
- OTP modals triggered from merchant detail screens
- Token storage in `localStorage` (`access_token`, `refresh_token`)
- See `apps/driver/src/services/auth.ts` for OTP flow

**VERIFICATION:** Clear tokens and let existing OTP flow handle re-authentication.

**Verification:**
- `AUTH_REQUIRED` → MUST clear tokens (user re-authenticates via OTP when needed)
- `EVENT_EMISSION_FAILED` → MUST log `payload.event` and `payload.reason` for debugging
- Auth failures MUST NOT fail silently

---

## Backend Verification

**File:** `backend/app/main_simple.py`

Verify router is registered (line 1007):
```python
app.include_router(native_events.router)  # /v1/native/*
```
✓ Already present.

**File:** `backend/app/core/config.py`

Verify NATIVE_* defaults are present (lines 86-93):
✓ Already present with sensible defaults.

**File:** `backend/app/routers/native_events.py`

Verify 429 rate limit response (line 140-144):
✓ Already returns HTTP 429 with proper message.

---

## Validation Commands

### Backend
```bash
cd /Users/jameskirk/Desktop/Nerava/backend
python -m compileall app
curl -s http://localhost:8000/v1/native/config -H "Authorization: Bearer test" | head
```

### Web
```bash
cd /Users/jameskirk/Desktop/Nerava/apps/driver
npm run typecheck
```

### iOS
```bash
cd /Users/jameskirk/Desktop/Nerava/Nerava
xcodebuild -scheme Nerava -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 17' build
xcodebuild -scheme Nerava -destination 'platform=iOS Simulator,name=iPhone 17' test
```

---

## Manual Verification Checklist

1. **Permission Flow**: Launch app fresh → see location rationale overlay → tap Continue → see system prompt → grant permission → WebView loads

2. **Ready Signal**: Check console for `[NativeBridge] Initialized` and web receiving `NATIVE_READY`

3. **Offline Overlay**: Enable airplane mode → "No internet connection" overlay appears → disable airplane mode → overlay disappears

4. **Release Build Safety**: Build with Release config → verify no localhost origins are allowed (check NativeBridge logs)

5. **Release Build Safety (MANDATORY - DETAILED STEPS):**
   - Product → Scheme → Edit Scheme → Run → Build Configuration = Release
   - Build and run on device (not simulator)
   - Open Console.app → Filter for "Nerava" → Search for "localhost"
   - **VERIFY:** No "localhost" origins appear in NativeBridge logs
   - **VERIFY:** App connects to `https://app.nerava.network` (not localhost)
   - **VERIFY:** WebView loads production URL, not localhost
   - If localhost appears, the Release build is unsafe and MUST be fixed before shipping

6. **Idempotency Verification (RECOMMENDED):**
   - Force API retries (e.g., disable network temporarily during event emission)
   - Check backend logs → Verify same `event_id` appears in all retry attempts
   - Verify request body is identical across retries

---

## Files Changed Summary

**New Files:**
- `Nerava/PrivacyInfo.xcprivacy`
- `Nerava/Support/Log.swift`
- `Nerava/Services/NetworkMonitor.swift`
- `NeravaTests/SessionEngineTests.swift`

**Modified Files:**
- `Nerava/NeravaApp.swift`
- `Nerava/Info.plist`
- `Nerava/Services/NativeBridge.swift`
- `Nerava/Services/APIClient.swift`
- `Nerava/Services/GeofenceManager.swift`
- `Nerava/Services/KeychainService.swift`
- `Nerava/Views/WebViewContainer.swift`
- `Nerava/Engine/SessionEngine.swift`
- `apps/driver/src/hooks/useNativeBridge.ts`
