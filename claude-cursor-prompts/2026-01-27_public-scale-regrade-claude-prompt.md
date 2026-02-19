# NERAVA PUBLIC SCALE REGRADE -- VALIDATION REPORT

**Date:** 2026-01-27
**Validator:** Claude Code (Opus 4.5)
**Role:** Independent validator (read-only verification against source code)
**Scope:** Phase 1 (Step 0) + Phase 2 (14 items) + Phase 3 (4 items) = 18 verifications
**Prior scores:** Application logic 9.0/10, Infrastructure 5.5/10, Compliance 3.5/10, Performance 6.0/10

---

## VALIDATION SUMMARY

| # | Change | Status | Evidence |
|---|--------|--------|----------|
| **Phase 1 (Step 0) -- Pre-existing** | | | |
| 0a | Exclusive activate idempotency | **PASS** | `backend/app/routers/exclusive.py:168-186` -- X-Idempotency-Key header extracted, checked, returned |
| 0b | Exclusive session idempotency_key persisted | **PASS** | `backend/app/routers/exclusive.py:330` -- `idempotency_key=idempotency_key` on new session |
| 0c | nova_transactions.idempotency_key unique | **PASS** | `backend/app/models/domain.py:241` -- `unique=True, index=True` |
| 0d | Stripe webhook atomic commit | **PASS** | `backend/app/services/stripe_service.py:248,265` -- single `db.commit()` after flush + grant |
| 0e | Intent service bounding-box query | **PASS** | `backend/app/services/intent_service.py:51-90` -- SQL Haversine + `.between()` pre-filter |
| 0f | Google Places API key from env | **PASS** | `backend/app/integrations/google_places_client.py` -- `os.getenv("GOOGLE_PLACES_API_KEY")` |
| 0g | Redis OTP rate limiting | **PASS** | `backend/app/services/auth/rate_limit.py:53-76` -- Redis sorted sets with fallback |
| 0h | Migrations 056/057/058 | **PASS** | 056: exclusive_sessions idempotency_key; 057: nova_transactions unique; 058: chargers spatial index |
| **Phase 2 -- Compliance + Resilience** | | | |
| 1 | Consent system (model + router + migration) | **PARTIAL** | Model at `backend/app/models/user_consent.py:11-34` -- functional but missing `ip_address` and `privacy_policy_version` columns. Router at `backend/app/routers/consent.py` with GET/grant/revoke. Migration 059 creates table with unique `(user_id, consent_type)` index. Registered in `__init__.py:66` and `main.py:191`. |
| 2 | PostHog consent gating | **PARTIAL** | `identifyIfConsented()` exists in all 3 analytics files (driver:163, merchant:154, admin:154). `ActivateExclusiveModal.tsx:142` calls `identifyIfConsented()` but line 6 imports `identify` not `identifyIfConsented` -- **missing import** will cause TypeScript compile error. |
| 3 | Account deletion with anonymization | **PASS** | `backend/app/routers/account.py:173-268` -- anonymizes email/phone/name, cascades refresh_tokens/vehicle_tokens/favorites/consents, anonymizes session/transaction references, audit logs via `log_admin_action()` |
| 4 | Account export endpoint | **PASS** | `backend/app/routers/account.py:44-170` -- returns real JSON: user, wallet, transactions, sessions, intents, consents. Not a placeholder. |
| 5 | Data retention job | **PASS** | `backend/app/jobs/data_retention.py` -- deletes intent_sessions (90d), otp_challenges (7d), claim_sessions (30d), vehicle_onboarding (1yr), merchant_cache (30d). Anonymizes exclusive_sessions locations >1yr. |
| 6 | Admin merchant N+1 fix | **FAIL** | `backend/app/routers/admin_domain.py:196-248` -- subquery join is correct (lines 198-210), but **merchant is appended to list TWICE** (lines 229-237 AND 238-246 are identical). Every merchant appears duplicated in the response. |
| 7 | Redis cache on admin overview | **PASS** | `backend/app/routers/admin_domain.py:128-174` -- `LayeredCache` with `cache.get()` / `cache.set(key, data, ttl=60)` |
| 8 | Duplicate /merchants route fix | **PASS** | `admin_domain.py:179` is `/merchants` (list); `admin_domain.py:655` is `/merchants/search`. `apps/admin/src/services/api.ts:98` calls `/v1/admin/merchants/search`. |
| 9 | Remove alert() in Exclusives | **PASS** | `apps/admin/src/components/Exclusives.tsx:42` -- `setFeedback({ type: 'error', message: '...' })`. Line 53 -- `setFeedback({ type: 'success', message: '...' })`. Line 60 -- `setFeedback({ type: 'error', message: errorMessage })`. Zero `alert()` calls remain. |
| 10 | Google Places resilience | **PASS** | `backend/app/integrations/google_places_client.py` -- CircuitBreaker (lines 22-87), stale-while-revalidate with `allow_expired=True` (lines 172-178, 278-282), request coalescing via per-geo-cell locks (lines 30-49, 182-192). |
| 11 | Replace bare excepts | **PASS** | `admin_domain.py` -- all `except` clauses now use specific types (`ValueError`, `Exception as e`) with structured logging. `exclusive.py` -- same pattern. No bare `except:` remains in verified locations. |
| **Phase 3 -- Hardening** | | | |
| 12 | p95 latency instrumentation | **PASS** | `backend/app/middleware/metrics.py:10-18` -- Histogram for critical endpoints (otp/verify, exclusive/activate, exclusive/complete, intent/capture, merchants/nearby, verify-visit). P95 calculated via sorted percentile. |
| 13 | Remove hardcoded demo values | **PARTIAL** | `bootstrap.py` PASS -- requires `BOOTSTRAP_KEY` env var, no default. `intents.py` **FAIL** -- `"demo-user-123"` hardcoded on line 23 (and 5 more locations). `activity.py` **FAIL** -- `demo-user-1` through `demo-user-5` on lines 67-108. |
| 14 | Stripe SDK async wrapping | **PASS** | `backend/app/services/stripe_service.py` -- `asyncio.to_thread()` wraps `create_checkout_session` (lines 32-54), `handle_webhook` (lines 138-163), `reconcile_payment` (lines 286-301). |
| 15 | System-wide kill switch | **PASS** | `admin_domain.py:1555-1615` -- `/system/pause` and `/system/resume` endpoints set/delete Redis key. `middleware/auth.py:34-45,82-93` -- `_is_system_paused()` checks Redis; returns 503 for non-admin, non-health paths. |

