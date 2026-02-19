# Nerava iOS Flow: API Endpoints & PostHog/HubSpot Attribute Guide

**Audience:** Engineer setting up PostHog event tracking and HubSpot contact property sync
**Date:** 2026-01-30

---

## How to Read This Document

This document walks through every API endpoint the iOS (driver) app calls, **in the order a real user encounters them**. For each endpoint you'll find:

- What the user is doing when it fires
- The full request and response payload
- Which fields are good candidates for PostHog event properties or HubSpot contact properties

The app has three states: **Pre-Charging** (browsing chargers) → **Charging Active** (browsing merchants near their charger) → **Exclusive Active** (timer countdown after securing a deal). The user progresses through these linearly.

---

## Phase 1: App Launch & Onboarding

**What happens:** User opens the app for the first time. A 3-screen onboarding slideshow plays. No API calls are made — this is entirely local.

**PostHog events to track:**

| Event Name | When | Properties |
|---|---|---|
| `driver.onboarding.started` | First screen shown | — |
| `driver.onboarding.completed` | User finishes all 3 screens | — |
| `driver.location.permission.granted` | User taps "Enable Location" | — |
| `driver.location.permission.denied` | User taps "Skip" or denies OS prompt | — |

**HubSpot properties:**

| Property | Type | Source |
|---|---|---|
| `onboarding_completed` | Boolean | Set `true` when onboarding finishes |
| `location_permission` | String | `"granted"` or `"denied"` |

---

## Phase 2: Intent Capture — Finding Chargers & Merchants

### Endpoint: `POST /v1/intent/capture`

**What the user sees:** The main discovery screen. The app sends the user's GPS coordinates and gets back the nearest charger + nearby merchants.

**When it fires:** Immediately after the app gets a GPS fix. Re-fires if the user moves significantly or pulls to refresh.

**Auth required:** Optional. Works for anonymous users (no session created) and authenticated users (creates an intent session).

#### Request

```json
{
  "lat": 30.2672,
  "lng": -97.7431,
  "accuracy_m": 12.5,
  "client_ts": "2026-01-30T14:30:00Z"
}
```

| Field | Type | Description |
|---|---|---|
| `lat` | float | User's latitude from GPS |
| `lng` | float | User's longitude from GPS |
| `accuracy_m` | float (optional) | GPS accuracy in meters. If too high (>150m), the request is rejected |
| `client_ts` | string (optional) | ISO 8601 timestamp from the client clock |

#### Response

```json
{
  "session_id": "a1b2c3d4-uuid",
  "confidence_tier": "A",
  "charger_summary": {
    "id": "canyon_ridge_tesla",
    "name": "Tesla Supercharger - Canyon Ridge",
    "distance_m": 45,
    "network_name": "Tesla"
  },
  "merchants": [
    {
      "place_id": "ChIJ_google_place_id",
      "name": "Asadas Grill",
      "lat": 30.4028,
      "lng": -97.6719,
      "distance_m": 149,
      "types": ["restaurant", "food"],
      "photo_url": "https://...",
      "icon_url": "https://...",
      "badges": ["exclusive", "popular"],
      "daily_cap_cents": 500
    }
  ],
  "fallback_message": null,
  "next_actions": {
    "request_wallet_pass": false,
    "require_vehicle_onboarding": false
  }
}
```

| Response Field | Type | Description | PostHog? | HubSpot? |
|---|---|---|---|---|
| `session_id` | string | Unique session ID (null for anonymous users) | Yes — attach to all subsequent events | No |
| `confidence_tier` | string | `"A"` (within 120m of charger), `"B"` (within 400m), `"C"` (no charger found) | Yes | Yes — `last_confidence_tier` |
| `charger_summary.id` | string | Charger identifier | Yes | No |
| `charger_summary.name` | string | Human-readable charger name | Yes | Yes — `last_charger_name` |
| `charger_summary.distance_m` | int | Meters from user to charger | Yes | No |
| `charger_summary.network_name` | string | Charger network (Tesla, ChargePoint, etc.) | Yes | Yes — `charger_network` |
| `merchants` | array | Nearby merchants. Count = number found | Yes — `merchant_count` | Yes — `merchants_shown_count` |
| `merchants[].name` | string | Merchant business name | Yes | No |
| `merchants[].distance_m` | int | Walking distance from charger to merchant | Yes | No |
| `merchants[].badges` | array | Special badges like `"exclusive"`, `"popular"` | Yes | No |
| `fallback_message` | string | Shown when Tier C (no chargers nearby) | Yes — indicates user is outside service area | Yes — `in_service_area: false` |

