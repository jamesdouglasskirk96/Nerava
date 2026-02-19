# Codex: Test EV Arrival System

**Date:** 2026-02-01
**Purpose:** Write comprehensive tests for the EV Arrival system.

---

## Context

The EV Arrival system has been implemented. Write tests that verify correctness of all endpoints, models, and business logic. The spec is at `docs/EV_ARRIVAL_SYSTEM_DESIGN.md`.

## Test Files to Create/Update

### 1. Backend Unit Tests: `backend/tests/test_arrival_unit.py`

Test the following WITHOUT requiring a database:

```python
# Import targets
from app.models.arrival_session import (
    ArrivalSession, ACTIVE_STATUSES, TERMINAL_STATUSES, VALID_TRANSITIONS, _generate_reply_code
)
from app.services.pos_adapter import ManualPOSAdapter, get_pos_adapter, POSOrder

# Test cases:
# 1. _generate_reply_code() returns 4-digit string
# 2. _generate_reply_code() produces sufficiently unique codes (100 runs, >90 unique)
# 3. ACTIVE_STATUSES and TERMINAL_STATUSES are disjoint
# 4. All active statuses have valid transitions defined
# 5. ManualPOSAdapter.lookup_order() returns POSOrder with status='unknown'
# 6. ManualPOSAdapter.get_order_total() returns None
# 7. get_pos_adapter('none', None) returns ManualPOSAdapter
# 8. get_pos_adapter('toast', None) returns ManualPOSAdapter (no credentials)
# 9. VALID_TRANSITIONS includes 'canceled' from every active status
# 10. VALID_TRANSITIONS includes 'expired' from every active status
```

### 2. Backend Integration Tests: `backend/tests/test_arrival_integration.py`

Use the existing `client` and `db` fixtures from `conftest.py`.

```python
# Pre-requisites: Create test charger + merchant in db fixtures

# Test cases:
# 1. POST /v1/arrival/create with valid data → 201, returns session_id
# 2. POST /v1/arrival/create with same idempotency_key → returns same session (idempotent)
# 3. POST /v1/arrival/create while active session exists → 409 ACTIVE_SESSION_EXISTS
# 4. POST /v1/arrival/create with invalid arrival_type → 422
# 5. PUT /v1/arrival/{id}/order → binds order, transitions to awaiting_arrival
# 6. PUT /v1/arrival/{id}/order with estimated_total_cents → stored in driver_estimate_cents
# 7. POST /v1/arrival/{id}/confirm-arrival WITHOUT charger_id → 422 (anti-spoofing)
# 8. POST /v1/arrival/{id}/confirm-arrival with charger_id but >250m away → 400 TOO_FAR_FROM_CHARGER
# 9. POST /v1/arrival/{id}/confirm-arrival with valid charger_id + location → 200, status=arrived or merchant_notified
# 10. POST /v1/arrival/{id}/merchant-confirm → creates billing_event if total available
# 11. POST /v1/arrival/{id}/merchant-confirm with no total → status=completed_unbillable, no billing_event
# 12. POST /v1/arrival/{id}/merchant-confirm with merchant_reported_total_cents → uses that as billing total
# 13. POST /v1/arrival/{id}/feedback with rating=up → stored
# 14. POST /v1/arrival/{id}/feedback with rating=down + reason → stored
# 15. POST /v1/arrival/{id}/feedback with invalid rating → 422
# 16. GET /v1/arrival/active → returns current active session or null
# 17. GET /v1/arrival/active for expired session → returns null, session marked expired
# 18. POST /v1/arrival/{id}/cancel → status=canceled
# 19. POST /v1/arrival/{id}/cancel on already canceled session → 400
```

### 3. Charge Context Tests: `backend/tests/test_charge_context.py`

```python
# Test cases:
# 1. GET /v1/charge-context/nearby with lat/lng → 200, returns merchants list
# 2. Response includes charger info when charger is nearby
# 3. Response includes merchant_id, name, walk_minutes, distance_m
# 4. Category filter works (pass category=coffee)
# 5. Merchants sorted by distance
# 6. Response includes active_arrival_count for social proof
# 7. Response includes verified_visit_count
```

### 4. SMS Webhook Tests: `backend/tests/test_twilio_sms_webhook.py`

```python
# Test cases:
# 1. POST /v1/webhooks/twilio-arrival-sms with "DONE 1234" → finds session by reply code, confirms
# 2. POST with "DONE" (no code) → returns error message asking for code
# 3. POST with "DONE 9999" (invalid code) → returns "no active arrival found"
# 4. POST with "HELP" → returns dashboard URL
# 5. POST with random text → returns usage instructions
# 6. Confirmed session creates billing_event if total available
# 7. Confirmed session with no total → completed_unbillable
# 8. Response is valid TwiML XML
```

### 5. Merchant Arrivals Tests: `backend/tests/test_merchant_arrivals.py`

```python
# Test cases:
# 1. GET /v1/merchants/{id}/arrivals → 200, returns sessions list
# 2. GET /v1/merchants/{id}/notification-config → returns defaults if not set
# 3. PUT /v1/merchants/{id}/notification-config → creates config
# 4. PUT same endpoint again → updates existing config (upsert)
# 5. Config changes persist across requests
```

### 6. Vehicle Endpoint Tests: `backend/tests/test_vehicle.py`

```python
# Test cases:
# 1. PUT /v1/account/vehicle → sets vehicle_color, vehicle_model, vehicle_set_at on user
# 2. GET /v1/account/vehicle → returns saved vehicle
# 3. GET /v1/account/vehicle with no vehicle saved → 404
# 4. PUT again → updates vehicle (overwrite)
```

### 7. POS Adapter Tests: `backend/tests/test_pos_adapter.py`

```python
# Test cases:
# 1. ManualPOSAdapter.lookup_order returns POSOrder with correct order_number
# 2. ManualPOSAdapter.get_order_status returns 'unknown'
# 3. ManualPOSAdapter.get_order_total returns None
# 4. ToastPOSAdapter.lookup_order returns None (stub)
# 5. SquarePOSAdapter.lookup_order returns None (stub)
# 6. get_pos_adapter factory returns correct adapter types
```

## Running Tests

```bash
cd backend
# Run all arrival tests
pytest tests/test_arrival_unit.py tests/test_arrival_integration.py tests/test_charge_context.py tests/test_twilio_sms_webhook.py tests/test_merchant_arrivals.py tests/test_vehicle.py tests/test_pos_adapter.py -v

# Run with coverage
pytest tests/test_arrival_*.py tests/test_charge_context.py tests/test_twilio_sms_webhook.py -v --cov=app.routers.arrival --cov=app.services.pos_adapter --cov=app.services.notification_service
```

## Key Patterns from Existing Tests

Look at these existing test files for patterns:
- `backend/tests/test_exclusive_sessions.py` — session lifecycle tests
- `backend/tests/test_merchant_funnel.py` — signature/auth tests
- `backend/tests/conftest.py` — fixtures (client, db)

## Important Validation Rules

1. **confirm-arrival MUST require charger_id** — if the test passes without charger_id, the endpoint is broken
2. **Billing events MUST NOT be created when total is 0 or None** — verify completed_unbillable path
3. **SMS reply code must be present** — every ArrivalSession should have a non-null merchant_reply_code
4. **One active session per driver** — second create while one is active must return 409
5. **Expired sessions auto-detected** — GET /active should return null for expired sessions
