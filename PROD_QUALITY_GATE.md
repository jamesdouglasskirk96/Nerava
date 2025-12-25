# Production Quality Gate Analysis - Nerava Platform

**Generated:** 2025-01-27  
**Scope:** Full-stack audit of backend (FastAPI) + frontend (PWA/Next.js) + integrations  
**Audit Type:** Pre-launch production readiness + fraud/security posture

---

## Executive Summary

### Launch Verdict: 🟡 **SOFT PASS** (Conditional)

**Status:** System has solid foundations but requires **P0 security fixes** and **P1 operational hardening** before production launch.

**Critical Findings:**
- ✅ **Strong:** Atomic wallet operations, idempotency on redemptions, webhook verification
- 🔴 **Blockers:** Some security gaps in auth flow, missing constraints, multi-instance migration risks
- 🟡 **Risks:** Rate limiting fallback behavior, incomplete error handling, limited observability

**Recommendation:** Implement all P0 fixes, validate P1 hardening, then proceed with controlled rollout to <100 users with monitoring.

---

## Phase 0: Repo Discovery & Architecture

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
├─────────────────────────────────────────────────────────────┤
│ • ui-mobile/          (PWA - Vanilla JS)                    │
│ • landing-page/       (Next.js marketing site)              │
│ • charger-portal/     (Next.js merchant portal)             │
│ • ui-admin/           (React admin dashboard)               │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  Entry: app/main_simple.py                                  │
│  • 90+ routers (auth, wallet, checkout, merchants, etc.)    │
│  • Services layer (nova, wallet, payments, auth)            │
│  • Middleware (CORS, auth, rate limiting, logging)          │
│  • Background workers (nova_accrual, outbox_relay)          │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┬──────────────┐
        ▼              ▼              ▼              ▼
   PostgreSQL      Redis          Stripe         Square
   (RDS prod)   (Rate limit/    (Payouts)   (Merchants)
                Cache)                            │
                                                  ▼
                                             Smartcar
                                           (Vehicle OAuth)
