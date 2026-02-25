# Nerava Functional Gap Report

> **Generated:** 2026-02-20
> **Scope:** All 5 apps (driver, merchant, admin, landing, link) + FastAPI backend + iOS native shell
> **Method:** Automated source-code audit with manual verification against actual files

---

## Table of Contents

1. ["Ghost" UI — Buttons/Elements That Do Nothing](#1-ghost-ui--buttonselements-that-do-nothing)
2. [Missing Backend Logic — UI Calls a Void](#2-missing-backend-logic--ui-calls-a-void)
3. [Mock Data / Placeholders](#3-mock-data--placeholders)
4. ["Simple vs Full" Mismatches — Routers Missing from Production](#4-simple-vs-full-mismatches--routers-missing-from-production)
5. [Native Bridge Gaps](#5-native-bridge-gaps)

---

## 1. "Ghost" UI — Buttons/Elements That Do Nothing

### Driver App (5 confirmed items)

| File | Element | Issue |
|------|---------|-------|
| `apps/driver/src/components/PreCharging/ChargerCard.tsx:73-78` | "Navigate to Charger" button | `onClick` fires `console.log('Navigate to charger:', charger.id)` + `TODO: Wire to backend navigation` — no actual navigation |
| `apps/driver/src/components/PreCharging/PreChargingScreen.tsx:79-82` | Charger card click handler | `handleChargerClick` is `console.log` only with `TODO: Wire to backend navigation` |
| `apps/driver/src/components/Account/AccountPage.tsx:244-255` | "Settings" row button | `<button>` with chevron icon but **no `onClick` handler** — completely inert |
| `apps/driver/src/components/Wallet/WalletModal.tsx:87-94` | "Withdraw to Bank" button | Enabled when balance >= $10, but handler only does `console.log('Open Stripe Express payout')` |
| `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx:541-542` | Favorite (heart) and Share icon buttons | Both callbacks passed as `() => {}` (empty functions) to HeroImageHeader |

### Merchant Portal (10 confirmed items)

| File | Element | Issue |
|------|---------|-------|
| `apps/merchant/app/components/Billing.tsx` | Entire Billing section | "Coming soon" stub — no buttons, forms, or API calls exist at all |
| `apps/merchant/app/components/Settings.tsx` | Entire Settings section | "Coming soon" stub — no profile, notifications, or branding UI exists |
| `apps/merchant/app/components/PickupPackages.tsx` | Entire Pickup Packages list | "Coming soon" stub — no create/edit/delete buttons |
| `apps/merchant/app/components/CreatePickupPackage.tsx:15-18` | "Create Package" form submit | `handleSubmit` silently discards all form data and navigates back — no API call |
| `apps/merchant/app/components/PrimaryExperience.tsx:84` | "Reserve Primary Experience" button (demo mode) | `<button>` with **no `onClick` handler** — bare element |
| `apps/merchant/app/components/PrimaryExperience.tsx:88-92` | Primary Experience (production mode) | Renders "Coming Soon" banner instead of any controls; state hardcoded to `'available'`, setter never destructured |
| `apps/merchant/app/components/SelectLocation.tsx:90-92` | "Contact Support" button (no locations state) | `<button>` with **no `onClick` handler** |
| `apps/merchant/app/components/SelectLocation.tsx:55-59` | "Join Waitlist" and "Contact Support" buttons (claimed state) | Both `<button>` elements with **no `onClick` handlers** |
| `apps/merchant/app/components/Overview.tsx:65-68` | Primary Experience status on Overview | Hardcoded `status: 'available'` with `TODO: Fetch real status from backend`; renders as static "Coming Soon" span |
| `apps/merchant/app/components/Overview.tsx:19-21` | Overview KPI cards (when no merchantId) | `loadData` exits early if `localStorage.getItem('merchant_id')` is empty, leaving all stats at zero |

### Admin Dashboard (5 confirmed items)

| File | Element | Issue |
|------|---------|-------|
| `apps/admin/src/components/ChargingLocations.tsx` | Entire component | "Coming soon" stub — zero functionality, no data, no interactions |
| `apps/admin/src/components/Dashboard.tsx:165-173` | "Recent Alerts" panel | Static placeholder card: heading + "Alert monitoring coming soon" — no data source |
| `apps/admin/src/components/Logs.tsx:2` | Download/export button | `Download` icon imported from lucide-react but never rendered — planned export feature absent |
| `apps/admin/src/components/Exclusives.tsx:2` | Edit and Ban action buttons | `Edit` and `Ban` icons imported but never rendered — planned actions never implemented |
| `apps/admin/src/components/Merchants.tsx:2` | View details, Ban, and Verify buttons | `Eye`, `Ban`, `CheckCircle` icons imported but never rendered — only ExternalLink, Mail, Pause/Play are wired |

---

## 2. Missing Backend Logic — UI Calls a Void

| Feature | Frontend Expectation | Backend Reality |
|---------|---------------------|-----------------|
| **Nova issuance on merchant confirmation** | Driver expects Nova credits after a confirmed visit | No automatic Nova grant exists in the checkout/confirmation flow. `checkin_service.py` sets `session.status = 'merchant_confirmed'` but never calls `NovaService.grant_to_driver()`. Nova issuance is manual admin-only via `/v1/nova/grant` with comment: *"can be automated later"* |
| **Driver wallet payouts** | "Withdraw to Bank" button in `WalletModal.tsx` | `driver_wallet` router exists at `app/routers/driver_wallet.py` with Stripe Express payout logic, but is **not included in `main_simple.py`** — unreachable in production |
| **Push notifications** | Notification preferences referenced in merchant settings concept | `notifications` router exists at `app/routers/notifications.py` but is **not included in `main_simple.py`** — dead in production |
| **Platform fee inconsistency** | Billing expects a coherent fee rate | `config.py` sets `PLATFORM_FEE_BPS=1500` (15%) used by `merchant_analytics.py` for billing summaries. `ArrivalSession.platform_fee_bps` defaults to `500` (5%) used by `checkin_service.py` for actual `BillingEvent` calculations. A merchant could be billed at 5% per-transaction while the dashboard reports 15% |
| **Deal redemption (Nova-for-deals)** | Merchant-initiated Nova redemption via `/v1/merchants/redeem_from_driver` | Endpoint exists and is functional, but `FIX_DATABASE.md` references a missing `merchant_redemptions` table for `/v1/wallet/timeline`. No driver-initiated "redeem a deal coupon" flow exists |

---

## 3. Mock Data / Placeholders

| Flag / Pattern | Location | What It Fakes | Production Risk |
|---------------|----------|--------------|-----------------|
| `TESLA_MOCK_MODE` | `backend/app/core/config.py:63`, consumed by `backend/app/services/mock_tesla_fleet_api.py` | Returns fake vehicle lists, hardcoded `"Charging"` state, mock VINs and battery levels without calling Tesla Fleet API | Default `false`; safe if not set |
| `OTP_PROVIDER=stub` | `backend/app/core/config.py:163`, factory at `backend/app/services/auth/otp_factory.py` | **Default value is `stub`**. Accepts code `000000` or *any non-empty code* in non-prod. Twilio is never called | **High risk**: a fresh deployment without `OTP_PROVIDER=twilio_verify` silently runs stubbed OTP |
| `MERCHANT_AUTH_MOCK` | `backend/app/core/config.py:96`, consumed by `backend/app/services/google_business_profile.py` | Returns mock OAuth URLs, fake tokens, two hardcoded locations ("Mock Coffee Shop", "Mock Restaurant"). The real `list_locations()` path raises `NotImplementedError` — **the mock is the only working path** | Default `false`; GBP integration is non-functional regardless |
| `VITE_MOCK_MODE` | `apps/driver/src/services/api.ts:27-29` | Three mock functions: `captureIntentMock`, `getMerchantDetailsMock`, `activateExclusiveMock` — hardcoded fixture data with simulated delays | Vite build + Dockerfile enforce `VITE_MOCK_MODE=false` for production |
| `VITE_DEMO_MODE` | `apps/merchant/app/App.tsx:46`, `SelectLocation.tsx`, `PrimaryExperience.tsx` | Shows `<DemoNav>` component, substitutes real location API with hardcoded mock locations, gates mock status displays | Only affects merchant portal demo instances |
| Hardcoded Primary Experience status | `apps/merchant/app/components/Overview.tsx:65-68` | `status: 'available'` with `TODO: Fetch real status from backend` — never changes | Always shown as "Coming Soon" regardless of actual state |

---

## 4. "Simple vs Full" Mismatches — Routers Missing from Production

`main.py` (dev/legacy) includes all routers. `main_simple.py` (production, used by App Runner) omits the following **14 routers**, all of which exist as files in `backend/app/routers/`:

| Router | Module | Prefix | Production Impact |
|--------|--------|--------|-------------------|
| `checkin` | `app.routers.checkin` | `/v1/checkin/*` | EV Arrival Code (V0) flow — check-in via code at charger |
| `driver_wallet` | `app.routers.driver_wallet` | `/v1/wallet/*` | Stripe Express payouts for drivers — "Withdraw to Bank" is dead |
| `charge_context` | `app.routers.charge_context` | `/v1/charge-context/*` | Charge session context for driver app |
| `ev_context` | `app.routers.ev_context` | `/v1/ev-context/*` | EV detection context for driver app |
| `virtual_key` | `app.routers.virtual_key` | `/v1/virtual-key/*` | Tesla virtual key provisioning |
| `clo` | `app.routers.clo` | `/v1/clo/*` | Card-linked offers via Fidel |
| `notifications` | `app.routers.notifications` | `/v1/notifications/*` | Push notification management and delivery |
| `account` | `app.routers.account` | `/v1/account/*` | Account management (profile, deletion) |
| `consent` | `app.routers.consent` | `/v1/consent/*` | User consent tracking |
| `merchant_funnel` | `app.routers.merchant_funnel` | `/v1/merchant/funnel/*` | Merchant signup funnel |
| `merchant_arrivals` | `app.routers.merchant_arrivals` | `/v1/merchants/{id}/arrivals` | Merchant arrival views + notification config |
| `twilio_sms_webhook` | `app.routers.twilio_sms_webhook` | `/v1/webhooks/twilio-arrival-sms` | SMS webhook handler for arrival notifications |
| `client_telemetry` | `app.routers.client_telemetry` | `/v1/telemetry/*` | Frontend telemetry/error collection |
| `arrival` (legacy) | `app.routers.arrival` | `/v1/arrival/*` | Legacy arrival flow (only `arrival_v2` is in production) |

**Routers present in `main_simple.py`:** `auth_domain`, `drivers_domain`, `merchants_domain`, `stripe_domain` (optional), `admin_domain`, `nova_domain`, `ev_smartcar`, `virtual_cards`, `tesla_auth`, `arrival_v2`, `bootstrap`, `pilot_party`, `native_events`, plus legacy scaffold routers (`users`, `hubs`, `places`, `recommend`, `wallet`, `chargers`, `webhooks`, `incentives`, `energyhub`, `social`, `activity`, `vehicle_onboarding`, `perks`, `exclusive`, `checkout`, `merchant_claim`, `merchant_onboarding`).

---

## 5. Native Bridge Gaps

### Implemented Commands (10 — full web ↔ native parity)

| Direction | Command | Handler |
|-----------|---------|---------|
| Web → Native | `SET_CHARGER_TARGET` | `sessionEngine.setChargerTarget()` — sets geofence target |
| Web → Native | `SET_AUTH_TOKEN` | Stores token in Keychain + APIClient |
| Web → Native | `EXCLUSIVE_ACTIVATED` | `sessionEngine.webConfirmsExclusiveActivated()` |
| Web → Native | `VISIT_VERIFIED` | `sessionEngine.webConfirmsVisitVerified()` |
| Web → Native | `END_SESSION` | `sessionEngine.webRequestsSessionEnd()` |
| Web → Native | `REQUEST_ALWAYS_LOCATION` | `locationService.requestAlwaysPermission()` |
| Web → Native (req/res) | `GET_LOCATION` | Returns lat/lng/accuracy; web falls back to `navigator.geolocation` |
| Web → Native (req/res) | `GET_SESSION_STATE` | Returns current session state enum |
| Web → Native (req/res) | `GET_PERMISSION_STATUS` | Returns location permission status |
| Web → Native (req/res) | `GET_AUTH_TOKEN` | Returns token from Keychain |

### Native → Web Messages (8 implemented)

| Message | Web Handling | Issue |
|---------|-------------|-------|
| `NATIVE_READY` | Sets `bridgeReady = true` | Sent twice per navigation (injection script + `didFinishNavigation`); idempotent, no harm |
| `SESSION_STATE_CHANGED` | Updates `sessionState` React state | Working correctly |
| `SESSION_START_REJECTED` | **`console.warn` only** | User gets no feedback when activation is rejected (reasons: `NOT_ANCHORED`, `NO_CHARGER_TARGET`, `INVALID_MERCHANT_LOCATION`) |
| `AUTH_REQUIRED` | Clears `localStorage` tokens | Silent logout with no re-auth prompt; code comment says *"V2: show banner"* |
| `EVENT_EMISSION_FAILED` | **`console.error` only** | Failed backend events (network/HTTP errors) produce no user-visible feedback |
| `PERMISSION_STATUS` | Request/response only | No push listener — if user revokes location permission while app is open, web can't react without polling |
| `LOCATION_RESPONSE` | Request/response only | Working correctly for on-demand use |
| `ERROR` | **Not handled** | Native sends `ERROR` when `GET_LOCATION` fails, but it resolves the Promise with an error payload instead of rejecting — callers must check for `message` field |

### Missing Capabilities

| Gap | Description | Impact |
|-----|-------------|--------|
| **`nerava://` custom scheme not registered** | `DeepLinkHandler.swift` has full logic for `nerava://` URLs but `Info.plist` has no `CFBundleURLTypes` entry — the OS will never route these URLs to the app | Dead code; custom scheme deep links don't work |
| **No native OAuth callback handling** | No `ASAuthorizationAppleIDProvider`, no Google Sign-In SDK (`GIDSignIn`), no Tesla OAuth redirect handler. All OAuth flows run entirely within the WKWebView | If any OAuth flow opens external Safari, the redirect back to the app depends entirely on Universal Links (AASA covers `/*` broadly, so this may work, but is untested at the native layer) |
| **No proactive permission change detection** | If the user toggles location permission in iOS Settings while the app is open, the web layer has no mechanism to learn about it without manually calling `GET_PERMISSION_STATUS` | Stale permission state in the web UI until next explicit check |
| **`AUTH_TOKEN_RESPONSE` type inconsistency** | `getAuthToken()` returns `Promise<AuthTokenResponse \| null>` but the `null` branch (no bridge) lacks `requestId` typing | Minor TypeScript inconsistency, no runtime impact |

---

## Priority Summary

### Critical (production functionality broken)

1. **14 routers missing from `main_simple.py`** — entire features unreachable in production (Section 4)
2. **`OTP_PROVIDER` defaults to `stub`** — fresh deployments silently accept any OTP code (Section 3)
3. **Platform fee mismatch** — 5% billed vs 15% reported in analytics (Section 2)
4. **Nova not auto-issued** — core reward loop is manual-only (Section 2)

### High (user-facing gaps)

5. **Driver "Withdraw to Bank"** — button exists, router unreachable in production (Sections 1 + 4)
6. **Merchant Billing/Settings** — "Coming soon" stubs behind nav items (Section 1)
7. **CreatePickupPackage form** — appears to work but silently discards data (Section 1)
8. **`SESSION_START_REJECTED` silently logged** — users get no feedback on failed activations (Section 5)
9. **`AUTH_REQUIRED` silent logout** — users lose session with no explanation (Section 5)

### Medium (incomplete features)

10. **Admin ChargingLocations** — nav item leads to empty stub (Section 1)
11. **Admin action buttons** — Edit/Ban/Verify icons imported but never rendered (Section 1)
12. **Driver "Navigate to Charger"** — button is console.log only (Section 1)
13. **Merchant SelectLocation** — "Contact Support" / "Join Waitlist" buttons have no handlers (Section 1)
14. **Google Business Profile** — `list_locations()` raises `NotImplementedError`; mock is only working path (Section 3)

### Low (cosmetic / minor)

15. **Driver favorite/share** — empty function callbacks (Section 1)
16. **Driver Settings row** — button with no onClick (Section 1)
17. **`nerava://` scheme not registered** — dead code in DeepLinkHandler (Section 5)
18. **`NATIVE_READY` sent twice** — no harm, minor noise (Section 5)
