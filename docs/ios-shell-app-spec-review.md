# iOS Shell App Implementation Spec Review

## Executive Summary

This document reviews the comprehensive iOS native shell app specification and identifies gaps, improvements, and implementation requirements. The spec is well-structured but requires several enhancements before implementation.

---

## 1. Swift Type Definitions

### Issue
The spec references `SessionState`, `SessionEvent`, and `SessionConfig` but doesn't provide complete Swift definitions.

### Complete Type Definitions

#### SessionState.swift

```swift
import Foundation

/// Authoritative session state managed by native engine
enum SessionState: String, Codable {
    case idle = "IDLE"
    case nearCharger = "NEAR_CHARGER"
    case anchored = "ANCHORED"
    case sessionActive = "SESSION_ACTIVE"
    case inTransit = "IN_TRANSIT"
    case atMerchant = "AT_MERCHANT"
    case sessionEnded = "SESSION_ENDED"
    
    /// Human-readable description for debugging
    var description: String {
        switch self {
        case .idle: return "No active session, passive monitoring"
        case .nearCharger: return "User entered charger intent zone"
        case .anchored: return "User has dwelled at charger"
        case .sessionActive: return "Exclusive activated + anchored"
        case .inTransit: return "User left charger heading to merchant"
        case .atMerchant: return "User arrived at merchant"
        case .sessionEnded: return "Session complete or expired"
        }
    }
}
```

#### SessionEvent.swift

```swift
import Foundation

/// Events that trigger state transitions
enum SessionEvent: String, Codable {
    // Pre-session events (no session_id)
    case chargerTargeted = "chargerTargeted"
    case enteredChargerIntentZone = "enteredChargerIntentZone"
    case exitedChargerIntentZone = "exitedChargerIntentZone"
    case anchorDwellComplete = "anchorDwellComplete"
    case exitedChargerAnchorZone = "exitedChargerAnchorZone"
    case activationRejected = "activationRejected"
    
    // Session events (has session_id)
    case exclusiveActivatedByWeb = "exclusiveActivatedByWeb"
    case exitedChargerAnchorZone = "exitedChargerAnchorZone"
    case enteredMerchantZone = "enteredMerchantZone"
    case gracePeriodExpired = "gracePeriodExpired"
    case hardTimeoutExpired = "hardTimeoutExpired"
    case visitVerifiedByWeb = "visitVerifiedByWeb"
    case webRequestedEnd = "webRequestedEnd"
    case reset = "reset"
    
    /// Returns true if this event requires a session_id
    var requiresSessionId: Bool {
        switch self {
        case .chargerTargeted,
             .enteredChargerIntentZone,
             .exitedChargerIntentZone,
             .anchorDwellComplete,
             .exitedChargerAnchorZone,
             .activationRejected:
            return false
        default:
            return true
        }
    }
}
```

#### SessionConfig.swift

```swift
import Foundation

/// Remote configuration for session engine (fetched from backend)
struct SessionConfig: Codable {
    let chargerIntentRadius_m: Double
    let chargerAnchorRadius_m: Double
    let chargerDwellSeconds: Int
    let merchantUnlockRadius_m: Double
    let gracePeriodSeconds: Int
    let hardTimeoutSeconds: Int
    let locationAccuracyThreshold_m: Double
    let speedThresholdForDwell_mps: Double
    
    /// Default configuration (fallback if backend unavailable)
    static let `default` = SessionConfig(
        chargerIntentRadius_m: 400.0,
        chargerAnchorRadius_m: 30.0,
        chargerDwellSeconds: 120,
        merchantUnlockRadius_m: 40.0,
        gracePeriodSeconds: 900,
        hardTimeoutSeconds: 3600,
        locationAccuracyThreshold_m: 50.0,
        speedThresholdForDwell_mps: 1.5
    )
    
    /// Validate configuration values are within acceptable ranges
    func validate() -> Bool {
        return chargerIntentRadius_m > 0 && chargerIntentRadius_m <= 1000 &&
               chargerAnchorRadius_m > 0 && chargerAnchorRadius_m <= 100 &&
               chargerDwellSeconds > 0 && chargerDwellSeconds <= 600 &&
               merchantUnlockRadius_m > 0 && merchantUnlockRadius_m <= 200 &&
               gracePeriodSeconds > 0 && gracePeriodSeconds <= 3600 &&
               hardTimeoutSeconds > 0 && hardTimeoutSeconds <= 7200 &&
               locationAccuracyThreshold_m > 0 && locationAccuracyThreshold_m <= 200 &&
               speedThresholdForDwell_mps > 0 && speedThresholdForDwell_mps <= 10
    }
}
```