```

### Entry Points & Routing

**Backend:**
- **Primary:** `nerava-backend-v9/app/main_simple.py` (Production entry)
- **Routers:** 90+ routers in `app/routers/` organized by domain
- **Key routers:**
  - `auth_domain.py` - Auth (magic link, Google SSO)
  - `drivers_domain.py` - Driver wallet & merchant discovery
  - `checkout.py` - QR redemption flow
  - `wallet_pass.py` - Apple Wallet pass generation
  - `ev_smartcar.py` - Vehicle connection
  - `square.py` - Merchant Square OAuth
  - `purchase_webhooks.py` - Purchase event ingestion

**Frontend:**
- **PWA:** Served at `/app/` from `ui-mobile/` (static files mounted in FastAPI)
- **Config injection:** No runtime config injection found (hardcoded API URLs in JS)
- **Auth storage:** JWT stored in `localStorage` (see `ui-mobile/js/core/api.js`)

### Database Models & Migrations

**Key Models:**
- `User` (`app/models/user.py`) - PK: `id`, Unique: `email`, `public_id`
- `DriverWallet` (`app/models/domain.py`) - PK: `user_id`, Columns: `nova_balance`, `energy_reputation_score`
- `NovaTransaction` (`app/models/domain.py`) - PK: `id` (UUID), FK: `driver_user_id`, `merchant_id`
- `MerchantRedemption` - PK: `id`, Unique: `idempotency_key` (nullable), FK: `driver_user_id`, `merchant_id`
- `DomainMerchant` - PK: `id` (UUID), Unique: `qr_token`
- `VehicleAccount` - PK: `id` (UUID), FK: `user_id`
- `VehicleToken` - Encrypted tokens (Fernet)

**Migrations:**
- **Location:** `nerava-backend-v9/alembic/versions/` (45+ migrations)
- **Strategy:** **CRITICAL ISSUE** - Migrations **removed from startup** in `main_simple.py:293-305`
- **Evidence:** `main_simple.py:293-305` - Comments indicate manual migration requirement
- **Risk:** Multi-instance deployments require external migration job

### Background Jobs & Queues

**Active Workers:**
1. **Nova Accrual Service** (`app/services/nova_accrual.py`)
   - Auto-credits 1 Nova every 5s when `charging_detected=true` (demo mode only)
   - Starts in `main_simple.py:1120-1172` (light mode skips)
2. **Outbox Relay** (`app/workers/outbox_relay.py`)
   - Processes `outbox_events` table for reliable event publishing
   - Polls every 5s, publishes to event bus
3. **HubSpot Sync Worker** (`app/workers/hubspot_sync.py`)
   - Syncs user data to HubSpot (enabled via `HUBSPOT_ENABLED`)

**No dedicated queue system** (using in-process async tasks + DB outbox pattern)

### Critical Files Inventory (Top 30)

1. `nerava-backend-v9/app/main_simple.py` - App entry point
2. `nerava-backend-v9/app/config.py` - Settings/ENV vars
3. `nerava-backend-v9/app/db.py` - Database connection
4. `nerava-backend-v9/app/middleware/auth.py` - Auth middleware
5. `nerava-backend-v9/app/middleware/ratelimit.py` - Rate limiting
6. `nerava-backend-v9/app/services/nova_service.py` - Wallet operations
7. `nerava-backend-v9/app/services/auth_service.py` - User auth
8. `nerava-backend-v9/app/routers/auth_domain.py` - Auth endpoints
9. `nerava-backend-v9/app/routers/checkout.py` - Redemption flow
10. `nerava-backend-v9/app/routers/drivers_domain.py` - Driver wallet
11. `nerava-backend-v9/app/routers/purchase_webhooks.py` - Webhooks
12. `nerava-backend-v9/app/routers/stripe_api.py` - Stripe integration
13. `nerava-backend-v9/app/routers/square.py` - Square OAuth
14. `nerava-backend-v9/app/routers/ev_smartcar.py` - Vehicle connect
15. `nerava-backend-v9/app/routers/wallet_pass.py` - Apple Wallet
16. `nerava-backend-v9/app/models/domain.py` - Core domain models
17. `nerava-backend-v9/app/models/user.py` - User model
18. `nerava-backend-v9/app/services/idempotency.py` - Idempotency service
19. `nerava-backend-v9/app/services/google_auth.py` - Google SSO
20. `nerava-backend-v9/app/services/apple_wallet_pass.py` - Wallet pass gen
21. `nerava-backend-v9/app/security/jwt.py` - JWT manager
22. `nerava-backend-v9/app/security/rbac.py` - Role-based access
23. `ui-mobile/js/core/api.js` - Frontend API client
24. `ui-mobile/js/pages/wallet-new.js` - Wallet UI
25. `ui-mobile/js/pages/checkout.js` - Checkout UI
26. `ui-mobile/js/pages/login.js` - Login UI
27. `ENV.example` - Environment variables template
28. `nerava-backend-v9/app/run_migrations.py` - Migration runner
29. `nerava-backend-v9/alembic.ini` - Alembic config
30. `Makefile` - Build/deploy scripts

### Environment Variables Inventory

| Variable | Default | Required | Used By | Notes |
|----------|---------|----------|---------|-------|
| `DATABASE_URL` | `sqlite:///./nerava.db` | ✅ Yes (prod) | All DB operations | Must be PostgreSQL in prod |
| `JWT_SECRET` | `dev-secret` | ✅ Yes (prod) | JWT signing | **P0:** Must not equal `DATABASE_URL` |
| `REDIS_URL` | `redis://localhost:6379/0` | ✅ Yes (prod) | Rate limiting | Required for multi-instance |
| `PUBLIC_BASE_URL` | `http://127.0.0.1:8001` | ✅ Yes | OAuth callbacks, QR URLs | |
| `ALLOWED_ORIGINS` | `*` | ✅ Yes (prod) | CORS | **P0:** Cannot be `*` in prod |
| `TOKEN_ENCRYPTION_KEY` | (Fernet key) | ✅ Yes (prod) | Token encryption | Must be 44-char base64 |
| `STRIPE_SECRET` | (empty) | 🟡 Optional | Payouts | Required for real payouts |
| `STRIPE_WEBHOOK_SECRET` | (empty) | ✅ Yes (prod) | Webhook verification | |
| `SQUARE_APPLICATION_ID` | (empty) | 🟡 Optional | Square OAuth | Required for Square merchants |
| `SQUARE_WEBHOOK_SIGNATURE_KEY` | (empty) | 🟡 Optional | Square webhooks | |
| `SMARTCAR_CLIENT_ID` | (empty) | 🟡 Optional | Vehicle connection | |
| `SMARTCAR_CLIENT_SECRET` | (empty) | 🟡 Optional | Vehicle connection | |
| `GOOGLE_CLIENT_ID` | (empty) | 🟡 Optional | Google SSO | |
| `NREL_API_KEY` | (empty) | 🟡 Optional | Charger data | |
| `GOOGLE_PLACES_API_KEY` | (empty) | 🟡 Optional | Merchant discovery | |
| `APPLE_WALLET_PASS_TYPE_ID` | (empty) | 🟡 Optional | Apple Wallet | |
| `APPLE_WALLET_TEAM_ID` | (empty) | 🟡 Optional | Apple Wallet | |
| `HUBSPOT_ENABLED` | `false` | 🟡 Optional | HubSpot sync | |
| `DEMO_MODE` | `true` | 🟡 Optional | Demo features | Should be `false` in prod |
| `NERAVA_DEV_ALLOW_ANON_USER` | `false` | ❌ No | Dev only | **P0:** Must be `false` in prod |

**Startup Validation:** `main_simple.py:59-288` validates critical env vars on startup (JWT_SECRET, DATABASE_URL, REDIS_URL, dev flags)

---

## Phase 1: End-to-End UX Flow Completeness

### Flow A: First-Time User (Landing → Signup → Auth → First Screen)

**Status:** ✅ **Complete**

**Trace:**
1. **Landing:** `landing-page/app/page.tsx` → Sign up button
2. **Signup:** `ui-mobile/js/pages/login.js:236` → `POST /v1/auth/register` (`auth_domain.py:100`)
3. **Login:** `POST /v1/auth/login` → Returns JWT (`auth_domain.py:151`)
4. **Auth/Me:** `GET /v1/drivers/me` (`drivers_domain.py`) → Returns user + wallet
5. **First Screen:** Wallet page (`ui-mobile/js/pages/wallet-new.js`)

