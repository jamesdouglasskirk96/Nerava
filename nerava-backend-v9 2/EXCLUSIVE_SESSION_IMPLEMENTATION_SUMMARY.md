# Exclusive Session Implementation Summary

## Overview

Implemented production-usable "Exclusive Session" backend for web-only driver flow. Supports driver activation of exclusive sessions when within charger radius, with proper validation, logging, and state management.

## Files Created

### Models
- **`app/models/exclusive_session.py`**: ExclusiveSession model with status enum
  - Fields: driver_id, merchant_id/place_id, charger_id/place_id, intent_session_id, status, timestamps, activation location data
  - Status enum: ACTIVE, COMPLETED, EXPIRED, CANCELED

### Migrations
- **`alembic/versions/048_add_exclusive_sessions.py`**: Alembic migration
  - Creates `exclusive_sessions` table
  - Adds indexes: driver_id, status, merchant_id, charger_id, expires_at, composite indexes
  - Handles SQLite and PostgreSQL compatibility

### Router
- **`app/routers/exclusive.py`**: API endpoints
  - `POST /v1/exclusive/activate`: Activate exclusive session
  - `POST /v1/exclusive/complete`: Complete exclusive session
  - `GET /v1/exclusive/active`: Get active session (with expiry handling)

### Utilities
- **`app/utils/exclusive_logging.py`**: Structured logging helper
  - `log_event()` function for consistent event logging

### Tests
- **`tests/api/test_exclusive_sessions.py`**: Comprehensive test suite
  - Tests for all endpoints
  - Auth requirements
  - Radius validation
  - State transitions
  - Expiry handling

### Documentation
- **`EXCLUSIVE_API.md`**: API documentation
  - Endpoint descriptions
  - Request/response examples
  - Error codes
  - cURL examples
  - Constants reference

## Files Modified

### Configuration
- **`app/core/config.py`**: Added constants
  - `CHARGER_RADIUS_M`: 150 meters (configurable via env var)
  - `EXCLUSIVE_DURATION_MIN`: 60 minutes (configurable via env var)

### Model Exports
- **`app/models/__init__.py`**: Added ExclusiveSession and ExclusiveSessionStatus exports

### Router Registration
- **`app/main.py`**: Added exclusive router to app
  - `app.include_router(exclusive.router)`

## Key Features

### 1. Radius Validation
- Uses existing `haversine_m()` function from `app/services/geo.py`
- Validates driver is within 150m of charger before activation
- Returns 403 with distance details if outside radius
- Stores computed distance in session record

### 2. State Management
- Only one ACTIVE session per driver at a time
- Automatic expiry detection and marking
- Status transitions: ACTIVE → COMPLETED/EXPIRED/CANCELED

### 3. Anti-Abuse
- Radius validation prevents remote activation
- Single active session enforcement
- Rate limiting handled by existing middleware

### 4. Logging
- Structured JSON logging for all events:
  - `exclusive_activated`
  - `exclusive_activation_blocked`
  - `exclusive_completed`
  - `exclusive_expired`

### 5. Refresh Resilience
- `GET /v1/exclusive/active` supports polling
- Automatically marks expired sessions
- Returns null when no active session

## API Endpoints

### POST /v1/exclusive/activate
**Purpose**: Activate exclusive session
**Auth**: Required (driver)
**Validation**: 
- Must be within 150m of charger
- Either merchant_id or merchant_place_id required
- charger_id required

**Response**: Session details with expires_at and remaining_seconds

### POST /v1/exclusive/complete
**Purpose**: Complete exclusive session
**Auth**: Required (driver)
**Validation**: Session must be ACTIVE and belong to driver

**Response**: Status confirmation

### GET /v1/exclusive/active
**Purpose**: Get active session (for refresh resilience)
**Auth**: Required (driver)
**Query Params**: `include_expired` (boolean, default: false)

**Response**: Active session or null

## Database Schema

```sql
CREATE TABLE exclusive_sessions (
    id UUID PRIMARY KEY,
    driver_id INTEGER NOT NULL REFERENCES users(id),
    merchant_id VARCHAR REFERENCES merchants(id),
    merchant_place_id VARCHAR,
    charger_id VARCHAR REFERENCES chargers(id),
    charger_place_id VARCHAR,
    intent_session_id UUID REFERENCES intent_sessions(id),
    status VARCHAR NOT NULL DEFAULT 'ACTIVE',
    activated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    activation_lat FLOAT,
    activation_lng FLOAT,
    activation_accuracy_m FLOAT,
    activation_distance_to_charger_m FLOAT
);
```

## Testing

Run tests with:
```bash
pytest tests/api/test_exclusive_sessions.py -v
```

Test coverage:
- ✅ Authentication requirements
- ✅ Radius validation (403 when outside)
- ✅ Successful activation creates session
- ✅ Expires_at is ~60 minutes from activation
- ✅ Existing active session returns 409 with session
- ✅ Completion marks session as COMPLETED
- ✅ Active endpoint returns active session
- ✅ Active endpoint marks expired sessions

## Migration

Run migration:
```bash
alembic upgrade head
```

Or programmatically:
```python
from app.run_migrations import run_migrations
run_migrations()
```

## Example Usage

### Activate Exclusive Session
```bash
curl -X POST "http://localhost:8001/v1/exclusive/activate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "m_123",
    "charger_id": "ch_456",
    "lat": 30.2672,
    "lng": -97.7431
  }'
```

### Complete Session
```bash
curl -X POST "http://localhost:8001/v1/exclusive/complete" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exclusive_session_id": "uuid-here"
  }'
```

### Get Active Session
```bash
curl -X GET "http://localhost:8001/v1/exclusive/active" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Configuration

Environment variables:
- `CHARGER_RADIUS_M`: Charger radius in meters (default: 150)
- `EXCLUSIVE_DURATION_MIN`: Session duration in minutes (default: 60)

## Next Steps

1. Run migration: `alembic upgrade head`
2. Run tests: `pytest tests/api/test_exclusive_sessions.py`
3. Test endpoints with curl (see examples above)
4. Integrate with frontend (update DriverHome to call `/v1/exclusive/activate` instead of `/v1/wallet/pass/activate`)

## Notes

- No Apple Wallet pass work in this implementation (web-only)
- Uses existing `get_current_driver` dependency for auth
- Leverages existing `haversine_m` utility for distance calculation
- Structured logging follows existing patterns
- All timestamps are timezone-aware (UTC)

