# V0 Web-First EV Arrival — Implementation Spec

**Date:** 2026-02-03
**Constraint:** 2-day turnaround (ship by EOD Feb 5)
**Author:** Principal Product Architect + Staff Engineer

---

## 1. Goals & Non-Goals

### Goals
- **Revenue Day 1.** A merchant pays Nerava a per-arrival fee the moment a verified driver orders from them while charging.
- **Web-only driver experience.** No app download required. Driver opens a URL, authenticates via phone OTP, sees nearby merchants, places order through merchant's existing channel, gets verified at charger.
- **Merchant onboarding in < 5 minutes.** Google Business Profile search → personalized preview page → claim → set notification phone → done.
- **Toast read-only integration design.** Deep link ordering now, API order-total lookup when Toast partner access is approved.
- **Google Maps as distribution.** Merchants update their Google Business Profile with a Nerava link ("Order ahead for EV drivers") that drives organic traffic.
- **Founder-call path.** Every preview page has a "Schedule a walkthrough" CTA to Calendly.

### Non-Goals (deferred)
- Native app required for drivers (web-first, native is additive)
- Real-time POS order status polling (manual confirmation is V0)
- Stripe automated invoicing (CSV billing export is V0)
- Push notifications to drivers (SMS to merchants only)
- Multi-session support (1 active arrival per driver)
- Email notifications to merchants (SMS only in V0)
- Square POS integration (Toast first)
- Wallet pass integration

---

## 2. System Architecture Changes

### What Already Exists (from EV Arrival System Design)
| Component | Status | File |
|-----------|--------|------|
| ArrivalSession model + migration 062 | Done | `backend/app/models/arrival_session.py` |
| MerchantNotificationConfig model | Done | `backend/app/models/merchant_notification_config.py` |
| MerchantPOSCredentials model | Done | `backend/app/models/merchant_pos_credentials.py` |
| BillingEvent model | Done | `backend/app/models/billing_event.py` |
| Arrival router (7 endpoints) | Done | `backend/app/routers/arrival.py` |
| Charge-context router | Done | `backend/app/routers/charge_context.py` |
| Twilio SMS webhook | Done | `backend/app/routers/twilio_sms_webhook.py` |
| Merchant arrivals + notification config | Done | `backend/app/routers/merchant_arrivals.py` |
| POS adapter (Manual + Toast/Square stubs) | Done | `backend/app/services/pos_adapter.py` |
| Notification service (SMS via Twilio) | Done | `backend/app/services/notification_service.py` |
| Merchant funnel (search/resolve/preview) | Done | `backend/app/routers/merchant_funnel.py` |
| Merchant claim flow (4 steps) | Done | `backend/app/routers/merchant_claim.py` |
| Driver OTP auth | Done | `backend/app/services/otp_service_v2.py` |
| Driver app (React) | Done | `apps/driver/` |
| Merchant portal (React) | Done | `apps/merchant/` |
| EVArrival components (5) | Done but **NOT wired** | `apps/driver/src/components/EVArrival/` |

### What Needs to Change for V0

**Backend changes (small):**
1. Wire EVArrival flow entry point into driver app routes
2. Add session expiry background task
3. Add billing CSV export endpoint
4. Add `GET /v1/arrival/active` polling support (already exists, just needs frontend wiring)

**Frontend changes (medium):**
1. Wire 5 EVArrival components into DriverHome.tsx
2. Add "EV Arrival" entry point to merchant card + detail screen
3. Add polling to ActiveSession (5s interval)
4. Add billing export button to merchant portal EVArrivals tab

**No new database migrations needed.** All tables exist from migration 062.

### Architecture Diagram (V0 Scope)