**PostHog event:**

```
Event: "driver.intent.capture.success"
Properties: {
  session_id, confidence_tier, merchant_count,
  charger_id, charger_name, charger_network,
  lat, lng, accuracy_m, is_anonymous
}
```

---

## Phase 3: Location Polling — Detecting Charger Arrival

### Endpoint: `GET /v1/drivers/location/check`

**What the user sees:** Nothing visible — this runs in the background every 10 seconds. When it detects the user is within the charger radius, a toast notification appears: "You're in charging range!" and the app switches from charger browsing to merchant browsing.

**Auth required:** Optional.

#### Request

```
GET /v1/drivers/location/check?lat=30.4037&lng=-97.6730
```

| Parameter | Type | Description |
|---|---|---|
| `lat` | float | Current latitude |
| `lng` | float | Current longitude |

#### Response

```json
{
  "in_charger_radius": true,
  "nearest_charger_id": "canyon_ridge_tesla",
  "distance_m": 35
}
```

| Response Field | Type | Description | PostHog? | HubSpot? |
|---|---|---|---|---|
| `in_charger_radius` | boolean | Whether user is within the charger's geofence | Yes — state transition trigger | Yes — `currently_at_charger` |
| `nearest_charger_id` | string | Which charger they're near | Yes | No |
| `distance_m` | float | Distance to nearest charger in meters | Yes | No |

**PostHog event:** Track the state transition:

```
Event: "driver.state.transition"
Properties: {
  from: "PRE_CHARGING",
  to: "CHARGING_ACTIVE",
  charger_id, distance_m
}
```

---

## Phase 4: Merchant Detail View

### Endpoint: `GET /v1/merchants/{merchant_id}`

**What the user sees:** User taps a merchant card and sees the full detail screen — hero image, hours, distance, exclusive offer, amenity votes, and action buttons.

**Auth required:** Optional.

#### Request

```
GET /v1/merchants/asadas_grill_canyon_ridge?session_id=a1b2c3d4-uuid
```

#### Response

```json
{
  "merchant": {
    "id": "asadas_grill_canyon_ridge",
    "name": "Asadas Grill",
    "category": "Mexican Restaurant",
    "photo_url": "https://...",
    "photo_urls": ["https://...", "https://..."],
    "description": "Authentic Mexican grill...",
    "hours_today": "11:00 AM - 10:00 PM",
    "address": "501 W Canyon Ridge Dr, Austin, TX",
    "rating": 4.5,
    "price_level": 2,
    "activations_today": 3,
    "verified_visits_today": 2,
    "place_id": "ChIJ_google_place_id",
    "amenities": {
      "bathroom": { "upvotes": 12, "downvotes": 1 },
      "wifi": { "upvotes": 8, "downvotes": 3 }
    }
  },
  "moment": {
    "label": "5 min walk",
    "distance_miles": 0.2,
    "moment_copy": "Perfect for a quick bite while charging"
  },
  "perk": {
    "title": "Free Beverage with Meal",
    "badge": "exclusive",
    "description": "Show your Nerava code to receive a complimentary drink"
  },
  "wallet": {
    "can_add": true,
    "state": "available",
    "active_copy": null
  },
  "actions": {
    "add_to_wallet": true,
    "get_directions_url": "https://www.google.com/maps/dir/..."
  }
}
```

| Response Field | Type | PostHog? | HubSpot? |
|---|---|---|---|
| `merchant.id` | string | Yes — on all merchant events | No |
| `merchant.name` | string | Yes | Yes — `last_merchant_viewed` |
| `merchant.category` | string | Yes | Yes — `preferred_category` (aggregate) |
| `merchant.rating` | float | Yes | No |
| `merchant.activations_today` | int | Yes — social proof metric | No |
| `merchant.verified_visits_today` | int | Yes | No |
| `perk.title` | string | Yes | Yes — `last_perk_viewed` |
| `moment.distance_miles` | float | Yes | No |

**PostHog event:**

```
Event: "driver_merchant_detail_viewed"
Properties: {
  merchant_id, merchant_name, category,
  has_exclusive: true/false,
  perk_title, distance_miles,
  rating, activations_today
}
```

---

## Phase 5: OTP Authentication

### Endpoint: `POST /v1/auth/otp/start`

**What the user sees:** After tapping "Activate Exclusive," if they're not logged in, a phone number input modal appears. User enters their phone number and taps "Send Code."

**Auth required:** No.

#### Request

```json
{
  "phone": "+15125551234"
}
```

| Field | Type | Description |
|---|---|---|
| `phone` | string | Phone number in E.164 format (`+1XXXXXXXXXX`) |

