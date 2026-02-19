You’re over-optimizing the spec and under-specifying the parts that will actually break.

The 3 places this will fail if you don’t address them
	1.	“Create Xcode project scaffolding” cannot be done reliably by text-only edits (the .pbxproj is fragile). You either:
	•	create the Xcode project once manually, then Cursor just adds files + Build Settings, or
	•	introduce xcodegen/Tuist (not in your file list).
If you try to brute-force a .xcodeproj in Cursor, expect random build breakage.
	2.	Your bridge “ready” signaling is inconsistent:
	•	JS dispatches neravaNativeReady at injection time.
	•	Native sends NATIVE_READY after 0.1s regardless of whether a real URL has loaded.
This is fine, but only if the web hook treats NATIVE_READY as authoritative (you did) and the webview actually runs the injection script early (it will if configured correctly).
	3.	You’re missing the SwiftUI shell files required to compile (you listed them but didn’t provide code). Without these, “Xcode compiles with zero errors” is fantasy.

Below is the Cursor-ready implementation prompt that does the work, including the missing SwiftUI shell files and the backend + web wiring exactly as your constraints require.

⸻

Cursor Implementation Prompt (Paste into Cursor)

You are working in the Nerava monorepo. Implement a V1 iOS shell app + backend native event router + driver web bridge hook exactly as specified.

