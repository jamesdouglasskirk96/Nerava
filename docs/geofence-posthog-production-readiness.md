# Geofence PostHog Events - Production Readiness Report

**Date:** January 29, 2026  
**Purpose:** Verify feasibility of geofence-based PostHog events and document production requirements

## Executive Summary

✅ **Feasibility Confirmed:** The iOS app's background geofencing infrastructure can support PostHog geo-detected events.  
⚠️ **Production Requirements:** 3 key changes needed before production deployment.

---

## Test Events Created

Three test PostHog events have been created with real coordinates from Asadas Grill area:

### 1. User Entered Charger Radius
- **Event:** `ios.geofence.charger.entered`
- **Location:** Charger entry point (near Canyon Ridge Tesla Supercharger)
- **Coordinates:** `lat: 30.4037865, lng: -97.6732044`
- **Properties:** Includes charger_id, radius_m, distance_to_charger_m

### 2. User Entered Merchant Radius
- **Event:** `ios.geofence.merchant.entered`
- **Location:** Merchant entry point (Asadas Grill)
- **Coordinates:** `lat: 30.4028469, lng: -97.6719938`
- **Properties:** Includes merchant_id, charger_id, radius_m, distance_to_merchant_m

### 3. User Left Merchant Radius
- **Event:** `ios.geofence.merchant.exited`
- **Location:** Merchant exit point (outside Asadas Grill radius)
- **Coordinates:** `lat: 30.4037969, lng: -97.6729438`
- **Properties:** Includes merchant_id, charger_id, radius_m, distance_to_merchant_m

**Test Script:** `scripts/create_geofence_test_events.py`  
**To Run:** `POSTHOG_KEY=your_key python3 scripts/create_geofence_test_events.py`

---

## Current iOS Implementation Analysis

### ✅ What's Already Working

1. **Geofence Detection**
   - `GeofenceManager` handles charger and merchant geofences
   - Background monitoring enabled via `CLLocationManager`
   - Entry/exit callbacks implemented (`didEnterRegion`, `didExitRegion`)

2. **Event Emission**
   - `SessionEngine` emits events via `emitEventWithPending()`
   - Events sent to backend via `/v1/native/session-events` and `/v1/native/pre-session-events`
   - Idempotency and retry logic implemented
   - Events persist across app launches

3. **Location Access**
   - `LocationService` provides current location
   - High-accuracy mode available when needed
   - Background location updates enabled

### ⚠️ What's Missing for PostHog Geo Events

1. **Location Not Included in Event Payload**
   - Current events don't include `lat`/`lng` in metadata
   - Backend receives events but can't add geo coordinates

2. **Backend PostHog Integration**
   - Backend captures events but doesn't include geo coordinates
   - `native_events.py` router doesn't extract location from request

3. **Event Naming**
   - Current events use generic names (`enteredChargerIntentZone`, `enteredMerchantZone`)
   - Need standardized PostHog event names

---

## Production Requirements

### 1. iOS App Changes

#### 1.1 Include Location in Event Metadata

**File:** `Nerava/Nerava/Engine/SessionEngine.swift`

**Current Code (lines 619-633):**
```swift
let metadata: [String: String] = [
    "previous_state": previousState.rawValue,
    "new_state": newState.rawValue
]
```

**Required Change:**
```swift
// Get current location
let currentLocation = locationService.currentLocation
var metadata: [String: String] = [
    "previous_state": previousState.rawValue,
    "new_state": newState.rawValue
]

// Add geo coordinates if available
if let location = currentLocation {
    metadata["lat"] = String(location.coordinate.latitude)
    metadata["lng"] = String(location.coordinate.longitude)
    metadata["accuracy_m"] = String(location.horizontalAccuracy)
}
```

**Impact:** Low risk - adds optional metadata fields

#### 1.2 Standardize Geofence Event Names

**File:** `Nerava/Nerava/Engine/SessionState.swift`

**Current Events:**
- `enteredChargerIntentZone` → Should be `geofence.charger.entered`
- `enteredMerchantZone` → Should be `geofence.merchant.entered`
- `exitedChargerIntentZone` → Should be `geofence.charger.exited`
- (Merchant exit not currently tracked)

**Required Change:**
```swift
enum SessionEvent: String {
    // ... existing events ...
    case geofenceChargerEntered = "geofence.charger.entered"
    case geofenceChargerExited = "geofence.charger.exited"
    case geofenceMerchantEntered = "geofence.merchant.entered"
    case geofenceMerchantExited = "geofence.merchant.exited"
}
```

**Impact:** Medium risk - requires updating event handling logic

#### 1.3 Track Merchant Exit Events

**File:** `Nerava/Nerava/Engine/SessionEngine.swift`

**Current:** Merchant geofence has `notifyOnExit: false`

**Required Change:**
```swift
// In GeofenceManager.swift, line 30
func addMerchantGeofence(id: String, coordinate: CLLocationCoordinate2D, radius: Double) {
    let identifier = "merchant_\(id)"
    addRegion(identifier: identifier, coordinate: coordinate, radius: radius, notifyOnExit: true) // Changed to true
}
```

**And add handler:**
```swift
// In SessionEngine.swift, handleGeofenceExit()
if identifier.hasPrefix("merchant_") && state == .atMerchant {
    transition(to: .inTransit, event: .geofenceMerchantExited, occurredAt: now)
}
```

**Impact:** Medium risk - changes session state machine behavior

---

### 2. Backend Changes

#### 2.1 Extract Geo from Event Metadata

**File:** `backend/app/routers/native_events.py`

**Current Code (lines 201-213):**
```python
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
```

