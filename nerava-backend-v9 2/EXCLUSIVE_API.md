# Exclusive Session API

API endpoints for managing driver exclusive activation sessions (web-only flow).

## Base URL

All endpoints are under `/v1/exclusive/`

## Authentication

All endpoints require driver authentication via Bearer token:
```
Authorization: Bearer <access_token>
```

## Endpoints

### POST /v1/exclusive/activate

Activate an exclusive session for a driver.

**Request Body:**
```json
{
  "merchant_id": "m_123",              // Optional: Merchant ID
  "merchant_place_id": "ChIJ...",      // Optional: Google Places ID (either merchant_id or merchant_place_id required)
  "charger_id": "ch_456",              // Required: Charger ID
  "charger_place_id": "ChIJ...",       // Optional: Charger place ID
  "intent_session_id": "uuid-here",   // Optional: Link to intent capture session
  "lat": 30.2672,                      // Required: Activation latitude
  "lng": -97.7431,                     // Required: Activation longitude
  "accuracy_m": 10.0                   // Optional: Location accuracy in meters
}
```

**Response (200 OK):**
```json
{
  "status": "ACTIVE",
  "exclusive_session": {
    "id": "uuid-here",
    "merchant_id": "m_123",
    "charger_id": "ch_456",
    "expires_at": "2025-01-27T13:00:00Z",
    "activated_at": "2025-01-27T12:00:00Z",
    "remaining_seconds": 3600
  }
}
```

**Error Responses:**

- `400 Bad Request`: Missing required fields (merchant_id or merchant_place_id)
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Driver is outside charger radius
  ```json
  {
    "detail": "You must be at the charger to activate. Distance: 250m, required: 150m"
  }
  ```
- `404 Not Found`: Charger not found
- `409 Conflict`: Active session already exists (returns existing session)

**Behavior:**
- Validates driver is within 150m of charger
- Creates ACTIVE session with 60-minute expiration
- If driver already has ACTIVE session, returns existing session
- If existing session is expired, marks it EXPIRED and creates new one

---

### POST /v1/exclusive/complete

Complete an exclusive session.

**Request Body:**
```json
{
  "exclusive_session_id": "uuid-here",  // Required: Session ID
  "feedback": {                          // Optional: Feedback data
    "thumbs_up": true,
    "tags": ["great_service", "fast"]
  }
}
```

**Response (200 OK):**
```json
{
  "status": "COMPLETED"
}
```

**Error Responses:**

- `401 Unauthorized`: Authentication required
- `404 Not Found`: Session not found or doesn't belong to driver
- `409 Conflict`: Session is not ACTIVE
  ```json
  {
    "detail": "Session is not active. Current status: COMPLETED"
  }
  ```

**Behavior:**
- Marks session as COMPLETED
- Sets `completed_at` timestamp
- Logs completion event with duration

---

### GET /v1/exclusive/active

Get the currently active exclusive session for the driver.

**Query Parameters:**
- `include_expired` (boolean, default: false): Include expired sessions in response

**Response (200 OK):**
```json
{
  "exclusive_session": {
    "id": "uuid-here",
    "merchant_id": "m_123",
    "charger_id": "ch_456",
    "expires_at": "2025-01-27T13:00:00Z",
    "activated_at": "2025-01-27T12:00:00Z",
    "remaining_seconds": 1800
  }
}
```

**Response (No Active Session):**
```json
{
  "exclusive_session": null
}
```

**Error Responses:**

- `401 Unauthorized`: Authentication required

**Behavior:**
- Returns active session if exists and not expired
- If session is expired, marks it as EXPIRED and returns null (unless `include_expired=true`)
- Supports refresh resilience: frontend can poll this endpoint to check session status

---

## Constants

### Charger Radius
- **CHARGER_RADIUS_M**: `150` meters
- Configurable via `CHARGER_RADIUS_M` environment variable

### Session Duration
- **EXCLUSIVE_DURATION_MIN**: `60` minutes
- Configurable via `EXCLUSIVE_DURATION_MIN` environment variable

---

## Example cURL Commands

### Activate Exclusive Session
```bash
curl -X POST "http://localhost:8001/v1/exclusive/activate" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "m_123",
    "charger_id": "ch_456",
    "lat": 30.2672,
    "lng": -97.7431,
    "accuracy_m": 10.0
  }'
```

### Complete Exclusive Session
```bash
curl -X POST "http://localhost:8001/v1/exclusive/complete" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exclusive_session_id": "uuid-here"
  }'
```

### Get Active Session
```bash
curl -X GET "http://localhost:8001/v1/exclusive/active" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Error Codes Summary

| Status Code | Meaning | Common Causes |
|------------|---------|---------------|
| 400 | Bad Request | Missing required fields |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Outside charger radius |
| 404 | Not Found | Charger/session not found |
| 409 | Conflict | Session already active/completed |

---

## Notes

- Sessions automatically expire after 60 minutes
- Only one ACTIVE session per driver at a time
- Activation requires driver to be within 150m of charger
- All timestamps are in ISO 8601 format (UTC)
- `remaining_seconds` is calculated from current time to `expires_at`

