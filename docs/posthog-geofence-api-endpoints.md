# PostHog Geofence Events API - Swagger Endpoints

**Date:** January 29, 2026  
**Status:** ✅ All endpoints tested and validated

---

## API Endpoints

All endpoints are available in Swagger UI at: **http://localhost:8001/docs**

### Base Path
`/v1/posthog`

---

## 1. Charger Geofence Entry

**Endpoint:** `POST /v1/posthog/geofence/charger/entered`

**Description:** Trigger PostHog event when user enters charger geofence radius

**Event Name:** `ios.geofence.charger.entered`

**Request Body:**
```json
{
  "distinct_id": "driver:test_driver_123",
  "charger_id": "canyon_ridge_tesla",
  "charger_name": "Tesla Supercharger - Canyon Ridge",
  "charger_address": "500 W Canyon Ridge Dr, Austin, TX 78753",
  "lat": 30.4037865,
  "lng": -97.6730044,
  "accuracy_m": 10.0,
  "radius_m": 400,
  "distance_to_charger_m": 15.0,
  "user_id": "optional_user_id",
  "session_id": "optional_session_id"
}
```

**Required Fields:**
- `distinct_id` (string)
- `charger_id` (string)
- `lat` (float)
- `lng` (float)

**Response:**
```json
{
  "ok": true,
  "event": "ios.geofence.charger.entered",
  "distinct_id": "driver:test_driver_123",
  "message": "Event sent to PostHog",
  "note": "Check PostHog dashboard in ~30 seconds"
}
```

---

## 2. Merchant Geofence Entry

**Endpoint:** `POST /v1/posthog/geofence/merchant/entered`

**Description:** Trigger PostHog event when user enters merchant geofence radius

**Event Name:** `ios.geofence.merchant.entered`

**Request Body:**
```json
{
  "distinct_id": "driver:test_driver_123",
  "merchant_id": "asadas_grill_canyon_ridge",
  "merchant_name": "Asadas Grill",
  "merchant_address": "501 W Canyon Ridge Dr, Austin, TX 78753",
  "charger_id": "canyon_ridge_tesla",
  "lat": 30.4028469,
  "lng": -97.6718938,
  "accuracy_m": 8.0,
  "radius_m": 40,
  "distance_to_merchant_m": 5.0,
  "distance_to_charger_m": 149.0,
  "user_id": "optional_user_id",
  "session_id": "optional_session_id"
}
```

**Required Fields:**
- `distinct_id` (string)
- `merchant_id` (string)
- `lat` (float)
- `lng` (float)

**Response:**
```json
{
  "ok": true,
  "event": "ios.geofence.merchant.entered",
  "distinct_id": "driver:test_driver_123",
  "message": "Event sent to PostHog",
  "note": "Check PostHog dashboard in ~30 seconds"
}
```

---

## 3. Merchant Geofence Exit

**Endpoint:** `POST /v1/posthog/geofence/merchant/exited`

**Description:** Trigger PostHog event when user exits merchant geofence radius

**Event Name:** `ios.geofence.merchant.exited`

**Request Body:**
```json
{
  "distinct_id": "driver:test_driver_123",
  "merchant_id": "asadas_grill_canyon_ridge",
  "merchant_name": "Asadas Grill",
  "merchant_address": "501 W Canyon Ridge Dr, Austin, TX 78753",
  "charger_id": "canyon_ridge_tesla",
  "lat": 30.4037969,
  "lng": -97.6709438,
  "accuracy_m": 12.0,
  "radius_m": 40,
  "distance_to_merchant_m": 120.0,
  "distance_to_charger_m": 150.0,
  "user_id": "optional_user_id",
  "session_id": "optional_session_id"
}
```

**Required Fields:**
- `distinct_id` (string)
- `merchant_id` (string)
- `lat` (float)
- `lng` (float)

**Response:**
```json
{
  "ok": true,
  "event": "ios.geofence.merchant.exited",
  "distinct_id": "driver:test_driver_123",
  "message": "Event sent to PostHog",
  "note": "Check PostHog dashboard in ~30 seconds"
}
```

---

## Test Data (Asadas Grill Area)

### Real Coordinates

**Charger (Canyon Ridge Tesla Supercharger):**
- Address: 500 W Canyon Ridge Dr, Austin, TX 78753
- Coordinates: `lat: 30.403686500000003, lng: -97.6731044`
- Charger ID: `canyon_ridge_tesla`

**Merchant (Asadas Grill):**
- Address: 501 W Canyon Ridge Dr, Austin, TX 78753
- Coordinates: `lat: 30.4027969, lng: -97.6719438`
- Merchant ID: `asadas_grill_canyon_ridge`
- Distance to charger: ~149 meters

### Example Test Requests

**Charger Entry (inside radius):**
```json
{
  "distinct_id": "driver:test_demo",
  "charger_id": "canyon_ridge_tesla",
  "lat": 30.4037865,
  "lng": -97.6730044,
  "accuracy_m": 10.0
}
```

**Merchant Entry (inside radius):**
```json
{
  "distinct_id": "driver:test_demo",
  "merchant_id": "asadas_grill_canyon_ridge",
  "lat": 30.4028469,
  "lng": -97.6718938,
  "accuracy_m": 8.0
}
```

**Merchant Exit (outside radius):**
```json
{
  "distinct_id": "driver:test_demo",
  "merchant_id": "asadas_grill_canyon_ridge",
  "lat": 30.4037969,
  "lng": -97.6709438,
  "accuracy_m": 12.0
}
```

---

## Using Swagger UI

1. **Open Swagger:** http://localhost:8001/docs
2. **Find Section:** Look for "PostHog Events" tag
3. **Select Endpoint:** Click on the endpoint you want to test
4. **Click "Try it out"**
5. **Fill Request Body:** Use the example JSON above
6. **Click "Execute"**
7. **View Response:** Check the response for `"ok": true`

---

## Validation Results

✅ **All 3 endpoints tested and working:**
- ✅ Charger entered endpoint: Returns 200 OK
- ✅ Merchant entered endpoint: Returns 200 OK  
- ✅ Merchant exited endpoint: Returns 200 OK

✅ **Events sent to PostHog:**
- All events include geo coordinates (`lat`, `lng`, `accuracy_m`)
- Events appear in PostHog dashboard within 30-60 seconds
- Filter by `distinct_id` to find your test events

---

## PostHog Dashboard Verification

After triggering events via Swagger:

1. Go to PostHog dashboard
2. Navigate to **Activity** → **Events**
3. Filter by:
   - **distinct_id:** Your test distinct_id
   - **Event name:** `ios.geofence.*`
4. Check **"Last hour"** time range
5. Verify events include:
   - `lat` and `lng` properties
   - `accuracy_m` property
   - Charger/merchant details

---

## For Your PostHog Engineer Call

**Endpoints to demonstrate:**
1. `POST /v1/posthog/geofence/charger/entered`
2. `POST /v1/posthog/geofence/merchant/entered`
3. `POST /v1/posthog/geofence/merchant/exited`

**Swagger UI:** http://localhost:8001/docs

**Test distinct_id:** `driver:test_driver_geofence_demo`

**Real coordinates used:**
- Charger: `30.403686500000003, -97.6731044`
- Merchant: `30.4027969, -97.6719438`

All endpoints are production-ready and include full geo coordinate tracking.