---

## PASS/FAIL SUMMARY

**18 items verified:**
- **PASS:** 14 (78%)
- **PARTIAL PASS:** 3 (17%) -- consent model missing 2 fields; PostHog import bug; demo values 2/3 not fixed
- **FAIL:** 1 (5%) -- N+1 fix duplicates merchants in response

---

## BUGS FOUND

### BUG 1 (P0): Admin merchant list duplicates every merchant

**File:** `backend/app/routers/admin_domain.py:229-246`

Lines 229-237 append a merchant dict to `merchant_list`. Lines 238-246 append the **exact same dict** again. This doubles every merchant in the admin merchant list response.

**Fix:** Delete lines 238-246 (the duplicate `.append()` block).

### BUG 2 (P1): ActivateExclusiveModal missing import

**File:** `apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx:6`

Line 6 imports `{ capture, identify, DRIVER_EVENTS }` but line 142 calls `identifyIfConsented()`. The function is exported from `../../analytics` but not imported here. This will cause a TypeScript compile error (`ReferenceError: identifyIfConsented is not defined`).

**Fix:** Change line 6 to: `import { capture, identifyIfConsented, DRIVER_EVENTS } from '../../analytics'`

### BUG 3 (P2): Consent model missing fields

**File:** `backend/app/models/user_consent.py`

Missing `ip_address` (String) and `privacy_policy_version` (String) columns. These were specified in the plan for GDPR audit trail but not implemented by Cursor.

**Fix:** Add columns and include in next migration.

---

## COMPONENT SCORECARDS

### 1. iOS App (Shell): 8.0 / 10 (unchanged)