#### Response

```json
{
  "otp_sent": true
}
```

**Errors:**
- `429` — Rate limited (max 5 OTPs per 12 hours per phone)
- `400` — Invalid phone number format

**PostHog event:**

```
Event: "driver.otp.start"
Properties: {
  phone_hash: "sha256_first_16_chars",  // NEVER the raw phone number
  success: true/false
}
```

**HubSpot:** Do NOT sync raw phone here. Wait for verified OTP.

---

### Endpoint: `POST /v1/auth/otp/verify`

**What the user sees:** A 6-digit code input screen. User enters the code from their SMS. Auto-submits when all 6 digits are entered.

**Auth required:** No (this IS the auth step).

#### Request

```json
{
  "phone": "+15125551234",
  "code": "482910"
}
```

#### Response (Success)

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer",
  "user": {
    "public_id": "usr_abc123def456",
    "auth_provider": "phone_otp",
    "email": null,
    "phone": "+15125551234",
    "display_name": null,
    "created_at": "2026-01-30T14:35:00Z"
  }
}
```

| Response Field | Type | PostHog? | HubSpot? |
|---|---|---|---|
| `user.public_id` | string | Yes — use as `distinct_id` from this point on | Yes — `nerava_user_id` |
| `user.auth_provider` | string | Yes | Yes — `auth_method` |
| `user.phone` | string | No (PII — hash only) | Yes — `phone` (HubSpot contact identifier) |
| `user.created_at` | string | Yes — detect new vs returning | Yes — `first_seen_at` |

**Errors:**
- `401` — Wrong code
- `429` — Too many failed attempts (lockout)

**PostHog events:**

```
Event: "driver.otp.verify.success"
Properties: { user_id, auth_provider, is_new_user }

