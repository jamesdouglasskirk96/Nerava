# Merchant Portal + Onboarding — UX Quality Review

**Date:** 2026-01-27
**Reviewer:** Claude Code (Opus 4.5)
**Scope:** `apps/merchant/` (frontend) + `backend/app/routers/merchant_claim.py` (backend)

---

## UX Score: 6.5 / 10

The merchant portal has a solid structural foundation — clean layout, sensible navigation, and a well-designed claim flow backed by real backend endpoints. However, the dashboard is half-finished: multiple pages display hardcoded mock data, key features have no backend, and auth/state management relies on raw `localStorage` with no session persistence. This is a functional prototype, not a production-ready portal.

---

## Top 3 UX Wins

### 1. Claim Flow Is Real and Well-Architected
The onboarding claim flow (`ClaimBusiness.tsx` → `ClaimVerify.tsx`) is the strongest part of the portal. It has:
- A genuine 3-step wizard with progress indicator (form → phone OTP → email magic link)
- Full backend implementation at `backend/app/routers/merchant_claim.py` with 5 endpoints: `start`, `verify-phone`, `send-magic-link`, `verify-magic-link`, `session/{id}`
- Proper error handling at each step (invalid merchant, already claimed, OTP failure, expired link)
- Real Twilio OTP + SES magic link email with branded HTML template
- Idempotent session handling — re-starting a claim for the same merchant reuses the session

This is production-ready infrastructure. The UX is clear: each step has one action, loading states on buttons, and the user always knows what to do next.

**Files:** `apps/merchant/app/components/ClaimBusiness.tsx:1-322`, `apps/merchant/app/components/ClaimVerify.tsx:1-94`, `backend/app/routers/merchant_claim.py:1-399`

### 2. Dashboard Layout and Navigation
The sidebar layout (`DashboardLayout.tsx`) follows standard SaaS dashboard conventions:
- Fixed 264px sidebar with clear icon+label nav items
- Active state uses high-contrast inverted colors (black bg, white text)
- 7 well-organized sections matching a merchant's mental model: Overview → Exclusives → Visits → Primary Experience → Pickup Packages → Billing → Settings
- Lucide icons are consistently used across all pages

The information architecture is correct for the domain. A merchant can orient themselves immediately.

**Files:** `apps/merchant/app/components/DashboardLayout.tsx:1-55`

### 3. Demo Navigation System
The `DemoNav.tsx` component provides an excellent review/QA tool:
- Purple collapsible banner at top of viewport organizes all screens into Flow A (Onboarding), Flow B (Dashboard), Flow G (Staff View)
- One-click navigation to any screen with automatic `localStorage` state management
- "Reset Demo" button clears all state
- Shows current route and claim status in footer

This is the right approach for stakeholder demos and internal testing. It allows non-technical reviewers to explore every state without knowing the URL structure.

**Files:** `apps/merchant/app/components/DemoNav.tsx:1-137`

---

## Top 3 UX Gaps

### 1. Overview Dashboard Shows Hardcoded Mock Data Alongside Real API Data (P0)
The Overview page (`Overview.tsx`) has a split personality:
- **Lines 17-35**: The "Today" stats section correctly calls `getMerchantAnalytics(merchantId)` from the real backend and gracefully falls back to zeros on error
- **Lines 47-58**: The "Active Exclusive" and "Primary Experience" sections are **entirely hardcoded** — `"Free Pastry with Coffee"`, `43/100 activations`, `status: 'on'`, `status: 'available'`

A merchant logging in after claiming their business will see fabricated data that has no relationship to their actual business. The "Active Exclusive" card shows an offer they never created. The progress bar shows 43% utilization of a fictional cap. This is actively misleading.

The real analytics API (`/v1/merchants/{id}/analytics`) only returns `activations`, `completes`, `unique_drivers`, `completion_rate`. There is no backend endpoint to fetch the merchant's active exclusive or primary experience status.

**Files:**
- `apps/merchant/app/components/Overview.tsx:47-58` (hardcoded data)
- `apps/merchant/app/services/api.ts:140-142` (analytics endpoint exists)
- Missing backend: no `GET /v1/merchants/{id}/active-exclusive`, no `GET /v1/merchants/{id}/primary-status`