- No Phase 2/3 changes targeted iOS
- Production push entitlement is correct (`Nerava.entitlements`)
- 7-state session engine, NativeBridge, crash recovery all solid
- **Remaining:** Force-unwrapped optional in `APIClient.swift:13`, silent `try?` failures

### 2. Driver Web App: 9.0 -> 9.3 / 10

- **PASS:** `identifyIfConsented()` function exists in analytics layer (line 163)
- **PASS:** `ActivateExclusiveModal.tsx:142` uses `identifyIfConsented()` (consent-gated)
- **PARTIAL:** Import on line 6 is `identify` not `identifyIfConsented` -- compile error
- **Remaining:** Skeleton loading states, accessibility aria-labels, import fix needed

### 3. Merchant Portal: 8.5 -> 8.7 / 10

- **PASS:** `identifyIfConsented()` added to `apps/merchant/app/analytics/index.ts:154`
- **PASS:** Consent check via localStorage + API fallback (lines 86-121)
- **Remaining:** Coming-soon screens, no merchant-side consent UI

### 4. Admin Portal: 9.2 -> 9.6 / 10

- **PASS:** `Exclusives.tsx` alert() fully replaced with `setFeedback()` (lines 42, 53, 60)
- **PASS:** `/merchants/search` route separated; `api.ts:98` updated
- **PASS:** Consent gating in admin analytics (lines 154-163)
- **Remaining:** JWT refresh/expiry handling

### 5. Backend: 9.3 -> 9.5 / 10

- **PASS (13 items):** Consent system, account deletion/export, retention job, Redis cache, circuit breaker, stale-while-revalidate, request coalescing, bare excepts fixed, idempotency, atomic Stripe, bounding-box query, kill switch, p95 metrics, Stripe async
- **FAIL (1 item):** Merchant list duplicates every entry (lines 238-246)
- **PARTIAL (1 item):** Demo values in `intents.py` and `activity.py` not removed
- **Remaining:** N+1 duplicate bug fix (1 line), demo value cleanup (2 files), consent model field additions

### 6. Landing Page: 8.5 / 10 (unchanged)

- No Phase 2/3 changes targeted landing page
- HTTPS CTAs and mobile redirect banner remain correct
- **Remaining:** App Store / universal link support

---

## CROSS-CUTTING SCORES

### Infrastructure: 5.5 -> 7.0 / 10

**Evidence:**
- Code now supports Redis-backed rate limiting (`rate_limit.py:53-76`) and caching (`admin_domain.py:128`)
- Kill switch requires Redis (`middleware/auth.py:34-45`)
- Bounding-box query reduces DB load (`intent_service.py:66-83`)
- Composite spatial index added (migration 058)

**Still needed (manual):** Scale ECS to 2-3 tasks, enable Redis in prod, upgrade RDS to t3.small, add CloudWatch alarms

### Compliance: 3.5 -> 7.5 / 10

**Evidence:**
- `user_consents` table exists with unique `(user_id, consent_type)` constraint (migration 059)
- Consent API: GET + grant + revoke (`backend/app/routers/consent.py`)
- PostHog `identifyIfConsented()` gates PII behind consent
- Account deletion anonymizes PII, cascades related data (`account.py:173-268`)
- Account export returns real data (`account.py:44-170`)
- Data retention job cleans old data + anonymizes old locations (`jobs/data_retention.py`)
- Audit logging on deletion (`log_admin_action()`)

**Still needed:** Consent model missing `ip_address`/`privacy_policy_version` fields; no cookie consent banner on frontend; no "Do Not Sell" CCPA mechanism

### Performance: 6.0 -> 8.5 / 10

**Evidence:**
- Intent service uses SQL bounding-box query (intent_service.py:51-90) instead of all-in-memory
- Admin overview cached with 60s Redis TTL (admin_domain.py:128-174)
- Merchant N+1 query converted to subquery join (admin_domain.py:196-210) -- correct pattern, but response duplicated (bug)
- Google Places circuit breaker prevents cascading failures (google_places_client.py:22-87)
- Stripe calls run in executor thread (stripe_service.py:32-54)
- Composite index on chargers(is_public, lat, lng) for spatial queries (migration 058)
- p95 latency instrumentation on 6 critical endpoints (metrics.py:10-18)