```
┌──────────────────────────────────────────────────────────────────┐
│                    DRIVER (Web Browser)                           │
│  Phone OTP → DriverHome → MerchantCard → "Add EV Arrival"       │
│  → ModeSelector → VehicleSetup → ConfirmationSheet               │
│  → [Order via Toast deep link] → Enter order # → ActiveSession   │
│  → [Geofence confirm OR manual "I'm here"] → CompletionScreen    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI) — ALL EXISTS                 │
│  POST /v1/arrival/create     PUT /v1/arrival/{id}/order          │
│  POST /v1/arrival/{id}/confirm-arrival                           │
│  POST /v1/arrival/{id}/merchant-confirm                          │
│  POST /v1/arrival/{id}/feedback    GET /v1/arrival/active        │
│  POST /v1/arrival/{id}/cancel                                    │
│  GET  /v1/charge-context/nearby                                  │
│  POST /v1/webhooks/twilio-arrival-sms                            │
│                                                                  │
│  NEW: GET /v1/admin/billing-export?month=2026-02                 │
│  NEW: Background task — expire stale sessions every 60s          │
└──────────────────────────────────────────────────────────────────┘
                              │
               ┌──────────────┼──────────────┐
               ▼              ▼              ▼
         ┌──────────┐  ┌──────────────┐  ┌────────────────────┐
         │ Twilio   │  │ Toast deep   │  │ Merchant Portal    │
         │ SMS      │  │ link (no API │  │ EVArrivals tab     │
         │          │  │ in V0)       │  │ + billing export   │
         └──────────┘  └──────────────┘  └────────────────────┘
```

### Web-First Driver Flow (No Native Bridge)

The existing EV Arrival system was designed for native geofence confirmation. For V0 web-first:

1. **Geofence → Manual "I'm here" button.** The `confirm-arrival` endpoint already accepts lat/lng. The web app uses browser Geolocation API (`navigator.geolocation`) to get coordinates. If the driver is within 250m of the charger (server-side check), confirmation succeeds. If geolocation is denied, show a manual "I'm at the charger" button that skips distance check (set `skip_geo_check=true` flag — requires a small backend change to allow web-only confirmations).

2. **No native bridge dependency.** The `useNativeBridge.ts` hook already has `isNative` detection. When `isNative === false`, the EVArrival components should use browser APIs directly:
   - Location: `navigator.geolocation.getCurrentPosition()`
   - No geofence monitoring (driver taps "I'm here" manually)
   - No foreground service needed

---

## 3. Database Changes & Migrations

**No new migrations required.** All tables exist:
- `arrival_sessions` (migration 062)
- `merchant_notification_config` (migration 062)
- `merchant_pos_credentials` (migration 062)
- `billing_events` (migration 062)
- User vehicle fields (`vehicle_color`, `vehicle_model`, `vehicle_set_at` on `users`)
- Merchant ordering fields (`ordering_url`, `ordering_app_scheme`, `ordering_instructions` on `merchants`)

### One-time Data Setup
For pilot merchants, manually set:
```sql
UPDATE merchants SET
  ordering_url = 'https://order.toasttab.com/online/asadas-grill',
  ordering_instructions = 'Order online, then enter your order number in Nerava'
WHERE id = 'asadas-grill-id';
```

---

## 4. API Contracts

### Existing Endpoints (no changes needed)

All 7 arrival endpoints are implemented per the EV Arrival System Design doc:
- `POST /v1/arrival/create` — Create session
- `PUT /v1/arrival/{id}/order` — Bind order number
- `POST /v1/arrival/{id}/confirm-arrival` — Geofence/location confirm
- `POST /v1/arrival/{id}/merchant-confirm` — Merchant marks delivered
- `POST /v1/arrival/{id}/feedback` — Driver feedback
- `GET /v1/arrival/active` — Current active session
- `POST /v1/arrival/{id}/cancel` — Cancel session

### New Endpoint: Billing CSV Export

```
GET /v1/admin/billing-export?month=2026-02
Authorization: Bearer {admin_token}
Content-Type: text/csv

Response:
session_id,merchant_id,merchant_name,driver_id,order_number,order_total_cents,fee_bps,billable_cents,total_source,completed_at
uuid-1,m_abc,Asadas Grill,42,1234,2847,500,142,pos,2026-02-01T14:00:00Z
uuid-2,m_def,Epoch Coffee,43,5678,1200,500,60,driver_estimate,2026-02-01T15:30:00Z
```

### Backend Change: Web-Only Arrival Confirmation

Modify `POST /v1/arrival/{id}/confirm-arrival` to accept an optional `web_confirm` flag:

```json
// Request (web-only, no native geofence)
{
  "lat": 30.2672,
  "lng": -97.7431,
  "accuracy_m": 50.0,
  "web_confirm": true  // NEW: skips charger_id requirement for web users
}
```

**Logic change:** When `web_confirm=true`:
- `charger_id` is optional (web users may not have it)
- Still checks lat/lng against nearest charger within 500m
- If no geolocation available, allow confirmation without distance check but set `arrival_accuracy_m = null` and `total_source` priority drops (POS > merchant_reported only, no driver_estimate billing)
- PostHog event includes `confirmation_method: "web_manual"` vs `"native_geofence"`

