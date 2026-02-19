# Admin Portal Gap Review Report

**Date:** 2026-01-27
**Scope:** `apps/admin/` (frontend) + `backend/app/routers/admin_domain.py` (backend)
**Reviewer:** Claude Code (Opus 4.5)

---

## UX Score: 5.5 / 10

The admin portal has solid bones — 5 of 8 screens are wired to real backend APIs, the audit log is searchable with pagination, and the emergency override flow has a proper confirmation-token pattern. However, the portal is not production-ready: 2 screens are 100% hardcoded mock data, there is no authentication gate or login UI, 7 backend endpoints the frontend calls don't exist, `api.ts` has duplicate function definitions that will break the TypeScript build, and user feedback relies entirely on `alert()`/`prompt()` browser dialogs.

---

## Top 3 Wins

### 1. Merchants Screen — Real API with Full CRUD
`apps/admin/src/components/Merchants.tsx` is the most complete screen. It calls real backend endpoints (`searchMerchants`, `pauseMerchant`, `resumeMerchant`, `sendMerchantPortalLink`), has search with debounce, proper loading/error/empty states, and a reason dialog for pause/resume actions. This is the gold standard the other screens should match.

### 2. Overrides Screen — Emergency Controls with Confirmation Token
`apps/admin/src/components/Overrides.tsx` implements a proper emergency-pause flow requiring the operator to type `CONFIRM-EMERGENCY-PAUSE` before executing. Warning banners, reason requirements, and force-close with session ID validation are all present. This is exactly the level of friction admin override actions should have.

### 3. Logs Screen — Searchable Audit Trail with Pagination
`apps/admin/src/components/Logs.tsx` provides a searchable, filterable, paginated audit log with color-coded action types. It calls `getAdminLogs` with query params for search, filter, page, and limit. This is critical for production operations and compliance.

---

## Top 5 Gaps

### Gap 1: Dashboard is 100% Hardcoded Mock Data (CRITICAL)
**Files:** `apps/admin/src/components/Dashboard.tsx:3-70`
**Evidence:** Lines 3-32 define `const stats = [{ label: 'Active Merchants', value: '847' }, { label: 'Charging Locations', value: '1,243' }, ...]` — all static strings. Lines 34-63 define `const recentAlerts = [...]` with fixed timestamps. Lines 65-70 define `const recentActivity = [...]` — also static. Zero API calls in the entire component.
**Impact:** The dashboard is the first screen every admin sees. Showing fake data ("847 merchants", "312 active sessions") in production would destroy operator trust. The backend already has `GET /v1/admin/overview` returning real counts (`total_drivers`, `total_merchants`, `total_driver_nova`, etc.) — it just needs to be wired up.

### Gap 2: No Authentication Gate, No Login UI, No Logout
**Files:** `apps/admin/src/App.tsx` (no auth check), `apps/admin/src/components/Sidebar.tsx:54` (hardcoded email), `apps/admin/src/services/api.ts:210` (`adminLogin()` exists but no UI)
**Evidence:** `App.tsx` renders the dashboard immediately — no token check, no redirect to login. `Sidebar.tsx` line 54 shows `Operator: admin@nerava.com` hardcoded. `api.ts` has an `adminLogin(email, password)` function at line ~210 but there is no `Login.tsx` component. There is no logout button anywhere.
**Impact:** Any user who navigates to the admin URL gets full admin access. This is a security gap that must be closed before production. The backend already has `require_admin` dependency injection on all admin routes — the frontend just needs a login screen and token-gated routing.

### Gap 3: ChargingLocations is 100% Hardcoded Mock Data with No Backend
**Files:** `apps/admin/src/components/ChargingLocations.tsx:13-68`
**Evidence:** Lines 13-68 define `const mockLocations: ChargingLocation[] = [...]` with 6 static locations. The "View Details" button (line ~138) has no `onClick` handler. Zero API calls. Unlike Dashboard, there is **no backend endpoint** for listing charging locations — the endpoint would need to be created.
**Impact:** Admins cannot see real charger infrastructure status. This screen is entirely decorative. Either wire it to a real data source or remove it from navigation to avoid confusion.