**Still needed:** Fix N+1 duplicate bug; nearby merchant bounding-box pre-filter (P2); eager loading patterns across codebase

---

## REMAINING GAPS

### P0 -- Fix Before Ship (2 items)

| # | Component | Issue | Fix |
|---|-----------|-------|-----|
| 1 | Backend: admin_domain.py:238-246 | Merchant list duplicates every entry | Delete lines 238-246 (duplicate `.append()` block) |
| 2 | Driver: ActivateExclusiveModal.tsx:6 | Missing `identifyIfConsented` import | Change import to `{ capture, identifyIfConsented, DRIVER_EVENTS }` |

### P1 -- Fix Before Broad Growth (5 items)

| # | Component | Issue |
|---|-----------|-------|
| 1 | Backend: intents.py:23 | `"demo-user-123"` hardcoded in 6 locations |
| 2 | Backend: activity.py:67-108 | `demo-user-1` through `demo-user-5` fallback data |
| 3 | Backend: user_consent.py | Missing `ip_address` and `privacy_policy_version` columns |
| 4 | Infra (manual) | Scale ECS to 2-3 tasks, enable Redis, upgrade RDS |
| 5 | Frontend | No cookie consent banner or CCPA "Do Not Sell" mechanism |

### P2 -- Post-Launch (4 items)

| # | Component | Issue |
|---|-----------|-------|
| 1 | iOS | Force-unwrapped optional in APIClient.swift:13 |
| 2 | Driver | No skeleton loading states or accessibility aria-labels |
| 3 | Backend | Systemic N+1 across all relationship queries (no eager loading) |
| 4 | Admin | No JWT refresh/expiry handling |

---

## FINAL SCORECARD

| Component | Previous | New | Delta |
|-----------|----------|-----|-------|
| Admin Portal | 9.2 | 9.6 | +0.4 |
| Backend | 9.3 | 9.5 | +0.2 |
| Driver Web App | 9.0 | 9.3 | +0.3 |
| Merchant Portal | 8.5 | 8.7 | +0.2 |
| Landing Page | 8.5 | 8.5 | 0.0 |
| iOS App (Shell) | 8.0 | 8.0 | 0.0 |
| **Application Logic** | **9.0** | **9.2** | **+0.2** |

| Cross-Cutting | Previous | New | Delta |
|---------------|----------|-----|-------|
| Infrastructure | 5.5 | 7.0 | +1.5 |
| Compliance | 3.5 | 7.5 | +4.0 |
| Performance | 6.0 | 8.5 | +2.5 |

| Composite | Score |
|-----------|-------|
| Application logic (weighted) | 9.2 / 10 |
| Infrastructure readiness | 7.0 / 10 |
| Compliance readiness | 7.5 / 10 |
| Performance readiness | 8.5 / 10 |
| **Public Scale Composite** | **8.3 / 10** |

---

## SHIP VERDICT

**Ship-ready for pilot. Approaching public-scale readiness.**

The 2 P0 bugs are trivial (1 deleted duplicate block, 1 import fix). After those, the application logic is at 9.5+/10. The compliance gap has narrowed dramatically (3.5 -> 7.5) with consent management, deletion, export, and retention all implemented. Performance is strong with the bounding-box query and Redis caching.

**What blocks true 10/10 public scale:**
1. Infrastructure manual steps (ECS 2-3 tasks, Redis enabled, RDS upgrade) -- can be done in a day
2. Demo value cleanup in intents.py and activity.py -- 2 files, straightforward
3. Consent model field additions (ip_address, privacy_policy_version) -- 1 migration
4. Cookie consent banner on frontend -- new component needed
5. N+1 duplicate fix -- delete 8 lines

After these 5 items + the infra manual steps, the system reaches public-scale 10/10.

---

*Report generated by Claude Code (Opus 4.5) on 2026-01-27. All findings verified against source code with file paths and line numbers.*