---

## 5. Frontend UX Flows — Driver App

### Entry Point: Wire EVArrival into DriverHome

The 5 EVArrival components exist at `apps/driver/src/components/EVArrival/`:
- `ModeSelector.tsx`
- `VehicleSetup.tsx`
- `ConfirmationSheet.tsx`
- `ActiveSession.tsx`
- `CompletionScreen.tsx`

**Wiring plan:**

1. **DriverHome.tsx** — Add "EV Arrival" mode. When driver is near a charger (from `/v1/charge-context/nearby`), show merchant cards with "Add EV Arrival" CTA instead of the current "Secure Spot" flow.

2. **MerchantDetailModal.tsx** — Add primary CTA "Add EV Arrival" that launches the EVArrival flow (ModeSelector → VehicleSetup if needed → ConfirmationSheet).

3. **ActiveSession.tsx** — Add 5-second polling to `GET /v1/arrival/active` to detect merchant confirmation. Add browser geolocation "I'm at the charger" button for web users.

4. **New route:** `/arrival` in `App.tsx` that renders the active session or redirects to home if no active session.

### Web-Specific UX Adaptations

| Native App | Web V0 |
|------------|--------|
| Geofence auto-triggers arrival confirmation | "I'm at the charger" button + browser geolocation |
| Background location monitoring | No background — manual confirmation only |
| Push notification when merchant confirms | 5s polling on ActiveSession screen |
| Deep link return from ordering app | "I've placed my order" button (manual return) |

### Flow Wireframes

**Step 1: Merchant Card in DriverHome**
```
┌─────────────────────────────┐
│ [photo]  Asadas Grill       │
│          ★ 4.5 · 3 min walk │
│                             │
│  [ Add EV Arrival → ]      │  ← NEW CTA
└─────────────────────────────┘
```

**Step 2: After "Add EV Arrival" → ModeSelector (existing)**
Select EV Curbside or EV Dine-In → VehicleSetup if needed → ConfirmationSheet

**Step 3: Active Session with web adaptations**
```
┌─────────────────────────────┐
│  EV Arrival Active          │
│  Asadas Grill · EV Curbside │
│                             │
│  Step 1: Place your order   │
│  [ Order from Asadas → ]    │  ← Opens Toast URL in new tab
│                             │
│  Step 2: Enter order #      │
│  [ Order # _________ ]     │
│  [ Save Order # ]           │
│                             │
│  Step 3: Confirm arrival    │
│  [ I'm at the charger ✓ ]  │  ← NEW for web (uses browser geolocation)
│                             │
│  Status: Waiting...         │  ← Polls every 5s
│  Expires in 1h 45m          │
└─────────────────────────────┘
```

---

## 6. Merchant Onboarding Portal Flow

### Existing Flow (already built)
1. `/find` — Search for business via Google Places (`FindBusiness.tsx`)
2. `/preview` — Personalized preview page with HMAC-signed URL (`MerchantPreview.tsx`)
3. `/claim` — 4-step claim: enter info → verify phone → send magic link → verify email (`ClaimBusiness.tsx`)
4. Dashboard: Overview, Exclusives, EVArrivals, Billing, Settings

### V0 Changes to Onboarding

**No code changes needed.** The existing flow already supports:
- Google Places search → resolve → signed preview URL
- Phone verification via OTP
- Email verification via magic link
- Redirect to dashboard after claim

**Content changes** (copy updates in existing components):
- FindBusiness: Update heading to "See what EV drivers see when they charge near you"
- MerchantPreview: Emphasize arrival notifications over exclusives
- ClaimBusiness: Add "Set your notification phone number" step (already exists in notification config)

### Post-Claim First-Run
After claiming, merchant lands on Overview. The EVArrivals tab should show:
- "No arrivals yet" empty state
- Notification settings card with SMS phone pre-filled from claim flow
- "How it works" explainer (3 bullets: driver charges → orders from you → we notify you)

---

## 7. Google Maps Distribution Plan

### The Strategy
Merchants add a link to their Google Business Profile that says "Order ahead for EV drivers" pointing to the driver-facing discovery page. This turns every Google Maps listing near a charger into a free acquisition channel.