### Gap 4: 7 Missing Backend Endpoints + Data Contract Mismatches
**Files:** `apps/admin/src/services/api.ts` (frontend calls), `backend/app/routers/admin_domain.py` (backend routes)
**Evidence — Missing endpoints the frontend calls that don't exist:**
1. `GET /v1/admin/sessions/active` — `ActiveSessions.tsx` calls `getActiveSessions()` but no such route exists in `admin_domain.py`
2. `POST /v1/admin/sessions/force-close` — `Overrides.tsx` calls `forceCloseSessions()` but no route exists
3. `POST /v1/admin/overrides/emergency-pause` — `Overrides.tsx` calls `emergencyPause()` but no route exists
4. `GET /v1/admin/logs` — `Logs.tsx` calls `getAdminLogs()` but backend has `/audit` not `/logs`
5. `POST /v1/admin/merchants/{id}/pause` — `Merchants.tsx` calls `pauseMerchant()` but no route exists (backend has `/merchants/{id}/status` which is different)
6. `POST /v1/admin/merchants/{id}/resume` — same issue as #5
7. `POST /v1/admin/merchants/{id}/send-portal-link` — no route exists

**Evidence — Data contract mismatches:**
- **Exclusives toggle:** Backend `POST /v1/admin/exclusives/{id}/toggle` expects `?enabled=true` query param; frontend sends POST body `{reason}`
- **Audit logs:** Backend returns `{actor_id, action, target_type, target_id, metadata}`; frontend expects `{operator_id, operator_email, action_type, reason, ip_address}`
- **Exclusives list:** Backend returns basic perk fields; frontend expects `{merchant_name, activations_today, activations_this_month, nova_reward}` which don't exist on the model

**Impact:** 4 of 8 screens (ActiveSessions, Overrides, Logs partially, Merchants partially) will fail with 404/422 errors in production. The screens appear to work in development only because error states are swallowed or fall back to empty arrays.

### Gap 5: api.ts Has Duplicate Function Definitions (Build Breaker) + Pervasive alert()/prompt()
**Files:** `apps/admin/src/services/api.ts:121-133,185-197`, plus `Merchants.tsx:45,51,54`, `Exclusives.tsx:41,52`, `Overrides.tsx:15,23,37,42,49`, `Deployments.tsx:42,45,48`
**Evidence — Duplicate functions:**
- `pauseMerchant` defined at lines ~121-126 AND lines ~185-190
- `resumeMerchant` defined at lines ~128-133 AND lines ~192-197
- This will cause a TypeScript compilation error (`Duplicate function implementation`)

**Evidence — alert()/prompt() usage:**
- `Merchants.tsx:45`: `const email = prompt('Enter merchant email address:')` — browser prompt for critical admin action
- `Overrides.tsx:15,23,37,42,49`: All success/error feedback via `alert()`
- `Deployments.tsx:42,45,48`: All deployment feedback via `alert()`
- `Exclusives.tsx:41,52`: Validation and error via `alert()`

**Impact:** The duplicate functions are a hard build error. The `alert()`/`prompt()` usage is an admin UX antipattern — these block the JS thread, can't be styled, provide no context, and are jarring in a professional admin tool. They should be replaced with toast notifications and modal dialogs.

---

## Production Readiness Verdict

**NOT SHIP-READY.** The admin portal has 3 blocking issues:

1. **No auth gate** — anyone can access all admin functions (security blocker)
2. **Duplicate function definitions in api.ts** — TypeScript build will fail (build blocker)
3. **7 missing backend endpoints** — 4 of 8 screens will 404 in production (functionality blocker)

The portal needs a focused implementation sprint to reach production readiness. The good news: the architecture is sound, the component patterns are consistent, and the backend already has many of the needed primitives (`require_admin`, `log_admin_action`, audit table). The gaps are integration work, not architectural rework.

---

## Cursor-Ready Implementation Plan

### Priority 1: Fix Build Breaker + Add Auth Gate

**Step 1: Remove duplicate functions in api.ts**
- **File:** `apps/admin/src/services/api.ts`
- **Action:** Delete the duplicate `pauseMerchant` (lines ~185-190) and `resumeMerchant` (lines ~192-197) definitions. Keep the first definitions (lines ~121-133).

**Step 2: Create Login screen**
- **File:** Create `apps/admin/src/components/Login.tsx`
- **Action:** Build a login form that calls the existing `adminLogin(email, password)` function from `api.ts`. On success, store the token in localStorage. On failure, show inline error. Use the same Tailwind styling as existing components.

**Step 3: Add auth gate to App.tsx**
- **File:** `apps/admin/src/App.tsx`
- **Action:** Check `localStorage.getItem('access_token')` on mount. If no token, render `<Login />`. If token exists, render the current dashboard layout. Add a `handleLogout` function that clears localStorage and resets to login.

