# Nerava Actionable Audit Report

**Date:** 2026-02-25
**Scope:** Full monorepo — backend, driver app, iOS, infrastructure
**Mode:** Read-only analysis (no code changes made)

---

## Executive Summary

Five deep analyses were run in parallel across the codebase: security, test coverage, performance, technical debt, and production readiness. Below is a unified, prioritized punch list of everything found — organized by urgency so we can start knocking items out immediately.

**By the numbers:**
- **4 CRITICAL** items that could cause real money loss or security breaches
- **19 HIGH** items affecting security, reliability, or user experience
- **23 MEDIUM** items for stability and maintainability
- **11 LOW** items for cleanup

---

## TIER 1: FIX NOW (Critical — same day)

These items risk real money loss, security breaches, or complete feature breakage.

### 1. Registration endpoint allows admin role self-assignment
- **Source:** Security Audit
- **File:** `backend/app/routers/auth_domain.py:98-102`
- **Issue:** Any unauthenticated user can register with `{"role": "admin"}` and gain full admin access — Nova grants, merchant management, wallet adjustments, system pause.
- **Fix:** Remove `role` from `RegisterRequest` or hardcode it to `"driver"` server-side.
- **Effort:** 15 minutes

### 2. Wallet balance has no database constraint; withdrawals have no row locking
- **Source:** Production Readiness
- **File:** `backend/app/models/driver_wallet.py`, `backend/app/services/payout_service.py:274-317`
- **Issue:** No `CHECK (balance_cents >= 0)` constraint. No `SELECT ... FOR UPDATE` on wallet row during withdrawal. Two concurrent withdrawals can both pass the balance check and double-payout real money via Stripe.
- **Fix:** Add `CheckConstraint`, add `.with_for_update()` on wallet read in `request_withdrawal`.
- **Effort:** 3-5 hours

### 3. CORS origin reflection in exception handlers bypasses all CORS rules
- **Source:** Security Audit
- **File:** `backend/app/main_simple.py:1293-1382`
- **Issue:** Global exception handlers reflect the request `Origin` header directly in `Access-Control-Allow-Origin`, allowing ANY origin to make credentialed cross-origin requests when errors occur.
- **Fix:** Remove manual CORS headers from exception handlers. Let CORSMiddleware handle it.
- **Effort:** 30 minutes

### 4. Tesla OAuth states stored in-memory (lost on every deploy)
- **Source:** Production Readiness + Security Audit
- **File:** `backend/app/routers/tesla_auth.py:40`
- **Issue:** `_oauth_states: dict = {}` — lost on every App Runner restart/deploy. Users mid-Tesla-connect get "Invalid or expired state" errors. Dict also grows unbounded.
- **Fix:** Move to Redis with 10-minute TTL (Redis is already configured).
- **Effort:** 1-2 hours

---

## TIER 2: FIX THIS WEEK (High — before real user traffic)

### Security

| # | Issue | File | Fix | Effort |
|---|-------|------|-----|--------|
| 5 | Payout endpoint lacks user-scoped auth — any user can create payouts for any `user_id` | `backend/app/routers/stripe_api.py:34-37` | Add `Depends(get_current_user)`, verify `request.user_id == current_user.id` | 1h |
| 6 | Hardcoded ops API key in source | `backend/app/main_simple.py:1179` | Move to env var or use `require_admin` | 15min |
| 7 | Google Places API key hardcoded in scripts | `backend/scripts/find_walkable_merchants.py:16` + 2 others | Replace with `os.environ["GOOGLE_PLACES_API_KEY"]`, rotate key | 30min |
| 8 | Webhook fake_event endpoint has no auth | `backend/app/routers/webhooks.py:12` | Gate behind `require_admin` or `ENV != "prod"` | 15min |
| 9 | Debug endpoints conditionally accessible in prod | `backend/app/routers/debug_verify.py:11-20` | Only register when `ENV != "prod"` | 15min |
| 10 | Tesla OAuth tokens stored as plaintext in DB | `backend/app/models/tesla_connection.py:25-27` | Encrypt with `TOKEN_ENCRYPTION_KEY` (Fernet) | 4-8h |
| 11 | CORS regex allows any Vercel deployment | `backend/app/main_simple.py:953` | Restrict to `nerava-.*\.vercel\.app` | 15min |
| 12 | Driver wallet webhook accepts empty signature | `backend/app/routers/driver_wallet.py:108-123` | Require valid signature in non-local envs | 30min |

### Observability & Error Handling