### Implementation (Manual V0)
1. After merchant claims business, show instructions:
   ```
   Add this link to your Google Business Profile:

   https://app.nerava.network/m/{merchant_slug}?src=gmb

   Steps:
   1. Open Google Business Profile Manager
   2. Go to "Edit profile" → "Contact"
   3. Add website link with label "Order ahead for EV drivers"
   4. Save
   ```

2. The `/m/{merchant_slug}` route already exists in the driver app — it shows MerchantDetailModal.

3. Track `?src=gmb` in PostHog to measure Google Maps → Nerava conversion.

### Future (Post-V0)
- Google Business Profile API integration to auto-add the link during onboarding
- Google Maps "Place Action Links" API for richer integration
- Local Services Ads targeting "EV charging near [merchant]" keywords

---

## 8. Toast Auth Design

### V0: Deep Link Only (No API)
In V0, Toast integration is **deep link ordering only**:
- Merchant provides their Toast online ordering URL during onboarding
- Stored in `merchants.ordering_url`
- Driver taps "Order from [merchant]" → opens Toast URL in new browser tab
- Driver returns to Nerava, enters order number manually
- **No Toast API calls.** Order total comes from driver estimate or merchant report.

### V1 Design: Toast OAuth (Post-V0, when partner access approved)

```
Merchant clicks "Connect Toast" in Settings
  → Redirect to Toast OAuth: https://ws-api.toasttab.com/usermgmt/v1/oauth/authorize
    ?client_id={NERAVA_TOAST_CLIENT_ID}
    &response_type=code
    &scope=orders.read
    &redirect_uri=https://api.nerava.network/v1/oauth/toast/callback
    &state={encrypted_merchant_id}
  → Toast shows consent screen
  → Redirect back with ?code=...
  → Backend exchanges code for access_token + refresh_token
  → Stores in merchant_pos_credentials (Fernet-encrypted)
  → Sets merchant_notification_config.pos_integration = 'toast'
```

**Required env vars (future):**
```
TOAST_CLIENT_ID=
TOAST_CLIENT_SECRET=
TOAST_REDIRECT_URI=https://api.nerava.network/v1/oauth/toast/callback
```

**POS Adapter activation:** When `merchant_pos_credentials.pos_type = 'toast'` and tokens are valid, `arrival.py` instantiates `ToastPOSAdapter` instead of `ManualPOSAdapter`. Lookup flow:
1. `GET /orders/v2/orders?businessDate={today}` with restaurant GUID
2. Scan for check where `displayNumber` matches driver's order number
3. Extract `totalAmount` → store as `order_total_cents`
4. On completion, re-fetch for final total

**Failure mode:** All Toast API failures degrade to ManualPOSAdapter. The system always works without POS.

---

## 9. Personalized Merchant Onboarding Page

### URL Format
```
https://merchant.nerava.network/preview?merchant_id={id}&exp={unix_ts}&sig={hmac_hex}
```

### Already Implemented
`MerchantPreview.tsx` exists and fetches from `GET /v1/merchant/funnel/preview`. The backend validates HMAC signature and returns:
- Merchant name, address, photo, rating
- Nearest charger info
- Verified visit count

### V0 Content Additions (copy changes only)
Add to the existing MerchantPreview component:

1. **"What EV drivers see" card** — Mock of driver app merchant card
2. **Revenue estimate** — "Restaurants near EV chargers see 15-30 extra covers/month from charging drivers"
3. **How billing works** — "5% of order value, only on verified arrivals. No upfront cost."
4. **Loom video** — Auto-play after 800ms (already designed in plan, `LoomModal.tsx`)

### Post-View CTAs (already in plan)
1. **Primary:** "Claim your business" → `/claim`
2. **Secondary:** "Schedule a 10-minute walkthrough" → Calendly URL
3. **Tertiary:** "Text me the link" → SMS via `/v1/merchant/funnel/text-preview-link`

---

## 10. Merchant Portal — Notifications Toggle

### Already Built
`merchant_arrivals.py` has:
- `GET /v1/merchants/{id}/notification-config` — Read config
- `PUT /v1/merchants/{id}/notification-config` — Update config

`EVArrivals.tsx` in merchant portal already renders notification settings.

### V0 Requirements (verify existing implementation)
- [x] SMS phone field (E.164 format)
- [x] SMS toggle (on/off)
- [ ] Email toggle — **disable in V0** (email sending is a placeholder). Hide the email toggle or show "Coming soon".
- [x] POS integration dropdown — keep as "None" in V0 (no Toast OAuth yet)