**Step 4: Add logout to Sidebar**
- **File:** `apps/admin/src/components/Sidebar.tsx`
- **Action:** Replace hardcoded `admin@nerava.com` with the actual operator email (store in localStorage during login). Add a logout button that calls `handleLogout` passed as a prop.

### Priority 2: Wire Dashboard to Real Data

**Step 5: Connect Dashboard to /v1/admin/overview**
- **File:** `apps/admin/src/components/Dashboard.tsx`
- **Action:** Replace the hardcoded `stats` array with a `useEffect` that calls `fetchAPI('/v1/admin/overview')`. Map the response fields (`total_drivers`, `total_merchants`, etc.) to stat cards. Add loading and error states. For `recentAlerts` and `recentActivity`, either wire to the audit endpoint or remove them and show "Coming Soon".

### Priority 3: Add Missing Backend Endpoints

**Step 6: Add active sessions endpoint**
- **File:** `backend/app/routers/admin_domain.py`
- **Action:** Add `GET /v1/admin/sessions/active` that queries `ExclusiveSession` where `status='active'` and `expires_at > now()`. Return `{sessions: [...], total: int}`. Join with `User` and `MerchantPerk` for display names.

**Step 7: Add force-close and emergency-pause endpoints**
- **File:** `backend/app/routers/admin_domain.py`
- **Action:** Add `POST /v1/admin/sessions/force-close` accepting `{session_ids: string[], reason: string}`. Mark sessions as `force_closed`, log via `log_admin_action`. Add `POST /v1/admin/overrides/emergency-pause` accepting `{confirmation_token: string, reason: string}`. Validate token equals `CONFIRM-EMERGENCY-PAUSE`, then set all active exclusives to `is_active=false` and close all active sessions.

**Step 8: Align audit log endpoint with frontend contract**
- **File:** `backend/app/routers/admin_domain.py` (existing `/audit` endpoint)
- **Action:** Either rename to `/logs` to match frontend, or update `apps/admin/src/services/api.ts` to call `/audit`. Extend the response to include `operator_email` (join with User table on `actor_id`), `action_type` (alias for `action`), and `ip_address` (read from request headers). Update frontend types to match.

**Step 9: Add merchant pause/resume/portal-link endpoints**
- **File:** `backend/app/routers/admin_domain.py`
- **Action:** Add `POST /v1/admin/merchants/{id}/pause` and `/resume` that update a `is_paused` field on the merchant (or use existing status mechanism). Add `POST /v1/admin/merchants/{id}/send-portal-link` that generates a magic link and sends via email (or returns the link for manual sharing). Log all actions via `log_admin_action`.

### Priority 4: Replace alert()/prompt() with Proper UI

**Step 10: Add toast notification system**
- **File:** `apps/admin/src/App.tsx` + create `apps/admin/src/components/Toast.tsx`
- **Action:** Since Shadcn/ui is already installed (48+ components in `apps/admin/src/components/ui/`), use the existing `toast` component from Shadcn. Replace all `alert()` calls in Overrides, Deployments, Exclusives, and Merchants with `toast()` calls (success/error variants).

**Step 11: Replace prompt() with modal dialog**
- **File:** `apps/admin/src/components/Merchants.tsx`
- **Action:** Replace the `prompt('Enter merchant email address:')` on line 45 with a proper modal dialog using Shadcn's `Dialog` component. Include email validation and a cancel button.

### Priority 5: Handle ChargingLocations

**Step 12: Either wire or remove ChargingLocations**
- **File:** `apps/admin/src/components/ChargingLocations.tsx` + optionally `backend/app/routers/admin_domain.py`
- **Action (Option A — recommended):** Add `GET /v1/admin/charging-locations` endpoint that queries the charger table with status, location, and session count. Wire the frontend to this endpoint.
- **Action (Option B — faster):** Remove ChargingLocations from the Sidebar navigation and App.tsx routing until a real endpoint exists. This is honest — better than showing fake data.

---

## Score Path

| Action | Points |
|---|---|
| Current score | 5.5 |
| Fix build breaker (Step 1) | +0.3 |
| Add auth gate + login + logout (Steps 2-4) | +1.5 |
| Wire Dashboard to real API (Step 5) | +0.7 |
| Add missing backend endpoints (Steps 6-9) | +1.0 |
| Replace alert()/prompt() with toasts + modals (Steps 10-11) | +0.5 |
| Handle ChargingLocations (Step 12) | +0.5 |
| **Potential score** | **10.0** |

Completing Priorities 1-3 (Steps 1-9) would bring the score to **9.0** — ship-ready for internal operations. Priority 4-5 (Steps 10-12) are polish that can follow.
