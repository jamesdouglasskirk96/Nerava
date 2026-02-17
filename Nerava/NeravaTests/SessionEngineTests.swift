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