### Notification Config UI
```
┌──────────────────────────────────┐
│ Notification Settings            │
│                                  │
│ SMS Notifications  [ON]          │
│ Phone: (512) 555-1234  [Edit]    │
│                                  │
│ Email Notifications              │
│ Coming soon                      │
│                                  │
│ POS Integration                  │
│ None (manual confirmation)       │
│ Toast coming soon                │
└──────────────────────────────────┘
```

---

## 11. Analytics Events

### Existing PostHog Events (from arrival.py)
All `ev_arrival.*` events are already instrumented:
| Event | Trigger |
|-------|---------|
| `ev_arrival.created` | Session created |
| `ev_arrival.order_bound` | Order number entered |
| `ev_arrival.geofence_entered` | Arrival confirmed |
| `ev_arrival.merchant_notified` | SMS sent |
| `ev_arrival.merchant_confirmed` | Merchant replies DONE |
| `ev_arrival.completed` | Session completed |
| `ev_arrival.feedback_submitted` | Driver leaves feedback |
| `ev_arrival.expired` | Session timed out |
| `ev_arrival.canceled` | Session canceled |

### New Events for V0
| Event | Trigger | Properties |
|-------|---------|------------|
| `ev_arrival.web_confirm` | Driver taps "I'm at the charger" (web) | `has_geolocation`, `accuracy_m` |
| `ev_arrival.order_link_clicked` | Driver taps Toast ordering link | `merchant_id`, `ordering_url` |
| `ev_arrival.billing_export` | Admin downloads CSV | `month`, `row_count`, `total_billable_cents` |
| `merchant_funnel.gmb_visit` | Driver arrives via `?src=gmb` | `merchant_id`, `referrer` |
| `merchant_funnel.calendly_click` | Merchant clicks "Schedule walkthrough" | `merchant_id` |

### Funnel Metrics to Track
1. **Driver conversion:** nearby merchants shown → "Add EV Arrival" tapped → order placed → arrival confirmed → completed
2. **Merchant conversion:** preview page viewed → claim started → claim completed → first arrival received
3. **Revenue:** total arrivals × average order value × fee_bps = gross revenue
4. **Billing accuracy:** % of sessions with POS-verified total vs. driver estimate vs. merchant reported

---

## 12. Security & Abuse Prevention

### Existing Protections
- **Anti-spoofing:** `confirm-arrival` requires charger_id + server-side haversine distance check (250m radius)
- **One session per driver:** Partial unique index on `driver_id` for active statuses
- **HMAC-signed preview URLs:** 7-day TTL, tamper-proof
- **OTP rate limiting:** Existing rate limit on phone verification
- **Fernet-encrypted POS tokens:** Separated from notification config

### V0 Web-Specific Concerns