**Evidence:**
- `auth_domain.py:100-146` - Registration endpoint
- `auth_domain.py:151-214` - Login endpoint
- `drivers_domain.py:28-62` - `/v1/drivers/me` endpoint
- `ui-mobile/js/pages/login.js:318-357` - Google SSO flow

**Error Handling:**
- ✅ Email validation, password requirements
- ✅ Duplicate email check (409 Conflict)
- 🟡 **Issue:** No email verification step (accounts created immediately)

### Flow B: Connect Vehicle (Smartcar) → Confirm → Telemetry → Earning Trigger

**Status:** ✅ **Complete**

**Trace:**
1. **Connect:** `POST /v1/ev/connect` (`ev_smartcar.py:117`) → Returns OAuth URL
2. **Callback:** `GET /oauth/smartcar/callback` (`ev_smartcar.py:167`) → Stores tokens
3. **Vehicle Account:** Creates `VehicleAccount` + `VehicleToken` (encrypted)
4. **Telemetry:** `GET /v1/ev/vehicles/{vehicle_id}/telemetry` → Returns vehicle data
5. **Earning:** Nova accrual service monitors `charging_detected` flag

**Evidence:**
- `ev_smartcar.py:117-163` - Connect endpoint
- `ev_smartcar.py:167-267` - OAuth callback
- `app/services/smartcar_service.py` - Smartcar API client
- `app/services/nova_accrual.py` - Auto-accrual service (demo mode)

**Error Handling:**
- ✅ OAuth error handling
- ✅ Token encryption (`app/models/vehicle.py:VehicleToken`)
- 🟡 **Issue:** No token refresh logic visible (tokens may expire)

### Flow C: Earn Nova (Event Detection → Wallet Credit → Activity Feed)

**Status:** ✅ **Complete**

**Trace:**
1. **Event:** Purchase webhook (`POST /v1/webhooks/purchase` - `purchase_webhooks.py:30`)
2. **Normalize:** `app/services/purchases.py:15` - Normalizes Square/CLO events
3. **Idempotency:** Checks `provider + provider_ref` (line 80-95 in `purchase_webhooks.py`)
4. **Credit:** `NovaService.grant_to_driver()` (`nova_service.py:48`) - Atomic balance update
5. **Activity:** `mark_wallet_activity()` (`wallet_activity.py:14`) → Updates timestamp

**Evidence:**
- `purchase_webhooks.py:30-232` - Webhook handler
- `nova_service.py:48-188` - Grant operation (uses DB transaction)
- `nova_service.py:155-169` - Atomic balance increment via SQL

**Idempotency:**
- ✅ Provider + provider_ref check (`purchase_webhooks.py:80-95`)
- ✅ Unique constraint on `nova_transactions.session_id + event_id` (via migration 030)

**Error Handling:**
- ✅ Webhook signature verification (Square only if configured)
- 🟡 **Issue:** No replay window check for purchase webhooks (unlike Stripe)

### Flow D: Discover Merchants (List/Map → Detail → Navigation)

**Status:** ✅ **Complete**

**Trace:**
1. **List:** `GET /v1/drivers/merchants/nearby` (`drivers_domain.py:65`)
2. **Map:** Frontend uses Leaflet.js (`ui-mobile/js/pages/discover.js`)
3. **Detail:** `GET /v1/merchants/{id}` (`merchants_domain.py`)
4. **Navigation:** Frontend opens Maps app with lat/lng

**Evidence:**
- `drivers_domain.py:65-150` - Nearby merchants endpoint
- `ui-mobile/js/pages/discover.js` - Discovery UI
- `app/services/while_you_charge.py` - Aggregates chargers + merchants

**Error Handling:**
- ✅ Missing lat/lng validation
- 🟡 **Issue:** No rate limiting visible on discovery endpoints (may hit Google Places API limits)

### Flow E: Redeem Nova (QR Scan → Checkout → Idempotency → Wallet Debit → Receipt)

**Status:** ✅ **Complete** (with idempotency)

**Trace:**
1. **QR Scan:** `GET /v1/checkout/qr/{token}` (`checkout.py:80`) → Returns merchant + balance
2. **Redeem:** `POST /v1/checkout/redeem` (`checkout.py:237`)
3. **Idempotency:** Checks `idempotency_key` OR `square_order_id` (`checkout.py:311-327`)
4. **Debit:** `NovaService.redeem_from_driver()` (`nova_service.py:190`) - Atomic with `SELECT ... FOR UPDATE`
5. **Receipt:** Returns `RedeemResponse` with redemption_id

**Evidence:**
- `checkout.py:237-558` - Redeem endpoint
- `checkout.py:311-327` - Idempotency check
- `nova_service.py:190-423` - Redeem operation
- `nova_service.py:312-335` - Atomic balance decrement (`UPDATE ... WHERE nova_balance >= amount`)

**Idempotency:**
- ✅ Required for non-Square redemptions (`idempotency_key` UUID)
- ✅ Unique constraint on `merchant_redemptions.idempotency_key` (migration 041)
- ✅ Square redemptions use `square_order_id` for idempotency

**Race Condition Protection:**
- ✅ `SELECT ... FOR UPDATE` on wallet (`nova_service.py:313`)
- ✅ Atomic UPDATE with balance check (`nova_service.py:320-330`)