| # | Issue | File | Fix | Effort |
|---|-------|------|-----|--------|
| 13 | No React Error Boundary in driver app | `apps/driver/src/App.tsx` | Add `<ErrorBoundary>` wrapping `<Routes>` | 2h |
| 14 | No Sentry in driver app frontend | `apps/driver/src/` | Install `@sentry/react`, init in `main.tsx` | 2h |
| 15 | Backend error messages leak internal details | `backend/app/routers/driver_wallet.py:41,55,71` + auth_domain + tesla_auth | Return generic messages in prod, log details server-side | 4h |
| 16 | No alerting for payment/Tesla/OTP failures | CloudWatch | Add metric filters + alarms for Stripe/Tesla/OTP errors | 4-6h |

### Data Integrity & Edge Cases

| # | Issue | File | Fix | Effort |
|---|-------|------|-----|--------|
| 17 | No Pydantic validation on withdrawal amount (zero/negative/huge) | `backend/app/routers/driver_wallet.py:18-19` | Add `Field(gt=0, le=100000)` | 15min |
| 18 | Tesla token refresh conflates revocation vs transient failure | `backend/app/services/tesla_oauth.py:364` | Return different errors for 401 vs 500/timeout from Tesla | 2-3h |
| 19 | Feature flag toggles are no-ops in production | `backend/app/routers/flags.py:161` | Store overrides in Redis/DB | 4-8h |
| 20 | Silent logout when refresh token expires — no user notification | `apps/driver/src/services/api.ts` | Add "Session expired" modal with re-login option | 3-5h |
| 21 | No rollback procedure documented | CLAUDE.md | Add rollback script + docs | 2h |
| 22 | Verify `ENABLE_STRIPE_PAYOUTS=true` is set in prod | App Runner env | Already set ✓ — add startup validation warning if Stripe key set but flag false | 30min |
| 23 | Stripe onboarding abandoned = stuck state | `apps/driver/src/components/Wallet/WalletModal.tsx` | Show "Complete setup" button when `stripe_onboarding_complete=false` with account ID present | 2-4h |

---

## TIER 3: FIX WITHIN 2 WEEKS (Medium)

### Performance (High-Impact)

| # | Issue | Impact | Fix | Effort |
|---|-------|--------|-----|--------|
| 24 | Full table scan for nearest charger — loads ALL chargers into Python | 10-100x slower | Use SQL haversine with bounding box (already exists in `intent_service.py`) | 2h |
| 25 | N+1 queries in `_get_nearby_merchants` | 5x more DB queries | Replace with JOIN query | 1h |
| 26 | No code splitting — all routes eagerly loaded (731KB bundle) | 15-25% bundle bloat | `React.lazy()` for all routes except DriverHome | 2h |
| 27 | Blanket `invalidateQueries()` on foreground return — 7+ concurrent refetches | Thundering herd | Only invalidate stale-sensitive queries | 1h |
| 28 | 1-second auth check interval (60 state updates/min) | Wasted CPU | Replace with `storage` event listener | 30min |
| 29 | 80+ router imports at startup (20 are stubs) | 2-5s cold start | Remove stub routers or lazy-load | 4h |
| 30 | posthog-js blocks initial render (45KB) | Slower TTI | Dynamic import after first paint | 1h |
| 31 | In-memory rate limiter + cache dicts grow unbounded | Memory leak | Use `cachetools.TTLCache` with maxsize | 1h |

### Security (Medium)

| # | Issue | Fix | Effort |
|---|-------|-----|--------|
| 32 | Registration/login rate limit too loose (10/min) | Add `/v1/auth/otp/start` at 3/min, `/v1/auth/register` at 3/min | 30min |
| 33 | Critical endpoints exempted from rate limiting | Apply higher but non-zero limits (120/min) | 30min |
| 34 | JWT tokens lack audience/issuer claims | Add `iss: "nerava"` + `aud` claims | 2h |
| 35 | Email addresses logged in auth flows | Log email domain only for failures, user ID for successes | 1h |
| 36 | No password strength validation | Add `Field(min_length=8)` to `RegisterRequest.password` | 15min |
| 37 | Admin credit endpoint lacks audit trail | Add structured audit logging, max single-credit limit | 4h |

### Technical Debt (Quick Wins)

| # | Issue | Fix | Effort |
|---|-------|-----|--------|
| 38 | `main.py` (legacy) still exists, diverged from `main_simple.py` | Delete `main.py` | 5min |
| 39 | `backups/` directory in repo (1.1GB) | Add to `.gitignore`, remove from tracking | 5min |
| 40 | Legacy `ui-mobile/` directory (63MB) + static-serving code | Remove directory + remove serving code from `main_simple.py` | 30min |
| 41 | `apps/console` and `Nerava-Campaign-Portal` are near-identical copies | Keep one, delete the other | 1h |
| 42 | Unpinned `posthog` in requirements.txt | Add to `requirements.in` with pin, re-run `pip-compile` | 5min |
| 43 | Duplicate `os` import + duplicate inline imports in main_simple.py | Deduplicate | 5min |
| 44 | 96 console.log statements in production driver app | Gate behind `import.meta.env.DEV` | 1h |