### Action Required
Add these complete type definitions to the spec document under "Implementation Code" section, before SessionEngine.swift.

---

## 2. Backend Dependencies Verification

### Status: ✅ All Critical Dependencies Exist

Verified dependencies:
- ✅ `get_current_driver` exists in `backend/app/dependencies/driver.py`
- ✅ `ExclusiveSession` model exists in `backend/app/models/exclusive_session.py`
- ✅ `get_analytics_client()` exists in `backend/app/services/analytics.py`

### Issues Identified

#### 2.1 In-Memory Rate Limiter
**Location**: `backend/app/routers/native_events.py` (lines 1667-1688)

**Problem**: Uses in-memory dictionary that:
- Resets on server restart
- Doesn't scale across multiple server instances
- Can be bypassed by restarting server

**Redis Migration Plan**:

```python
# backend/app/services/rate_limiter.py
import redis
from typing import Optional
from app.core.config import settings

class RateLimiter:
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        if settings.REDIS_URL:
            self.redis_client = redis.from_url(settings.REDIS_URL)
    
    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        if not self.redis_client:
            # Fallback to in-memory for local dev
            return self._check_memory(key, limit, window_seconds)
        
        # Use Redis sliding window
        pipe = self.redis_client.pipeline()
        now = time.time()
        cutoff = now - window_seconds
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, cutoff)
        # Count current entries
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set expiry
        pipe.expire(key, window_seconds)
        
        results = pipe.execute()
        count = results[1]
        
        return count < limit
    
    def _check_memory(self, key: str, limit: int, window_seconds: int) -> bool:
        # In-memory fallback (existing logic)
        ...
```

**Migration Steps**:
1. Add `REDIS_URL` to `backend/app/core/config.py`
2. Create `backend/app/services/rate_limiter.py`
3. Update `native_events.py` to use new RateLimiter
4. Deploy Redis instance (AWS ElastiCache, Railway Redis, etc.)
5. Set `REDIS_URL` environment variable

#### 2.2 In-Memory Idempotency Cache
**Location**: `backend/app/routers/native_events.py` (lines 1737-1756)

**Problem**: Uses in-memory set that:
- Resets on server restart
- Can grow unbounded
- Doesn't persist across restarts

**Redis Migration Plan**:

```python
def _check_idempotency(key: str) -> bool:
    """Returns True if this is a duplicate (already processed)."""
    if not redis_client:
        # Fallback to in-memory
        return _check_idempotency_memory(key)
    
    # Use Redis with TTL (24 hour expiry)
    exists = redis_client.exists(f"idempotency:{key}")
    if exists:
        return True
    
    redis_client.setex(f"idempotency:{key}", 86400, "1")
    return False
```

**Migration Steps**:
1. Use same Redis client as rate limiter
2. Add TTL of 24 hours (events older than 24h can be reprocessed)
3. Use key prefix `idempotency:{key}`

#### 2.3 Hardcoded Config Values
**Location**: `backend/app/routers/native_events.py` (lines 1880-1889)

**Problem**: Config endpoint returns hardcoded values instead of reading from environment/config.

**Fix Required**:

```python
@router.get("/config", response_model=NativeConfigResponse)
async def get_native_config(
    driver: User = Depends(get_current_driver)
):
    """
    Get remote configuration for native session engine.
    Cache this client-side for 24 hours.
    """
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

**Add to `backend/app/core/config.py`**:

```python
# Native session engine configuration
NATIVE_CHARGER_INTENT_RADIUS_M: float = float(os.getenv("NATIVE_CHARGER_INTENT_RADIUS_M", "400"))
NATIVE_CHARGER_ANCHOR_RADIUS_M: float = float(os.getenv("NATIVE_CHARGER_ANCHOR_RADIUS_M", "30"))
NATIVE_CHARGER_DWELL_SECONDS: int = int(os.getenv("NATIVE_CHARGER_DWELL_SECONDS", "120"))
NATIVE_MERCHANT_UNLOCK_RADIUS_M: float = float(os.getenv("NATIVE_MERCHANT_UNLOCK_RADIUS_M", "40"))
NATIVE_GRACE_PERIOD_SECONDS: int = int(os.getenv("NATIVE_GRACE_PERIOD_SECONDS", "900"))
NATIVE_HARD_TIMEOUT_SECONDS: int = int(os.getenv("NATIVE_HARD_TIMEOUT_SECONDS", "3600"))
NATIVE_LOCATION_ACCURACY_THRESHOLD_M: float = float(os.getenv("NATIVE_LOCATION_ACCURACY_THRESHOLD_M", "50"))
NATIVE_SPEED_THRESHOLD_FOR_DWELL_MPS: float = float(os.getenv("NATIVE_SPEED_THRESHOLD_FOR_DWELL_MPS", "1.5"))
```

### Action Required
1. Add config values to `backend/app/core/config.py`
2. Update config endpoint to use settings
3. Document Redis migration path (can be done post-MVP)

---

## 3. Web App Integration Points

### Status: ⚠️ Integration Hooks Don't Exist Yet

### Integration Map

#### 3.1 Charger Discovery Integration

**Location**: `apps/driver/src/components/DriverHome/DriverHome.tsx`

**Current Code** (around line 200-300):
```typescript
const { data: intentData } = useIntentCapture(intentRequest)
// Stores charger in state when discovered
```

**Integration Point**:
```typescript
import { useNativeBridge } from '../../hooks/useNativeBridge'

// Inside DriverHome component
const { setChargerTarget, isNative } = useNativeBridge()

// After charger is discovered
useEffect(() => {
  if (isNative && intentData?.charger_summary?.charger_id) {
    const charger = intentData.charger_summary
    setChargerTarget(
      charger.charger_id,
      charger.lat,
      charger.lng
    )
  }
}, [isNative, intentData, setChargerTarget])
```

**Exact Location**: Add after line ~220 where `intentData` is used.

#### 3.2 Exclusive Activation Integration

**Location**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`

**Current Code** (around line 86-99):
```typescript
const response = await activateExclusive.mutateAsync({
  merchant_id: merchantId,
  merchant_place_id: merchantId,
  charger_id: chargerId,
  lat: lat ?? 0,
  lng: lng ?? 0,
  accuracy_m,
})

setExclusiveSessionId(response.exclusive_session.id)
```

**Integration Point**:
```typescript
import { useNativeBridge } from '../../hooks/useNativeBridge'

// Inside MerchantDetailsScreen component
const { confirmExclusiveActivated, isNative } = useNativeBridge()

// After successful activation
const handleActivateExclusive = useCallback(async () => {
  // ... existing activation code ...
  
  try {
    const response = await activateExclusive.mutateAsync({...})
    
    setExclusiveSessionId(response.exclusive_session.id)
    setRemainingSeconds(response.exclusive_session.remaining_seconds)
    
    // NEW: Notify native app
    if (isNative && merchantData?.merchant) {
      confirmExclusiveActivated(
        response.exclusive_session.id,
        merchantData.merchant.id,
        merchantData.merchant.lat,
        merchantData.merchant.lng
      )
    }
    
    setFlowState('activated')
  } catch (err) {
    // ... error handling ...
  }
}, [isNative, confirmExclusiveActivated, merchantData])
```

**Exact Location**: Add after line 96 where `setExclusiveSessionId` is called.

#### 3.3 Visit Verification Integration

**Location**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`

**Current Code** (around line 120-150):
```typescript
const handleVerifyVisit = useCallback(async () => {
  if (!exclusiveSessionId || !verificationCode) return
  
  try {
    await verifyVisit.mutateAsync({
      session_id: exclusiveSessionId,
      verification_code: verificationCode,
    })
    // ... success handling ...
  } catch (err) {
    // ... error handling ...
  }
}, [exclusiveSessionId, verificationCode])
```

**Integration Point**:
```typescript
import { useNativeBridge } from '../../hooks/useNativeBridge'

// Inside MerchantDetailsScreen component
const { confirmVisitVerified, isNative } = useNativeBridge()