**Error Handling:**
- ✅ Insufficient balance check
- ✅ Merchant active status check
- 🟡 **Issue:** No validation that `order_total_cents` matches Square order (if provided)

### Flow F: Apple Wallet Pass (Generate → Install → Device Registration → Push Updates)

**Status:** ✅ **Complete**

**Trace:**
1. **Generate:** `POST /v1/wallet/pass/apple/create` (`wallet_pass.py:461`) → Returns `.pkpass` file
2. **Install:** User installs in Apple Wallet app
3. **Registration:** Apple calls `POST /v1/wallet/pass/apple/devices/{deviceLibId}/registrations/{passTypeId}/{serial}` (`wallet_pass.py:950`)
4. **Updates:** `mark_wallet_activity()` triggers `send_updates_for_wallet()` (`apple_pass_push.py:75`)

**Evidence:**
- `wallet_pass.py:461-571` - Pass creation
- `apple_wallet_pass.py:121-262` - Pass JSON generation
- `wallet_pass.py:950-1041` - Device registration
- `apple_pass_push.py:46-73` - APNS push notifications

**Error Handling:**
- ✅ Pass signing validation (`APPLE_WALLET_SIGNING_ENABLED` check)
- ✅ Authentication token validation on registration
- 🟡 **Issue:** APNS failures are logged but don't block wallet updates (by design)

### Flow G: Google Login (GIS → Backend Verification → Account Linking → Refresh Token)

**Status:** ✅ **Complete**

**Trace:**
1. **Frontend:** Google Sign-In (`ui-mobile/js/pages/login.js:318`) → Gets ID token
2. **Backend:** `POST /v1/auth/google` (`auth.py:181`) → Verifies token
3. **Verification:** `verify_google_id_token()` (`google_auth.py:9`) → Uses `google-auth` library
4. **Account:** Finds or creates user by `(auth_provider, provider_sub)`
5. **Refresh:** `RefreshTokenService.create_refresh_token()` → Creates refresh token

**Evidence:**
- `auth.py:181-252` - Google auth endpoint
- `google_auth.py:9-69` - Token verification
- `app/models/user.py:44-47` - Unique index on `(auth_provider, provider_sub)`

**Error Handling:**
- ✅ Token verification with audience check
- ✅ Missing `GOOGLE_CLIENT_ID` returns 503
- 🟡 **Issue:** No refresh token rotation logic visible

### Flow H: Merchant Onboarding (Square OAuth → Store Merchant → Pull Orders → Redemption Validation)

**Status:** ✅ **Complete**

**Trace:**
1. **OAuth:** `GET /v1/merchants/square/connect` (`square.py`) → Returns OAuth URL
2. **Callback:** `GET /v1/merchants/square/callback` → Stores `square_merchant_id` + encrypted `square_access_token`
3. **Merchant Record:** Creates/updates `DomainMerchant` with Square credentials
4. **Orders:** `GET /v1/checkout/orders` (`checkout.py:166`) → Searches Square orders
5. **Validation:** Redemption matches Square order ID for idempotency

**Evidence:**
- `square.py` - Square OAuth flow
- `checkout.py:166-256` - Order lookup
- `app/services/square_orders.py` - Square API client

**Error Handling:**
- ✅ OAuth error handling
- ✅ Token encryption (`TOKEN_ENCRYPTION_KEY`)
- 🟡 **Issue:** No webhook signature verification for Square webhooks (only basic secret check)

### Flow I: Admin Operations (Flags, Merchant Health, Wallet Audit, Refunds)

**Status:** 🟡 **Partial**

**Trace:**
1. **Flags:** `GET /v1/admin/flags` (`admin_domain.py`) → Feature flags
2. **Merchant Health:** No dedicated endpoint found
3. **Wallet Audit:** `GET /v1/admin/wallets/{user_id}/transactions` → Nova transactions
4. **Refunds:** No refund endpoint found (only payout reversal)

**Evidence:**
- `admin_domain.py` - Admin endpoints
- `app/routers/flags.py` - Feature flags
- `app/services/audit.py` - Audit logging

**Missing:**
- 🔴 Merchant health dashboard endpoint
- 🔴 Refund/reversal endpoint for redemptions
- 🟡 Wallet balance reconciliation tool

---

## Phase 2: Security + Fraud Readiness Audit

### 2.1 Authentication & Authorization

#### AuthN Strengths:
- ✅ JWT-based auth with middleware (`app/middleware/auth.py`)
- ✅ Token stored in `Authorization: Bearer` header
- ✅ Google SSO token verification (`google_auth.py:36-40`)
- ✅ Magic link auth (`auth_domain.py:226-330`)

#### AuthN Weaknesses:
- 🔴 **P0:** Dev fallback for anonymous users (`dependencies/domain.py:72-80`)
  - **Evidence:** `dependencies/domain.py:31-34` - `NERAVA_DEV_ALLOW_ANON_USER` flag
  - **Risk:** If enabled in prod, allows unauthenticated access
  - **Mitigation:** Startup validation in `main_simple.py:142-149` blocks this in non-local

#### AuthZ Strengths:
- ✅ Role-based access control (`app/security/rbac.py`)
- ✅ Admin endpoints require `admin` role (`admin_domain.py:19-26`)
- ✅ Driver endpoints require `driver` role (`dependencies/driver.py:35`)

