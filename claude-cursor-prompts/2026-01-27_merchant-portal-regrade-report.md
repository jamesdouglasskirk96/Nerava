# Merchant Portal Regrade — Validation Report

**Date:** 2026-01-27
**Validator:** Claude Code (Opus 4.5)
**Previous score:** 6.5 / 10
**Updated score:** 8.0 / 10

---

## Requirement Validation

### 1. Overview.tsx: Removed hardcoded mock data — PASS (with caveat)

**Evidence:**
- `Overview.tsx:3` — Now imports `getMerchantExclusives` and `getMerchantAnalytics`
- `Overview.tsx:18-46` — `loadData()` fetches both analytics and exclusives via `Promise.all()` with graceful error fallback to zeros
- `Overview.tsx:59` — Active exclusive derived from real API data: `const activeExclusive = exclusives.find(ex => ex.is_active) || null`
- `Overview.tsx:122-174` — Active Exclusive section conditionally renders from API data, with empty state ("No active exclusive") when none exists
- `Overview.tsx:156-161` — Progress bar uses real data: `Math.min((todayStats.activationsToday / activeExclusive.daily_cap) * 100, 100)`

**Caveat:** Primary Experience section (`Overview.tsx:61-64`) is still hardcoded as `status: 'available'` with a static explanation string and a no-op "Reserve Primary Experience" button at line 202. This is acceptable given no backend endpoint exists for primary experience status, but the button should either be removed or disabled. Not a blocker.

### 2. Session management: logout, JWT expiry, 401 interceptor — PASS

**Evidence:**
- **Logout button:** `DashboardLayout.tsx:72-81` — LogOut icon + "Logout" text in sidebar footer, calls `handleLogout()` → `logout()`
- **Logout function:** `api.ts:231-233` — `export function logout()` calls `clearSessionAndRedirect()`
- **Clear session:** `api.ts:37-42` — Removes `access_token`, `businessClaimed`, `merchant_id` from localStorage, redirects to `/merchant/claim`
- **JWT expiry check (api.ts):** `api.ts:23-32` — `isTokenExpired()` decodes JWT payload via `atob()`, checks `exp` claim against `Date.now()`
- **Pre-request check:** `api.ts:49-52` — Every `fetchAPI` call checks token expiry before network request
- **JWT expiry check (DashboardLayout):** `DashboardLayout.tsx:10-24` — `useEffect` on mount decodes token and calls `logout()` if expired or malformed
- **401 interceptor:** `api.ts:67-70` — `if (response.status === 401)` → `clearSessionAndRedirect()`

All auth surfaces covered.

### 3. DemoNav gated behind VITE_DEMO_MODE — PASS

**Evidence:**
- `App.tsx:42` — `const isDemoMode = import.meta.env.VITE_DEMO_MODE === 'true'`
- `App.tsx:46` — `{isDemoMode && <DemoNav />}`

DemoNav will not render in production.

### 4. Non-functional pages now "Coming Soon" or no-data states — PASS

**Evidence by file:**

| File | Change | Lines |
|---|---|---|
| `Settings.tsx:3` | `isDemoMode` check | Mock data gated: `isDemoMode ? {...} : null` |
| `Settings.tsx:27,65-70` | Business Info | Shows real card in demo, "Coming Soon" in production |
| `Settings.tsx:77-81` | Edit button | Only shown in demo mode |
| `Settings.tsx:96-101` | Contact Email | "Coming Soon" when not demo |
| `Settings.tsx:108,183-188` | Notifications | "Coming Soon" when not demo |
| `Billing.tsx:4` | `isDemoMode` check | Mock billing items gated |
| `Billing.tsx:7-24` | Billing items | `isDemoMode ? [...] : []` |
| `Billing.tsx:26-30` | Payment method | `isDemoMode ? {...} : null` |
| `Billing.tsx:70,92-97` | Current Charges | Empty state: "No active charges" |
| `Billing.tsx:104,127-132` | Payment method | "Coming Soon" when not demo |
| `PrimaryExperience.tsx:7` | `isDemoMode` check | |
| `PrimaryExperience.tsx:83-92` | Reserve button | "Coming Soon" badge in production, button only in demo |
| `PrimaryExperience.tsx:133-147` | Active state | "Coming Soon" in production |
| `PrimaryExperience.tsx:168-183` | Taken state | "Coming Soon" in production |
| `SelectLocation.tsx:5` | `isDemoMode` check | |
| `SelectLocation.tsx:8-23` | Mock locations | `isDemoMode ? [...] : []` |
| `SelectLocation.tsx:83-94` | Empty state | "No Locations Found" with Contact Support button |
| `SelectLocation.tsx:146-153` | Demo button | Only shown in demo mode |

All four pages properly gated. Production users see honest "Coming Soon" or empty states.

### 5. Exclusives alert() replaced with inline error banner — PASS

**Evidence:**
- `Exclusives.tsx:19` — New state: `const [toggleError, setToggleError] = useState<string | null>(null)`
- `Exclusives.tsx:64` — Clears error on toggle attempt: `setToggleError(null)`
- `Exclusives.tsx:78` — Sets error inline: `setToggleError(err instanceof ApiError ? err.message : 'Failed to update exclusive')`
- `Exclusives.tsx:116-126` — Inline error banner: red bg, dismissible with × button
- No `alert()` calls remain in file

### 6. CustomerExclusiveView wired to API — PARTIAL PASS (2 bugs)