### 2. Auth Is localStorage-Only With No Session Management (P0)
The entire portal auth model is:
```
localStorage.getItem('businessClaimed') === 'true'  → show dashboard
localStorage.getItem('access_token')                 → send Bearer token
localStorage.getItem('merchant_id')                  → identify merchant
```

Problems:
- **No token expiry check**: The JWT from `ClaimVerify.tsx:25` is stored forever. No refresh flow exists. When the token expires, API calls will silently fail with 401 and the user will see error states with no recovery path.
- **No logout**: There is no logout button or function anywhere in the portal. The only way to "log out" is to clear localStorage manually or use the demo "Reset Demo" button.
- **No route guards**: `App.tsx:36` checks `localStorage.getItem('businessClaimed')` synchronously on render. This is not reactive — if the token is invalidated server-side, the portal keeps showing the dashboard with failing API calls.
- **merchant_id fallback**: Multiple components fall back to `'current_merchant'` as a string literal (`Overview.tsx:9`, `Exclusives.tsx:19`, `CreateExclusive.tsx:13`), which will hit the backend with a fake ID and get 404s.

**Files:**
- `apps/merchant/app/App.tsx:36` (auth check)
- `apps/merchant/app/components/ClaimVerify.tsx:25-26` (token storage)
- `apps/merchant/app/services/api.ts:22-28` (token usage)
- `apps/merchant/app/components/Overview.tsx:9` (merchant_id fallback)

### 3. Settings, Billing, PrimaryExperience, and PickupPackages Are Non-Functional Mocks (P1)
Four of seven dashboard pages have **zero backend connectivity**:

| Page | File | Issue |
|---|---|---|
| Settings | `Settings.tsx:4-8` | Hardcoded "Downtown Coffee Shop" data. "Edit" button is no-op. Notification toggles use `defaultChecked` — state isn't persisted anywhere. |
| Billing | `Billing.tsx:5-28` | Hardcoded mock items ($99 Primary, $45.30 Pickups). "Update" payment button is no-op. No Stripe/payment integration. |
| PrimaryExperience | `PrimaryExperience.tsx:8-10` | `useState('available')` with no API call. "Reserve" and "Join Waitlist" buttons are no-ops. Pricing ($99/mo) is displayed but not purchasable. |
| SelectLocation | `SelectLocation.tsx:6-21` | Hardcoded mock locations. "Demo: Show Already Claimed State" button visible to users. No Google Places integration. |

A merchant navigating to Billing will see fake charges they haven't incurred. Settings shows a business name and address that isn't theirs. The "Reserve Primary Experience" button does nothing. These pages create false expectations and erode trust.

**Files:**
- `apps/merchant/app/components/Settings.tsx:4-8`
- `apps/merchant/app/components/Billing.tsx:5-28`
- `apps/merchant/app/components/PrimaryExperience.tsx:8-10`
- `apps/merchant/app/components/SelectLocation.tsx:6-21`

---

## Additional Issues

### CustomerExclusiveView Uses Mock Data (P1)
`CustomerExclusiveView.tsx:6-13` has a hardcoded `mockExclusiveData` object. This is the staff-facing screen shown when a customer arrives. It should fetch real session data via `GET /v1/exclusive/{session_id}` but instead uses a static map with key `'1'`.

**File:** `apps/merchant/app/components/CustomerExclusiveView.tsx:6-13`

### Exclusives Progress Bar Is Always 0% (P1)
`Exclusives.tsx:175-176` renders a progress bar for daily cap but the width is hardcoded to `style={{ width: '0%' }}`. The component fetches real exclusives from the backend but has no way to get current-day activation counts to fill the bar. The `getStatusColor` function at line 60-64 has a TODO comment acknowledging this.

**File:** `apps/merchant/app/components/Exclusives.tsx:60-64, 175-176`

### Exclusives Toggle Error Uses `alert()` (P2)
`Exclusives.tsx:56` uses `alert()` for toggle failures — a browser alert dialog in a modern SaaS portal is jarring.

**File:** `apps/merchant/app/components/Exclusives.tsx:56`

### CreateExclusive Sends Incomplete Data (P2)
The form collects `type`, `startTime`, `endTime`, and `staffInstructions` but `handleSubmit` at line 36-41 only sends `title`, `description`, `daily_cap`, and a hardcoded `eligibility: 'charging_only'`. Four form fields are collected from the user but discarded.

**File:** `apps/merchant/app/components/CreateExclusive.tsx:36-41`

