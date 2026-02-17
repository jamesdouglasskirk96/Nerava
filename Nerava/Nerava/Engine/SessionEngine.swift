import Foundation
import Combine
import CoreLocation
import UIKit
import os

final class SessionEngine: ObservableObject {
    // MARK: - Published State (private(set) for internal mutation only)
    @Published private(set) var state: SessionState = .idle
    @Published private(set) var activeSession: ActiveSessionInfo?
    @Published private(set) var targetedCharger: ChargerTarget?
    @Published var shouldShowNotificationRationale = false

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
        Log.session.debug("Snapshot persisted: state=\(self.state.rawValue), pendingEvent=\(eventToStore?.eventName ?? "nil")")
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
            Log.session.debug("No snapshot to restore")
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

        Log.session.info("Restored from snapshot: state=\(self.state.rawValue)")

        // 1. Retry pending event FIRST (before any other events)
        if let pending = pendingEvent {
            Log.session.info("Retrying pending event: \(pending.eventName)")
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
                    Log.session.info("Pending event retry succeeded")
                    self.clearPendingEvent()
                }
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
                Log.session.info("Reconciliation: IN_TRANSIT without grace period, starting timer")
                startGracePeriodTimer()
            }

            // Sanity check: if user "teleported" extremely far (>50km), end session
            // NOTE: This emits a non-canonical diagnostic event, then ends with grace_period_expired
            if let merchant = merchantTarget, let location = locationService.currentLocation {
                let distance = location.distance(from: CLLocation(
                    latitude: merchant.latitude,
                    longitude: merchant.longitude
                ))
                if distance > self.maxTeleportDistance_m {
                    Log.session.error("Reconciliation: teleport detected (\(Int(distance))m > \(Int(self.maxTeleportDistance_m))m), ending session")
                    // Emit non-canonical diagnostic (fire-and-forget, not in taxonomy)
                    if let session = activeSession {
                        emitDiagnosticEvent("teleport_detected", sessionId: session.sessionId, metadata: [
                            "distance_to_merchant": "\(Int(distance))",
                            "max_teleport_distance": "\(Int(self.maxTeleportDistance_m))"
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
                    Log.session.info("Reconciliation: anchor lost (\(Int(distance))m from charger)")
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
                    Log.session.info("Reconciliation: left charger zone (\(Int(distance))m)")
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
                    Log.session.info("Reconciliation: departed charger (\(Int(distance))m)")
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

        Log.session.debug("Rebuilt geofences for state: \(self.state.rawValue)")
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

    func triggerNotificationPermissionRationaleIfNeeded() {
        guard !shouldShowNotificationRationale else { return }

        NotificationService.shared.shouldShowRationale { [weak self] shouldShow in
            guard shouldShow else { return }
            DispatchQueue.main.async {
                NotificationService.shared.markRationaleShown()
                self?.shouldShowNotificationRationale = true
            }
        }
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

        // Validate coordinates are not (0,0) which indicates invalid data
        guard merchantLat != 0 || merchantLng != 0 else {
            Log.session.error("Invalid merchant coordinates (0,0)")
            notifyWeb(.sessionStartRejected(reason: "INVALID_MERCHANT_LOCATION"))
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

        triggerNotificationPermissionRationaleIfNeeded()
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
                    triggerNotificationPermissionRationaleIfNeeded()
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
            triggerNotificationPermissionRationaleIfNeeded()
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

        Log.session.info("Transition: \(previousState.rawValue) → \(newState.rawValue) via \(event.rawValue)")

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

        triggerHaptics(for: newState)

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

    private func triggerHaptics(for newState: SessionState) {
        switch newState {
        case .sessionActive, .atMerchant:
            triggerNotificationHaptic(.success)
        case .nearCharger:
            triggerHaptic(.light)
        case .sessionEnded:
            triggerHaptic(.medium)
        default:
            break
        }
    }

    private func triggerHaptic(_ style: UIImpactFeedbackGenerator.FeedbackStyle) {
        DispatchQueue.main.async {
            let generator = UIImpactFeedbackGenerator(style: style)
            generator.prepare()
            generator.impactOccurred()
        }
    }

    private func triggerNotificationHaptic(_ type: UINotificationFeedbackGenerator.FeedbackType) {
        DispatchQueue.main.async {
            let generator = UINotificationFeedbackGenerator()
            generator.prepare()
            generator.notificationOccurred(type)
        }
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
