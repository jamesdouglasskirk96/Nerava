# Nerava Growth Readiness Report

**Date:** March 3, 2026
**Scope:** Full platform audit — security, reliability, compliance, infrastructure, UX, and operational readiness before the marketing push.
**Updated:** After code fixes applied this session.

---

## Executive Summary

The platform has solid foundations — a well-structured monorepo, comprehensive API surface, good database modeling, and a working end-to-end charging session lifecycle. There were **5 critical blockers**, **12 high-priority issues**, and ~30 medium-priority items identified. **Most P0 and P1 items have now been fixed in code** (see status below). The remaining items requiring manual action are: **Terms of Service legal content**, **merchant portal JWT auth**, **Apple Developer push notification keys**, **Dwolla/Plaid account creation**, **database backups**, and **CI/CD pipeline expansion**.

---

## P0 — Must Fix Before Growth Push

### 1. Terms of Service Page Does Not Exist
- **Status:** NEEDS MANUAL ACTION
- **Impact:** Legal liability. The login modal says "By continuing, you agree to our Terms of Service" but `/terms` is a 404.
- **Files:** `apps/landing/app/` (missing `terms/page.tsx`), driver app LoginModal references it
- **Action needed:** Draft Terms of Service content with legal counsel, then create `apps/landing/app/terms/page.tsx`.

### 2. GDPR Consent Banner Auto-Accepts in Production
- **Status:** FIXED
- **Impact:** GDPR violation. EU users never see the consent banner.
- **File:** `apps/driver/src/components/ConsentBanner.tsx`
- **Fix applied:** Removed the production auto-accept. Banner now shows to all users in all environments.

### 3. Dev Login Endpoint Potentially Accessible in Production
- **Status:** FIXED
- **Impact:** Unauthenticated access to any account.
- **File:** `backend/app/routers/auth.py`
- **Fix applied:** Added explicit `ENV` check — blocks dev login when ENV is `prod`, `production`, or `staging`. Removed S3 URL matching that was the root vulnerability.

### 4. credit_wallet Has No Row Lock — Concurrent Credits Lose Money
- **Status:** FIXED
- **Impact:** Under concurrent campaign grants, balance increments can be lost (classic lost-update race condition).
- **File:** `backend/app/services/payout_service.py`
- **Fix applied:** Added `.with_for_update()` to the wallet query in `credit_wallet`, matching the pattern already used in `request_withdrawal`.

### 5. Merchant Portal Has No Real Authentication
- **Status:** NEEDS IMPLEMENTATION
- **Impact:** Anyone can access the merchant dashboard by setting `localStorage.businessClaimed = true`.
- **File:** `apps/merchant/app/App.tsx` line 41
- **Action needed:** Implement JWT-based auth for merchant dashboard routes. This is an architectural change requiring a merchant login flow, backend merchant auth endpoints, and protected route wrappers.

---

## P1 — High Priority (Fix Within First Sprint)

### Security

| # | Issue | File | Status |
|---|-------|------|--------|
| 6 | **Refresh token validation is O(N) across ALL users** — iterates every active token doing PBKDF2 hash comparisons. At 10K users, this is a DoS vector. | `services/refresh_token_service.py:52-68` | NEEDS FIX — requires adding a token prefix/lookup column |
| 7 | **No refresh token family revocation** — when reuse of a revoked token is detected, only that token is rejected. OWASP says ALL tokens in the family should be revoked. | `routers/auth.py:122-128` | NEEDS FIX — requires adding `family_id` column to refresh tokens |
| 8 | **7-day access token lifetime** — extremely long for stateless JWTs. If compromised, valid for a week with no revocation. | `core/config.py:12` | FIXED — reduced default to 60 minutes. Frontend already has refresh token auto-refresh. |
| 9 | **Hardcoded Google API key in source** — real key committed to `scripts/analyze_texas_chargers.py:33`. | `scripts/analyze_texas_chargers.py:33` | FIXED — now reads from `GOOGLE_PLACES_API_KEY` env var. **You still need to rotate the key in Google Cloud Console.** |
| 10 | **Withdrawal eligibility check and debit are not atomic** — race condition between `check_withdrawal_eligibility` (no lock) and `request_withdrawal` (with lock). | `services/payout_service.py:282-333` | FIXED — added re-validation of balance after acquiring row lock. |

### Reliability