// After successful verification
const handleVerifyVisit = useCallback(async () => {
  if (!exclusiveSessionId || !verificationCode) return
  
  try {
    await verifyVisit.mutateAsync({
      session_id: exclusiveSessionId,
      verification_code: verificationCode,
    })
    
    // NEW: Notify native app
    if (isNative) {
      confirmVisitVerified(exclusiveSessionId, verificationCode)
    }
    
    setFlowState('completed')
  } catch (err) {
    // ... error handling ...
  }
}, [isNative, confirmVisitVerified, exclusiveSessionId, verificationCode])
```

**Exact Location**: Add after successful `verifyVisit.mutateAsync` call.

### Action Required
1. Create `apps/driver/src/hooks/useNativeBridge.ts` (spec already provides code)
2. Add integration points at exact locations above
3. Test that native bridge is only called when `isNative === true`

---

## 4. State Machine Validation

### State Transition Matrix

| Current State | Event | Next State | Valid? | Notes |
|--------------|-------|------------|--------|-------|
| IDLE | chargerTargetSet | IDLE | ✅ | Sets geofence, stays idle |
| IDLE | enteredChargerIntentZone | NEAR_CHARGER | ✅ | User enters 400m zone |
| NEAR_CHARGER | exitedChargerIntentZone | IDLE | ✅ | User leaves 400m zone |
| NEAR_CHARGER | anchorDwellComplete | ANCHORED | ✅ | User dwelled 120s within 30m |
| ANCHORED | exclusiveActivatedByWeb | SESSION_ACTIVE | ✅ | Requires ANCHORED state |
| ANCHORED | exitedChargerAnchorZone | NEAR_CHARGER | ✅ | Lost anchor, back to near |
| SESSION_ACTIVE | exitedChargerAnchorZone | IN_TRANSIT | ✅ | User left charger |
| IN_TRANSIT | enteredMerchantZone | AT_MERCHANT | ✅ | User arrived at merchant |
| IN_TRANSIT | gracePeriodExpired | SESSION_ENDED | ✅ | 15min grace period expired |
| AT_MERCHANT | visitVerifiedByWeb | SESSION_ENDED | ✅ | Web confirms verification |
| AT_MERCHANT | hardTimeoutExpired | SESSION_ENDED | ✅ | 60min timeout expired |
| SESSION_ACTIVE | hardTimeoutExpired | SESSION_ENDED | ✅ | 60min timeout expired |
| IN_TRANSIT | hardTimeoutExpired | SESSION_ENDED | ✅ | 60min timeout expired |
| SESSION_ENDED | reset | IDLE | ✅ | Reset for new session |

### Invalid Transitions (Should Be Rejected)

| Current State | Event | Expected Behavior |
|--------------|-------|-------------------|
| IDLE | exclusiveActivatedByWeb | ❌ Reject - not anchored |
| NEAR_CHARGER | exclusiveActivatedByWeb | ❌ Reject - not anchored |
| ANCHORED | visitVerifiedByWeb | ❌ Reject - not at merchant |
| SESSION_ACTIVE | enteredMerchantZone | ⚠️ Should transition via IN_TRANSIT |

### Backend Event Name Mapping

**Pre-session events** (no session_id):
- `chargerTargeted` → `native_presession_chargerTargeted`
- `enteredChargerIntentZone` → `native_presession_enteredChargerIntentZone`
- `anchorDwellComplete` → `native_presession_anchorDwellComplete`
- `activationRejected` → `native_presession_activationRejected`

**Session events** (has session_id):
- `exclusiveActivatedByWeb` → `native_session_exclusiveActivatedByWeb`
- `exitedChargerAnchorZone` → `native_session_exitedChargerAnchorZone`
- `enteredMerchantZone` → `native_session_enteredMerchantZone`
- `gracePeriodExpired` → `native_session_gracePeriodExpired`
- `hardTimeoutExpired` → `native_session_hardTimeoutExpired`
- `visitVerifiedByWeb` → `native_session_visitVerifiedByWeb`

### Validation Required
✅ State names match backend expectations (case-sensitive)
✅ All transition conditions are clearly defined
✅ Invalid transitions are properly handled (see SessionEngine.swift line 276-280)
✅ Timer-based transitions are correctly implemented

### Action Required
No changes needed - spec correctly defines state machine. Add validation matrix to spec document for reference.

---

## 5. iOS Background Execution Limitations

### iOS Background Location Restrictions

#### 5.1 Background Location Updates
**Requirement**: "Always" location permission + `UIBackgroundModes` with `location`

**Limitations**:
- iOS suspends background location updates if user force-quits app
- Geofence monitoring continues even if app is terminated (system-level)
- Significant location changes continue even if app is terminated

**Workaround**:
```swift
// In LocationService.swift
func startMonitoring() {
    if authorizationStatus == .authorizedAlways {
        // Use significant location changes for background
        locationManager.startMonitoringSignificantLocationChanges()
    }
    
    if isHighAccuracyMode {
        // High accuracy only when app is active
        locationManager.startUpdatingLocation()
    }
}
```

#### 5.2 Geofence Events When App Terminated
**Behavior**: iOS delivers geofence events even if app is terminated via:
- `locationManager:didEnterRegion:` (app launches in background)
- `locationManager:didExitRegion:` (app launches in background)

**Handling**:
```swift
// In AppDelegate.swift
func application(_ application: UIApplication, 
                didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
    
    // Check if app launched due to location event
    if launchOptions?[.location] != nil {
        // Restore session engine state from UserDefaults
        sessionEngine.restoreFromBackground()
    }
    
    return true
}
```

#### 5.3 Force-Quit During IN_TRANSIT
**Problem**: If user force-quits app during IN_TRANSIT, grace period timer stops.

**Solution**: 
1. Persist grace period deadline to UserDefaults (already implemented)
2. On app launch, check if deadline has passed
3. If passed, transition to SESSION_ENDED

**Implementation** (already in spec):
```swift
// SessionEngine.swift lines 576-595
private func restoreTimersIfNeeded() {
    gracePeriodDeadline = UserDefaults.standard.object(forKey: "gracePeriodDeadline") as? Date
    hardTimeoutDeadline = UserDefaults.standard.object(forKey: "hardTimeoutDeadline") as? Date
    
    // Check if already expired
    checkTimerDeadlines()
    
    // Recreate timers if still valid
    if let deadline = gracePeriodDeadline, deadline > Date() {
        gracePeriodTimer = BackgroundTimer(deadline: deadline) { [weak self] in
            self?.handleGracePeriodExpired()
        }
    }
}
```

#### 5.4 Background Execution Time Limits
**iOS Limits**:
- Background location updates: ~3 minutes after app enters background
- Significant location changes: Unlimited (but battery-intensive)
- Geofence monitoring: Unlimited (system-level)

**Recommendation**: 
- Use geofence monitoring for charger/merchant zones (unlimited)
- Use significant location changes for transit tracking (battery-efficient)
- Use high-accuracy location only when app is foreground

### Action Required
Add background execution limitations section to spec document with workarounds documented above.

---

## 6. Security Considerations

### ✅ Good Security Practices (Already in Spec)

1. **Origin Validation**: Exact match (not substring) - `NativeBridge.swift` line 1067-1083
2. **Token Storage**: Keychain (not UserDefaults) - `KeychainService.swift`
3. **Rate Limiting**: Prevents abuse - `native_events.py` line 1774
4. **Idempotency**: Prevents duplicate events - `native_events.py` line 1781

### ⚠️ Security Improvements Needed

#### 6.1 Certificate Pinning
**Issue**: No mention of certificate pinning for API calls.

**Recommendation**:
```swift
// In APIClient.swift
import Security

