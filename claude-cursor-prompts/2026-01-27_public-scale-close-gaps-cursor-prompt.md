# CURSOR PROMPT — CLOSE REMAINING PUBLIC‑SCALE GAPS

Context
- Validation found 2 P0 bugs, 3 P1 code gaps, and some manual infra tasks.
- Fix code gaps now. Do NOT touch manual infra steps.
- Keep changes surgical and backward‑compatible.
- ASCII only. No new dependencies.

Priority Order (do in order)
1) P0 fixes (build + correctness)
2) P1 code fixes (consent fields + demo values)
3) Add cookie consent banner (simple, no new deps)

## P0 FIXES

### P0‑1: Admin merchant list duplication
**File:** `backend/app/routers/admin_domain.py`
**Problem:** Merchant list appended twice.
**Fix:** Delete the duplicate append block.
- Remove lines that append a second identical dict to `merchant_list` (the block immediately after the first append).
- Keep only one append per merchant.

### P0‑2: Missing import in ActivateExclusiveModal
**File:** `apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx`
**Problem:** `identifyIfConsented()` used but not imported.
**Fix:** Update import line:
```ts
// BEFORE
import { capture, identify, DRIVER_EVENTS } from '../../analytics'

// AFTER
import { capture, identifyIfConsented, DRIVER_EVENTS } from '../../analytics'
```
- Ensure no unused imports remain.

## P1 CODE FIXES

### P1‑1: Consent model missing fields
**Files:**
- `backend/app/models/user_consent.py`
- New migration (next revision number)

**Model change:** add columns:
- `ip_address = Column(String, nullable=True)`
- `privacy_policy_version = Column(String, nullable=True)`

**Migration:** add the two columns to `user_consents` table.
- Use a new Alembic revision (do NOT reuse 059).
- Upgrade adds columns; downgrade drops them.

### P1‑2: Remove hardcoded demo IDs in intents
**File:** `backend/app/routers/intents.py`
**Problem:** `"demo-user-123"` used in multiple places.
**Fix:**
- Replace demo IDs with authenticated user from request state (or dependency).
- If no authenticated user is present and endpoint requires auth, return 401 with clear detail.
- Keep behavior for anonymous endpoints only if they are explicitly documented to allow it.

### P1‑3: Remove hardcoded demo IDs in activity
**File:** `backend/app/routers/activity.py`
**Problem:** `demo-user-1` through `demo-user-5` hardcoded.
**Fix:**
- Remove demo fallbacks.
- Require authenticated user; return 401 when missing.
- Ensure the response still works for real users.

## P1 FRONTEND COMPLIANCE UI

### Add cookie consent banner (simple)
**Scope:** Driver web + Merchant portal + Admin portal
- Implement a minimal consent banner with two buttons: “Accept analytics” and “Decline”.
- Store choice in `localStorage` as `consent_analytics=granted|denied`.
- If already set, do not show the banner.
- No new dependencies.

**Files / Locations:**
1) Driver web:
   - Add a new component `apps/driver/src/components/ConsentBanner.tsx`.
   - Render it once in the app shell (likely `apps/driver/src/App.tsx` or top‑level layout).

2) Merchant portal:
   - Add `apps/merchant/app/components/ConsentBanner.tsx`.
   - Render in `apps/merchant/app/App.tsx` just inside Router so it appears globally.

3) Admin portal:
   - Add `apps/admin/src/components/ConsentBanner.tsx`.
   - Render in `apps/admin/src/App.tsx` for global display.

**Behavior:**
- Banner appears bottom‑fixed, small, dismissible by choosing accept/decline.
- On accept, set `consent_analytics=granted`.
- On decline, set `consent_analytics=denied`.

**Style:** Use existing Tailwind patterns (neutral background, subtle shadow). Keep it minimal.

## VALIDATION
- Backend:
  - Run targeted tests: `cd backend && pytest tests/test_exclusive_sessions.py -q`
  - Run alembic upgrade on a DB with migration 059 already applied.
- Driver app:
  - `cd apps/driver && npx tsc --noEmit`
  - Confirm no unused import warnings.
- Manual:
  - Ensure no demo IDs remain in `intents.py` or `activity.py`.
  - Confirm banner appears when `consent_analytics` is unset and disappears after choice.

## OUTPUT
- Provide a concise summary of changes with file paths.
- List any remaining manual infra tasks (ECS scaling, Redis, RDS upgrade, alarms).