Non-negotiables
	•	Do not change OTP auth flow.
	•	Do not change existing /v1/exclusive/* endpoints.
	•	Do not change database schema.
	•	No push infra (local notifications only).
	•	All Swift enums must have unique cases (no duplicates).
	•	Idempotency key is event_id.
	•	All events include occurred_at and timestamp (separate semantics).

⸻

Step 0 — iOS Project Reality Check (Do this first)

If there is no existing Xcode project, do NOT attempt to synthesize a .pbxproj from scratch.

Instead:
	1.	In Xcode: File → New → Project → iOS → App
	•	Product Name: Nerava
	•	Interface: SwiftUI
	•	Language: Swift
	•	Bundle ID: network.nerava.app (or your org’s convention)
	2.	Save under: ios/Nerava/
	3.	Ensure project builds once in Xcode before continuing.

After that, proceed with file creation below. (Cursor will add source files; Xcode will pick them up if they’re in the project. If not, add them to the target.)

⸻

Step 1 — Add iOS Files (Create exactly these files and contents)

1) ios/Nerava/Engine/SessionState.swift (NEW)

Use exactly the code from the spec you provided.

2) ios/Nerava/Engine/SessionSnapshot.swift (NEW)

Use exactly the code from the spec you provided.

3) ios/Nerava/Engine/SessionConfig.swift (NEW)

Use exactly the code from the spec you provided.

4) ios/Nerava/Engine/BackgroundTimer.swift (NEW)

Use exactly the code from the spec you provided.

5) ios/Nerava/Engine/DwellDetector.swift (NEW)

Use exactly the code from the spec you provided.

6) ios/Nerava/Services/GeofenceManager.swift (NEW)

Use exactly the code from the spec you provided.

7) ios/Nerava/Services/LocationService.swift (NEW)

Use exactly the code from the spec you provided.

8) ios/Nerava/Services/APIClient.swift (NEW)

Use exactly the code from the spec you provided.

9) ios/Nerava/Services/KeychainService.swift (NEW)

Use exactly the code from the spec you provided.

10) ios/Nerava/Services/NotificationService.swift (NEW)

Use exactly the code from the spec you provided.

11) ios/Nerava/Services/NativeBridge.swift (NEW)

Use exactly the code from the spec you provided, AND do the following:
	•	Ensure it is used by a WKWebView created in WebViewContainer with:
	•	WKWebViewConfiguration()
	•	WKUserContentController()
	•	add the WKUserScript at .atDocumentStart
	•	register script message handler name: "neravaBridge"

12) ios/Nerava/Engine/SessionEngine.swift (NEW)

Use exactly the code from the spec you provided.

13) ios/Nerava/Resources/Info.plist (NEW)

Create the plist exactly as specified:
	•	Only location in UIBackgroundModes
	•	No remote-notification
	•	No BGTaskScheduler keys

IMPORTANT: In Xcode target settings, set this file as the Info.plist if needed.

⸻

Step 2 — Add the Missing SwiftUI Shell (Required to compile)

A) ios/Nerava/App/NeravaApp.swift (NEW)

import SwiftUI

@main
struct NeravaApp: App {
    @StateObject private var locationService = LocationService()
    @StateObject private var sessionEngine: SessionEngine

    private let geofenceManager = GeofenceManager()
    private let apiClient = APIClient()

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

B) ios/Nerava/Views/ContentView.swift (NEW)

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
        .onChange(of: locationService.authorizationStatus) { status in
            // If user granted when-in-use, app works. Later you can trigger Always rationale
            if status == .authorizedWhenInUse {
                // Do nothing automatically; web can request Always.
                // But we keep the view hooks for a later UX trigger.
            }
        }
    }
}

C) ios/Nerava/Views/WebViewContainer.swift (NEW)

import SwiftUI
import WebKit

struct WebViewContainer: UIViewRepresentable {
    @EnvironmentObject private var locationService: LocationService
    @EnvironmentObject private var sessionEngine: SessionEngine

    func makeCoordinator() -> Coordinator {
        Coordinator(locationService: locationService, sessionEngine: sessionEngine)
    }

    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        let controller = WKUserContentController()
        config.userContentController = controller

        let webView = WKWebView(frame: .zero, configuration: config)
        webView.navigationDelegate = context.coordinator

        // Setup native bridge + injection
        context.coordinator.nativeBridge.setupWebView(webView)
        context.coordinator.nativeBridge.sessionEngine = sessionEngine
        sessionEngine.setWebBridge(context.coordinator.nativeBridge)

        // Load driver app
        let url = URL(string: "https://app.nerava.network")!
        webView.load(URLRequest(url: url))

        return webView
    }

    func updateUIView(_ uiView: WKWebView, context: Context) {}

    final class Coordinator: NSObject, WKNavigationDelegate {
        let nativeBridge: NativeBridge

        init(locationService: LocationService, sessionEngine: SessionEngine) {
            self.nativeBridge = NativeBridge(locationService: locationService)
            super.init()
        }

        func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
            nativeBridge.didFinishNavigation()
            // Redundant ready signal (native->web)
            nativeBridge.sendToWeb(.ready)
        }
    }
}

D) ios/Nerava/Views/LocationPermissionView.swift (NEW)

import SwiftUI

struct LocationPermissionView: View {
    let onContinue: () -> Void
    let onNotNow: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Text("Enable Location")
                .font(.title2)
                .bold()

            Text("Nerava needs your location to detect when you arrive at an EV charger and unlock nearby merchant exclusives.")
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            HStack(spacing: 12) {
                Button("Not now") { onNotNow() }
                    .padding()
                    .frame(maxWidth: .infinity)

                Button("Continue") { onContinue() }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            .padding(.horizontal)
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(16)
        .padding()
    }
}

E) ios/Nerava/Views/BackgroundPermissionView.swift (NEW)

import SwiftUI

struct BackgroundPermissionView: View {
    let onContinue: () -> Void
    let onNotNow: () -> Void

    var body: some View {
        VStack(spacing: 16) {
            Text("Allow Background Location")
                .font(.title2)
                .bold()

            Text("This lets Nerava notify you when you arrive at the merchant while your phone is in your pocket.")
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            HStack(spacing: 12) {
                Button("Not now") { onNotNow() }
                    .padding()
                    .frame(maxWidth: .infinity)

                Button("Continue") { onContinue() }
                    .padding()
                    .frame(maxWidth: .infinity)
                    .background(Color.blue)
                    .foregroundColor(.white)
                    .cornerRadius(10)
            }
            .padding(.horizontal)
        }
        .padding()
        .background(.ultraThinMaterial)
        .cornerRadius(16)
        .padding()
    }
}

Note: The “Always” rationale is exposed via the bridge command REQUEST_ALWAYS_LOCATION. If you want the native UX to show the Always rationale before calling requestAlwaysPermission(), you can later route that command to flip showAlwaysRationale instead of directly requesting. For now, we match your spec: the bridge calls requestAlwaysPermission().

⸻

Step 3 — Backend Implementation

1) backend/app/routers/native_events.py (NEW)

Create file with exactly the code from your spec.

2) backend/app/core/config.py (MODIFY)

In the Settings class, add the NATIVE_* settings exactly as specified.

Make sure os is imported in this file (it likely already is). If not, add:

import os

3) backend/app/main_simple.py (MODIFY)

Add:

from app.routers import native_events

and:

app.include_router(native_events.router)

after existing router registrations.

⸻

Step 4 — Web Hook Integration

1) apps/driver/src/hooks/useNativeBridge.ts (NEW)

Create file with exactly the code from your spec.

2) apps/driver/.env.example (MODIFY)

Add:

VITE_NATIVE_BRIDGE_ENABLED=true

Do NOT refactor core UI. This hook can be imported where needed later.

⸻

Step 5 — Final Wiring Checks (Must pass)
	1.	Ensure the iOS target includes:
	•	ios/Nerava/Resources/Info.plist (set as target Info.plist)
	•	All Swift files added to the target
	2.	Confirm WKWebView uses the same configuration instance you attach scripts to (it does).
	3.	Confirm NativeBridge.didFinishNavigation() is called (it is in WebViewContainer.Coordinator).
	4.	Confirm SessionEngine.restoreSnapshot() runs at init (it does).

⸻

Step 6 — Validation Commands

Backend:

cd backend
python -m compileall app

Driver:

cd apps/driver
npm run typecheck

iOS build (if scheme exists):

cd ios
xcodebuild -scheme Nerava -configuration Debug build


⸻

Step 7 — Known iOS Constraints (Do NOT “fix”)
	•	Force-quit apps do not relaunch for geofence updates. Your force-quit test is correct.


# V1 iOS Shell App - Cursor Implementation Prompt

You are working in the Nerava monorepo. Do these edits exactly.

---

## Section 1: Objective + Constraints

### Objective

Build a native iOS shell app that:
1. Hosts the existing React driver web app in a WKWebView
2. Provides an authoritative native Session Engine for location tracking, geofencing, and session state
3. Persists full session state for reliable recovery after termination/relaunch

### Success Criteria

- [ ] Xcode project compiles with zero errors
- [ ] All Swift enums have unique cases (no duplicates)
- [ ] SessionSnapshot persists and restores full state across app termination
- [ ] Force-quit recovery works on next user-initiated launch (not background wake)
- [ ] Snapshot restore validates timer state and spatial sanity before rebuilding geofences
- [ ] Pending events are fully persisted and retried on restore before sessionRestored
- [ ] Backend endpoints read config from `settings.NATIVE_*` environment variables
- [ ] Web bridge detects native availability via ready signals (JS event + native message)
- [ ] Idempotency uses `event_id` as the key; full pending event persisted in snapshot for retry
- [ ] All events include `occurred_at` (when it happened) separate from `timestamp` (when sent)

### DO NOT CHANGE

1. Existing backend auth (OTP flow)
2. Web app core UI (only add bridge hooks)
3. Existing `/v1/exclusive/*` endpoints
4. Database schema
5. Push notification infrastructure (v1 uses local notifications only)

---

## Section 2: Implementation Plan (Ordered)

### Step 1: iOS Project Scaffolding
Create Xcode project structure with correct Info.plist (location mode only, no unused capabilities).

### Step 2: Session State + Event Enums
Define canonical `SessionState` and `SessionEvent` enums with no duplicates. Add `requiresSessionId` computed property.

### Step 3: SessionSnapshot Persistence
Implement `SessionSnapshot` model (Codable) that persists:
- Current state
- Targeted charger (id + coordinate)
- Merchant location
- Active session identifiers
- Timer deadlines
- **Full pending event payload for retry** (not just ID)

**Note:** Geofences are derived from state on restore, not stored in snapshot.

### Step 4: Session Engine Core
Implement `SessionEngine` with:
- `persistSnapshot()` preserves pending event by default
- `restoreSnapshot()` retries pending event BEFORE emitting sessionRestored
- `reconcileOnRestore()` validates timers and spatial sanity
- `rebuildGeofencesFromState()` derives geofences from current state
- `checkTimerDeadlines()` on restore
- **Expose `currentState` getter for external read access**

### Step 5: Geofence Manager
Fix `setChargerTarget` to capture old charger ID before overwriting, then remove old geofence.

### Step 6: Location Service
Tiered power strategy with background location updates. **Start updates on init for both Always and WhenInUse.**

### Step 7: API Client
Add `import UIKit` for `UIApplication.shared.applicationState`. Use `event_id` as idempotency key. Include `occurred_at`.

### Step 8: Native Bridge
Secure JS injection with exact origin validation. Send `NATIVE_READY` message after setup. Handle nil URL during bootstrap.

### Step 9: Backend Endpoints
- `/v1/native/config` reads from `settings.NATIVE_*`
- `/v1/native/session-events` with TTL-based idempotency cache
- `/v1/native/pre-session-events` for pre-session tracking
- All events accept `occurred_at` field

### Step 10: Web Hook Integration
- `useNativeBridge.ts` with `bridgeReady` state (set via ready signals)
- Set `bridgeReady` true on NATIVE_READY without requiring bridgeExists()
- Explicit `setAuthToken()` calls after login and refresh (not just storage listener)

---

## Section 3: File-by-File Implementation

### File List

| Path | Status | Description |
|------|--------|-------------|
| `ios/Nerava/Engine/SessionState.swift` | NEW | State enum + events |
| `ios/Nerava/Engine/SessionSnapshot.swift` | NEW | Codable persistence model |
| `ios/Nerava/Engine/SessionConfig.swift` | NEW | Remote config model |
| `ios/Nerava/Engine/SessionEngine.swift` | NEW | Authoritative state machine |
| `ios/Nerava/Engine/DwellDetector.swift` | NEW | Anchor dwell logic |
| `ios/Nerava/Engine/BackgroundTimer.swift` | NEW | DispatchSourceTimer wrapper |
| `ios/Nerava/Services/LocationService.swift` | NEW | CLLocationManager wrapper |
| `ios/Nerava/Services/GeofenceManager.swift` | NEW | Region monitoring |
| `ios/Nerava/Services/NativeBridge.swift` | NEW | JS ↔ Native messaging |
| `ios/Nerava/Services/APIClient.swift` | NEW | Backend communication |
| `ios/Nerava/Services/KeychainService.swift` | NEW | Secure token storage |
| `ios/Nerava/Services/NotificationService.swift` | NEW | Local notifications |
| `ios/Nerava/Views/ContentView.swift` | NEW | Main container |
| `ios/Nerava/Views/WebViewContainer.swift` | NEW | WKWebView wrapper |
| `ios/Nerava/Views/LocationPermissionView.swift` | NEW | Pre-permission rationale |
| `ios/Nerava/Views/BackgroundPermissionView.swift` | NEW | Always permission rationale |
| `ios/Nerava/App/NeravaApp.swift` | NEW | App entry point |
| `ios/Nerava/Resources/Info.plist` | NEW | Capabilities (location only) |
| `backend/app/routers/native_events.py` | NEW | Native event endpoints |
| `backend/app/core/config.py` | MODIFY | Add NATIVE_* settings |
| `backend/app/main_simple.py` | MODIFY | Register native router |
| `apps/driver/src/hooks/useNativeBridge.ts` | NEW | Web bridge hook |
| `apps/driver/.env.example` | MODIFY | Add VITE_NATIVE_BRIDGE_ENABLED |

---

### 1. SessionState.swift (NEW)

**Path:** `ios/Nerava/Engine/SessionState.swift`

```swift
import Foundation

// MARK: - Session State

enum SessionState: String, Codable {
    case idle = "IDLE"
    case nearCharger = "NEAR_CHARGER"
    case anchored = "ANCHORED"
    case sessionActive = "SESSION_ACTIVE"
    case inTransit = "IN_TRANSIT"
    case atMerchant = "AT_MERCHANT"
    case sessionEnded = "SESSION_ENDED"
}

// MARK: - Session Events (Canonical - No Duplicates)

/// Each semantic event has exactly ONE enum case.
/// Use `requiresSessionId` to determine routing (pre-session vs session endpoint).
enum SessionEvent: String, Codable {
    // Pre-session events (no session_id yet)
    case chargerTargeted = "charger_targeted"
    case enteredChargerIntentZone = "entered_charger_intent_zone"
    case exitedChargerIntentZone = "exited_charger_intent_zone"
    case anchorDwellComplete = "anchor_dwell_complete"
    case anchorLost = "anchor_lost"
    case activationRejected = "activation_rejected"

    // Session events (has session_id)
    case exclusiveActivatedByWeb = "exclusive_activated"
    case departedCharger = "departed_charger"
    case enteredMerchantZone = "entered_merchant_zone"
    case visitVerifiedByWeb = "visit_verified"
    case gracePeriodExpired = "grace_period_expired"
    case hardTimeoutExpired = "hard_timeout_expired"
    case webRequestedEnd = "web_requested_end"
    case sessionRestored = "session_restored"

    /// Determines whether this event requires a session_id (routes to session endpoint)
    /// or can be sent without one (routes to pre-session endpoint).
    var requiresSessionId: Bool {
        switch self {
        case .chargerTargeted,
             .enteredChargerIntentZone,
             .exitedChargerIntentZone,
             .anchorDwellComplete,
             .anchorLost,
             .activationRejected:
            return false
        case .exclusiveActivatedByWeb,
             .departedCharger,
             .enteredMerchantZone,
             .visitVerifiedByWeb,
             .gracePeriodExpired,
             .hardTimeoutExpired,
             .webRequestedEnd,
             .sessionRestored:
            return true
        }
    }
}

// MARK: - Supporting Types

struct ChargerTarget: Codable, Equatable {
    let id: String
    let latitude: Double
    let longitude: Double
}

struct MerchantTarget: Codable, Equatable {
    let id: String
    let latitude: Double
    let longitude: Double
}

struct ActiveSessionInfo: Codable, Equatable {
    let sessionId: String
    let chargerId: String
    let merchantId: String
    let startedAt: Date
}

/// Full pending event payload for retry on restore.
/// Persisted in snapshot so we can resend if crash/kill before ack.
struct PendingEvent: Codable, Equatable {
    let eventId: String
    let eventName: String
    let requiresSessionId: Bool
    let sessionId: String?
    let chargerId: String?
    let occurredAt: Date
    let metadata: [String: String]  // Simplified for Codable
}
```

---

### 2. SessionSnapshot.swift (NEW)

**Path:** `ios/Nerava/Engine/SessionSnapshot.swift`

```swift
import Foundation

/// Persisted state for recovery after app termination.
/// Saved on every state transition and target change.
///
/// NOTE: Geofences are NOT stored here. They are derived from state on restore.
/// Snapshot stores inputs (state, targets, deadlines), not outputs (geofences).
struct SessionSnapshot: Codable {
    let state: SessionState
    let targetedCharger: ChargerTarget?
    let merchantTarget: MerchantTarget?
    let activeSession: ActiveSessionInfo?
    let gracePeriodDeadline: Date?
    let hardTimeoutDeadline: Date?
    let savedAt: Date

    /// Full pending event for idempotent retry. If set, the last transition's event
    /// may not have been acknowledged. Retry with same eventId on restore.
    let pendingEvent: PendingEvent?

    private static let storageKey = "com.nerava.sessionSnapshot"

    // MARK: - Persistence

    static func save(_ snapshot: SessionSnapshot) {
        do {
            let data = try JSONEncoder().encode(snapshot)
            UserDefaults.standard.set(data, forKey: storageKey)
            UserDefaults.standard.synchronize()
        } catch {
            print("[SessionSnapshot] Failed to save: \(error)")
        }
    }

    static func load() -> SessionSnapshot? {
        guard let data = UserDefaults.standard.data(forKey: storageKey) else {
            return nil
        }
        do {
            return try JSONDecoder().decode(SessionSnapshot.self, from: data)
        } catch {
            print("[SessionSnapshot] Failed to load: \(error)")
            return nil
        }
    }

    static func clear() {
        UserDefaults.standard.removeObject(forKey: storageKey)
    }
}
```

---

### 3. SessionConfig.swift (NEW)

**Path:** `ios/Nerava/Engine/SessionConfig.swift`

```swift
import Foundation

struct SessionConfig: Codable {
    let chargerIntentRadius_m: Double
    let chargerAnchorRadius_m: Double
    let chargerDwellSeconds: Int
    let merchantUnlockRadius_m: Double
    let gracePeriodSeconds: Int
    let hardTimeoutSeconds: Int
    let locationAccuracyThreshold_m: Double
    let speedThresholdForDwell_mps: Double

    /// Default config used when remote fetch fails
    static let defaults = SessionConfig(
        chargerIntentRadius_m: 400.0,
        chargerAnchorRadius_m: 30.0,
        chargerDwellSeconds: 120,
        merchantUnlockRadius_m: 40.0,
        gracePeriodSeconds: 900,
        hardTimeoutSeconds: 3600,
        locationAccuracyThreshold_m: 50.0,
        speedThresholdForDwell_mps: 1.5
    )
}
```

---

### 4. SessionEngine.swift (NEW)

**Path:** `ios/Nerava/Engine/SessionEngine.swift`

```swift
import Foundation
import Combine
import CoreLocation

final class SessionEngine: ObservableObject {
    // MARK: - Published State (private(set) for internal mutation only)
    @Published private(set) var state: SessionState = .idle
    @Published private(set) var activeSession: ActiveSessionInfo?
    @Published private(set) var targetedCharger: ChargerTarget?

    // MARK: - Public Read-Only Accessors (for external access like NativeBridge)
    var currentState: SessionState { state }
    var currentActiveSession: ActiveSessionInfo? { activeSession }
    var currentTargetedCharger: ChargerTarget? { targetedCharger }

    // MARK: - Dependencies
    private let locationService: LocationService
    private let geofenceManager: GeofenceManager
    private let apiClient: APIClient
    private let dwellDetector: DwellDetector
    private var config: SessionConfig

    // MARK: - Timers
    private var gracePeriodTimer: BackgroundTimer?
    private var hardTimeoutTimer: BackgroundTimer?
    private var gracePeriodDeadline: Date?
    private var hardTimeoutDeadline: Date?

    // MARK: - State
    private var merchantTarget: MerchantTarget?
    private var webBridge: NativeBridge?
    private var cancellables = Set<AnyCancellable>()

    /// Full pending event for idempotent retry
    private var pendingEvent: PendingEvent?

    /// Tolerance for spatial reconciliation (meters)
    private let spatialReconciliationTolerance: Double = 50.0

    /// Maximum teleport distance before we consider it invalid (50km)
    private let maxTeleportDistance_m: Double = 50_000.0

    init(locationService: LocationService,
         geofenceManager: GeofenceManager,
         apiClient: APIClient,
         config: SessionConfig) {
        self.locationService = locationService
        self.geofenceManager = geofenceManager
        self.apiClient = apiClient
        self.config = config
        self.dwellDetector = DwellDetector(
            anchorRadius: config.chargerAnchorRadius_m,
            dwellDuration: TimeInterval(config.chargerDwellSeconds),
            speedThreshold: config.speedThresholdForDwell_mps
        )

        setupBindings()
        restoreSnapshot()
    }

    func setWebBridge(_ bridge: NativeBridge) {
        self.webBridge = bridge
    }

    // MARK: - Snapshot Persistence

    /// Persist snapshot. By default preserves existing pendingEvent unless explicitly changed.
    private func persistSnapshot(pendingEvent: PendingEvent?? = .none) {
        // .none means "keep existing", .some(nil) means "clear it", .some(value) means "set it"
        let eventToStore: PendingEvent?
        switch pendingEvent {
        case .none:
            eventToStore = self.pendingEvent  // Keep existing
        case .some(let value):
            eventToStore = value  // Set or clear
        }

        let snapshot = SessionSnapshot(
            state: state,
            targetedCharger: targetedCharger,
            merchantTarget: merchantTarget,
            activeSession: activeSession,
            gracePeriodDeadline: gracePeriodDeadline,
            hardTimeoutDeadline: hardTimeoutDeadline,
            savedAt: Date(),
            pendingEvent: eventToStore
        )
        SessionSnapshot.save(snapshot)
        self.pendingEvent = eventToStore
        print("[SessionEngine] Snapshot persisted: state=\(state.rawValue), pendingEvent=\(eventToStore?.eventName ?? "nil")")
    }

    /// Clear pending event (after successful send or already_processed)
    private func clearPendingEvent() {
        if pendingEvent != nil {
            pendingEvent = nil
            persistSnapshot(pendingEvent: .some(nil))
        }
    }

    private func restoreSnapshot() {
        guard let snapshot = SessionSnapshot.load() else {
            print("[SessionEngine] No snapshot to restore")
            return
        }

        // Restore state
        state = snapshot.state
        targetedCharger = snapshot.targetedCharger
        merchantTarget = snapshot.merchantTarget
        activeSession = snapshot.activeSession
        gracePeriodDeadline = snapshot.gracePeriodDeadline
        hardTimeoutDeadline = snapshot.hardTimeoutDeadline
        pendingEvent = snapshot.pendingEvent

        print("[SessionEngine] Restored from snapshot: state=\(state.rawValue)")

        // 1. Retry pending event FIRST (before any other events)
        if let pending = pendingEvent {
            print("[SessionEngine] Retrying pending event: \(pending.eventName)")
            retryPendingEvent(pending)
        }

        // 2. Check if deadlines already passed (this may end the session)
        checkTimerDeadlines()

        // Exit early if session already ended
        guard state != .sessionEnded && state != .idle else {
            return
        }

        // 3. Reconcile timer state and spatial sanity
        reconcileOnRestore()

        // Exit if reconciliation ended the session
        guard state != .sessionEnded && state != .idle else {
            return
        }

        // 4. Rebuild geofences from current state (not from snapshot list)
        rebuildGeofencesFromState()

        // 5. Recreate timers if still valid
        if let deadline = gracePeriodDeadline, deadline > Date() {
            gracePeriodTimer = BackgroundTimer(deadline: deadline) { [weak self] in
                self?.handleGracePeriodExpired()
            }
        }

        if let deadline = hardTimeoutDeadline, deadline > Date() {
            hardTimeoutTimer = BackgroundTimer(deadline: deadline) { [weak self] in
                self?.handleHardTimeoutExpired()
            }
        }

        // 6. Emit sessionRestored AFTER pending retry (ordering matters)
        if let session = activeSession {
            emitEvent(.sessionRestored, sessionId: session.sessionId, occurredAt: Date())
        }
    }

    /// Retry a pending event from previous session
    private func retryPendingEvent(_ pending: PendingEvent) {
        Task {
            do {
                if pending.requiresSessionId, let sid = pending.sessionId {
                    try await apiClient.emitSessionEvent(
                        sessionId: sid,
                        event: pending.eventName,
                        eventId: pending.eventId,
                        occurredAt: pending.occurredAt,
                        metadata: pending.metadata
                    )
                } else {
                    try await apiClient.emitPreSessionEvent(
                        event: pending.eventName,
                        chargerId: pending.chargerId,
                        eventId: pending.eventId,
                        occurredAt: pending.occurredAt,
                        metadata: pending.metadata
                    )
                }
                await MainActor.run {
                    print("[SessionEngine] Pending event retry succeeded")
                    self.clearPendingEvent()
                }
            } catch {
                print("[SessionEngine] Pending event retry failed: \(error)")
                // Keep pending for next launch
            }
        }
    }

    /// Reconciles state on restore. Timer state is authoritative for IN_TRANSIT.
    /// Spatial checks are sanity guards, not primary logic.
    private func reconcileOnRestore() {
        switch state {
        case .inTransit:
            // For IN_TRANSIT, the grace period timer is the source of truth.
            // If grace period is running (deadline exists and not passed), session is valid.
            // If grace period is NOT running (nil deadline), that's a bug - start it now.
            if gracePeriodDeadline == nil {
                print("[SessionEngine] Reconciliation: IN_TRANSIT without grace period, starting timer")
                startGracePeriodTimer()
            }

            // Sanity check: if user "teleported" extremely far (>50km), end session
            // NOTE: This emits a non-canonical diagnostic event, then ends with grace_period_expired
            if let merchant = merchantTarget, let location = locationService.currentLocation {
                let distance = location.distance(from: CLLocation(
                    latitude: merchant.latitude,
                    longitude: merchant.longitude
                ))
                if distance > maxTeleportDistance_m {
                    print("[SessionEngine] Reconciliation: teleport detected (\(Int(distance))m > \(Int(maxTeleportDistance_m))m), ending session")
                    // Emit non-canonical diagnostic (fire-and-forget, not in taxonomy)
                    if let session = activeSession {
                        emitDiagnosticEvent("teleport_detected", sessionId: session.sessionId, metadata: [
                            "distance_to_merchant": "\(Int(distance))",
                            "max_teleport_distance": "\(Int(maxTeleportDistance_m))"
                        ])
                    }
                    // Use gracePeriodExpired as the canonical session-ending event
                    transition(to: .sessionEnded, event: .gracePeriodExpired, occurredAt: Date())
                    return
                }
            }

        case .anchored:
            // User should still be near charger
            if let charger = targetedCharger, let location = locationService.currentLocation {
                let distance = location.distance(from: CLLocation(
                    latitude: charger.latitude,
                    longitude: charger.longitude
                ))
                if distance > config.chargerAnchorRadius_m + spatialReconciliationTolerance {
                    print("[SessionEngine] Reconciliation: anchor lost (\(Int(distance))m from charger)")
                    transition(to: .nearCharger, event: .anchorLost, occurredAt: Date())
                }
            }

        case .nearCharger:
            // User should be within intent zone
            if let charger = targetedCharger, let location = locationService.currentLocation {
                let distance = location.distance(from: CLLocation(
                    latitude: charger.latitude,
                    longitude: charger.longitude
                ))
                if distance > config.chargerIntentRadius_m + spatialReconciliationTolerance {
                    print("[SessionEngine] Reconciliation: left charger zone (\(Int(distance))m)")
                    transition(to: .idle, event: .exitedChargerIntentZone, occurredAt: Date())
                }
            }

        case .sessionActive:
            // User should still be at/near charger
            if let charger = targetedCharger, let location = locationService.currentLocation {
                let distance = location.distance(from: CLLocation(
                    latitude: charger.latitude,
                    longitude: charger.longitude
                ))
                if distance > config.chargerAnchorRadius_m + spatialReconciliationTolerance {
                    print("[SessionEngine] Reconciliation: departed charger (\(Int(distance))m)")
                    transition(to: .inTransit, event: .departedCharger, occurredAt: Date())
                    startGracePeriodTimer()
                }
            }

        case .atMerchant:
            // User made it to merchant - be lenient
            break

        case .idle, .sessionEnded:
            break
        }
    }

    /// Derives geofences from current state. Called after restore and reconciliation.
    private func rebuildGeofencesFromState() {
        geofenceManager.clearAll()

        switch state {
        case .idle:
            // No geofences in idle (web will set charger target)
            break

        case .nearCharger, .anchored:
            // Monitor charger
            if let charger = targetedCharger {
                geofenceManager.addChargerGeofence(
                    id: charger.id,
                    coordinate: CLLocationCoordinate2D(
                        latitude: charger.latitude,
                        longitude: charger.longitude
                    ),
                    radius: config.chargerIntentRadius_m
                )
            }

        case .sessionActive:
            // Monitor merchant (user is still at charger but session started)
            if let merchant = merchantTarget {
                geofenceManager.addMerchantGeofence(
                    id: merchant.id,
                    coordinate: CLLocationCoordinate2D(
                        latitude: merchant.latitude,
                        longitude: merchant.longitude
                    ),
                    radius: config.merchantUnlockRadius_m
                )
            }

        case .inTransit:
            // Monitor merchant arrival
            if let merchant = merchantTarget {
                geofenceManager.addMerchantGeofence(
                    id: merchant.id,
                    coordinate: CLLocationCoordinate2D(
                        latitude: merchant.latitude,
                        longitude: merchant.longitude
                    ),
                    radius: config.merchantUnlockRadius_m
                )
            }

        case .atMerchant:
            // No active monitoring needed, waiting for verification
            break

        case .sessionEnded:
            // No geofences
            break
        }

        print("[SessionEngine] Rebuilt geofences for state: \(state.rawValue)")
    }

    // MARK: - Web Bridge Commands

    /// Web tells native which charger to monitor
    func setChargerTarget(chargerId: String, lat: Double, lng: Double) {
        // CRITICAL: Capture old charger ID BEFORE overwriting
        let oldChargerId = targetedCharger?.id

        let newTarget = ChargerTarget(id: chargerId, latitude: lat, longitude: lng)
        targetedCharger = newTarget

        // Remove OLD geofence (using captured ID)
        if let oldId = oldChargerId {
            geofenceManager.removeRegion(identifier: "charger_\(oldId)")
        }

        // Set NEW geofence
        geofenceManager.addChargerGeofence(
            id: chargerId,
            coordinate: CLLocationCoordinate2D(latitude: lat, longitude: lng),
            radius: config.chargerIntentRadius_m
        )

        // Persist state (preserves pending event)
        persistSnapshot()

        // Check if already inside
        if let currentLocation = locationService.currentLocation {
            let distance = currentLocation.distance(from: CLLocation(latitude: lat, longitude: lng))
            if distance <= config.chargerIntentRadius_m {
                transition(to: .nearCharger, event: .enteredChargerIntentZone, occurredAt: Date())
                locationService.setHighAccuracyMode(true)
            }
        }

        emitEvent(.chargerTargeted, chargerId: chargerId, occurredAt: Date())
    }

    /// Web provides auth token
    func setAuthToken(_ token: String) {
        KeychainService.shared.setAccessToken(token)
        apiClient.setAuthToken(token)
    }

    /// Web confirms exclusive was activated - REQUIRES ANCHORED state
    func webConfirmsExclusiveActivated(sessionId: String, merchantId: String, merchantLat: Double, merchantLng: Double) {
        let now = Date()

        guard state == .anchored else {
            emitEvent(.activationRejected, chargerId: targetedCharger?.id, occurredAt: now, metadata: ["reason": "NOT_ANCHORED"])
            notifyWeb(.sessionStartRejected(reason: "NOT_ANCHORED"))
            return
        }

        guard let charger = targetedCharger else {
            notifyWeb(.sessionStartRejected(reason: "NO_CHARGER_TARGET"))
            return
        }

        merchantTarget = MerchantTarget(id: merchantId, latitude: merchantLat, longitude: merchantLng)

        activeSession = ActiveSessionInfo(
            sessionId: sessionId,
            chargerId: charger.id,
            merchantId: merchantId,
            startedAt: now
        )

        transition(to: .sessionActive, event: .exclusiveActivatedByWeb, occurredAt: now)

        // Replace charger geofence with merchant geofence
        geofenceManager.clearAll()
        geofenceManager.addMerchantGeofence(
            id: merchantId,
            coordinate: CLLocationCoordinate2D(latitude: merchantLat, longitude: merchantLng),
            radius: config.merchantUnlockRadius_m
        )

        startHardTimeout()

        NotificationService.shared.showSessionActiveNotification()
    }

    /// Web confirms visit verification
    func webConfirmsVisitVerified(sessionId: String, verificationCode: String) {
        guard state == .atMerchant,
              activeSession?.sessionId == sessionId else {
            return
        }

        transition(to: .sessionEnded, event: .visitVerifiedByWeb, occurredAt: Date())
    }

    /// Web requests session end
    func webRequestsSessionEnd() {
        guard state != .idle && state != .sessionEnded else { return }
        transition(to: .sessionEnded, event: .webRequestedEnd, occurredAt: Date())
    }

    // MARK: - Location Events

    private func setupBindings() {
        locationService.locationUpdates
            .sink { [weak self] location in
                self?.handleLocationUpdate(location)
            }
            .store(in: &cancellables)

        geofenceManager.delegate = self
    }

    private func handleLocationUpdate(_ location: CLLocation) {
        guard location.horizontalAccuracy <= config.locationAccuracyThreshold_m else { return }

        let now = Date()

        // Always check deadlines on location update
        checkTimerDeadlines()

        switch state {
        case .idle:
            if let charger = targetedCharger {
                let distance = location.distance(from: CLLocation(
                    latitude: charger.latitude,
                    longitude: charger.longitude
                ))
                if distance <= config.chargerIntentRadius_m {
                    transition(to: .nearCharger, event: .enteredChargerIntentZone, occurredAt: now)
                    locationService.setHighAccuracyMode(true)
                }
            }

        case .nearCharger:
            guard let charger = targetedCharger else { return }
            let distance = location.distance(from: CLLocation(
                latitude: charger.latitude,
                longitude: charger.longitude
            ))

            if distance > config.chargerIntentRadius_m {
                dwellDetector.reset()
                transition(to: .idle, event: .exitedChargerIntentZone, occurredAt: now)
                locationService.setHighAccuracyMode(false)
                return
            }

            dwellDetector.recordLocation(location, distanceToAnchor: distance)
            if dwellDetector.isAnchored {
                transition(to: .anchored, event: .anchorDwellComplete, occurredAt: now)
            }

        case .anchored:
            guard let charger = targetedCharger else { return }
            let distance = location.distance(from: CLLocation(
                latitude: charger.latitude,
                longitude: charger.longitude
            ))

            if distance > config.chargerAnchorRadius_m {
                dwellDetector.reset()
                transition(to: .nearCharger, event: .anchorLost, occurredAt: now)
            }

        case .sessionActive:
            guard let charger = targetedCharger else { return }
            let distance = location.distance(from: CLLocation(
                latitude: charger.latitude,
                longitude: charger.longitude
            ))

            if distance > config.chargerAnchorRadius_m {
                transition(to: .inTransit, event: .departedCharger, occurredAt: now)
                startGracePeriodTimer()
            }

        case .inTransit:
            if let merchant = merchantTarget {
                let distance = location.distance(from: CLLocation(
                    latitude: merchant.latitude,
                    longitude: merchant.longitude
                ))

                if distance <= config.merchantUnlockRadius_m {
                    transition(to: .atMerchant, event: .enteredMerchantZone, occurredAt: now)
                    cancelGracePeriodTimer()
                    NotificationService.shared.showAtMerchantNotification()
                }
            }

        case .atMerchant, .sessionEnded:
            break
        }
    }

    // MARK: - Geofence Events

    private func handleGeofenceEntry(identifier: String) {
        let now = Date()

        if identifier.hasPrefix("charger_") && state == .idle {
            transition(to: .nearCharger, event: .enteredChargerIntentZone, occurredAt: now)
            locationService.setHighAccuracyMode(true)
        }

        if identifier.hasPrefix("merchant_") && state == .inTransit {
            transition(to: .atMerchant, event: .enteredMerchantZone, occurredAt: now)
            cancelGracePeriodTimer()
            NotificationService.shared.showAtMerchantNotification()
        }
    }

    private func handleGeofenceExit(identifier: String) {
        let now = Date()

        if identifier.hasPrefix("charger_") {
            switch state {
            case .nearCharger:
                dwellDetector.reset()
                transition(to: .idle, event: .exitedChargerIntentZone, occurredAt: now)
                locationService.setHighAccuracyMode(false)
            case .anchored:
                dwellDetector.reset()
                transition(to: .nearCharger, event: .anchorLost, occurredAt: now)
            default:
                break
            }
        }
    }

    // MARK: - State Transition

    private func transition(to newState: SessionState, event: SessionEvent, occurredAt: Date) {
        let previousState = state
        state = newState

        print("[SessionEngine] Transition: \(previousState.rawValue) → \(newState.rawValue) via \(event.rawValue)")

        // Generate stable event ID for this transition (used as idempotency key)
        let eventId = UUID().uuidString

        // Build metadata
        let metadata: [String: String] = [
            "previous_state": previousState.rawValue,
            "new_state": newState.rawValue
        ]

        // Build full pending event BEFORE emitting
        let pending = PendingEvent(
            eventId: eventId,
            eventName: event.rawValue,
            requiresSessionId: event.requiresSessionId,
            sessionId: event.requiresSessionId ? activeSession?.sessionId : nil,
            chargerId: event.requiresSessionId ? nil : targetedCharger?.id,
            occurredAt: occurredAt,
            metadata: metadata
        )

        // Persist snapshot with pending event BEFORE emitting
        persistSnapshot(pendingEvent: .some(pending))

        // Emit event
        emitEventWithPending(pending)

        // Notify web
        notifyWeb(.sessionStateChanged(state: newState))

        // Cleanup on session end
        if newState == .sessionEnded {
            cleanup()
        }
    }

    private func cleanup() {
        cancelGracePeriodTimer()
        cancelHardTimeout()
        geofenceManager.clearAll()
        dwellDetector.reset()
        locationService.setHighAccuracyMode(false)
        persistSnapshot()  // Preserves pending event
    }

    func reset() {
        guard state == .sessionEnded else { return }
        activeSession = nil
        merchantTarget = nil
        state = .idle
        persistSnapshot()
        notifyWeb(.sessionStateChanged(state: .idle))
    }

    // MARK: - Timers

    private func startGracePeriodTimer() {
        gracePeriodDeadline = Date().addingTimeInterval(TimeInterval(config.gracePeriodSeconds))
        persistSnapshot()

        gracePeriodTimer = BackgroundTimer(deadline: gracePeriodDeadline!) { [weak self] in
            self?.handleGracePeriodExpired()
        }
    }

    private func cancelGracePeriodTimer() {
        gracePeriodTimer?.cancel()
        gracePeriodTimer = nil
        gracePeriodDeadline = nil
        persistSnapshot()
    }

    private func startHardTimeout() {
        hardTimeoutDeadline = Date().addingTimeInterval(TimeInterval(config.hardTimeoutSeconds))
        persistSnapshot()

        hardTimeoutTimer = BackgroundTimer(deadline: hardTimeoutDeadline!) { [weak self] in
            self?.handleHardTimeoutExpired()
        }
    }

    private func cancelHardTimeout() {
        hardTimeoutTimer?.cancel()
        hardTimeoutTimer = nil
        hardTimeoutDeadline = nil
        persistSnapshot()
    }

    private func handleGracePeriodExpired() {
        guard state == .inTransit else { return }
        transition(to: .sessionEnded, event: .gracePeriodExpired, occurredAt: Date())
    }

    private func handleHardTimeoutExpired() {
        guard state == .sessionActive || state == .inTransit || state == .atMerchant else { return }
        transition(to: .sessionEnded, event: .hardTimeoutExpired, occurredAt: Date())
    }

    /// Check deadlines on location update or app launch
    private func checkTimerDeadlines() {
        let now = Date()

        if let deadline = gracePeriodDeadline, now >= deadline {
            handleGracePeriodExpired()
        }

        if let deadline = hardTimeoutDeadline, now >= deadline {
            handleHardTimeoutExpired()
        }
    }

    // MARK: - Event Emission

    /// Emit event using pending event payload
    private func emitEventWithPending(_ pending: PendingEvent) {
        Task {
            do {
                if pending.requiresSessionId, let sid = pending.sessionId {
                    try await apiClient.emitSessionEvent(
                        sessionId: sid,
                        event: pending.eventName,
                        eventId: pending.eventId,
                        occurredAt: pending.occurredAt,
                        metadata: pending.metadata
                    )
                } else {
                    try await apiClient.emitPreSessionEvent(
                        event: pending.eventName,
                        chargerId: pending.chargerId,
                        eventId: pending.eventId,
                        occurredAt: pending.occurredAt,
                        metadata: pending.metadata
                    )
                }
                await MainActor.run {
                    self.clearPendingEvent()
                }
            } catch {
                print("[SessionEngine] Event emission failed: \(error)")
                // Keep pendingEvent for retry on next launch
            }
        }
    }

    /// Simple emit for non-transition events (chargerTargeted, activationRejected, sessionRestored)
    private func emitEvent(
        _ event: SessionEvent,
        sessionId: String? = nil,
        chargerId: String? = nil,
        occurredAt: Date,
        metadata: [String: String] = [:]
    ) {
        let eventId = UUID().uuidString

        Task {
            if event.requiresSessionId, let sid = sessionId {
                try? await apiClient.emitSessionEvent(
                    sessionId: sid,
                    event: event.rawValue,
                    eventId: eventId,
                    occurredAt: occurredAt,
                    metadata: metadata
                )
            } else {
                try? await apiClient.emitPreSessionEvent(
                    event: event.rawValue,
                    chargerId: chargerId,
                    eventId: eventId,
                    occurredAt: occurredAt,
                    metadata: metadata
                )
            }
        }
    }

    /// Emit non-canonical diagnostic event (fire-and-forget, not in taxonomy)
    /// Used for teleport_detected and other debugging events.
    private func emitDiagnosticEvent(_ eventName: String, sessionId: String?, metadata: [String: String] = [:]) {
        let eventId = UUID().uuidString
        Task {
            if let sid = sessionId {
                try? await apiClient.emitSessionEvent(
                    sessionId: sid,
                    event: eventName,
                    eventId: eventId,
                    occurredAt: Date(),
                    metadata: metadata
                )
            }
        }
    }

    // MARK: - Web Bridge

    private func notifyWeb(_ message: NativeBridgeMessage) {
        webBridge?.sendToWeb(message)
    }
}

// MARK: - GeofenceManagerDelegate

extension SessionEngine: GeofenceManagerDelegate {
    func geofenceManager(_ manager: GeofenceManager, didEnterRegion identifier: String) {
        handleGeofenceEntry(identifier: identifier)
    }

    func geofenceManager(_ manager: GeofenceManager, didExitRegion identifier: String) {
        handleGeofenceExit(identifier: identifier)
    }
}
```

---

### 5. BackgroundTimer.swift (NEW)

**Path:** `ios/Nerava/Engine/BackgroundTimer.swift`

```swift
import Foundation

final class BackgroundTimer {
    private var timer: DispatchSourceTimer?
    private let deadline: Date
    private let handler: () -> Void

    init(deadline: Date, handler: @escaping () -> Void) {
        self.deadline = deadline
        self.handler = handler

        let interval = deadline.timeIntervalSinceNow
        guard interval > 0 else {
            DispatchQueue.main.async { handler() }
            return
        }

        timer = DispatchSource.makeTimerSource(queue: .main)
        timer?.schedule(deadline: .now() + interval)
        timer?.setEventHandler { [weak self] in
            self?.handler()
        }
        timer?.resume()
    }

    func cancel() {
        timer?.cancel()
        timer = nil
    }

    deinit {
        cancel()
    }
}
```

---

### 6. DwellDetector.swift (NEW)

**Path:** `ios/Nerava/Engine/DwellDetector.swift`

```swift
import CoreLocation

final class DwellDetector {
    private let anchorRadius: Double
    private let dwellDuration: TimeInterval
    private let speedThreshold: Double

    private var dwellStartTime: Date?
    private var locationHistory: [(location: CLLocation, timestamp: Date)] = []

    var isAnchored: Bool {
        guard let startTime = dwellStartTime else { return false }
        return Date().timeIntervalSince(startTime) >= dwellDuration
    }

    init(anchorRadius: Double, dwellDuration: TimeInterval, speedThreshold: Double) {
        self.anchorRadius = anchorRadius
        self.dwellDuration = dwellDuration
        self.speedThreshold = speedThreshold
    }

    func recordLocation(_ location: CLLocation, distanceToAnchor: Double) {
        let now = Date()

        locationHistory = locationHistory.filter { now.timeIntervalSince($0.timestamp) < 300 }
        locationHistory.append((location, now))

        let isWithinRadius = distanceToAnchor <= anchorRadius
        let isStationary = location.speed < 0 || location.speed < speedThreshold

        if isWithinRadius && isStationary {
            if dwellStartTime == nil {
                dwellStartTime = now
            }
        } else {
            dwellStartTime = nil
        }
    }

    func reset() {
        dwellStartTime = nil
        locationHistory.removeAll()
    }
}
```

---

### 7. GeofenceManager.swift (NEW)

**Path:** `ios/Nerava/Services/GeofenceManager.swift`

```swift
import CoreLocation

protocol GeofenceManagerDelegate: AnyObject {
    func geofenceManager(_ manager: GeofenceManager, didEnterRegion identifier: String)
    func geofenceManager(_ manager: GeofenceManager, didExitRegion identifier: String)
}

final class GeofenceManager: NSObject {
    private let locationManager: CLLocationManager
    private var activeRegions: [String: CLCircularRegion] = [:]
    private let maxRegions = 2

    weak var delegate: GeofenceManagerDelegate?

    override init() {
        self.locationManager = CLLocationManager()
        super.init()
        locationManager.delegate = self
    }

    func addChargerGeofence(id: String, coordinate: CLLocationCoordinate2D, radius: Double) {
        let identifier = "charger_\(id)"
        addRegion(identifier: identifier, coordinate: coordinate, radius: radius, notifyOnExit: true)
    }

    func addMerchantGeofence(id: String, coordinate: CLLocationCoordinate2D, radius: Double) {
        let identifier = "merchant_\(id)"
        addRegion(identifier: identifier, coordinate: coordinate, radius: radius, notifyOnExit: false)
    }

    private func addRegion(identifier: String, coordinate: CLLocationCoordinate2D, radius: Double, notifyOnExit: Bool) {
        if activeRegions.count >= maxRegions {
            // NOTE: Dictionary ordering is undefined, so this removes an arbitrary region, not "oldest"
            if let anyKey = activeRegions.keys.first {
                removeRegion(identifier: anyKey)
            }
        }

        let clampedRadius = min(radius, locationManager.maximumRegionMonitoringDistance)
        let region = CLCircularRegion(
            center: coordinate,
            radius: clampedRadius,
            identifier: identifier
        )
        region.notifyOnEntry = true
        region.notifyOnExit = notifyOnExit

        activeRegions[identifier] = region
        locationManager.startMonitoring(for: region)
        locationManager.requestState(for: region)

        print("[GeofenceManager] Added region: \(identifier)")
    }

    func removeRegion(identifier: String) {
        guard let region = activeRegions[identifier] else { return }
        locationManager.stopMonitoring(for: region)
        activeRegions.removeValue(forKey: identifier)
        print("[GeofenceManager] Removed region: \(identifier)")
    }

    func clearAll() {
        for (_, region) in activeRegions {
            locationManager.stopMonitoring(for: region)
        }
        activeRegions.removeAll()
        print("[GeofenceManager] Cleared all regions")
    }
}

extension GeofenceManager: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didEnterRegion region: CLRegion) {
        print("[GeofenceManager] Entered: \(region.identifier)")
        delegate?.geofenceManager(self, didEnterRegion: region.identifier)
    }

    func locationManager(_ manager: CLLocationManager, didExitRegion region: CLRegion) {
        print("[GeofenceManager] Exited: \(region.identifier)")
        delegate?.geofenceManager(self, didExitRegion: region.identifier)
    }

    func locationManager(_ manager: CLLocationManager, didDetermineState state: CLRegionState, for region: CLRegion) {
        if state == .inside {
            print("[GeofenceManager] Already inside: \(region.identifier)")
            delegate?.geofenceManager(self, didEnterRegion: region.identifier)
        }
    }

    func locationManager(_ manager: CLLocationManager, monitoringDidFailFor region: CLRegion?, withError error: Error) {
        print("[GeofenceManager] Monitoring failed: \(region?.identifier ?? "unknown") - \(error)")
    }
}
```

---

### 8. LocationService.swift (NEW)

**Path:** `ios/Nerava/Services/LocationService.swift`

```swift
import CoreLocation
import Combine

final class LocationService: NSObject, ObservableObject {
    private let locationManager = CLLocationManager()

    @Published private(set) var currentLocation: CLLocation?
    @Published private(set) var authorizationStatus: CLAuthorizationStatus = .notDetermined

    private var isHighAccuracyMode = false

    var locationUpdates: AnyPublisher<CLLocation, Never> {
        $currentLocation.compactMap { $0 }.eraseToAnyPublisher()
    }

    override init() {
        super.init()
        locationManager.delegate = self
        locationManager.allowsBackgroundLocationUpdates = true
        locationManager.pausesLocationUpdatesAutomatically = false
        authorizationStatus = locationManager.authorizationStatus

        // Initialize to low accuracy mode settings (but don't start yet)
        locationManager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        locationManager.distanceFilter = 100

        // Start monitoring on init if already authorized
        // This ensures we get location updates even in When-In-Use mode
        if authorizationStatus == .authorizedAlways || authorizationStatus == .authorizedWhenInUse {
            startMonitoring()
        }
    }

    func requestWhenInUsePermission() {
        locationManager.requestWhenInUseAuthorization()
    }

    func requestAlwaysPermission() {
        locationManager.requestAlwaysAuthorization()
    }

    func startMonitoring() {
        // Always start standard location updates to get at least one fix
        // This works for both Always and When-In-Use authorization
        locationManager.startUpdatingLocation()

        // For Always authorization, also use significant location changes for background
        if authorizationStatus == .authorizedAlways {
            locationManager.startMonitoringSignificantLocationChanges()
        }

        print("[LocationService] Started monitoring (auth=\(authorizationStatus.description), highAccuracy=\(isHighAccuracyMode))")
    }

    func stopMonitoring() {
        locationManager.stopUpdatingLocation()
        locationManager.stopMonitoringSignificantLocationChanges()
    }

    func setHighAccuracyMode(_ enabled: Bool) {
        guard enabled != isHighAccuracyMode else { return }
        isHighAccuracyMode = enabled

        if enabled {
            locationManager.desiredAccuracy = kCLLocationAccuracyBest
            locationManager.distanceFilter = 5
            print("[LocationService] High accuracy mode ON")
        } else {
            locationManager.desiredAccuracy = kCLLocationAccuracyHundredMeters
            locationManager.distanceFilter = 100
            print("[LocationService] High accuracy mode OFF")
        }

        // Restart updates to apply new settings
        if authorizationStatus == .authorizedAlways || authorizationStatus == .authorizedWhenInUse {
            locationManager.stopUpdatingLocation()
            locationManager.startUpdatingLocation()
        }
    }
}

extension LocationService: CLLocationManagerDelegate {
    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        currentLocation = locations.last
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus
        print("[LocationService] Authorization changed: \(authorizationStatus.description)")

        if authorizationStatus == .authorizedAlways || authorizationStatus == .authorizedWhenInUse {
            startMonitoring()
        }
    }
}

extension CLAuthorizationStatus {
    var description: String {
        switch self {
        case .notDetermined: return "notDetermined"
        case .restricted: return "restricted"
        case .denied: return "denied"
        case .authorizedAlways: return "authorizedAlways"
        case .authorizedWhenInUse: return "authorizedWhenInUse"
        @unknown default: return "unknown"
        }
    }
}
```

---

### 9. APIClient.swift (NEW)

**Path:** `ios/Nerava/Services/APIClient.swift`

```swift
import Foundation
import UIKit  // Required for UIApplication.shared.applicationState

final class APIClient {
    private let baseURL: URL
    private var accessToken: String?

    init(baseURL: URL = URL(string: "https://api.nerava.network")!) {
        self.baseURL = baseURL
        self.accessToken = KeychainService.shared.getAccessToken()
    }

    func setAuthToken(_ token: String) {
        self.accessToken = token
    }

    // MARK: - Session Events

    /// Emit session event. `eventId` is used as the idempotency key.
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
            "idempotency_key": eventId,  // event_id IS the idempotency key
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

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw APIError.requestFailed
        }

        // Treat both 2xx and "already_processed" as success for idempotency
        if (200...299).contains(httpResponse.statusCode) {
            // Check if response indicates already_processed
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let status = json["status"] as? String,
               status == "already_processed" {
                print("[APIClient] Session event already processed: \(event) (id=\(eventId))")
            } else {
                print("[APIClient] Session event sent: \(event) (id=\(eventId))")
            }
        } else {
            throw APIError.requestFailed
        }
    }

    // MARK: - Pre-Session Events

    /// Emit pre-session event. `eventId` is used as the idempotency key.
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
            "idempotency_key": eventId,  // event_id IS the idempotency key
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

        let (_, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw APIError.requestFailed
        }

        print("[APIClient] Pre-session event sent: \(event) (id=\(eventId))")
    }

    // MARK: - Config

    func fetchConfig() async throws -> SessionConfig {
        let url = baseURL.appendingPathComponent("/v1/native/config")
        var request = URLRequest(url: url)

        if let token = accessToken {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(SessionConfig.self, from: data)
    }

    enum APIError: Error {
        case requestFailed
        case invalidResponse
    }
}
```

---

### 10. NativeBridge.swift (NEW)

**Path:** `ios/Nerava/Services/NativeBridge.swift`

```swift
import WebKit
import Foundation

// MARK: - Message Types

enum NativeBridgeMessage {
    case sessionStateChanged(state: SessionState)
    case permissionStatus(status: String, alwaysGranted: Bool)
    case locationResponse(requestId: String, lat: Double, lng: Double, accuracy: Double)
    case sessionStartRejected(reason: String)
    case error(requestId: String?, message: String)
    case ready

    var action: String {
        switch self {
        case .sessionStateChanged: return "SESSION_STATE_CHANGED"
        case .permissionStatus: return "PERMISSION_STATUS"
        case .locationResponse: return "LOCATION_RESPONSE"
        case .sessionStartRejected: return "SESSION_START_REJECTED"
        case .error: return "ERROR"
        case .ready: return "NATIVE_READY"
        }
    }

    var payload: [String: Any] {
        switch self {
        case .sessionStateChanged(let state):
            return ["state": state.rawValue]
        case .permissionStatus(let status, let alwaysGranted):
            return ["status": status, "alwaysGranted": alwaysGranted]
        case .locationResponse(let requestId, let lat, let lng, let accuracy):
            return ["requestId": requestId, "lat": lat, "lng": lng, "accuracy": accuracy]
        case .sessionStartRejected(let reason):
            return ["reason": reason]
        case .error(let requestId, let message):
            var p: [String: Any] = ["message": message]
            if let rid = requestId { p["requestId"] = rid }
            return p
        case .ready:
            return [:]
        }
    }
}

// MARK: - Bridge Implementation

final class NativeBridge: NSObject {
    weak var webView: WKWebView?
    weak var sessionEngine: SessionEngine?
    private let locationService: LocationService

    // Exact origin matching (NOT substring)
    private let allowedOrigins: Set<String> = [
        "https://app.nerava.network",
        "http://localhost:5173",
        "http://localhost:5174"
    ]

    /// Track if navigation has committed (origin is now reliable)
    private var navigationCommitted = false

    init(locationService: LocationService) {
        self.locationService = locationService
        super.init()
    }

    var injectionScript: String {
        """
        (function() {
            if (window.neravaNative) return;

            const pendingRequests = new Map();
            let requestCounter = 0;

            window.neravaNative = {
                postMessage: function(action, payload) {
                    window.webkit.messageHandlers.neravaBridge.postMessage({
                        action: action,
                        payload: payload || {}
                    });
                },

                request: function(action, payload) {
                    return new Promise((resolve, reject) => {
                        const requestId = 'req_' + (++requestCounter) + '_' + Date.now();
                        pendingRequests.set(requestId, { resolve, reject, timestamp: Date.now() });

                        window.webkit.messageHandlers.neravaBridge.postMessage({
                            action: action,
                            payload: { ...(payload || {}), requestId: requestId }
                        });

                        setTimeout(() => {
                            if (pendingRequests.has(requestId)) {
                                pendingRequests.delete(requestId);
                                reject(new Error('Request timeout'));
                            }
                        }, 10000);
                    });
                },

                setChargerTarget: function(chargerId, chargerLat, chargerLng) {
                    this.postMessage('SET_CHARGER_TARGET', {
                        chargerId: chargerId,
                        chargerLat: chargerLat,
                        chargerLng: chargerLng
                    });
                },

                setAuthToken: function(token) {
                    this.postMessage('SET_AUTH_TOKEN', { token: token });
                },

                confirmExclusiveActivated: function(sessionId, merchantId, merchantLat, merchantLng) {
                    this.postMessage('EXCLUSIVE_ACTIVATED', {
                        sessionId: sessionId,
                        merchantId: merchantId,
                        merchantLat: merchantLat,
                        merchantLng: merchantLng
                    });
                },

                confirmVisitVerified: function(sessionId, verificationCode) {
                    this.postMessage('VISIT_VERIFIED', {
                        sessionId: sessionId,
                        verificationCode: verificationCode
                    });
                },

                endSession: function() {
                    this.postMessage('END_SESSION', {});
                },

                requestAlwaysLocation: function() {
                    this.postMessage('REQUEST_ALWAYS_LOCATION', {});
                },

                getLocation: function() {
                    return this.request('GET_LOCATION', {});
                },

                getSessionState: function() {
                    return this.request('GET_SESSION_STATE', {});
                },

                getPermissionStatus: function() {
                    return this.request('GET_PERMISSION_STATUS', {});
                }
            };

            window.neravaNativeCallback = function(action, payload) {
                if (payload && payload.requestId && pendingRequests.has(payload.requestId)) {
                    const { resolve } = pendingRequests.get(payload.requestId);
                    pendingRequests.delete(payload.requestId);
                    resolve(payload);
                    return;
                }

                window.dispatchEvent(new CustomEvent('neravaNative', {
                    detail: { action: action, payload: payload }
                }));
            };

            console.log('[NativeBridge] Initialized');

            // Dispatch ready event for listeners waiting for bridge
            window.dispatchEvent(new CustomEvent('neravaNativeReady'));
        })();
        """
    }

    func setupWebView(_ webView: WKWebView) {
        self.webView = webView

        let script = WKUserScript(
            source: injectionScript,
            injectionTime: .atDocumentStart,
            forMainFrameOnly: true
        )
        webView.configuration.userContentController.addUserScript(script)
        webView.configuration.userContentController.add(self, name: "neravaBridge")

        // Send native → web ready message after setup (redundant signal for reliability)
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [weak self] in
            self?.sendToWeb(.ready)
        }
    }

    /// Call this from WKNavigationDelegate.webView(_:didFinish:) to mark navigation committed
    func didFinishNavigation() {
        navigationCommitted = true
    }

    func sendToWeb(_ message: NativeBridgeMessage) {
        guard let webView = webView else { return }

        do {
            let payloadData = try JSONSerialization.data(withJSONObject: message.payload)
            guard let payloadStr = String(data: payloadData, encoding: .utf8) else { return }

            let js = "window.neravaNativeCallback('\(message.action)', \(payloadStr));"

            DispatchQueue.main.async {
                webView.evaluateJavaScript(js) { _, error in
                    if let error = error {
                        print("[NativeBridge] JS error: \(error)")
                    }
                }
            }
        } catch {
            print("[NativeBridge] JSON encoding error: \(error)")
        }
    }

    /// Validate origin. During bootstrap (before navigation commits), we're lenient.
    /// After navigation commits, we strictly validate.
    private func isValidOrigin(_ webView: WKWebView?) -> Bool {
        guard let url = webView?.url else {
            // URL is nil during bootstrap - allow if navigation hasn't committed yet
            // This handles the case where scripts run before about:blank → real URL
            return !navigationCommitted
        }

        // about:blank during bootstrap
        if url.absoluteString == "about:blank" {
            return !navigationCommitted
        }

        var origin = ""
        if let scheme = url.scheme {
            origin += scheme + "://"
        }
        if let host = url.host {
            origin += host
        }
        if let port = url.port, port != 80 && port != 443 {
            origin += ":\(port)"
        }

        return allowedOrigins.contains(origin)
    }
}

extension NativeBridge: WKScriptMessageHandler {
    func userContentController(_ userContentController: WKUserContentController,
                               didReceive message: WKScriptMessage) {
        guard isValidOrigin(webView) else {
            print("[NativeBridge] Rejected from unauthorized origin")
            return
        }

        guard let body = message.body as? [String: Any],
              let actionStr = body["action"] as? String,
              let payload = body["payload"] as? [String: Any] else { return }

        let requestId = payload["requestId"] as? String

        switch actionStr {
        case "SET_CHARGER_TARGET":
            guard let chargerId = payload["chargerId"] as? String,
                  let lat = payload["chargerLat"] as? Double,
                  let lng = payload["chargerLng"] as? Double else { return }
            sessionEngine?.setChargerTarget(chargerId: chargerId, lat: lat, lng: lng)

        case "SET_AUTH_TOKEN":
            guard let token = payload["token"] as? String else { return }
            sessionEngine?.setAuthToken(token)

        case "EXCLUSIVE_ACTIVATED":
            guard let sessionId = payload["sessionId"] as? String,
                  let merchantId = payload["merchantId"] as? String,
                  let lat = payload["merchantLat"] as? Double,
                  let lng = payload["merchantLng"] as? Double else { return }
            sessionEngine?.webConfirmsExclusiveActivated(
                sessionId: sessionId,
                merchantId: merchantId,
                merchantLat: lat,
                merchantLng: lng
            )

        case "VISIT_VERIFIED":
            guard let sessionId = payload["sessionId"] as? String,
                  let code = payload["verificationCode"] as? String else { return }
            sessionEngine?.webConfirmsVisitVerified(sessionId: sessionId, verificationCode: code)

        case "END_SESSION":
            sessionEngine?.webRequestsSessionEnd()

        case "REQUEST_ALWAYS_LOCATION":
            locationService.requestAlwaysPermission()

        case "GET_LOCATION":
            if let location = locationService.currentLocation {
                sendToWeb(.locationResponse(
                    requestId: requestId ?? "",
                    lat: location.coordinate.latitude,
                    lng: location.coordinate.longitude,
                    accuracy: location.horizontalAccuracy
                ))
            } else {
                sendToWeb(.error(requestId: requestId, message: "Location unavailable"))
            }

        case "GET_SESSION_STATE":
            // Use public getter to avoid private(set) access issue
            if let engine = sessionEngine {
                sendToWeb(.sessionStateChanged(state: engine.currentState))
            }

        case "GET_PERMISSION_STATUS":
            let status = locationService.authorizationStatus
            let alwaysGranted = status == .authorizedAlways
            sendToWeb(.permissionStatus(status: status.description, alwaysGranted: alwaysGranted))

        default:
            print("[NativeBridge] Unknown action: \(actionStr)")
        }
    }
}
```

---

### 11. KeychainService.swift (NEW)

**Path:** `ios/Nerava/Services/KeychainService.swift`

```swift
import Foundation
import Security

final class KeychainService {
    static let shared = KeychainService()
    private init() {}

    private let accessTokenKey = "com.nerava.accessToken"

    func setAccessToken(_ token: String) {
        let data = token.data(using: .utf8)!

        let deleteQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: accessTokenKey
        ]
        SecItemDelete(deleteQuery as CFDictionary)

        let addQuery: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: accessTokenKey,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock
        ]
        SecItemAdd(addQuery as CFDictionary, nil)
    }

    func getAccessToken() -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: accessTokenKey,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let token = String(data: data, encoding: .utf8) else {
            return nil
        }
        return token
    }

    func deleteAccessToken() {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: accessTokenKey
        ]
        SecItemDelete(query as CFDictionary)
    }
}
```

---

### 12. NotificationService.swift (NEW)

**Path:** `ios/Nerava/Services/NotificationService.swift`

```swift
import UserNotifications

final class NotificationService {
    static let shared = NotificationService()
    private init() {}

    func requestPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound]) { _, _ in }
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

---

### 13. Info.plist (NEW)

**Path:** `ios/Nerava/Resources/Info.plist`

**CRITICAL:** Only include `location` in UIBackgroundModes. No `remote-notification` or `BGTaskSchedulerPermittedIdentifiers`.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
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
</dict>
</plist>
```

---

### 14. Backend: native_events.py (NEW)

**Path:** `backend/app/routers/native_events.py`

```python
"""
Native App Events Router
Receives session events from iOS native app.
"""
import logging
import uuid
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.models.exclusive_session import ExclusiveSession
from app.dependencies.driver import get_current_driver
from app.services.analytics import get_analytics_client
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/native", tags=["native"])


# ============================================================
# RATE LIMITER
# ============================================================

class InMemoryRateLimiter:
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)

    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        cutoff = now - window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        if len(self._requests[key]) >= limit:
            return False
        self._requests[key].append(now)
        return True


_rate_limiter = InMemoryRateLimiter()


# ============================================================
# IDEMPOTENCY CACHE WITH TTL
# ============================================================

class TTLIdempotencyCache:
    """Idempotency cache with TTL-based eviction. Replace with Redis in production."""

    TTL_SECONDS = 3600  # 1 hour

    def __init__(self):
        self._cache: Dict[str, float] = {}  # key -> timestamp

    def check_and_set(self, key: str) -> bool:
        """Returns True if this is a duplicate (already processed)."""
        now = time.time()

        # Evict expired entries periodically
        if len(self._cache) > 1000:
            self._evict_expired(now)

        if key in self._cache:
            # Check if still within TTL
            if now - self._cache[key] < self.TTL_SECONDS:
                return True
            # Expired, allow re-processing

        self._cache[key] = now
        return False

    def _evict_expired(self, now: float):
        """Remove entries older than TTL."""
        cutoff = now - self.TTL_SECONDS
        self._cache = {k: v for k, v in self._cache.items() if v > cutoff}


_idempotency_cache = TTLIdempotencyCache()


# ============================================================
# MODELS
# ============================================================

class SessionEventRequest(BaseModel):
    schema_version: str = "1.0"
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    idempotency_key: str  # Should equal event_id
    session_id: str
    event: str
    occurred_at: str  # When the event actually happened (client time)
    timestamp: str    # When the request was sent
    source: str = "ios_native"
    app_state: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PreSessionEventRequest(BaseModel):
    schema_version: str = "1.0"
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    idempotency_key: str  # Should equal event_id
    charger_id: Optional[str] = None
    event: str
    occurred_at: str  # When the event actually happened (client time)
    timestamp: str    # When the request was sent
    source: str = "ios_native"
    metadata: Optional[Dict[str, Any]] = None


class SessionEventResponse(BaseModel):
    status: str
    event_id: str


class NativeConfigResponse(BaseModel):
    chargerIntentRadius_m: float
    chargerAnchorRadius_m: float
    chargerDwellSeconds: int
    merchantUnlockRadius_m: float
    gracePeriodSeconds: int
    hardTimeoutSeconds: int
    locationAccuracyThreshold_m: float
    speedThresholdForDwell_mps: float


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/session-events", response_model=SessionEventResponse)
async def emit_session_event(
    request: SessionEventRequest,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    if not _rate_limiter.check(f"native_events:{driver.id}", limit=60, window_seconds=60):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )

    if _idempotency_cache.check_and_set(request.idempotency_key):
        logger.debug(f"Duplicate event ignored: {request.idempotency_key}")
        return SessionEventResponse(status="already_processed", event_id=request.event_id)

    session = db.query(ExclusiveSession).filter(
        ExclusiveSession.id == request.session_id,
        ExclusiveSession.driver_id == driver.id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    analytics = get_analytics_client()
    analytics.capture(
        distinct_id=str(driver.id),
        event=f"native_session_{request.event}",
        properties={
            "session_id": request.session_id,
            "event_id": request.event_id,
            "source": request.source,
            "app_state": request.app_state,
            "occurred_at": request.occurred_at,
            **(request.metadata or {})
        }
    )

    logger.info(f"Native session event: {request.event}", extra={
        "driver_id": driver.id,
        "session_id": request.session_id,
        "event": request.event,
        "occurred_at": request.occurred_at
    })

    return SessionEventResponse(status="ok", event_id=request.event_id)


@router.post("/pre-session-events", response_model=SessionEventResponse)
async def emit_pre_session_event(
    request: PreSessionEventRequest,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    if not _rate_limiter.check(f"native_presession:{driver.id}", limit=30, window_seconds=60):
        return SessionEventResponse(status="throttled", event_id=request.event_id)

    if _idempotency_cache.check_and_set(request.idempotency_key):
        return SessionEventResponse(status="already_processed", event_id=request.event_id)

    analytics = get_analytics_client()
    analytics.capture(
        distinct_id=str(driver.id),
        event=f"native_presession_{request.event}",
        properties={
            "charger_id": request.charger_id,
            "event_id": request.event_id,
            "source": request.source,
            "occurred_at": request.occurred_at,
            **(request.metadata or {})
        }
    )

    logger.info(f"Native pre-session event: {request.event}", extra={
        "driver_id": driver.id,
        "charger_id": request.charger_id,
        "event": request.event,
        "occurred_at": request.occurred_at
    })

    return SessionEventResponse(status="ok", event_id=request.event_id)


@router.get("/config", response_model=NativeConfigResponse)
async def get_native_config(driver: User = Depends(get_current_driver)):
    """Get remote configuration. Reads from settings.NATIVE_* environment variables."""
    return NativeConfigResponse(
        chargerIntentRadius_m=settings.NATIVE_CHARGER_INTENT_RADIUS_M,
        chargerAnchorRadius_m=settings.NATIVE_CHARGER_ANCHOR_RADIUS_M,
        chargerDwellSeconds=settings.NATIVE_CHARGER_DWELL_SECONDS,
        merchantUnlockRadius_m=settings.NATIVE_MERCHANT_UNLOCK_RADIUS_M,
        gracePeriodSeconds=settings.NATIVE_GRACE_PERIOD_SECONDS,
        hardTimeoutSeconds=settings.NATIVE_HARD_TIMEOUT_SECONDS,
        locationAccuracyThreshold_m=settings.NATIVE_LOCATION_ACCURACY_THRESHOLD_M,
        speedThresholdForDwell_mps=settings.NATIVE_SPEED_THRESHOLD_FOR_DWELL_MPS
    )
```

---

### 15. Backend: config.py (MODIFY)

**Path:** `backend/app/core/config.py`

**Add these settings to the Settings class:**

```python
# Native iOS App Configuration
NATIVE_SESSION_ENGINE_ENABLED: bool = os.getenv("NATIVE_SESSION_ENGINE_ENABLED", "true").lower() == "true"
NATIVE_BRIDGE_ENABLED: bool = os.getenv("NATIVE_BRIDGE_ENABLED", "true").lower() == "true"

NATIVE_CHARGER_INTENT_RADIUS_M: float = float(os.getenv("NATIVE_CHARGER_INTENT_RADIUS_M", "400.0"))
NATIVE_CHARGER_ANCHOR_RADIUS_M: float = float(os.getenv("NATIVE_CHARGER_ANCHOR_RADIUS_M", "30.0"))
NATIVE_CHARGER_DWELL_SECONDS: int = int(os.getenv("NATIVE_CHARGER_DWELL_SECONDS", "120"))
NATIVE_MERCHANT_UNLOCK_RADIUS_M: float = float(os.getenv("NATIVE_MERCHANT_UNLOCK_RADIUS_M", "40.0"))
NATIVE_GRACE_PERIOD_SECONDS: int = int(os.getenv("NATIVE_GRACE_PERIOD_SECONDS", "900"))
NATIVE_HARD_TIMEOUT_SECONDS: int = int(os.getenv("NATIVE_HARD_TIMEOUT_SECONDS", "3600"))
NATIVE_LOCATION_ACCURACY_THRESHOLD_M: float = float(os.getenv("NATIVE_LOCATION_ACCURACY_THRESHOLD_M", "50.0"))
NATIVE_SPEED_THRESHOLD_FOR_DWELL_MPS: float = float(os.getenv("NATIVE_SPEED_THRESHOLD_FOR_DWELL_MPS", "1.5"))
```

---

### 16. Backend: main_simple.py (MODIFY)

**Path:** `backend/app/main_simple.py`

**Add import and router registration:**

```python
# Add to imports
from app.routers import native_events

# Add after other router includes
app.include_router(native_events.router)
```

---

### 17. Web: useNativeBridge.ts (NEW)

**Path:** `apps/driver/src/hooks/useNativeBridge.ts`

**Note:** `bridgeReady` is stateful. On NATIVE_READY message, set true unconditionally (don't require bridgeExists check).

```typescript
import { useEffect, useCallback, useState, useRef } from 'react';

interface NativeLocation {
  lat: number;
  lng: number;
  accuracy: number;
}

type SessionState =
  | 'IDLE'
  | 'NEAR_CHARGER'
  | 'ANCHORED'
  | 'SESSION_ACTIVE'
  | 'IN_TRANSIT'
  | 'AT_MERCHANT'
  | 'SESSION_ENDED';

interface PermissionStatus {
  status: string;
  alwaysGranted: boolean;
}

declare global {
  interface Window {
    neravaNative?: {
      postMessage: (action: string, payload: any) => void;
      request: (action: string, payload: any) => Promise<any>;
      setChargerTarget: (chargerId: string, chargerLat: number, chargerLng: number) => void;
      setAuthToken: (token: string) => void;
      confirmExclusiveActivated: (sessionId: string, merchantId: string, merchantLat: number, merchantLng: number) => void;
      confirmVisitVerified: (sessionId: string, verificationCode: string) => void;
      endSession: () => void;
      requestAlwaysLocation: () => void;
      getLocation: () => Promise<NativeLocation>;
      getSessionState: () => Promise<{ state: SessionState }>;
      getPermissionStatus: () => Promise<PermissionStatus>;
    };
  }
}

const NATIVE_BRIDGE_ENABLED = import.meta.env.VITE_NATIVE_BRIDGE_ENABLED !== 'false';

/**
 * Check if native bridge object exists right now.
 */