Event: "driver.otp.verify.fail"
Properties: { phone_hash, error_type: "wrong_code" | "rate_limited" }
```

**HubSpot:** This is the moment to create/update a HubSpot contact:

```
Contact: {
  phone: "+15125551234",
  nerava_user_id: "usr_abc123def456",
  auth_method: "phone_otp",
  first_seen_at: "2026-01-30T14:35:00Z",
  lifecycle_stage: "lead"
}
```

---

## Phase 6: Exclusive Activation

### Endpoint: `POST /v1/exclusive/activate`

**What the user sees:** After authenticating, the app automatically activates the exclusive. A confirmation screen appears showing the merchant name, the deal, and a 60-minute countdown timer.

**Auth required:** Yes (Bearer token).

#### Request

```json
{
  "merchant_id": "asadas_grill_canyon_ridge",
  "merchant_place_id": "ChIJ_google_place_id",
  "charger_id": "canyon_ridge_tesla",
  "intent_session_id": "a1b2c3d4-uuid",
  "lat": 30.4037,
  "lng": -97.6730,
  "accuracy_m": 10.0,
  "intent": "eat",
  "party_size": 2,
  "needs_power_outlet": false,
  "is_to_go": false
}
```

| Field | Type | Description |
|---|---|---|
| `merchant_id` | string | Internal merchant ID |
| `merchant_place_id` | string | Google Places ID |
| `charger_id` | string | Which charger they're at |
| `intent_session_id` | string | From the intent capture response |
| `lat`, `lng` | float | Current location (verified server-side) |
| `accuracy_m` | float | GPS accuracy |
| `intent` | string | What they plan to do: `"eat"`, `"work"`, or `"quick-stop"` |
| `party_size` | int | How many people (for restaurants) |
| `needs_power_outlet` | boolean | For "work" intent |
| `is_to_go` | boolean | For "eat" intent — takeout vs dine-in |

#### Response

```json
{
  "status": "activated",
  "exclusive_session": {
    "id": "es_xyz789",
    "merchant_id": "asadas_grill_canyon_ridge",
    "charger_id": "canyon_ridge_tesla",
    "expires_at": "2026-01-30T15:35:00Z",
    "activated_at": "2026-01-30T14:35:00Z",
    "remaining_seconds": 3600
  }
}
```

| Response Field | Type | PostHog? | HubSpot? |
|---|---|---|---|
| `exclusive_session.id` | string | Yes — attach to all session events | No |
| `exclusive_session.merchant_id` | string | Yes | Yes — `last_activated_merchant` |
| `exclusive_session.charger_id` | string | Yes | Yes — `last_charger_used` |
| `exclusive_session.expires_at` | string | Yes | No |
| `exclusive_session.remaining_seconds` | int | Yes | No |

**Request fields for PostHog/HubSpot:**

| Field | PostHog? | HubSpot? |
|---|---|---|
| `intent` | Yes — critical for segmentation | Yes — `last_intent_type` |
| `party_size` | Yes | Yes — `avg_party_size` (aggregate) |
| `is_to_go` | Yes | Yes — `prefers_takeout` (aggregate) |
| `needs_power_outlet` | Yes | Yes — `needs_power_outlet` |

**PostHog event:**

```
Event: "driver.exclusive.activate.success"
Properties: {
  session_id, merchant_id, merchant_name, charger_id,
  intent, party_size, is_to_go, needs_power_outlet,
  confidence_tier, distance_to_charger_m
}
```

**HubSpot update:**

```
Contact Update: {
  last_activation_date: "2026-01-30",
  total_activations: increment,
  last_activated_merchant: "Asadas Grill",
  last_charger_used: "Tesla Supercharger - Canyon Ridge",
  last_intent_type: "eat",
  lifecycle_stage: "customer"  // Upgrade from "lead"
}
```

---

## Phase 7: Active Session Polling

### Endpoint: `GET /v1/exclusive/active`

**What the user sees:** The countdown timer screen. This endpoint is polled every 30 seconds to keep the session in sync with the backend (handles edge cases like server-side expiration).

**Auth required:** Yes.

#### Response

```json
{
  "exclusive_session": {
    "id": "es_xyz789",
    "merchant_id": "asadas_grill_canyon_ridge",
    "charger_id": "canyon_ridge_tesla",
    "expires_at": "2026-01-30T15:35:00Z",
    "activated_at": "2026-01-30T14:35:00Z",
    "remaining_seconds": 2400
  }
}
```

If no active session: `{ "exclusive_session": null }`

**PostHog:** No event needed per poll. Track only state changes (expiration, completion).

---

## Phase 8: Arrival Verification

### Endpoint: `POST /v1/exclusive/verify`

**What the user sees:** User taps "I'm at the Merchant" button. The app sends their location for server-side verification. On success, a unique verification code is generated and displayed (e.g., `ATX-ASADAS-023`). The user shows this code to the merchant host.

**Auth required:** Yes.

#### Request

```json
{
  "exclusive_session_id": "es_xyz789",
  "lat": 30.4028,
  "lng": -97.6719
}
```

#### Response

```json
{
  "status": "VERIFIED",
  "verification_code": "ATX-ASADAS-023",
  "visit_number": 23,
  "merchant_name": "Asadas Grill",
  "verified_at": "2026-01-30T14:50:00Z"
}
```

| Response Field | Type | PostHog? | HubSpot? |
|---|---|---|---|
| `verification_code` | string | Yes | No |
| `visit_number` | int | Yes — shows merchant's total verified visits | Yes — `total_verified_visits` (increment) |
| `merchant_name` | string | Yes | Yes — `last_visited_merchant` |
| `verified_at` | string | Yes | Yes — `last_visit_date` |

**PostHog event:**

```
Event: "driver.arrival.verified"
Properties: {
  session_id, merchant_id, merchant_name,
  verification_code, visit_number,
  lat, lng, time_since_activation_seconds
}
```

**HubSpot update:**

```
Contact Update: {
  total_verified_visits: increment,
  last_visited_merchant: "Asadas Grill",
  last_visit_date: "2026-01-30"
}
```

---

## Phase 9: Session Completion

### Endpoint: `POST /v1/exclusive/complete`

**What the user sees:** After verifying arrival, the user sees a completion screen with optional feedback (thumbs up/down). Tapping "Done" completes the session.

**Auth required:** Yes.

#### Request

```json
{
  "exclusive_session_id": "es_xyz789",
  "feedback": {
    "thumbs_up": true,
    "tags": ["great_food", "fast_service"]
  }
}
```

#### Response

```json
{
  "status": "completed"
}
```

| Request Field | Type | PostHog? | HubSpot? |
|---|---|---|---|
| `feedback.thumbs_up` | boolean | Yes | Yes — `last_feedback_positive` |
| `feedback.tags` | array | Yes — understand satisfaction drivers | Yes — aggregate into `feedback_themes` |

**PostHog event:**

```
Event: "driver.exclusive.complete.success"
Properties: {
  session_id, merchant_id, merchant_name,
  feedback_positive: true/false,
  feedback_tags: ["great_food"],
  total_session_duration_seconds,
  time_to_arrival_seconds
}
```

**HubSpot update:**

```
Contact Update: {
  total_completed_sessions: increment,
  last_feedback_positive: true,
  nps_proxy_score: derived from feedback ratio
}
```

---

## Phase 10: Token Refresh

### Endpoint: `POST /auth/refresh`

**What the user sees:** Nothing — this happens automatically when a request returns 401. The app silently refreshes the token and retries.

**Auth required:** No (uses refresh token).

#### Request

```json
{
  "refresh_token": "eyJhbGciOi..."
}
```

#### Response

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

**PostHog:** No event needed. If refresh fails, track:

```
Event: "driver.auth.session_expired"
Properties: { user_id }
```

---

## Amenity Voting (Optional Side Action)

### Endpoint: `POST /v1/merchants/{id}/amenities/{amenity}/vote`

**What the user sees:** On the merchant detail screen, there are WiFi and Bathroom indicators with up/down vote buttons. Tapping a vote updates the count.

**Auth required:** Optional.

#### Request

```
POST /v1/merchants/asadas_grill_canyon_ridge/amenities/wifi/vote
```

```json
{
  "vote_type": "up"
}
```

#### Response

```json
{
  "ok": true,
  "upvotes": 9,
  "downvotes": 3
}
```

**PostHog event:**

```
Event: "driver.amenity.voted"
Properties: {
  merchant_id, amenity: "wifi", vote_type: "up"
}
```

---

## Summary: All Endpoints in User Journey Order

| # | Endpoint | Method | Auth | User Action |
|---|---|---|---|---|
| 1 | `/v1/intent/capture` | POST | Optional | App opens, gets GPS fix |
| 2 | `/v1/drivers/location/check` | GET | Optional | Background polling (every 10s) |
| 3 | `/v1/merchants/{id}` | GET | Optional | User taps merchant card |
| 4 | `/v1/merchants/{id}/amenities/{amenity}/vote` | POST | Optional | User votes on WiFi/bathroom |
| 5 | `/v1/auth/otp/start` | POST | No | User enters phone number |
| 6 | `/v1/auth/otp/verify` | POST | No | User enters 6-digit code |
| 7 | `/v1/exclusive/activate` | POST | Yes | System activates exclusive after OTP |
| 8 | `/v1/exclusive/active` | GET | Yes | Background polling (every 30s) |
| 9 | `/v1/exclusive/verify` | POST | Yes | User taps "I'm at the Merchant" |
| 10 | `/v1/exclusive/complete` | POST | Yes | User taps "Done" on completion screen |
| 11 | `/auth/refresh` | POST | No | Automatic when token expires |

---

## Recommended HubSpot Contact Properties

These properties should be created in HubSpot and synced from PostHog or the backend:

| Property Name | Type | When Updated | Source |
|---|---|---|---|
| `nerava_user_id` | String | OTP verify | `user.public_id` |
| `phone` | String | OTP verify | `user.phone` |
| `auth_method` | String | OTP verify | `"phone_otp"` |
| `first_seen_at` | DateTime | OTP verify | `user.created_at` |
| `lifecycle_stage` | Enum | OTP verify → `lead`, Activate → `customer` | Derived |
| `location_permission` | String | Onboarding | `"granted"` or `"denied"` |
| `last_confidence_tier` | String | Intent capture | `"A"`, `"B"`, `"C"` |
| `last_charger_name` | String | Intent capture | `charger_summary.name` |
| `charger_network` | String | Intent capture | `charger_summary.network_name` |
| `in_service_area` | Boolean | Intent capture | `true` if tier A/B, `false` if C |
| `last_intent_type` | String | Exclusive activate | `"eat"`, `"work"`, `"quick-stop"` |
| `last_activated_merchant` | String | Exclusive activate | `merchant.name` |
| `last_charger_used` | String | Exclusive activate | `charger_summary.name` |
| `total_activations` | Number | Exclusive activate | Increment |
| `last_visited_merchant` | String | Arrival verify | `merchant_name` |
| `last_visit_date` | Date | Arrival verify | `verified_at` |
| `total_verified_visits` | Number | Arrival verify | Increment |
| `total_completed_sessions` | Number | Session complete | Increment |
| `last_feedback_positive` | Boolean | Session complete | `feedback.thumbs_up` |
| `avg_party_size` | Number | Exclusive activate | Rolling average |
| `prefers_takeout` | Boolean | Exclusive activate | Most common `is_to_go` value |

---

## PostHog Event Naming Convention

All events follow this pattern:

- **Frontend events:** `driver.{feature}.{action}` or `driver_{feature}_{action}`
- **Backend events:** `server.driver.{feature}.{action}`

Examples:
- `driver.otp.verify.success` (frontend)
- `server.driver.intent.capture.success` (backend)
- `driver_merchant_clicked` (frontend, legacy format)

---

*Last updated: 2026-01-30*
