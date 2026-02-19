# Cursor: Validate EV Arrival Implementation

**Date:** 2026-02-01
**Purpose:** Validate that all EV Arrival implementation is correct, complete, and wired up.

---

## Context

Claude Code just implemented the full EV Arrival system. Your job is to validate that everything is correct, nothing is missing, and all the pieces connect properly.

## Files Created (verify these exist and are correct)

### Backend Models
1. `backend/app/models/arrival_session.py` — ArrivalSession with partial unique index enforcement, merchant_reply_code, driver_estimate_cents, merchant_reported_total_cents, total_source, feedback fields
2. `backend/app/models/merchant_notification_config.py` — Notification preferences (NO POS tokens here)
3. `backend/app/models/merchant_pos_credentials.py` — SEPARATE table for POS OAuth tokens (Fernet encrypted)
4. `backend/app/models/billing_event.py` — Billing records with total_source field

### Backend Routers
5. `backend/app/routers/arrival.py` — 7 endpoints: create, bind order, confirm-arrival (requires charger_id!), merchant-confirm, feedback, active, cancel
6. `backend/app/routers/charge_context.py` — GET /v1/charge-context/nearby (replaces /v1/intent/capture)
7. `backend/app/routers/twilio_sms_webhook.py` — POST /v1/webhooks/twilio-arrival-sms (parses DONE {code})
8. `backend/app/routers/merchant_arrivals.py` — GET arrivals list + GET/PUT notification-config

### Backend Services
9. `backend/app/services/pos_adapter.py` — POSAdapter ABC + ManualPOSAdapter + ToastPOSAdapter stub + SquarePOSAdapter stub + factory
10. `backend/app/services/notification_service.py` — SMS via Twilio with reply codes

### Migration
11. `backend/alembic/versions/062_add_ev_arrival_tables.py` — All tables + user vehicle fields + merchant ordering fields + partial unique index

### Frontend — Driver App
12. `apps/driver/src/components/EVArrival/ModeSelector.tsx` — Segmented control (EV Curbside / EV Dine-In)
13. `apps/driver/src/components/EVArrival/VehicleSetup.tsx` — One-time vehicle setup bottom sheet
14. `apps/driver/src/components/EVArrival/ConfirmationSheet.tsx` — Confirmation with "Verifying..." interstitial
15. `apps/driver/src/components/EVArrival/ActiveSession.tsx` — Order binding, status display, countdown timer
16. `apps/driver/src/components/EVArrival/CompletionScreen.tsx` — Thumbs up/down + reason chips + optional comment
17. `apps/driver/src/components/EVArrival/index.ts` — Barrel exports

### Frontend — Merchant Portal
18. `apps/merchant/app/components/EVArrivals.tsx` — Active/completed sessions list + notification settings

### Tests
19. `backend/tests/test_arrival_sessions.py` — Reply code generation, endpoint validation, charge-context, merchant arrivals

## Validation Checklist

### 1. Anti-Spoofing (CRITICAL)
- [ ] `confirm-arrival` endpoint in `arrival.py` requires `charger_id` in the request body
- [ ] Server looks up charger lat/lng from DB and calls `haversine_m()` to verify distance
- [ ] Rejects with 400 if driver is >250m from charger
- [ ] `ConfirmArrivalRequest` Pydantic model has `charger_id: str` as required field

### 2. DB Constraint
- [ ] Migration 062 creates a partial unique index on `driver_id` ONLY (not `driver_id, status`)
- [ ] The WHERE clause filters on active statuses only
- [ ] Application code in `_get_active_session()` also checks for active sessions before creation

### 3. SMS Reply Codes
- [ ] `ArrivalSession` model has `merchant_reply_code` field (4-digit string, auto-generated)
- [ ] `notification_service.py` includes `merchant_reply_code` in SMS body: "Reply DONE {code} when delivered"
- [ ] `twilio_sms_webhook.py` parses "DONE 1234" from SMS body and looks up session by reply code
- [ ] Webhook correctly handles DONE + code, HELP, and unknown messages

### 4. Billing
- [ ] `merchant-confirm` endpoint has `merchant_reported_total_cents` optional field
- [ ] Billing precedence: POS > merchant_reported > driver_estimate
- [ ] Sessions with NO total go to `completed_unbillable` (not `completed`)
- [ ] `BillingEvent` has `total_source` field
- [ ] `billing_events` only created when a total is available

### 5. POS Credentials Separated
- [ ] `merchant_notification_config` table has NO pos_access_token_encrypted column
- [ ] `merchant_pos_credentials` is a separate table with encrypted token fields
- [ ] `pos_adapter.py` factory function accepts credentials from the separate table

### 6. Copy Vocabulary
- [ ] Status flow uses: pending_order → awaiting_arrival → arrived → merchant_notified → completed
- [ ] No status called "notified" or "confirmed" (those were the old names)
- [ ] Spec document uses "On-site confirmed" / "Merchant notified" / "Completed" copy

### 7. Naming
- [ ] Router is at `/v1/charge-context/nearby` (NOT `/v1/intent/capture`)
- [ ] No "intent" language in the new charge-context router
- [ ] Old intent router still exists for backward compatibility (not deleted)

### 8. Router Registration
- [ ] `main.py` imports and registers: `arrival`, `charge_context`, `twilio_sms_webhook`, `merchant_arrivals`
- [ ] Models registered in `__init__.py`: `ArrivalSession`, `MerchantNotificationConfig`, `MerchantPOSCredentials`, `BillingEvent`

### 9. User Model Changes
- [ ] `user.py` has `vehicle_color`, `vehicle_model`, `vehicle_set_at` columns
- [ ] `account.py` has `PUT /v1/account/vehicle` and `GET /v1/account/vehicle` endpoints

### 10. Merchant Model Changes
- [ ] `while_you_charge.py` Merchant model has `ordering_url`, `ordering_app_scheme`, `ordering_instructions` columns

### 11. Analytics Events
- [ ] `apps/driver/src/analytics/events.ts` has EV_ARRIVAL_* event constants
- [ ] Backend fires `ev_arrival.created`, `ev_arrival.order_bound`, `ev_arrival.geofence_entered`, `ev_arrival.merchant_notified`, `ev_arrival.merchant_confirmed`, `ev_arrival.completed`, `ev_arrival.canceled`, `ev_arrival.feedback_submitted`

### 12. Merchant Portal
- [ ] `EVArrivals.tsx` added to merchant app
- [ ] Route `/ev-arrivals` added to `App.tsx`
- [ ] "EV Arrivals" nav item with `Car` icon added to `DashboardLayout.tsx`
- [ ] Component calls `GET /v1/merchants/{id}/arrivals` and `GET/PUT /v1/merchants/{id}/notification-config`

## Fix anything you find wrong. Do not add features — only fix bugs and missing connections.