function bridgeExists(): boolean {
  return NATIVE_BRIDGE_ENABLED && !!window.neravaNative;
}

export function useNativeBridge() {
  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  // bridgeReady is stateful - set via ready signals
  const [bridgeReady, setBridgeReady] = useState(bridgeExists());
  const initializedRef = useRef(false);

  // Listen for bridge ready - BOTH JS event AND native NATIVE_READY message
  useEffect(() => {
    if (!NATIVE_BRIDGE_ENABLED) return;

    // Check immediately
    if (bridgeExists()) {
      setBridgeReady(true);
    }

    // Listen for JS-dispatched ready event (from injection script)
    const handleJsReady = () => {
      if (bridgeExists()) {
        setBridgeReady(true);
      }
    };
    window.addEventListener('neravaNativeReady', handleJsReady);

    // Listen for native → web NATIVE_READY message
    // Set bridgeReady true unconditionally - the native sent it, so bridge exists
    const handleNativeMessage = (event: CustomEvent<{ action: string; payload: any }>) => {
      if (event.detail.action === 'NATIVE_READY') {
        setBridgeReady(true);  // Trust the native signal
      }
    };
    window.addEventListener('neravaNative', handleNativeMessage as EventListener);

    return () => {
      window.removeEventListener('neravaNativeReady', handleJsReady);
      window.removeEventListener('neravaNative', handleNativeMessage as EventListener);
    };
  }, []);

  // Listen for state changes from native
  useEffect(() => {
    if (!bridgeReady) return;

    const handleNativeEvent = (event: CustomEvent<{ action: string; payload: any }>) => {
      const { action, payload } = event.detail;

      if (action === 'SESSION_STATE_CHANGED') {
        setSessionState(payload.state);
      }

      if (action === 'SESSION_START_REJECTED') {
        console.warn('[NativeBridge] Session start rejected:', payload.reason);
      }
    };

    window.addEventListener('neravaNative', handleNativeEvent as EventListener);

    // Get initial state
    window.neravaNative?.getSessionState().then(({ state }) => setSessionState(state));

    return () => {
      window.removeEventListener('neravaNative', handleNativeEvent as EventListener);
    };
  }, [bridgeReady]);

  // Sync initial auth token (once)
  useEffect(() => {
    if (!bridgeReady || initializedRef.current) return;
    initializedRef.current = true;

    const token = localStorage.getItem('access_token');
    if (token) {
      window.neravaNative?.setAuthToken(token);
    }
  }, [bridgeReady]);

  // Listen for cross-tab storage changes only
  useEffect(() => {
    if (!bridgeReady) return;

    const handleStorage = (e: StorageEvent) => {
      if (e.key === 'access_token' && e.newValue) {
        window.neravaNative?.setAuthToken(e.newValue);
      }
    };

    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, [bridgeReady]);

  const setChargerTarget = useCallback((chargerId: string, chargerLat: number, chargerLng: number) => {
    if (bridgeExists()) {
      window.neravaNative?.setChargerTarget(chargerId, chargerLat, chargerLng);
    }
  }, []);

  /**
   * CRITICAL: Call this explicitly after login or token refresh.
   * The storage event listener only fires for cross-tab changes.
   */
  const setAuthToken = useCallback((token: string) => {
    if (bridgeExists()) {
      window.neravaNative?.setAuthToken(token);
    }
  }, []);

  const confirmExclusiveActivated = useCallback((
    sessionId: string,
    merchantId: string,
    merchantLat: number,
    merchantLng: number
  ) => {
    if (bridgeExists()) {
      window.neravaNative?.confirmExclusiveActivated(sessionId, merchantId, merchantLat, merchantLng);
    }
  }, []);

  const confirmVisitVerified = useCallback((sessionId: string, verificationCode: string) => {
    if (bridgeExists()) {
      window.neravaNative?.confirmVisitVerified(sessionId, verificationCode);
    }
  }, []);

  const endSession = useCallback(() => {
    if (bridgeExists()) {
      window.neravaNative?.endSession();
    }
  }, []);

  const requestAlwaysLocation = useCallback(() => {
    if (bridgeExists()) {
      window.neravaNative?.requestAlwaysLocation();
    }
  }, []);

  const getLocation = useCallback(async (): Promise<NativeLocation> => {
    if (bridgeExists()) {
      return window.neravaNative!.getLocation();
    }
    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          accuracy: pos.coords.accuracy,
        }),
        reject
      );
    });
  }, []);

  const getPermissionStatus = useCallback(async (): Promise<PermissionStatus> => {
    if (bridgeExists()) {
      return window.neravaNative!.getPermissionStatus();
    }
    return { status: 'notAvailable', alwaysGranted: false };
  }, []);

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
  };
}
```

---

## Section 4: Acceptance Tests (Corrected)

### Test 1: Permission Flow
1. Fresh install → pre-permission rationale appears BEFORE system dialog
2. Grant "When In Use" → app functions, location updates work
3. Later prompt for "Always" → rationale screen first
4. Deny "Always" → app continues with degraded background

### Test 2: Charger Targeting
1. Open app with no charger nearby → state = `IDLE`
2. Web calls `setChargerTarget(id, lat, lng)`
3. Verify console: `[GeofenceManager] Added region: charger_<id>`
4. Travel to within 400m → state = `NEAR_CHARGER`

### Test 3: Anchor Detection
1. `NEAR_CHARGER` state
2. Walk to within 30m, stand still 2 minutes
3. State → `ANCHORED`
4. Walk back to 50m → state → `NEAR_CHARGER` (anchor lost)

### Test 4: Full Session Flow
1. `ANCHORED` → complete OTP in web
2. Web calls `confirmExclusiveActivated(...)` → state = `SESSION_ACTIVE`
3. Notification: "You're all set!"
4. Walk away → state = `IN_TRANSIT`
5. Walk to merchant → state = `AT_MERCHANT`
6. Notification: "You've arrived!"
7. Web calls `confirmVisitVerified(...)` → state = `SESSION_ENDED`

### Test 5: Background Behavior (Corrected)

**App backgrounded (not force-quit):**
1. Start session, transition to `IN_TRANSIT`
2. Background app (swipe up but don't force-quit)
3. Walk to merchant
4. Notification fires while backgrounded
5. Open app → state is `AT_MERCHANT`

**App terminated by system:**
1. Start session, transition to `IN_TRANSIT`
2. Let iOS terminate app (memory pressure simulation)
3. Relaunch app
4. Console: `[SessionEngine] Restored from snapshot`
5. Console: `[SessionEngine] Retrying pending event: departed_charger`
6. State is restored, geofences rebuilt

**App force-quit by user:**
1. Start session, transition to `IN_TRANSIT`
2. Force-quit (swipe up from app switcher)
3. Walk to merchant
4. **NO notification fires** (iOS does not relaunch force-quit apps for location)
5. User relaunches app manually
6. Console: `[SessionEngine] Restored from snapshot`
7. Pending event retried first, then reconciliation
8. If grace period expired → `SESSION_ENDED`

### Test 6: Activation Rejection
1. `NEAR_CHARGER` state (not anchored)
2. Try to activate exclusive in web
3. Web receives `SESSION_START_REJECTED` with reason `NOT_ANCHORED`

### Test 7: Pending Event Retry
1. Activate session, transition to `IN_TRANSIT`
2. Kill network
3. Trigger another transition (won't send)
4. Kill app
5. Relaunch with network
6. Console: `[SessionEngine] Retrying pending event: ...`
7. Backend returns `ok` or `already_processed`
8. Pending cleared

### Test 8: Teleport Detection
1. Activate session, transition to `IN_TRANSIT`
2. Kill app
3. Simulate teleport: change device location to >50km away
4. Relaunch
5. Verify console: `teleport detected` (non-canonical diagnostic)
6. Session ends with `grace_period_expired`

### Test 9: Backend Events + Idempotency
Run full session and verify PostHog/logs contain:
- `native_presession_charger_targeted`
- `native_presession_entered_charger_intent_zone`
- `native_presession_anchor_dwell_complete`
- `native_session_exclusive_activated`
- `native_session_departed_charger`
- `native_session_entered_merchant_zone`
- `native_session_visit_verified`

All events have both `occurred_at` and `timestamp` in analytics.

**Idempotency test:**
1. Kill network after triggering event
2. Restore network, relaunch app
3. Event retry uses same `event_id`
4. Backend returns `already_processed` for duplicate

### Test 10: When-In-Use Location Updates
1. Grant only "When In Use" permission
2. Open app, stay in foreground
3. Verify location updates are received (check console)
4. setChargerTarget should trigger zone detection

---

## Section 5: Observability / Debugging

### Log Prefixes

| Prefix | Component |
|--------|-----------|
| `[SessionEngine]` | State machine transitions, persistence, reconciliation, retry |
| `[GeofenceManager]` | Region add/remove/enter/exit |
| `[LocationService]` | Authorization changes, accuracy mode |
| `[NativeBridge]` | JS ↔ Native messages |
| `[APIClient]` | Event emission |
| `[SessionSnapshot]` | Save/load failures |

### Verify Pending Event Retry (Xcode Console)

```
[SessionEngine] Restored from snapshot: state=IN_TRANSIT
[SessionEngine] Retrying pending event: departed_charger
[APIClient] Session event sent: departed_charger (id=abc123)
[SessionEngine] Pending event retry succeeded
```

### Verify Reconciliation (Xcode Console)

```
[SessionEngine] Reconciliation: IN_TRANSIT without grace period, starting timer
```

Or for teleport:
```
[SessionEngine] Reconciliation: teleport detected (52341m > 50000m), ending session
[SessionEngine] Transition: IN_TRANSIT → SESSION_ENDED via grace_period_expired
```

### Verify Backend Events (curl)

```bash
# Session event with occurred_at
curl -X POST https://api.nerava.network/v1/native/session-events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "abc123-uuid",
    "idempotency_key": "abc123-uuid",
    "session_id": "sess-abc",
    "event": "exclusive_activated",
    "occurred_at": "2026-01-25T12:00:00Z",
    "timestamp": "2026-01-25T12:00:05Z"
  }'