### DemoNav Is Visible in Production (P1)
`App.tsx:44` renders `<DemoNav />` unconditionally. There is no environment check. This purple banner will show in production.

**File:** `apps/merchant/app/App.tsx:44`

---

## Production Readiness Verdict

**Needs Fixes.** The claim flow is production-ready, but the dashboard is not. Shipping the current portal would expose merchants to:
1. Misleading hardcoded data they'll interpret as real metrics
2. No logout or session management
3. Non-functional feature pages with working CTAs that do nothing
4. A visible demo navigation banner

**Minimum to ship:**
- Remove or gate DemoNav behind `VITE_DEMO_MODE`
- Replace hardcoded data in Overview with "Coming Soon" cards or real API calls
- Add logout button + token expiry handling
- Hide or label Settings/Billing/PrimaryExperience as "Coming Soon"
- Remove `alert()` usage

---

## Cursor-Ready Implementation Plan

### Fix 1: Gate DemoNav and Mock Pages (30 min)

**File:** `apps/merchant/app/App.tsx`
```diff
+ const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true';
  return (
    <BrowserRouter basename={basename}>
-     <DemoNav />
+     {isDemoMode && <DemoNav />}
```

**Files:** `apps/merchant/app/components/Settings.tsx`, `Billing.tsx`, `PrimaryExperience.tsx`
- Wrap body content in a "Coming Soon" banner when no real data is available
- Remove hardcoded mock data objects

### Fix 2: Add Logout + Token Refresh (45 min)

**File:** `apps/merchant/app/components/DashboardLayout.tsx`
- Add logout button at bottom of sidebar
- `localStorage.removeItem('access_token', 'businessClaimed', 'merchant_id')` → navigate to `/claim`

**File:** `apps/merchant/app/services/api.ts`
- Add 401 response interceptor: on 401, clear localStorage, redirect to `/claim`
- Add token expiry check using JWT `exp` claim (decode without verification, check `Date.now()`)

### Fix 3: Fix Overview to Show Only Real Data (30 min)

**File:** `apps/merchant/app/components/Overview.tsx`
- Delete hardcoded `activeExclusive` and `primaryExperience` objects (lines 47-58)
- Replace "Active Exclusive" section with a conditional: if exclusives exist (fetch from `getMerchantExclusives`), show the first active one; otherwise show "Create your first exclusive" CTA linking to `/exclusives/new`
- Replace "Primary Experience" section with "Coming Soon" badge or remove entirely

### Fix 4: Fix Exclusives Progress Bar + Error Handling (20 min)

**File:** `apps/merchant/app/components/Exclusives.tsx`
- Line 56: Replace `alert(...)` with inline error state (`setError(...)`) rendered as a toast or banner
- Lines 175-176: Either remove progress bar entirely (no data source) or add `activations_today` to the `Exclusive` type and API response

### Fix 5: Fix CreateExclusive to Send All Fields (15 min)

**File:** `apps/merchant/app/components/CreateExclusive.tsx`
- Lines 36-41: Include `type`, `start_time`, `end_time`, `staff_instructions` in the API payload
- Or: Remove form fields that aren't sent to avoid collecting data you discard

### Fix 6: Wire CustomerExclusiveView to Real API (30 min)

**File:** `apps/merchant/app/components/CustomerExclusiveView.tsx`
- Replace `mockExclusiveData` with API call: `GET /v1/exclusive/{exclusiveId}/session`
- Add loading and error states
- Make countdown timer use `remaining_seconds` from `ExclusiveSessionResponse`

---

## Score Breakdown

| Dimension | Score | Notes |
|---|---|---|
| Claim flow UX | 9/10 | Real backend, clear steps, proper error handling |
| Dashboard layout | 8/10 | Clean SaaS sidebar, good IA, consistent styling |
| Data accuracy | 3/10 | Half the dashboard shows hardcoded fake data |
| Auth/security | 3/10 | localStorage-only, no logout, no token refresh, no route guards |
| Feature completeness | 5/10 | Exclusives + Visits are real; Settings/Billing/Primary/Pickup are shells |
| Error handling | 6/10 | Claim flow is solid; dashboard uses `alert()` and has gaps |
| Production hygiene | 4/10 | DemoNav visible, mock data exposed, fallback IDs hit backend |
| **Weighted average** | **6.5** | |