class APIClient {
    private func setupCertificatePinning() {
        // Pin to api.nerava.network certificate
        // Use URLSessionDelegate to validate certificate chain
    }
}
```

**Action**: Add certificate pinning to APIClient for production builds.

#### 6.2 Token Refresh Security
**Issue**: No mention of token refresh handling.

**Recommendation**:
- Web app handles token refresh as usual
- Web calls `neravaNative.setAuthToken(newToken)` when refreshed
- Native app updates Keychain immediately
- If native API call fails with 401, request fresh token from web

**Action**: Document token refresh flow in spec.

#### 6.3 Bridge Injection Security
**Issue**: Injection script is injected at document start - could be modified by malicious page.

**Mitigation** (already implemented):
- Origin validation prevents unauthorized origins
- Script is injected before page loads
- Bridge only responds to exact origin matches

**Action**: No changes needed - already secure.

#### 6.4 Rate Limiter Bypass
**Issue**: In-memory rate limiter can be bypassed by restarting server.

**Mitigation**:
- Use Redis for production (see section 2.1)
- Add per-IP rate limiting at nginx/load balancer level
- Monitor for unusual event patterns

**Action**: Document Redis migration as production requirement.

### Action Required
1. Add certificate pinning section to spec
2. Document token refresh flow
3. Mark Redis migration as production requirement

---

## 7. Testing Strategy

### ✅ Existing Acceptance Tests
The spec includes 8 comprehensive manual acceptance tests covering:
1. Permission flow
2. Charger targeting
3. Anchor detection
4. Full session flow
5. Background behavior
6. Activation rejection
7. Timer persistence
8. Backend event verification

### ⚠️ Missing Test Coverage

#### 7.1 Unit Tests Required

**SessionEngineTests.swift**:
```swift
import XCTest
@testable import Nerava