# Pre-session event
curl -X POST https://api.nerava.network/v1/native/pre-session-events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "def456-uuid",
    "idempotency_key": "def456-uuid",
    "charger_id": "charger123",
    "event": "charger_targeted",
    "occurred_at": "2026-01-25T12:00:00Z",
    "timestamp": "2026-01-25T12:00:01Z"
  }'

# Config
curl https://api.nerava.network/v1/native/config \
  -H "Authorization: Bearer $TOKEN"
```

### Web Console Verification

```javascript
// Check bridge presence
console.log('Bridge available:', !!window.neravaNative);

// Get current state
window.neravaNative?.getSessionState().then(console.log);

// Listen for state changes (including NATIVE_READY)
window.addEventListener('neravaNative', (e) => {
  console.log('Native event:', e.detail);
});
```

---

## Validation Checklist

### Xcode Build
```bash
cd ios
xcodebuild -scheme Nerava -configuration Debug build
```

### Manual Test Script
1. [ ] Fresh install shows permission rationale
2. [ ] When-In-Use grants location updates in foreground
3. [ ] `setChargerTarget` creates geofence (check logs)
4. [ ] Entering zone triggers `NEAR_CHARGER`
5. [ ] Dwelling 2min triggers `ANCHORED`
6. [ ] Activation from non-anchored state rejected
7. [ ] Full flow: IDLE → SESSION_ENDED
8. [ ] Background notification works (app backgrounded)
9. [ ] Force-quit → relaunch restores state
10. [ ] Pending event retried on restore
11. [ ] Expired grace period ends session on restore
12. [ ] Teleport (>50km) ends session on restore
13. [ ] Duplicate events return `already_processed`
14. [ ] Events have both `occurred_at` and `timestamp`

### Backend Endpoints
```bash
# Health check
curl https://api.nerava.network/v1/native/config -I