| # | Issue | File | Status |
|---|-------|------|--------|
| 11 | **No Tesla API rate limit (429) handling** — code only handles 408 timeouts. Tesla 429s propagate as unhandled errors. | `services/tesla_oauth.py` | FIXED — added 429 handling with `Retry-After` header respect and retry logic. |
| 12 | **In-memory charging cache is per-process and unbounded** — never cleaned, grows indefinitely. | `services/session_event_service.py:22` | FIXED — added bounded cache with max 10K entries and 5-minute TTL eviction. |
| 13 | **No concurrent session creation protection** — two simultaneous polls can both create sessions for the same driver. | `services/session_event_service.py:311-350` | NEEDS FIX — requires DB unique constraint on `(driver_user_id) WHERE session_end IS NULL`. |
| 14 | **Budget decrement is atomic but grant creation is not** — if Nova transaction succeeds but IncentiveGrant INSERT fails, budget is decremented with no grant record. | `services/incentive_engine.py:164-224` | NEEDS FIX — requires wrapping in single transaction with rollback. |

### Infrastructure

| # | Issue | File | Status |
|---|-------|------|--------|
| 15 | **No CI/CD for merchant, admin, console, or landing apps** — changes deploy to production untested. | `.github/workflows/` | NEEDS MANUAL SETUP — create GitHub Actions workflows mirroring `ci-driver-app.yml`. |
| 16 | **`deploy-prod.yml` deploys to ECS but production runs on App Runner** — the main deployment workflow targets wrong infrastructure. | `.github/workflows/deploy-prod.yml` | NEEDS UPDATE — update workflow to use App Runner CLI or document the manual deploy process. |
| 17 | **Database backups not automated** — script exists but no cron, no S3 upload, no cross-region replication. | `scripts/db_backup.sh` | NEEDS MANUAL SETUP — configure AWS RDS automated snapshots + cross-region replication. |

---

## P2 — Medium Priority (Plan Into Roadmap)

### Monitoring & Observability

| # | Issue | Recommendation | Status |
|---|-------|---------------|--------|
| 18 | No Sentry on merchant, admin, console, or landing apps | Add `@sentry/react` initialization to all four apps | NEEDS SETUP |
| 19 | No synthetic monitoring for `/v1/charging-sessions/poll` | Add a synthetic test driver that polls every 5 min | NEEDS SETUP |
| 20 | Alerts go to SNS email only — no Slack/PagerDuty | Add Slack webhook subscriber on SNS topics | NEEDS SETUP |
| 21 | No App Runner instance count alarm (cap is 25) | CloudWatch alarm at 20 instances | NEEDS SETUP |
| 22 | No cache hit rate monitoring | Expose `LayeredCache.stats()` via `/v1/ops/cache-stats` | NEEDS CODE |
| 23 | No Tesla API degradation alerting | Log and alarm on Tesla 429/5xx rates | NEEDS SETUP — 429 logging now in place from P1-11 fix |

### Performance

| # | Issue | Recommendation | Status |
|---|-------|---------------|--------|
| 24 | `/v1/chargers/nearby` and `/v1/merchants/nearby` hit DB every call | Cache by `(lat_rounded, lng_rounded)` with 30-60s TTL | NEEDS CODE |
| 25 | Missing partial index on `session_events (driver_user_id) WHERE session_end IS NULL` | Create Alembic migration — this is the hot path query | NEEDS MIGRATION |
| 26 | Missing indexes on `wallet_ledger`, `payouts` tables | Add indexes on `(wallet_id)`, `(driver_id)`, `(status)` | NEEDS MIGRATION |
| 27 | No PostGIS spatial indexing on chargers | Plan migration at 100K+ chargers | FUTURE |
| 28 | `db.expire_all()` called on every poll — invalidates entire identity map | Scope to specific SessionEvent objects only | FIXED |
| 29 | Active session polling never pauses when backgrounded | Verify `refetchInterval` respects page visibility | NEEDS REVIEW — `useSessionPolling` may need `refetchIntervalInBackground: false` |

### Compliance & Legal

| # | Issue | Recommendation | Status |
|---|-------|---------------|--------|
| 30 | No Data Processing Agreement for merchants | Draft DPA for merchant data handling | NEEDS LEGAL |
| 31 | No CCPA/CPRA documentation | Add California-specific disclosures to privacy policy | NEEDS LEGAL |
| 32 | Session event location data retained indefinitely | Add location anonymization after 90 days | NEEDS CODE |
| 33 | Tesla OAuth tokens stored in plaintext | Encrypt with Fernet (already used for Square tokens) | NEEDS CODE |
| 34 | No age verification on signup | Add minimum age gate (13 or 16 depending on jurisdiction) | NEEDS CODE + LEGAL |
| 35 | No cookie policy page | Create cookie policy, link from consent banner | NEEDS LEGAL |
| 36 | `before_send` Sentry hook is a no-op | Add PII scrubbing for phone numbers, tokens | FIXED — added regex scrubbing for phone, JWT, Stripe keys |

