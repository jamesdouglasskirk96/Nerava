# CURSOR PROMPT — CLOSE FINAL GAPS TO 10/10

Context
- Latest validation shows P0 is clear, but 2 P1 gaps remain for scale and several P2 polish items.
- Your task: implement ONLY what is needed to reach 10/10 public scale readiness.
- Keep changes surgical, backward‑compatible, ASCII only, no new dependencies.

## Targeted Gaps To Fix (in order)

### P1‑1: Fix SQLite‑specific check in intents.py
**File:** `backend/app/routers/intents.py`
**Problem:** Code checks `sqlite_master` which will fail on PostgreSQL.
**Fix (preferred):** Remove the sqlite_master check entirely if it was only for dev. If you must keep a table‑existence guard, use a try/except around the query or use SQLAlchemy inspector with existing connection.
**Acceptance:** No reference to `sqlite_master` remains; endpoint works on Postgres.

### P1‑2: Merchant claim verification stub
**File:** `apps/merchant/app/components/ClaimVerify.tsx`
**Problem:** Flow is a stub; merchants can’t complete claim in production.
**Fix:** Wire to real claim verify API flow (already present in backend):
- Use existing endpoints:
  - `POST /v1/merchant/claim/verify-phone` (OTP check)
  - `GET /v1/merchant/claim/verify-magic-link?token=...` (email magic link)
- Ensure the UI handles:
  - loading state
  - invalid/expired token
  - success → store JWT, merchant_id, businessClaimed in localStorage, navigate to `/overview`
- No new dependencies.

## P2 POLISH (Required to reach 10/10)

### P2‑1: Driver timer expiration recovery
**File:** `apps/driver/src/components/ExclusiveActiveView/ExclusiveActiveView.tsx` (or the countdown component)
**Fix:** When remaining time <= 0:
- Show “Your spot has expired” state
- Provide CTA “Find a New Spot” that clears active session state and navigates to discovery.

### P2‑2: Driver skeleton loading or empty state hint
**File:** `apps/driver/src/components/MerchantCarousel/*` or the main discovery screen
**Fix:** Add a minimal skeleton/empty state when results are loading or empty due to filters. No new deps.

### P2‑3: Admin merchant list pagination
**File:** `backend/app/routers/admin_domain.py` and `apps/admin/src/components/Merchants.tsx`
**Fix:**
- Backend: add `limit` and `offset` params to list endpoint and include total count.
- Frontend: add simple pagination controls (Prev/Next) using limit/offset.

### P2‑4: Make consent policy version configurable
**File:** `backend/app/routers/consent.py` and settings
**Fix:**
- Move `privacy_policy_version` to config: e.g., `PRIVACY_POLICY_VERSION` in settings/env.
- Use that value in grant/revoke instead of hardcoded "1.0".

### P2‑5: Replace hardcoded reputation defaults
**File:** `backend/app/routers/activity.py`
**Fix:**
- If no reputation row, return nulls or zeros with a clear `status: "new"` indicator; avoid fake stats.

### P2‑6: Landing page consent banner (if analytics enabled)
**File:** `apps/landing/app/components/` and layout
**Fix:**
- Add a minimal consent banner gated by `localStorage.consent_analytics` similar to other apps.
- Only render if PostHog is enabled; otherwise do not show.

### P2‑7: Accessibility for icon‑only buttons
**File:** `apps/driver/src/components/` (spot check key icon buttons)
**Fix:**
- Add `aria-label` to icon‑only buttons (close icons, share, back) in critical screens.
- Keep scope small: update top 5 most visible icon‑only buttons.

## Validation Checklist
- `backend/app/routers/intents.py` has no sqlite_master.
- Merchant claim flow completes using real API endpoints.
- Expired exclusive session shows recovery CTA.
- Admin merchant list paginates with total count.
- `PRIVACY_POLICY_VERSION` used in consent router.
- Activity endpoint returns non‑fake defaults.
- Landing page consent banner appears only when analytics enabled.
- Icon‑only buttons have aria-labels.

## Output
- Summarize changes with file paths.
- List any manual infra tasks still required (ECS scaling, Redis, RDS, alarms).