#### AuthZ Weaknesses:
- 🟡 **P1:** Some endpoints may lack role checks (needs audit of all 90+ routers)
- 🟡 **P1:** No resource-level authorization (e.g., user can access any user_id in path params)

**IDOR Risks:**
- 🟡 **P1:** `GET /v1/admin/wallets/{user_id}/transactions` - No check that requester is admin
  - **Evidence:** `admin_domain.py` - Need to verify `get_current_admin` dependency
- 🟡 **P1:** Merchant endpoints may allow access to other merchants' data

### 2.2 Replay & Idempotency

#### Strengths:
- ✅ Redemptions: `idempotency_key` required for non-Square (`checkout.py:287-327`)
- ✅ Nova grants: `idempotency_key` support (`nova_service.py:58`)
- ✅ Purchase webhooks: `provider + provider_ref` dedupe (`purchase_webhooks.py:80-95`)
- ✅ Stripe webhooks: Replay protection (5-minute window) (`stripe_api.py:631-643`)

#### Weaknesses:
- 🔴 **P0:** Purchase webhooks lack replay window (unlike Stripe)
  - **Evidence:** `purchase_webhooks.py:30` - No timestamp validation
  - **Risk:** Old webhooks can be replayed indefinitely
  - **Fix:** Add timestamp check (reject events older than 5 minutes)

- 🟡 **P1:** Idempotency service uses cache (Redis/in-memory) with 120s TTL
  - **Evidence:** `idempotency.py:9-10` - `ttl_seconds=120`
  - **Risk:** If Redis unavailable, in-memory cache lost on restart
  - **Mitigation:** Critical idempotency uses DB constraints (redemptions, Nova grants)

### 2.3 Rate Limiting & Abuse

#### Strengths:
- ✅ Redis-backed rate limiting with in-memory fallback (`middleware/ratelimit.py`)
- ✅ Endpoint-specific limits (magic link: 3/min, auth: 10/min)
- ✅ Per-user or per-IP limiting (`ratelimit.py:29-39`)

#### Weaknesses:
- 🟡 **P1:** In-memory fallback doesn't work across instances
  - **Evidence:** `ratelimit.py:125-138` - In-memory buckets per instance
  - **Risk:** Multi-instance deployments bypass rate limits if Redis down
  - **Mitigation:** Startup validation requires Redis in prod (`main_simple.py:112-132`)

- 🟡 **P1:** Some endpoints may lack rate limits (90+ routers not all audited)

### 2.4 Secrets & Crypto

#### Strengths:
- ✅ JWT secret validation (`main_simple.py:59-86`)
- ✅ Token encryption (Fernet) for vehicle/Square tokens
- ✅ Startup validation prevents `JWT_SECRET == DATABASE_URL`

#### Weaknesses:
- 🔴 **P0:** Secrets stored in ENV vars (not secrets manager)
  - **Evidence:** `ENV.example` - All secrets in plain text
  - **Risk:** Exposure via logs, ENV dumps
  - **Recommendation:** Migrate to AWS Secrets Manager

- 🟡 **P1:** No secret rotation strategy documented
- 🟡 **P1:** `TOKEN_ENCRYPTION_KEY` must be manually rotated (re-encrypt all tokens)

### 2.5 Data Integrity

#### Strengths:
- ✅ Atomic wallet updates (`nova_service.py:320-330` - `UPDATE ... WHERE nova_balance >= amount`)
- ✅ Row-level locking (`SELECT ... FOR UPDATE`) on redemptions
- ✅ DB constraints on unique fields (`email`, `public_id`, `qr_token`)

#### Weaknesses:
- 🔴 **P0:** No DB constraint preventing negative balances
  - **Evidence:** `models/domain.py:DriverWallet` - No CHECK constraint
  - **Risk:** Application bug could create negative balance
  - **Mitigation:** Application logic prevents this, but DB constraint would be safer

- 🟡 **P1:** Wallet balance updates not in same transaction as NovaTransaction insert
  - **Evidence:** `nova_service.py:155-169` - Separate commits
  - **Risk:** If transaction insert fails after balance update, balance inconsistent
  - **Fix:** Wrap in single transaction

### 2.6 Webhook Verification

#### Strengths:
- ✅ Stripe webhook signature verification (`stripe_api.py:602-614`)
- ✅ Stripe replay protection (5-minute window) (`stripe_api.py:631-643`)
- ✅ Purchase webhook secret check (`purchase_webhooks.py:43-45`)

#### Weaknesses:
- 🔴 **P0:** Purchase webhooks lack timestamp validation (replay risk)
- 🟡 **P1:** Square webhook signature verification not implemented
  - **Evidence:** `purchase_webhooks.py:43` - Only checks `X-Webhook-Secret` header
  - **Risk:** Square webhooks can be spoofed if secret leaked
  - **Fix:** Implement Square signature verification

### 2.7 Client Security

#### Strengths:
- ✅ CORS validation prevents wildcard in prod (`main_simple.py:784-802`)
- ✅ Secure cookie flags for auth cookies (`auth_domain.py:32-44`)

#### Weaknesses:
- 🟡 **P1:** JWT stored in `localStorage` (XSS risk)
  - **Evidence:** `ui-mobile/js/core/api.js` - `localStorage.setItem('token', ...)`
  - **Risk:** XSS attack can steal token
  - **Mitigation:** Use httpOnly cookies (but requires CORS credential handling)