| Risk | Mitigation |
|------|------------|
| **GPS spoofing via browser** | Server-side distance check still applies. For web-only confirms without geolocation, mark `total_source` as lower priority (don't bill on driver estimate alone). |
| **Fake order numbers** | In V0 (no POS API), we can't verify. Merchant confirmation via SMS is the trust anchor — merchant won't reply DONE if no order exists. |
| **Session farming** | Rate limit: max 3 arrival sessions per driver per day. Max 1 active at a time (already enforced). |
| **SMS abuse to merchants** | Only send SMS on confirmed arrival (geofence/location verified). Not on session creation. |
| **Preview URL sharing** | URLs expire in 7 days. Viewing a preview is harmless — claiming requires phone verification. |

### New Rate Limit
Add to `arrival.py`:
```python
# Max 3 completed arrivals per driver per calendar day
# Prevents session farming for billing manipulation
```

---

## 13. Acceptance Criteria & Test Plan

### P0 — Must ship (Day 1-2)

| # | Criterion | How to verify |
|---|-----------|---------------|
| 1 | Driver can see "Add EV Arrival" on merchant cards near a charger | Load DriverHome near Canyon Ridge chargers, verify CTA appears |
| 2 | Driver can create an EV Arrival session (curbside or dine-in) | Tap "Add EV Arrival" → select mode → confirm → session created (201) |
| 3 | Driver can enter order number | Enter "1234" → PUT /order returns 200 → status = awaiting_arrival |
| 4 | Driver can confirm arrival via browser location | Tap "I'm here" → browser geolocation → POST /confirm-arrival → 200 |
| 5 | Merchant receives SMS with order details | Check Twilio logs or test phone for SMS with order #, vehicle, arrival type |
| 6 | Merchant can reply DONE to complete session | Reply "DONE {code}" to Twilio number → session transitions to completed |
| 7 | Merchant can confirm via portal | Dashboard → EVArrivals → "Mark Delivered" → session completes |
| 8 | BillingEvent is created on completion | Query billing_events table → row exists with correct fee_bps and billable_cents |
| 9 | Driver sees completion screen with feedback | After merchant confirms → CompletionScreen renders → thumbs up/down works |
| 10 | Session expires after 2 hours | Create session, wait (or mock time) → status transitions to expired |

### P1 — Should ship (Day 2)

| # | Criterion | How to verify |
|---|-----------|---------------|
| 11 | Billing CSV export works | GET /v1/admin/billing-export?month=2026-02 → valid CSV with correct rows |
| 12 | ActiveSession polls for updates | Open ActiveSession → merchant confirms → screen updates within 10s |
| 13 | "I'm here" without geolocation works | Deny browser location → tap "I'm here anyway" → confirm with degraded accuracy |
| 14 | Cancel arrival works | Tap "Cancel" → POST /cancel → session canceled, no SMS sent |
| 15 | Vehicle setup persists | Set vehicle once → subsequent arrivals pre-fill vehicle info |

### P2 — Nice to have (Post Day 2)

| # | Criterion |
|---|-----------|
| 16 | Loom modal on merchant preview page |
| 17 | Google Maps instructions in post-claim flow |
| 18 | Calendly CTA on preview page |
| 19 | "Text me the link" on preview page |

---

## 14. 2-Day Task Breakdown

### Day 1 (Feb 4): Backend + Driver App Wiring

**Morning (4 hours):**

| Task | File(s) | Description |
|------|---------|-------------|
| 1. Add session expiry background task | `backend/app/main.py` or `backend/app/lifespan.py` | asyncio task every 60s: transition sessions past `expires_at` to `expired` |
| 2. Add `web_confirm` support to confirm-arrival | `backend/app/routers/arrival.py` | Accept `web_confirm=true`, make `charger_id` optional, use nearest-charger lookup |
| 3. Add billing CSV export endpoint | `backend/app/routers/admin_domain.py` | `GET /v1/admin/billing-export?month=YYYY-MM` → CSV response |
| 4. Add daily session rate limit | `backend/app/routers/arrival.py` | Max 3 completed sessions per driver per day |
| 5. Set ordering_url for pilot merchants | SQL / seed script | Update Asadas Grill and pilot merchants with Toast ordering URLs |

**Afternoon (4 hours):**

| Task | File(s) | Description |
|------|---------|-------------|
| 6. Wire EVArrival into DriverHome | `apps/driver/src/components/DriverHome/DriverHome.tsx` | Import ModeSelector, show "Add EV Arrival" CTA on merchant cards |
| 7. Wire EVArrival into App.tsx routes | `apps/driver/src/App.tsx` | Add `/arrival` route rendering ActiveSession |
| 8. Add MerchantDetailModal "Add EV Arrival" CTA | `apps/driver/src/components/MerchantDetail/MerchantDetailModal.tsx` or `MerchantDetailsScreen.tsx` | Primary button launches EVArrival flow |
| 9. Add browser geolocation "I'm here" to ActiveSession | `apps/driver/src/components/EVArrival/ActiveSession.tsx` | When `isNative=false`, show manual confirm button with browser geolocation |

### Day 2 (Feb 5): Polish + Merchant Portal + Test

**Morning (4 hours):**

| Task | File(s) | Description |
|------|---------|-------------|
| 10. Add 5s polling to ActiveSession | `apps/driver/src/components/EVArrival/ActiveSession.tsx` | `setInterval` calling `GET /v1/arrival/active`, clear on unmount |
| 11. Add billing export to merchant portal | `apps/merchant/app/components/EVArrivals.tsx` | "Download billing CSV" button (admin only) or add to admin portal |
| 12. Hide email toggle in notification config | `apps/merchant/app/components/EVArrivals.tsx` | Replace email toggle with "Coming soon" text |
| 13. Add Google Maps instructions post-claim | `apps/merchant/app/components/ClaimBusiness.tsx` | After successful claim, show "Add to Google Business Profile" instructions |
| 14. Disable email sending in notification service | `backend/app/services/notification_service.py` | Ensure `notify_email` path logs warning instead of silently failing |

**Afternoon (4 hours):**

| Task | File(s) | Description |
|------|---------|-------------|
| 15. End-to-end manual test | — | Full flow: create session → order → confirm → SMS → DONE reply → billing event |
| 16. Fix any issues found in testing | Various | Bug fixes from manual test |
| 17. Deploy to staging | — | `./scripts/deploy_aws.py` |
| 18. Smoke test on staging | — | Repeat E2E flow on staging environment |
| 19. Deploy to production | — | Production deploy after staging passes |

---

## 15. Bare Minimum Revenue Path

Here's the simplest possible path from "no revenue" to "first dollar":

### The 30-Second Version
1. **Driver charges at Canyon Ridge** (our pilot charger location)
2. **Opens `app.nerava.network`** on phone browser
3. **Logs in via OTP** (phone number, 6-digit code)
4. **Sees Asadas Grill** with "Add EV Arrival" button
5. **Taps it** → selects "EV Curbside" → confirms
6. **Orders from Asadas** via Toast online ordering link (opens in new tab)
7. **Returns to Nerava**, enters order # "1234"
8. **Taps "I'm at the charger"** → browser geolocation confirms location
9. **Asadas receives SMS:** "EV Arrival: Order #1234 | EV Curbside | Blue Tesla Model 3"
10. **Asadas prepares order**, brings to charger area
11. **Asadas replies "DONE 1234"** to SMS
12. **BillingEvent created:** Order $28.47 × 5% = **$1.42 revenue**
13. **Driver sees completion screen**, leaves thumbs-up feedback
14. At month end, download billing CSV → invoice Asadas for total arrivals

### What Makes This Work Without Any New Code
Almost everything above already exists. The gap is **wiring** — the EVArrival components exist but aren't connected to the driver app UI. The 2-day sprint is 80% wiring, 10% small backend additions (expiry task, CSV export, web confirm), 10% testing.

### Revenue Math (Pilot)
- 5 drivers/day × $25 avg order × 5% fee = **$6.25/day per merchant**
- 10 merchants × $6.25 × 30 days = **$1,875/month**
- At 50 merchants: **$9,375/month**
- At 8% fee (target): **$15,000/month**

### What Proves Product-Market Fit
1. **Repeat usage:** Do drivers use EV Arrival more than once?
2. **Merchant retention:** Do merchants keep SMS notifications on?
3. **Completion rate:** What % of created sessions reach `completed`?
4. **NPS signal:** Thumbs-up vs thumbs-down ratio

---

## Appendix A: File Change Summary

### Modified Files (9)
| File | Change |
|------|--------|
| `backend/app/routers/arrival.py` | Add `web_confirm` flag, daily rate limit |
| `backend/app/routers/admin_domain.py` | Add billing CSV export endpoint |
| `backend/app/main.py` or `lifespan.py` | Add session expiry background task |
| `backend/app/services/notification_service.py` | Log warning on email path |
| `apps/driver/src/App.tsx` | Add `/arrival` route |
| `apps/driver/src/components/DriverHome/DriverHome.tsx` | Wire EVArrival entry point |
| `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx` | Add "Add EV Arrival" CTA |
| `apps/driver/src/components/EVArrival/ActiveSession.tsx` | Add polling + web geolocation confirm |
| `apps/merchant/app/components/EVArrivals.tsx` | Hide email toggle, add billing export |

### New Files (0)
None. All components exist.

### Data Changes (1)
| Change | Method |
|--------|--------|
| Set `ordering_url` on pilot merchants | SQL update or seed script |

---

## Appendix B: Environment Variables

### Already Configured
All required env vars are already in `config.py`:
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `OTP_FROM_NUMBER` — SMS notifications
- `JWT_SECRET` — Auth tokens
- `DATABASE_URL` — PostgreSQL
- `PREVIEW_SIGNING_KEY` — HMAC for merchant preview URLs
- `GOOGLE_PLACES_API_KEY` — Merchant search

### Future (Toast OAuth, Post-V0)
```
TOAST_CLIENT_ID=
TOAST_CLIENT_SECRET=
TOAST_REDIRECT_URI=https://api.nerava.network/v1/oauth/toast/callback
```