---

## TIER 4: BACKLOG (Low / Longer-term)

### Technical Debt (Larger Refactors)

| # | Issue | Effort |
|---|-------|--------|
| 45 | Remove 20 stub scaffold services/routers/models | 4h |
| 46 | Remove deprecated pilot router + related files (2,000+ lines) | 2h |
| 47 | Consolidate 123 router files to ~40 | 2-3 days |
| 48 | Extract `main_simple.py` (1,474 lines) into focused modules | 4h |
| 49 | Remove 20 scaffold models from `extra.py` + consolidate overlaps | 4h |
| 50 | Create shared `@nerava/api-client` package | 2 days |
| 51 | Create shared `@nerava/ui` package for Radix components | 2 days |
| 52 | Align React/TS/Vite versions across apps | 2 days |
| 53 | Migrate from `python-jose` to `PyJWT` exclusively | 4h |
| 54 | Fix hardcoded localhost URLs in backend services | 2h |

### Test Coverage (Critical Gaps)

| # | Module | Priority | Effort |
|---|--------|----------|--------|
| 55 | `incentive_engine.py` — rule matching, grant creation, budget decrement | CRITICAL | 2-4 days |
| 56 | `campaign_service.py` — CRUD, status transitions, caps, clawback | CRITICAL | 2-4 days |
| 57 | `tesla_oauth.py` — OAuth flow, verify_charging, retry logic | CRITICAL | 2-4 days |
| 58 | `session_event_service.py` — session lifecycle, Tesla polling | CRITICAL | 2-4 days |
| 59 | `stripe_service.py` — checkout, webhook handling, reconciliation | CRITICAL | 4-7 days |
| 60 | `payout_service.py` — Express accounts, transfers, webhooks | CRITICAL | 2-3 days |
| 61 | Driver `auth.ts` + `api.ts` — token refresh, 401 retry, OTP flow | CRITICAL | 2-3 days |
| 62 | `WalletModal.tsx` — Stripe onboarding, withdrawal states | CRITICAL | 1-2 days |
| 63 | `useSessionPolling.ts` — polling lifecycle, incentive detection | CRITICAL | 1-2 days |
| 64 | `LoginModal.tsx` — OTP + Apple/Google/Tesla sign-in | CRITICAL | 1-2 days |
| 65 | E2E: Tesla login → vehicle select → charging → incentive | CRITICAL | 3-5 days |

### Performance (Lower Impact)

| # | Issue | Fix |
|---|-------|-----|
| 66 | Per-merchant cache check creates N queries in intent_service | Batch into single query |
| 67 | Missing index on `Charger.is_public` | Add composite index |
| 68 | Schema introspection on every Nova redemption | Cache column existence check |
| 69 | Missing `staleTime` on several React Query hooks | Add appropriate values |
| 70 | Raw `fetch()` for EV codes bypasses React Query | Convert to `useQuery` |
| 71 | No cross-instance intent capture cache | Add Redis-based caching |
| 72 | No location check caching for stationary users | Add server-side cache |

---

## Credential Rotation Reminder

**The following credentials were exposed in conversation and MUST be rotated:**

- [ ] Stripe Secret Key (`sk_live_...`)
- [ ] Stripe Webhook Secrets (both `whsec_...` values)
- [ ] JWT Secret
- [ ] Database password
- [ ] Twilio Auth Token
- [ ] SendGrid API Key
- [ ] Google Places API Key (also hardcoded in 3 scripts)
- [ ] HubSpot Private App Token
- [ ] Tesla Client ID / Client Secret
- [ ] Ops API Key (`nrv-seed-8f3a2c7d9e1b`)

**After rotating:** Update App Runner env vars (read existing first, merge new values).

---

## Recommended Sprint Plan

**Day 1 (Today):** Items 1-4 (Critical tier) + Items 6-9, 11, 17, 22 (quick HIGH wins)
**Days 2-3:** Items 5, 10, 12-16, 18 (security + observability)
**Days 4-5:** Items 20-23 (edge cases) + Items 24-28 (performance quick wins)
**Week 2:** Items 29-44 (medium tier cleanup)
**Week 3+:** Items 45-72 (backlog)