### Code Quality

| # | Issue | Recommendation | Status |
|---|-------|---------------|--------|
| 37 | Idempotency key for payouts includes timestamp+UUID — not idempotent | Accept client-supplied idempotency key | NEEDS CODE |
| 38 | Apple SSO flow missing event outbox emission | Emit `DriverSignedUpEvent` like Google SSO does | FIXED |
| 39 | In-memory rate limiting ineffective with multiple instances | Enforce Redis as required, not optional | NEEDS CODE |
| 40 | Demo location bypass still active in MerchantDetailsScreen | Remove `// TEMPORARY` demo bypass | FIXED |
| 41 | Stale CI workflows (`ci.yml`, `gameday.yml`) reference nonexistent dirs | Delete or update | NEEDS CLEANUP |
| 42 | `localStorage.getItem` / `JSON.parse` without try-catch in FavoritesContext | Add defensive parsing | FIXED |
| 43 | Several backend service stubs return mock data | Audit `virtual_cards`, `s3_storage`, `notify` stubs | NEEDS AUDIT |

### Frontend UX

| # | Issue | Recommendation | Status |
|---|-------|---------------|--------|
| 44 | Landing page missing structured data (JSON-LD) | Add Organization + Product schema | NEEDS CODE |
| 45 | No sitemap.xml or robots.txt customization | Configure Next.js static generation | NEEDS CODE |
| 46 | No analytics on landing page | Add PostHog or GA4 | NEEDS SETUP |
| 47 | OG images may not exist (referenced but not verified) | Verify `og-image.png` and `twitter-card.png` | NEEDS VERIFICATION |
| 48 | Twitter handle is `@neaborhood` not `@nerava` | Update if incorrect | NEEDS VERIFICATION |
| 49 | Data retention job not scheduled (manual-only) | Schedule via cron or AWS EventBridge | NEEDS SETUP |
| 50 | No feature flags for percentage-based rollout | Implement for gradual feature launches | FUTURE |

---

## Fix Summary

| Category | Total | Fixed | Needs Manual Action | Needs Code |
|----------|-------|-------|-------------------|-----------|
| P0 Critical | 5 | 3 | 2 (ToS, Merchant Auth) | 0 |
| P1 Security | 5 | 3 | 0 | 2 (Refresh Token O(N), Family Revocation) |
| P1 Reliability | 4 | 2 | 0 | 2 (Concurrent Sessions, Budget Atomicity) |
| P1 Infrastructure | 3 | 0 | 3 (CI/CD, Deploy, Backups) | 0 |
| P2 | 33 | 5 | ~15 | ~13 |
| **Total** | **50** | **13** | **~20** | **~17** |

---

## Deployment Readiness Checklist

Before growth push, verify:

- [x] Consent banner shows in production (auto-accept removed)
- [x] Dev login endpoint blocked in production
- [x] `credit_wallet` uses `with_for_update()`
- [x] Hardcoded Google API key removed from source
- [x] Withdrawal eligibility re-validated after lock acquisition
- [x] Tesla 429 handling added
- [x] Sentry PII scrubbing active
- [x] Apple SSO emits DriverSignedUpEvent
- [ ] Terms of Service page created and linked (needs legal)
- [ ] Merchant portal has JWT auth (needs implementation)
- [ ] Google API key rotated in Google Cloud Console
- [ ] Database backups automated and tested
- [ ] Sentry enabled on all frontend apps
- [ ] Missing database indexes added (migrations 025, 026)
- [ ] Push notifications configured (APNs key on App Runner)
- [ ] Dwolla account approved and configured
- [ ] Plaid account approved and configured
- [ ] CI workflows added for merchant, admin, console, landing
- [ ] Stale deploy workflow fixed or documented

---

## Recommended Implementation Order

| Week | Focus | Items |
|------|-------|-------|
| **Week 1** | Remaining security + legal | P0-1 (ToS), P0-5 (Merchant Auth), rotate Google API key, items 6-7 |
| **Week 2** | Reliability & infrastructure | Items 13-17, database indexes (25-26) |
| **Week 3** | Monitoring & compliance | Items 18-23, 30-36 |
| **Week 4** | Performance & polish | Items 24, 27, 29, 37-50 |

---

*Generated from comprehensive codebase audit covering backend/, apps/driver/, apps/merchant/, apps/landing/, infra/, and .github/workflows/. Updated with code fixes applied March 3, 2026.*
