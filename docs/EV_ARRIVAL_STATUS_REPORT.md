# Nerava EV Arrival Network — Status Report & 10/10 Gap Analysis

**Date:** 2026-02-01
**Prepared for:** ChatGPT briefing / internal review

---

## 1. What Was Built

The EV Arrival Network is a real-time coordination layer between EV drivers charging at stations and nearby merchants (restaurants, cafes). When a driver plugs in, they can place an order at a nearby merchant and get curbside delivery or dine-in coordination while they charge.

### Backend (Python/FastAPI)
| Component | File | Status |
|-----------|------|--------|
| ArrivalSession model | `backend/app/models/arrival_session.py` | Done |
| MerchantNotificationConfig model | `backend/app/models/merchant_notification_config.py` | Done |
| MerchantPOSCredentials model | `backend/app/models/merchant_pos_credentials.py` | Done |
| BillingEvent model | `backend/app/models/billing_event.py` | Done |
| Alembic migration 062 | `backend/alembic/versions/062_add_ev_arrival_tables.py` | Done |
| Arrival router (7 endpoints) | `backend/app/routers/arrival.py` | Done |
| Charge-context router | `backend/app/routers/charge_context.py` | Done |
| Twilio SMS webhook | `backend/app/routers/twilio_sms_webhook.py` | Done |
| Merchant arrivals router | `backend/app/routers/merchant_arrivals.py` | Done |
| POS adapter service | `backend/app/services/pos_adapter.py` | Done |
| Notification service | `backend/app/services/notification_service.py` | Done |
| Vehicle endpoints on account router | `backend/app/routers/account.py` | Done |
| User model vehicle fields | `backend/app/models/user.py` | Done |
| Merchant ordering fields | `backend/app/models/while_you_charge.py` | Done |

### Driver App (React/TypeScript)
| Component | File | Status |
|-----------|------|--------|
| ModeSelector | `apps/driver/src/components/EVArrival/ModeSelector.tsx` | Done |
| VehicleSetup | `apps/driver/src/components/EVArrival/VehicleSetup.tsx` | Done |
| ConfirmationSheet | `apps/driver/src/components/EVArrival/ConfirmationSheet.tsx` | Done |
| ActiveSession | `apps/driver/src/components/EVArrival/ActiveSession.tsx` | Done |
| CompletionScreen | `apps/driver/src/components/EVArrival/CompletionScreen.tsx` | Done |
| Analytics events | `apps/driver/src/analytics/events.ts` | Done |

### Merchant Portal (React/TypeScript)
| Component | File | Status |
|-----------|------|--------|
| EVArrivals dashboard | `apps/merchant/app/components/EVArrivals.tsx` | Done |
| Route + nav integration | `apps/merchant/app/App.tsx` + `DashboardLayout.tsx` | Done |

### Tests
| Suite | Status |
|-------|--------|
| `test_arrival_sessions.py` | Done |
| `test_arrival_unit.py` | Done (Cursor) |
| `test_arrival_integration.py` | Done (Cursor) |
| `test_charge_context.py` | Done (Cursor) |
| `test_merchant_arrivals.py` | Done (Cursor) |
| `test_pos_adapter.py` | Done (Cursor) |
| `test_twilio_sms_webhook.py` | Done (Cursor) |
| `test_vehicle.py` | Done (Cursor) |

### Documentation
- Full system design: `docs/EV_ARRIVAL_SYSTEM_DESIGN.md` (10 sections, all 7 critical fixes applied)
- Cursor validation prompt: `claude-cursor-prompts/2026-02-01_cursor-validate-ev-arrival.md`
- Codex test prompt: `claude-cursor-prompts/2026-02-01_codex-test-ev-arrival.md`

### Cursor Validation Results
Cursor ran against a 12-section checklist. Found and fixed 2 issues:
1. **SQLite migration compatibility** — Partial unique index now uses dialect check (PostgreSQL only)
2. **Column size mismatch** — `merchant_reply_code` corrected from `String(6)` to `String(4)` across model + migration

All other checklist items passed: router registration, model imports, foreign keys, state transitions, SMS reply code logic, billing precedence, PostHog events, error handling.

---

## 2. 10/10 Production Readiness Gaps

### GAP 1 — EVArrival components not wired to driver app (CRITICAL)

**Severity:** HIGH — blocks all user-facing functionality

The 5 EVArrival React components exist but are orphaned. They are not imported or rendered anywhere in `DriverHome.tsx` or the driver app router. A driver has no way to access the EV Arrival flow.

**Fix:** Wire `ModeSelector` into `DriverHome.tsx` (or a new route) as the entry point. Connect the flow: ModeSelector → VehicleSetup (if needed) → ConfirmationSheet → ActiveSession → CompletionScreen. Add a prominent "Order ahead" or "EV Arrival" button to the charging screen.

**Effort:** ~2 hours

### GAP 2 — charge_context.py full table scans (MEDIUM-HIGH)

**Severity:** Medium-High — works at pilot scale, breaks at production scale

`GET /v1/charge-context/nearby` loads all chargers and merchants from the database, then filters by haversine distance in Python. With hundreds of merchants this is fine; with thousands it will cause latency spikes.

**Fix:** Add spatial filtering in the SQL query. Either use PostGIS `ST_DWithin` or a bounding-box WHERE clause on lat/lng columns before the Python haversine filter.

**Effort:** ~1 hour

### GAP 3 — Email notifications are placeholder (MEDIUM)

**Severity:** Medium — merchants who enable email notifications get nothing

`notification_service.py` has `send_email_notification()` that logs and returns False. If a merchant sets `notify_email=True` and `notify_sms=False`, they receive zero notifications when a driver arrives.