**Required Change:**
```python
# Extract geo coordinates from metadata
lat = None
lng = None
accuracy_m = None

if request.metadata:
    lat_str = request.metadata.get("lat")
    lng_str = request.metadata.get("lng")
    accuracy_str = request.metadata.get("accuracy_m")
    
    if lat_str and lng_str:
        try:
            lat = float(lat_str)
            lng = float(lng_str)
            if accuracy_str:
                accuracy_m = float(accuracy_str)
        except (ValueError, TypeError):
            pass  # Invalid format, skip geo

analytics.capture(
    distinct_id=str(driver.id),
    event=f"native_session_{request.event}",
    lat=lat,
    lng=lng,
    accuracy_m=accuracy_m,
    properties={
        "session_id": request.session_id,
        "event_id": request.event_id,
        "source": request.source,
        "app_state": request.app_state,
        "occurred_at": request.occurred_at,
        **(request.metadata or {})
    }
)
```

**Impact:** Low risk - adds optional geo extraction

#### 2.2 Update Pre-Session Events Endpoint

**File:** `backend/app/routers/native_events.py`

**Similar changes needed for `emit_pre_session_event` endpoint (lines 237-248)**

**Impact:** Low risk - same pattern as above

---

### 3. Testing Requirements

#### 3.1 Unit Tests
- [ ] Test geofence entry with location metadata
- [ ] Test geofence exit with location metadata
- [ ] Test event emission when location unavailable
- [ ] Test backend geo extraction from metadata

#### 3.2 Integration Tests
- [ ] Test full flow: iOS geofence → backend → PostHog
- [ ] Test background geofence events
- [ ] Test event retry with geo coordinates
- [ ] Verify PostHog dashboard shows geo data

#### 3.3 Field Testing
- [ ] Test at Asadas Grill location (real coordinates)
- [ ] Test charger radius entry/exit
- [ ] Test merchant radius entry/exit
- [ ] Verify accuracy of coordinates in PostHog

---

## Background Location Capability Verification

### ✅ iOS Background Location Support

**Confirmed Capabilities:**

1. **Geofence Monitoring**
   - ✅ Works in background (system-level)
   - ✅ Works when app is terminated
   - ✅ Delivered via `didEnterRegion`/`didExitRegion` callbacks
   - ✅ App launches in background to handle events

2. **Location Updates**
   - ✅ `allowsBackgroundLocationUpdates = true` configured
   - ✅ Significant location changes enabled for Always permission
   - ✅ High-accuracy mode available when app is active

3. **Event Persistence**
   - ✅ Events persist to UserDefaults via `persistSnapshot()`
   - ✅ Retry logic handles offline scenarios
   - ✅ Idempotency prevents duplicate events

### ⚠️ Limitations

1. **Force-Quit Behavior**
   - If user force-quits app, background location stops
   - Geofence monitoring continues (system-level)
   - App will launch in background to handle geofence events

2. **Battery Impact**
   - High-accuracy location updates drain battery
   - Current implementation uses low-accuracy for background
   - Geofence monitoring is battery-efficient

3. **Location Accuracy**
   - Background location accuracy: ~100-500m
   - Geofence entry/exit accuracy: ~50-100m
   - May need to account for accuracy in radius calculations

---

## Implementation Checklist

### Phase 1: iOS Changes (Week 1)
- [ ] Add location to event metadata in `SessionEngine.swift`
- [ ] Standardize geofence event names
- [ ] Enable merchant exit tracking
- [ ] Update unit tests

### Phase 2: Backend Changes (Week 1)
- [ ] Extract geo from metadata in `native_events.py`
- [ ] Update both session and pre-session endpoints
- [ ] Add error handling for invalid geo data
- [ ] Update unit tests

### Phase 3: Testing (Week 2)
- [ ] Run test script to verify PostHog events
- [ ] Field test at Asadas Grill location
- [ ] Verify PostHog dashboard visualization
- [ ] Test background scenarios

### Phase 4: Production Deployment (Week 2)
- [ ] Deploy iOS app update
- [ ] Deploy backend update
- [ ] Monitor PostHog for geo events
- [ ] Verify event accuracy

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Location unavailable | Low | Events still work without geo, just missing coordinates |
| Invalid geo format | Low | Backend validates and skips invalid data |
| Battery drain | Medium | Use low-accuracy mode in background, geofence is efficient |
| State machine changes | Medium | Thorough testing of merchant exit flow |
| Event naming changes | Low | Backward compatible event names can be maintained |

---

## Success Criteria

✅ **Production Ready When:**
1. All 3 geofence events include geo coordinates in PostHog
2. Events appear in PostHog dashboard with `lat`/`lng` properties
3. PostHog map visualization shows events at correct locations
4. Background geofence events work reliably
5. Battery impact is acceptable (< 5% per day)

---

## Next Steps

1. **Immediate:** Review this report with iOS engineer
2. **This Week:** Implement iOS changes (location in metadata)
3. **This Week:** Implement backend changes (geo extraction)
4. **Next Week:** Field testing at Asadas Grill
5. **Next Week:** Production deployment

---

## Appendix: Real Coordinates Used

**Asadas Grill:**
- Address: 501 W Canyon Ridge Dr, Austin, TX 78753
- Coordinates: `lat: 30.4027969, lng: -97.6719438`

**Canyon Ridge Tesla Supercharger:**
- Address: 500 W Canyon Ridge Dr, Austin, TX 78753
- Coordinates: `lat: 30.403686500000003, lng: -97.6731044`
- Distance to Asadas: ~149 meters

**Geofence Radii:**
- Charger Intent Radius: 400m
- Merchant Unlock Radius: 40m