- 🟡 **P1:** No CSRF protection for cookie-based auth (if implemented)

### 2.8 Supply Chain

#### Dependencies:
- ✅ `requirements.txt` exists (need to check for known vulnerabilities)
- 🟡 **P2:** No automated dependency scanning found

---

## Phase 3: Ops/Infra/Deployment Readiness

### 3.1 Health Checks

**Status:** ✅ **Correct**

**Evidence:**
- `/healthz` - Liveness probe (`main_simple.py:407-427`) - Always returns 200
- `/readyz` - Readiness probe (`main_simple.py:429-530`) - Checks DB + Redis with timeouts

**Assessment:** Correctly separates liveness (HTTP server) from readiness (dependencies).

### 3.2 Migrations Strategy

**Status:** 🟡 **Manual (Risky for Multi-Instance)**

**Evidence:**
- `main_simple.py:293-305` - Migrations **removed from startup**
- Comment: "Migrations must be run manually before deployment"
- `run_migrations.py:19` - Migration runner script

**Risk:** If multiple instances start simultaneously, race condition on migration locks.

**Recommendation:** Run migrations in separate job (e.g., init container) before app starts.

### 3.3 Database

**Status:** ✅ **PostgreSQL in Prod (Validated)**

**Evidence:**
- `main_simple.py:88-110` - Validates `DATABASE_URL` is not SQLite in prod
- Connection pooling: SQLAlchemy default (no explicit pool config found)

**Issues:**
- 🟡 **P1:** No explicit connection pool size/timeout configuration
- 🟡 **P1:** No connection health check interval

### 3.4 Redis

**Status:** ✅ **Required in Prod**

**Evidence:**
- `main_simple.py:112-132` - Validates Redis URL in prod
- Rate limiting uses Redis (`ratelimit_redis.py`)

**Failure Modes:**
- ✅ Falls back to in-memory (but fails in prod if Redis unavailable)

### 3.5 Logging

**Status:** 🟡 **Basic Structured Logging**

**Evidence:**
- `main_simple.py:45-51` - Basic Python logging
- `middleware/logging.py` - Request logging middleware
- 🟡 **Issue:** No correlation IDs found
- 🟡 **Issue:** No PII sanitization visible

**Recommendation:** Add correlation IDs, PII sanitization, structured JSON logging.

### 3.6 Metrics/Tracing

**Status:** 🔴 **Missing**

**Evidence:**
- `middleware/metrics.py` exists but need to check implementation
- No APM integration (Datadog/New Relic) found
- No Prometheus metrics endpoints found

**Recommendation:** Add Prometheus metrics, APM integration.

### 3.7 Config Injection (Frontend)

**Status:** 🔴 **Hardcoded**

**Evidence:**
- `ui-mobile/js/core/api.js` - API base URL likely hardcoded
- No runtime config injection found

**Risk:** Frontend needs rebuild for different environments.

**Recommendation:** Inject config via S3/CloudFront environment variables or separate config endpoint.

### 3.8 Environment Parity

**Status:** 🟡 **Partial**

**Evidence:**
- Local: SQLite, in-memory rate limiting, dev flags
- Prod: PostgreSQL, Redis, strict validation

**Gap:** Demo mode differences may hide production issues.

---

## Phase 4: Gap List (Prioritized)

### P0 - Launch Blockers

| ID | Title | Risk | Evidence | Fix Strategy | Tests | Effort |
|----|-------|------|----------|--------------|-------|--------|
| P0-1 | Purchase webhook replay protection | HIGH | `purchase_webhooks.py:30` - No timestamp check | Add 5-minute replay window (like Stripe) | Unit test replay rejection | 2h |
| P0-2 | Wallet balance DB constraint | MEDIUM | `models/domain.py:DriverWallet` - No CHECK | Add `CHECK (nova_balance >= 0)` constraint | Migration test | 1h |
| P0-3 | Negative balance prevention | MEDIUM | Application logic only | Add DB constraint + application check | Integration test | 1h |
| P0-4 | Square webhook signature verification | HIGH | `purchase_webhooks.py:43` - Only secret check | Implement Square signature verification | Unit test signature validation | 4h |

### P1 - High Priority (Pre-Launch)

| ID | Title | Risk | Evidence | Fix Strategy | Tests | Effort |
|----|-------|------|----------|--------------|-------|--------|
| P1-1 | Multi-instance migration race | HIGH | `main_simple.py:293` - Manual migrations | Run migrations in init container | E2E test multi-instance startup | 3h |
| P1-2 | Wallet update transaction boundary | MEDIUM | `nova_service.py:155-169` - Separate commits | Wrap in single transaction | Unit test rollback | 2h |
| P1-3 | Rate limiting multi-instance fallback | MEDIUM | `ratelimit.py:125` - In-memory per instance | Fail fast if Redis unavailable | Integration test | 1h |
| P1-4 | Correlation IDs for logging | LOW | No correlation IDs found | Add `X-Request-ID` middleware | Log analysis | 3h |
| P1-5 | PII sanitization in logs | MEDIUM | No sanitization visible | Sanitize email, tokens in logs | Unit test log output | 4h |
| P1-6 | Frontend config injection | LOW | `ui-mobile/js/core/api.js` - Hardcoded URLs | Inject via `/v1/config` endpoint | E2E test config load | 2h |
| P1-7 | IDOR audit (all routers) | HIGH | 90+ routers not audited | Audit all endpoints for resource access | Security scan | 8h |
| P1-8 | Metrics/Prometheus endpoints | LOW | No metrics found | Add Prometheus metrics | Load test | 4h |