**Fix:** Either integrate SES/SendGrid for email, or remove the email toggle from the merchant notification config UI until implemented.

**Effort:** ~3 hours (SES integration) or ~30 min (disable toggle)

### GAP 4 — Toast/Square POS adapters are stubs (MEDIUM)

**Severity:** Medium — manual billing works, but POS integration is promised in the spec

`ToastPOSAdapter` and `SquarePOSAdapter` both return `None` for `get_order_total()`. The system falls back to manual billing (driver estimate or merchant-reported), which works correctly. But if a merchant configures `pos_integration=toast`, they may expect automatic order total lookup.

**Fix:** Implement Toast API integration for `get_order_total()` and `lookup_order()`. Square can follow. Or clearly mark POS integration as "coming soon" in the merchant portal UI.

**Effort:** ~1 week per POS integration (API keys, OAuth, testing)

### GAP 5 — No WebSocket/polling for real-time session updates (LOW-MEDIUM)

**Severity:** Low-Medium — functional but not delightful

The driver's `ActiveSession` component shows session status but relies on manual refresh or polling. When a merchant confirms delivery, the driver doesn't see the update immediately.

**Fix:** Add a polling interval (every 5s) to `ActiveSession` that calls `GET /v1/arrival/active`. Or implement SSE/WebSocket for push updates.

**Effort:** ~1 hour (polling) or ~4 hours (WebSocket)

### GAP 6 — No session expiry background job (LOW-MEDIUM)

**Severity:** Low-Medium — sessions with `expires_at` in the past remain in active status

The `expires_at` field is set but nothing transitions expired sessions to `status=expired`. The partial unique index means a driver with a stale session can't create a new one.

**Fix:** Add a background task (FastAPI `BackgroundTasks` or a cron job) that runs every 60s and transitions sessions past `expires_at` to `expired`.

**Effort:** ~1 hour

---

## 3. Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| Data model | 10/10 | All tables, indexes, constraints, migration done |
| API endpoints | 9/10 | All 7 arrival endpoints + charge-context + merchant arrivals + SMS webhook. Missing expiry job. |
| Anti-spoofing | 10/10 | Server-side haversine check on confirm-arrival, charger_id required |
| Billing logic | 10/10 | POS > merchant > driver precedence, completed_unbillable fallback |
| SMS notifications | 9/10 | Twilio integration with reply codes. Email placeholder. |
| Driver app components | 7/10 | All 5 components built but NOT wired into the app |
| Merchant portal | 9/10 | Dashboard + notification config. POS stubs noted in UI. |
| Tests | 9/10 | 8 test files, ~50 test cases. Cursor validated. |
| Documentation | 10/10 | Full system design, architectural decisions, all 7 fixes documented |
| Production readiness | 7/10 | No expiry job, no real-time updates, charge_context perf issue |

**Overall: 8.5/10** — Backend is solid. The critical gap is wiring the driver app components. Fix Gap 1 and Gap 6 to reach 9.5/10. Fix Gap 2 for true production scale.

---

## 4. Android App Timeline

### Current iOS Architecture
The iOS app is a **native Swift hybrid** — a thin native shell (~20 Swift files, ~2,700 LOC) wrapping the React driver web app in WKWebView. Native code handles:
- Push notifications (APNs)
- Location services (CLLocationManager)
- Apple Wallet pass integration
- Deep link routing (Universal Links)
- Native ↔ WebView bridge (postMessage/WKScriptMessageHandler)

The React web app (`apps/driver/`) does all UI rendering.

### Existing Flutter Scaffold
A Flutter project exists at `mobile/nerava_flutter/` with 14 Dart files. It's a basic WebView wrapper — no native bridge, no push notifications, no location services.

### Option A: Native Kotlin (Android)
Mirror the iOS approach: native Kotlin shell + WebView loading the same React app.

| Task | Notes |
|------|-------|
| Project setup + WebView wrapper | Kotlin + Jetpack Compose or XML |
| JavaScript bridge | `WebView.addJavascriptInterface()` matching iOS bridge |
| Push notifications | FCM integration |
| Location services | FusedLocationProviderClient |
| Google Wallet passes | Google Wallet API |
| Deep links | Android App Links |
| Play Store assets + submission | Screenshots, listing, review |

**Estimate: 6-8 weeks** for one developer. The WebView + JS bridge is straightforward since all UI logic lives in the React app.

### Option B: Flutter (Cross-Platform)
Enhance the existing Flutter scaffold to match iOS native capabilities.

| Task | Notes |
|------|-------|
| Enhance WebView bridge | `webview_flutter` + `JavaScriptChannel` |
| Push notifications | `firebase_messaging` plugin |
| Location services | `geolocator` plugin |
| Wallet passes | `google_wallet` plugin |
| Deep links | `uni_links` plugin |
| Play Store submission | Same as above |

**Estimate: 2-3 weeks** using existing scaffold. Risk: Flutter WebView has known quirks with keyboard handling and scroll behavior on some Android devices.

### Recommendation
**Option B (Flutter)** for speed to market. The app is fundamentally a WebView wrapper — Flutter's WebView plugin handles this well and you get iOS parity for free (could replace the native Swift app later). The 2-3 week estimate assumes one developer familiar with Flutter.

If long-term native performance or platform-specific UX matters more than speed, go with Option A.

---

## 5. Immediate Next Steps (Priority Order)

1. **Wire EVArrival components into DriverHome** — unblocks all user testing
2. **Add session expiry background job** — prevents stuck sessions
3. **Add polling to ActiveSession** — real-time feel without WebSocket complexity
4. **Add bounding-box filter to charge_context** — production-scale query performance
5. **Disable email toggle or implement SES** — don't show broken options
6. **Start Android app** — Flutter scaffold exists, enhance it
