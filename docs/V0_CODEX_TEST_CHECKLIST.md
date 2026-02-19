# V0 Web-First EV Arrival — Codex Test Checklist

Each section is a self-contained Codex prompt. Execute after the corresponding Cursor implementation task.

---

## Test Suite 1: Session Expiry Background Task

```
You are Codex. Write tests for the session expiry background task.

File: backend/tests/test_session_expiry.py

Use the existing test fixtures from backend/tests/conftest.py (client, db session).
Import ArrivalSession from backend/app/models/arrival_session.py.

Test cases:

1. test_expired_session_transitions_to_expired
   - Create an ArrivalSession with status='pending_order' and expires_at = 1 hour ago
   - Run the expiry logic (call the function directly, don't rely on the background loop)
   - Assert status is now 'expired' and completed_at is set

2. test_active_session_not_expired
   - Create an ArrivalSession with status='awaiting_arrival' and expires_at = 1 hour from now
   - Run expiry logic
   - Assert status is still 'awaiting_arrival'

3. test_completed_session_not_affected
   - Create an ArrivalSession with status='completed'
   - Run expiry logic
   - Assert status is still 'completed'

4. test_multiple_expired_sessions
   - Create 3 sessions all with expires_at in the past (different statuses: pending_order, awaiting_arrival, arrived)
   - Run expiry logic
   - Assert all 3 are now 'expired'

5. test_expiry_sets_completed_at
   - Create expired session
   - Run expiry
   - Assert completed_at is approximately now (within 5 seconds)
```

---

## Test Suite 2: Web Confirm Arrival

```
You are Codex. Write tests for the web-only arrival confirmation.

File: backend/tests/test_web_confirm_arrival.py

Use fixtures from backend/tests/conftest.py.
Import ArrivalSession from backend/app/models/arrival_session.py.

Test cases:

1. test_web_confirm_with_geolocation_near_charger
   - Create session in 'awaiting_arrival' status
   - POST /v1/arrival/{id}/confirm-arrival with { lat, lng, accuracy_m: 25, web_confirm: true }
   - lat/lng should be within 250m of a known charger
   - Assert 200, status transitions to 'merchant_notified' or 'arrived'

2. test_web_confirm_with_geolocation_too_far
   - Create session in 'awaiting_arrival'
   - POST with lat/lng that is 1km from any charger, web_confirm: true
   - Assert 400 or 403 with error about being too far

3. test_web_confirm_without_geolocation
   - Create session in 'awaiting_arrival'
   - POST with { web_confirm: true } (no lat/lng)
   - Assert 200 — confirmation succeeds but arrival_accuracy_m is null

4. test_native_confirm_still_requires_charger_id
   - Create session in 'awaiting_arrival'
   - POST with { lat, lng, accuracy_m: 25 } (no web_confirm, no charger_id)
   - Assert 400/422 — charger_id is required for native

5. test_web_confirm_wrong_session_status
   - Create session in 'pending_order' (not yet awaiting_arrival)
   - POST web_confirm
   - Assert 400/409 — wrong status for confirmation

6. test_web_confirm_posthog_event
   - Confirm via web
   - Verify PostHog capture was called with confirmation_method='web_manual'
   (mock the analytics client)
```

---

## Test Suite 3: Billing CSV Export

```
You are Codex. Write tests for the billing CSV export endpoint.

File: backend/tests/test_billing_export.py

Use fixtures from conftest.py. You'll need an admin user fixture.
Import BillingEvent from backend/app/models/billing_event.py.

Test cases:

1. test_billing_export_returns_csv
   - Create 2 BillingEvent rows for February 2026
   - GET /v1/admin/billing-export?month=2026-02 with admin auth
   - Assert 200, Content-Type is text/csv
   - Parse CSV, assert 2 data rows + 1 header row
   - Assert header columns match expected: session_id, merchant_id, merchant_name, etc.

2. test_billing_export_filters_by_month
   - Create 1 event in January, 1 in February
   - GET ?month=2026-02
   - Assert only 1 row in CSV (February)

3. test_billing_export_empty_month
   - GET ?month=2026-03 (no data)
   - Assert 200 with only header row

4. test_billing_export_requires_admin
   - GET with non-admin auth token
   - Assert 403

5. test_billing_export_invalid_month_format
   - GET ?month=invalid
   - Assert 400

6. test_billing_export_correct_totals
   - Create event with order_total_cents=2847, fee_bps=500
   - Assert billable_cents=142 in CSV (2847 * 500 / 10000 = 142.35, rounded down)
```

---

## Test Suite 4: Daily Rate Limit