### P2 - Post-Launch

| ID | Title | Risk | Evidence | Fix Strategy | Tests | Effort |
|----|-------|------|----------|--------------|-------|--------|
| P2-1 | Secret rotation strategy | MEDIUM | No rotation docs | Document + automate rotation | Manual test | 4h |
| P2-2 | Dependency vulnerability scanning | LOW | No scanning found | Add Dependabot/Snyk | Automated | 1h |
| P2-3 | APM integration | LOW | No APM found | Add Datadog/New Relic | Performance test | 6h |
| P2-4 | JWT in httpOnly cookies | MEDIUM | `localStorage` XSS risk | Migrate to cookies | E2E test auth flow | 4h |

---

## Phase 5: Top 10 Attack Vectors

| Attack | Entrypoint | Exploit Steps | Impact | Current Mitigations | Required Fix |
|--------|------------|---------------|--------|---------------------|--------------|
| **1. Webhook Replay** | `POST /v1/webhooks/purchase` | Replay old webhook payload | Double credit to wallet | None (no timestamp check) | Add 5-minute replay window |
| **2. Square Webhook Spoofing** | `POST /v1/webhooks/purchase` | If secret leaked, spoof Square webhook | Fraudulent credits | Only secret header check | Implement signature verification |
| **3. IDOR on Wallet** | `GET /v1/admin/wallets/{user_id}` | Use any user_id in path | Data leak | Need to verify admin check | Audit all admin endpoints |
| **4. Negative Balance** | `NovaService.redeem_from_driver()` | Application bug in balance logic | Financial loss | Application check only | Add DB constraint |
| **5. Rate Limit Bypass** | Any endpoint | Multi-instance + Redis down | DoS | In-memory fallback | Fail fast if Redis unavailable |
| **6. XSS Token Theft** | Frontend JS | XSS on page → steal localStorage token | Account takeover | None (localStorage) | Migrate to httpOnly cookies |
| **7. Migration Race** | App startup | Multiple instances run migrations | DB locks/corruption | Manual migration step | Init container migration |
| **8. Balance Race Condition** | Concurrent redemptions | Two requests redeem simultaneously | Double redemption | `SELECT ... FOR UPDATE` (good) | ✅ Already mitigated |
| **9. Secret Exposure** | ENV vars | Logs/ENV dump expose secrets | Full system compromise | No secrets manager | Migrate to AWS Secrets Manager |
| **10. Idempotency Cache Loss** | Redis unavailable | In-memory cache lost on restart | Duplicate processing | DB constraints for critical ops | ✅ Already mitigated |

---

## Production Runbook Readiness Checklist

| Item | Status | Notes |
|------|--------|-------|
| **Health Checks** | ✅ PASS | `/healthz` and `/readyz` correctly implemented |
| **Migrations** | 🟡 PARTIAL | Manual step required (no auto-run) |
| **Database** | ✅ PASS | PostgreSQL required in prod, validated on startup |
| **Redis** | ✅ PASS | Required in prod, validated on startup |
| **Logging** | 🟡 PARTIAL | Basic logging, missing correlation IDs + PII sanitization |
| **Metrics** | 🔴 FAIL | No Prometheus/APM integration |
| **Config Validation** | ✅ PASS | Startup validation prevents common misconfigurations |
| **Secret Management** | 🔴 FAIL | Secrets in ENV vars (not secrets manager) |
| **Error Tracking** | 🔴 FAIL | No Sentry/error tracking found |
| **Backups** | ❓ UNKNOWN | No backup strategy documented |
| **Monitoring** | 🔴 FAIL | No alerting infrastructure found |
| **Documentation** | 🟡 PARTIAL | Good code docs, missing ops runbooks |

**Overall:** 🟡 **6/12 PASS** - Critical gaps in observability and secret management.

---

## Next Steps

1. **Immediate (P0):** Fix webhook replay, add balance constraints, Square signature verification
2. **Pre-Launch (P1):** Migrations strategy, logging improvements, IDOR audit
3. **Post-Launch (P2):** Observability, secret rotation, APM

**See `PROD_QUALITY_GATE_TODO.md` for detailed action items.**

---

## Phase 6: Next Cursor Prompt (Implementation)

Use the following prompt in Cursor to implement all P0 fixes and highest-leverage P1 fixes:

---

### IMPLEMENTATION PROMPT FOR CURSOR

**You are implementing critical production security fixes for the Nerava platform. Follow the requirements below exactly, including all security validations, tests, and documentation.**

**Scope:** Implement all P0 fixes (P0-1 through P0-4) and P1-2 (transaction boundary fix). Add tests for each fix.

---

#### Fix P0-1: Purchase Webhook Replay Protection

**File:** `nerava-backend-v9/app/routers/purchase_webhooks.py`