# Should return 200 with JSON config
```

### Web Bridge
```javascript
// In browser console on app.nerava.network:
console.assert(!!window.neravaNative, 'Bridge should exist');
```

---

## Event Taxonomy (Canonical Names)

| Native Event | Backend Analytics Event |
|--------------|------------------------|
| `charger_targeted` | `native_presession_charger_targeted` |
| `entered_charger_intent_zone` | `native_presession_entered_charger_intent_zone` |
| `exited_charger_intent_zone` | `native_presession_exited_charger_intent_zone` |
| `anchor_dwell_complete` | `native_presession_anchor_dwell_complete` |
| `anchor_lost` | `native_presession_anchor_lost` |
| `activation_rejected` | `native_presession_activation_rejected` |
| `exclusive_activated` | `native_session_exclusive_activated` |
| `departed_charger` | `native_session_departed_charger` |
| `entered_merchant_zone` | `native_session_entered_merchant_zone` |
| `visit_verified` | `native_session_visit_verified` |
| `grace_period_expired` | `native_session_grace_period_expired` |
| `hard_timeout_expired` | `native_session_hard_timeout_expired` |
| `web_requested_end` | `native_session_web_requested_end` |
| `session_restored` | `native_session_session_restored` |

**Non-canonical diagnostic events** (not in taxonomy, fire-and-forget):
- `teleport_detected` - emitted when user appears >50km from expected location on restore