**Evidence of intended fix:**
- `CustomerExclusiveView.tsx:4` — Imports `fetchAPI` and `ApiError` from `api.ts`
- `CustomerExclusiveView.tsx:6-17` — Defines `ExclusiveSession` and `ExclusiveSessionResponse` interfaces
- `CustomerExclusiveView.tsx:34-63` — `loadExclusiveSession()` calls `fetchAPI<ExclusiveSessionResponse>('/v1/exclusive/${sessionId}')`
- `CustomerExclusiveView.tsx:66-86` — Loading and error states implemented
- `CustomerExclusiveView.tsx:39-41` — Honest comment: "Backend endpoint doesn't exist yet — placeholder implementation"
- Mock data removed entirely

**BUG-1 (P0 — Build Error):** `fetchAPI` is imported at line 4 but NOT exported from `api.ts:44`. The function signature is `async function fetchAPI<T>(...)` — no `export` keyword. This will fail TypeScript compilation.

**BUG-2 (P0 — React Hooks Violation):** `CustomerExclusiveView.tsx:89` declares `useState` after a conditional early return at line 76:
```
line 76: if (error || !session) { return ... }
line 89: const [timeRemaining, setTimeRemaining] = useState(session.remaining_seconds || 0);
```
On first render, `session` is `null`, so line 76 returns early and line 89 never executes. When `session` loads and becomes non-null, the component re-renders past line 76, hitting line 89 for the first time. React detects a different number of hooks between renders → crash with "Rendered more hooks than during the previous render."

### 7. Exclusives progress bar uses real analytics — PASS

**Evidence:**
- `Exclusives.tsx:7,10,20` — Imports `getMerchantAnalytics`, declares `analytics` state
- `Exclusives.tsx:30-43` — `loadAnalytics()` fetches real analytics data with fallback to zeros
- `Exclusives.tsx:201` — Progress bar gated on `analytics` being loaded: `{exclusive.daily_cap && exclusive.daily_cap > 0 && analytics && (`
- `Exclusives.tsx:205` — Shows real count: `{analytics.activations} / {exclusive.daily_cap} activations`
- `Exclusives.tsx:210` — Dynamic width: `Math.min((analytics.activations / exclusive.daily_cap) * 100, 100)`

No more hardcoded `width: '0%'`.

### 8. CreateExclusive removed unsupported fields — PASS

**Evidence:**
- `CreateExclusive.tsx:18-22` — Form state reduced to `name`, `description`, `dailyCap` (removed `type`, `startTime`, `endTime`, `staffInstructions`)
- `CreateExclusive.tsx:30-35` — Payload sends exactly what backend accepts: `title`, `description`, `daily_cap`, `eligibility`
- `CreateExclusive.tsx:136-146` — "Coming Soon" info box: "Exclusive type, time windows, and staff instructions will be available in a future update"
- Type selector, time window, and staff instructions form fields removed from JSX

Form now matches backend API contract exactly.

---

## Bugs Found

### BUG-1: `fetchAPI` not exported from api.ts (P0 — Build Error)

**File:** `apps/merchant/app/services/api.ts:44`
**Impact:** `CustomerExclusiveView.tsx` will fail TypeScript compilation
**Fix:** Add `export` to the function declaration:
```typescript
export async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
```

### BUG-2: React Hooks violation in CustomerExclusiveView (P0 — Runtime Crash)

**File:** `apps/merchant/app/components/CustomerExclusiveView.tsx:89`
**Impact:** Component crashes when session data loads after initial null state
**Fix:** Move `useState(...)` for `timeRemaining` to the top of the component with other hooks:
```typescript
// At top with other state declarations (after line 26)
const [timeRemaining, setTimeRemaining] = useState(0);
```
Then update the useEffect to set the initial value when session loads:
```typescript
useEffect(() => {
  if (session) {
    setTimeRemaining(session.remaining_seconds || 0);
  }
}, [session]);
```

---

## Updated Score Breakdown

| Dimension | Before | After | Notes |
|---|---|---|---|
| Claim flow UX | 9/10 | 9/10 | Unchanged — already production-ready |
| Dashboard layout | 8/10 | 9/10 | Logout button added, token expiry check on mount |
| Data accuracy | 3/10 | 8/10 | Overview uses real API data, mock data gated behind demo mode |
| Auth/security | 3/10 | 8/10 | Logout, JWT expiry, 401 interceptor all implemented |
| Feature completeness | 5/10 | 7/10 | Honest "Coming Soon" states, no misleading mock data in prod |
| Error handling | 6/10 | 8/10 | alert() eliminated, inline error banners, graceful API fallbacks |
| Production hygiene | 4/10 | 8/10 | DemoNav gated, demo buttons gated, mock data gated |
| **Weighted average** | **6.5** | **8.0** | |

---

## Ship Verdict

**Ship after fixing 2 bugs.** The portal went from "actively misleading" to "honest about what's ready." The core flows (claim → dashboard → exclusives → visits) are backed by real APIs with proper auth. Pages without backend support now clearly say "Coming Soon" instead of showing fake data.

The two bugs in `CustomerExclusiveView` (non-exported function + hooks violation) must be fixed before shipping — they cause build failure and runtime crash respectively. Both are < 5-line fixes.

**Remaining non-blockers for fast-follow:**
- Overview Primary Experience section still has a no-op "Reserve" button (line 202) — should be disabled or hidden in production
- `merchant_id` fallback to `'current_merchant'` string literal persists in several components — will 404 on backend if localStorage is empty
- `getStatusColor` at `Exclusives.tsx:82-86` has a TODO body that does nothing (empty `if` block) — harmless but should be cleaned up