class SessionEngineTests: XCTestCase {
    var sessionEngine: SessionEngine!
    var mockLocationService: MockLocationService!
    var mockGeofenceManager: MockGeofenceManager!
    var mockAPIClient: MockAPIClient!
    
    override func setUp() {
        super.setUp()
        // Setup mocks
        mockLocationService = MockLocationService()
        mockGeofenceManager = MockGeofenceManager()
        mockAPIClient = MockAPIClient()
        
        let config = SessionConfig.default
        sessionEngine = SessionEngine(
            locationService: mockLocationService,
            geofenceManager: mockGeofenceManager,
            apiClient: mockAPIClient,
            config: config
        )
    }
    
    func testInvalidTransitionFromIdleToSessionActive() {
        // Should reject activation when not anchored
        sessionEngine.webConfirmsExclusiveActivated(
            sessionId: "test-session",
            merchantId: "test-merchant",
            merchantLat: 0.0,
            merchantLng: 0.0
        )
        
        XCTAssertEqual(sessionEngine.state, .idle)
        // Verify rejection event was emitted
    }
    
    func testValidTransitionIdleToNearCharger() {
        // Set charger target
        sessionEngine.setChargerTarget(chargerId: "test-charger", lat: 0.0, lng: 0.0)
        
        // Simulate entering geofence
        mockGeofenceManager.simulateEnterRegion("charger_test-charger")
        
        XCTAssertEqual(sessionEngine.state, .nearCharger)
    }
    
    func testGracePeriodExpiration() {
        // Setup session in IN_TRANSIT
        // Fast-forward time
        // Verify transition to SESSION_ENDED
    }
    
    func testHardTimeoutExpiration() {
        // Setup session in SESSION_ACTIVE
        // Fast-forward time
        // Verify transition to SESSION_ENDED
    }
}
```

**DwellDetectorTests.swift**:
```swift
class DwellDetectorTests: XCTestCase {
    func testDwellDetectionWithinRadius() {
        // Record locations within anchor radius
        // Verify isAnchored becomes true after dwell duration
    }
    
    func testDwellResetOnExit() {
        // Start dwell
        // Exit radius
        // Verify dwell resets
    }
    
    func testDwellResetOnHighSpeed() {
        // Start dwell
        // Record high-speed location
        // Verify dwell resets
    }
}
```

**NativeBridgeTests.swift**:
```swift
class NativeBridgeTests: XCTestCase {
    func testOriginValidation() {
        // Test allowed origins pass
        // Test disallowed origins are rejected
    }
    
    func testMessageHandling() {
        // Test each message type is handled correctly
        // Test error handling for invalid messages
    }
}
```

#### 7.2 Integration Tests Required

**End-to-End Flow Test**:
```swift
class SessionFlowIntegrationTests: XCTestCase {
    func testFullSessionFlow() {
        // 1. Set charger target
        // 2. Enter charger zone
        // 3. Anchor at charger
        // 4. Activate exclusive
        // 5. Exit charger zone
        // 6. Enter merchant zone
        // 7. Verify visit
        // 8. Verify session ended
        
        // Assert all state transitions occurred
        // Assert all backend events were emitted
    }
}
```

### Action Required
Add unit test and integration test requirements to spec document under "Testing Strategy" section.

---

## 8. Configuration Management

### Issue
Config endpoint returns hardcoded values instead of reading from environment/config.

### Fix Required

**Update `backend/app/core/config.py`**:
```python
# Native session engine configuration
NATIVE_CHARGER_INTENT_RADIUS_M: float = float(os.getenv("NATIVE_CHARGER_INTENT_RADIUS_M", "400"))
NATIVE_CHARGER_ANCHOR_RADIUS_M: float = float(os.getenv("NATIVE_CHARGER_ANCHOR_RADIUS_M", "30"))
NATIVE_CHARGER_DWELL_SECONDS: int = int(os.getenv("NATIVE_CHARGER_DWELL_SECONDS", "120"))
NATIVE_MERCHANT_UNLOCK_RADIUS_M: float = float(os.getenv("NATIVE_MERCHANT_UNLOCK_RADIUS_M", "40"))
NATIVE_GRACE_PERIOD_SECONDS: int = int(os.getenv("NATIVE_GRACE_PERIOD_SECONDS", "900"))
NATIVE_HARD_TIMEOUT_SECONDS: int = int(os.getenv("NATIVE_HARD_TIMEOUT_SECONDS", "3600"))
NATIVE_LOCATION_ACCURACY_THRESHOLD_M: float = float(os.getenv("NATIVE_LOCATION_ACCURACY_THRESHOLD_M", "50"))
NATIVE_SPEED_THRESHOLD_FOR_DWELL_MPS: float = float(os.getenv("NATIVE_SPEED_THRESHOLD_FOR_DWELL_MPS", "1.5"))
```

**Update `backend/app/routers/native_events.py`**:
```python
@router.get("/config", response_model=NativeConfigResponse)
async def get_native_config(
    driver: User = Depends(get_current_driver)
):
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