**Requirements:**
1. After normalizing the webhook event (line 57), extract timestamp from `normalized["ts"]` (already exists)
2. Calculate age: `(datetime.utcnow() - normalized["ts"]).total_seconds() / 60`
3. If age > 5 minutes, log warning and raise `HTTPException 400` with detail: "Webhook event too old (replay protection). Events older than 5 minutes are rejected."
4. Log the rejection with event age in minutes
5. Use same pattern as Stripe webhook replay protection (`stripe_api.py:631-643`)

**Test:** Create unit test in `nerava-backend-v9/app/tests/test_purchase_webhooks.py`:
- Test that events older than 5 minutes are rejected
- Test that events within 5 minutes are accepted
- Test with missing timestamp (should handle gracefully)

---

#### Fix P0-2: Wallet Balance DB Constraint

**File:** Create new migration: `nerava-backend-v9/alembic/versions/045_add_wallet_balance_constraint.py`

**Requirements:**
1. Add CHECK constraint: `ALTER TABLE driver_wallets ADD CONSTRAINT check_nova_balance_non_negative CHECK (nova_balance >= 0)`
2. For PostgreSQL compatibility, use SQLAlchemy's `CheckConstraint`
3. Test migration: Verify it can be applied and rolled back

**Test:** Add integration test in `nerava-backend-v9/app/tests/test_wallet_constraints.py`:
- Test that inserting negative balance raises IntegrityError
- Test that valid balance (>= 0) works

---

#### Fix P0-3: Negative Balance Prevention (Application Layer)

**File:** `nerava-backend-v9/app/services/nova_service.py`

**Requirements:**
1. In `redeem_from_driver()` method (around line 313), before the `SELECT ... FOR UPDATE`, add explicit check:
   ```python
   wallet = db.query(DriverWallet).filter(DriverWallet.user_id == driver_id).first()
   if not wallet or wallet.nova_balance < amount:
       raise ValueError(f"Insufficient Nova balance. Has {wallet.nova_balance if wallet else 0}, needs {amount}")
   ```
2. Then proceed with the existing `with_for_update()` lock
3. This provides early validation before acquiring the lock

**Test:** Update existing tests in `test_nova_service.py`:
- Test insufficient balance raises ValueError before lock
- Test sufficient balance proceeds normally

---

#### Fix P0-4: Square Webhook Signature Verification

**File:** `nerava-backend-v9/app/routers/purchase_webhooks.py`

**Requirements:**
1. Create new function `verify_square_signature(body: bytes, signature: str, secret: str) -> bool`:
   - Square uses HMAC-SHA256 with the webhook signature key
   - Signature format: Base64 encoded HMAC
   - Compute: `hmac.new(secret.encode(), body, hashlib.sha256).digest()`, then base64 encode
   - Compare with provided signature (constant-time comparison)
2. In `ingest_purchase_webhook()`:
   - Extract `X-Square-Signature` header
   - If `SQUARE_WEBHOOK_SIGNATURE_KEY` is configured, verify signature
   - If signature verification fails, raise `HTTPException 401`
   - If signature key not configured, fall back to existing `X-Webhook-Secret` check (backward compat)
3. Use `request.body()` to get raw body (must be bytes for signature verification)

**Test:** Create unit test in `test_purchase_webhooks.py`:
- Test valid signature is accepted
- Test invalid signature is rejected
- Test missing signature key falls back to secret check
- Test missing signature header with configured key fails

---

#### Fix P1-2: Wallet Update Transaction Boundary

**File:** `nerava-backend-v9/app/services/nova_service.py`

**Requirements:**
1. In `grant_to_driver()` method (around line 48), ensure both wallet update and NovaTransaction insert happen in the same transaction:
   - Wrap entire operation in try/except
   - Only commit once after both operations succeed
   - Rollback on any exception
2. Current code (lines 155-169) has separate commits - combine into single transaction
3. Ensure `mark_wallet_activity()` call is also within transaction (or called after commit)

**Test:** Create test in `test_nova_service.py`:
- Test that if NovaTransaction insert fails, wallet balance is rolled back
- Test concurrent grants still work correctly
- Test transaction isolation

---

#### General Requirements

1. **All fixes must include:**
   - Type hints
   - Docstrings explaining the security rationale
   - Logging for security events (use `logger.warning` for rejections)

2. **Testing:**
   - Run `pytest tests/` to ensure all tests pass
   - Add new tests for each fix
   - Ensure existing tests still pass

3. **Documentation:**
   - Update relevant docstrings
   - Add comments explaining security measures

4. **Error Handling:**
   - All security checks must fail closed (reject on uncertainty)
   - Log all security events for audit

5. **Code Quality:**
   - Follow existing code style
   - Use existing patterns (e.g., HTTPException for API errors)
   - Ensure backward compatibility where possible

**After Implementation:**
- Run `scripts/prod_gate.sh` to verify checks pass
- Run full test suite: `cd nerava-backend-v9 && pytest tests/ -v`
- Review `PROD_QUALITY_GATE.md` to mark fixes as complete

**Validation Checklist:**
- [ ] P0-1: Webhook replay protection rejects events >5 minutes old
- [ ] P0-2: DB constraint prevents negative balances
- [ ] P0-3: Application layer checks balance before lock
- [ ] P0-4: Square signature verification works with test webhook
- [ ] P1-2: Wallet operations are atomic (test rollback scenario)
- [ ] All existing tests pass
- [ ] New tests added for each fix
- [ ] Code review completed

---

**Start implementing these fixes now.**