```
You are Codex. Write tests for the daily session rate limit.

File: backend/tests/test_arrival_rate_limit.py

Test cases:

1. test_first_three_sessions_succeed
   - Create and complete 2 sessions for driver
   - Create a 3rd session
   - Assert 201 — still under limit

2. test_fourth_session_blocked
   - Create and complete 3 sessions for driver today
   - Attempt to create a 4th
   - Assert 429 with message about daily limit

3. test_canceled_sessions_dont_count
   - Create 3 sessions, cancel all 3 (status='canceled')
   - Create a 4th session
   - Assert 201 — canceled sessions don't count toward limit

4. test_yesterdays_sessions_dont_count
   - Create 3 completed sessions with created_at = yesterday
   - Create a new session today
   - Assert 201 — yesterday's sessions don't affect today

5. test_different_driver_not_affected
   - Driver A has 3 completed sessions
   - Driver B creates a session
   - Assert 201 — per-driver limit
```

---

## Test Suite 5: EVArrival Driver Flow (Integration)

```
You are Codex. Write integration tests for the full EV Arrival flow.

File: backend/tests/integration/test_ev_arrival_flow.py

These are end-to-end API tests that walk through the complete flow.

Test cases:

1. test_happy_path_curbside
   - POST /v1/arrival/create with arrival_type='ev_curbside'
   - Assert 201, status='pending_order'
   - PUT /v1/arrival/{id}/order with order_number='1234', estimated_total_cents=2500
   - Assert 200, status='awaiting_arrival'
   - POST /v1/arrival/{id}/confirm-arrival with valid location + web_confirm=true
   - Assert 200, status='merchant_notified'
   - POST /v1/arrival/{id}/merchant-confirm with confirmed=true
   - Assert 200, status='completed'
   - Query billing_events — assert 1 row with correct amounts

2. test_happy_path_dine_in
   - Same as above but arrival_type='ev_dine_in'
   - Verify all transitions work identically

3. test_cancel_after_creation
   - Create session → cancel
   - Assert status='canceled', no billing event

4. test_cancel_after_order_bound
   - Create session → bind order → cancel
   - Assert status='canceled', no billing event, no SMS sent

5. test_merchant_confirm_without_geofence
   - Create → bind order → merchant-confirm (skipping confirm-arrival)
   - Assert appropriate error — merchant can't confirm before arrival

6. test_completed_unbillable_no_estimate
   - Create session → confirm arrival → merchant-confirm with no total
   - If no POS, no merchant_reported, no driver_estimate → status='completed_unbillable'
   - Assert no billing_event created

7. test_feedback_after_completion
   - Complete a session → POST feedback with rating='up', comment='Great'
   - Assert 200, feedback stored on session

8. test_duplicate_session_blocked
   - Create a session (status='pending_order')
   - Try to create another for same driver
   - Assert 409 — one active session at a time

9. test_expired_session_allows_new_creation
   - Create session → manually set expires_at to past → run expiry
   - Create a new session
   - Assert 201 — expired session doesn't block

10. test_sms_reply_done_completes_session
    - Create session → bind order → confirm arrival
    - Simulate Twilio webhook: POST /v1/webhooks/twilio-arrival-sms with Body="DONE {reply_code}"
    - Assert session status='completed', billing_event created
```

---

## Test Suite 6: Merchant Notification Config

```
You are Codex. Write tests for merchant notification configuration.

File: backend/tests/test_notification_config.py

Test cases:

1. test_get_default_config
   - GET /v1/merchants/{id}/notification-config for merchant with no config
   - Assert 200 with default values (notify_sms=true, notify_email=false)

2. test_update_sms_phone
   - PUT with { sms_phone: "+15125551234", notify_sms: true }
   - Assert 200
   - GET — assert phone is saved

3. test_invalid_phone_format
   - PUT with { sms_phone: "not-a-phone" }
   - Assert 400/422

4. test_disable_sms
   - PUT with { notify_sms: false }
   - Create arrival session → confirm arrival
   - Assert NO SMS sent (mock Twilio)

5. test_email_notifications_not_sent
   - PUT with { notify_email: true, email_address: "test@example.com" }
   - Create arrival → confirm
   - Assert no email sent (email is a no-op in V0)
   - Assert warning logged
```

---

## Running All Tests

```bash
# From backend directory
cd backend

# Run all V0 test suites
pytest tests/test_session_expiry.py tests/test_web_confirm_arrival.py tests/test_billing_export.py tests/test_arrival_rate_limit.py tests/integration/test_ev_arrival_flow.py tests/test_notification_config.py -v

# Run with coverage
pytest tests/test_session_expiry.py tests/test_web_confirm_arrival.py tests/test_billing_export.py tests/test_arrival_rate_limit.py tests/integration/test_ev_arrival_flow.py tests/test_notification_config.py --cov=app/routers/arrival --cov=app/routers/admin_domain --cov=app/services/notification_service -v
```

### Expected Coverage Targets
- `arrival.py` — 90%+ line coverage
- `admin_domain.py` (billing export) — 95%+
- `notification_service.py` — 80%+
- `twilio_sms_webhook.py` — 85%+