### Action Required
1. Add config values to `backend/app/core/config.py`
2. Update config endpoint to use settings
3. Document environment variables in `ENV.example`

---

## 9. Migration Strategy from Flutter App

### Current State
- Flutter app exists at `mobile/nerava_flutter/`
- Flutter app wraps web app but doesn't have session engine
- iOS native app will add session engine functionality

### Options

#### Option 1: Coexistence (Recommended for MVP)
**Strategy**: Maintain both apps during transition period.

**Pros**:
- Low risk - existing Flutter app continues working
- Can A/B test native vs Flutter
- Gradual migration path

**Cons**:
- Maintenance overhead (two codebases)
- User confusion (which app to use?)

**Implementation**:
- Deploy iOS native app as separate TestFlight build
- Monitor usage metrics
- Gradually migrate users to native app
- Deprecate Flutter app after 6 months

#### Option 2: Replace Flutter
**Strategy**: Replace Flutter app with native iOS app.

**Pros**:
- Single codebase to maintain
- Better performance (native vs Flutter)
- Access to iOS-specific features

**Cons**:
- Higher risk - need to rebuild Android app separately
- Lose cross-platform code sharing
- Longer development time

**Implementation**:
- Build iOS native app first
- Build Android native app second (or use Flutter for Android)
- Deprecate Flutter app after both native apps are stable

#### Option 3: Hybrid Approach
**Strategy**: Use Flutter for Android, native iOS for iOS.

**Pros**:
- Best of both worlds
- Native iOS performance + Flutter Android speed

**Cons**:
- Two codebases (but different platforms)
- Feature parity challenges

### Recommendation: Option 1 (Coexistence)

**Rationale**:
1. Lower risk for MVP launch
2. Allows validation of native app before full migration
3. Provides fallback if native app has issues
4. Can gather user feedback on both approaches

**Migration Timeline**:
- **Month 1-2**: Build iOS native app
- **Month 3**: TestFlight beta with 50 users
- **Month 4**: App Store release (coexist with Flutter)
- **Month 5-6**: Monitor metrics, gather feedback
- **Month 7**: Decide on full migration or continue coexistence

### Action Required
Document migration strategy in spec document under "Rollout Plan" section.

---

## Summary of Required Actions

### High Priority (Before Implementation)
1. ✅ Add complete Swift type definitions (SessionState, SessionEvent, SessionConfig)
2. ✅ Add config values to `backend/app/core/config.py`
3. ✅ Update config endpoint to use settings
4. ✅ Create web app integration map document

### Medium Priority (During Implementation)
5. ✅ Document Redis migration path (can use in-memory for MVP)
6. ✅ Add unit test requirements to spec
7. ✅ Document background execution limitations
8. ✅ Document security hardening recommendations

### Low Priority (Post-MVP)
9. ✅ Implement Redis rate limiter
10. ✅ Implement certificate pinning
11. ✅ Document migration strategy from Flutter

---

## Next Steps

1. **Update Spec Document**: Add missing Swift types, config management, testing requirements
2. **Create Backend Changes**: Add config values, update endpoint
3. **Create Integration Guide**: Document exact web app integration points
4. **Begin Implementation**: Start with backend endpoints, then iOS app, then web integration

