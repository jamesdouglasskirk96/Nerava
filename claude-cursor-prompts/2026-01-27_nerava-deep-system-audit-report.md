# NERAVA DEEP-SYSTEM AUDIT REPORT
**Date:** 2026-01-27  
**Auditor:** Elite CTO Deep-System Analysis  
**Scope:** Full system (iOS, Driver Web, Merchant Portal, Admin Portal, Backend, Landing)  
**Methodology:** Code path analysis, schema inspection, endpoint mapping, compliance review

---

## A. STRUCTURAL INTEGRITY

### A1. Core Domain Objects & Database Schema

#### Source-of-Truth Tables (Primary Data)

| Table | Primary Key | Ownership | Purpose |
|-------|-------------|-----------|---------|
| `users` | `id` (Integer) | System | User accounts (drivers, merchants, admins) |
| `driver_wallets` | `user_id` (FK → users.id) | Driver | Nova balance, energy reputation, Apple Wallet tokens |
| `domain_merchants` | `id` (UUID) | Merchant | Merchant business records, Nova balance, Square tokens |
| `exclusive_sessions` | `id` (UUID) | Driver | Active exclusive activation sessions (60min TTL) |
| `intent_sessions` | `id` (UUID) | Driver | Location-based intent captures for charging moments |
| `merchants` | `id` (String) | System | Google Places merchant data (cached, enriched) |
| `chargers` | `id` (String) | System | EV charging station data (NREL/OCM sourced) |
| `merchant_perks` | `id` (Integer) | Merchant | Active perks/rewards (exclusives flagged in metadata) |
| `nova_transactions` | `id` (UUID) | System | Immutable ledger of all Nova movements |
| `stripe_payments` | `id` (UUID) | System | Stripe payment records (merchant Nova purchases) |
| `verified_visits` | `id` (String UUID) | Driver | Merchant visit verification codes (ATX-ASADAS-023 format) |
| `admin_audit_logs` | `id` (UUID) | System | Admin action audit trail (before/after JSON snapshots) |

#### Transient/Derived Tables

| Table | Purpose | TTL/Retention |
|-------|---------|---------------|
| `merchant_cache` | Google Places enrichment cache | `expires_at` field, TTL configurable (default 3600s) |
| `otp_challenges` | Phone OTP verification codes | `expires_at` (short-lived, ~5min) |
| `refresh_tokens` | JWT refresh tokens | `expires_at` (long-lived, ~30 days) |
| `claim_sessions` | Merchant claim verification flow | `magic_link_expires_at` (24h) |
| `vehicle_onboarding` | Anti-fraud vehicle photos | `expires_at` (90 days retention) |
| `wallet_pass_activations` | Apple Wallet pass state | `expires_at` (pass expiration) |

#### Data Ownership Boundaries

**Driver-Owned Data:**
- `driver_wallets` (Nova balance, energy reputation)
- `exclusive_sessions` (active sessions)
- `intent_sessions` (location captures)
- `verified_visits` (visit verification codes)
- `favorite_merchants` (user preferences)

**Merchant-Owned Data:**
- `domain_merchants` (business info, Nova balance)
- `merchant_perks` (exclusives/offers)
- `merchant_balance` (discount budgets)
- `merchant_balance_ledger` (balance transactions)
- `merchant_accounts` (owner account, location claims)

**System-Owned Data:**
- `users` (authentication, role flags)
- `chargers` (infrastructure data)
- `merchants` (Google Places cache)
- `nova_transactions` (immutable ledger)
- `admin_audit_logs` (compliance trail)

**Admin-Owned Data:**
- Admin actions logged in `admin_audit_logs` (actor_id = admin user_id)

### A2. Critical Relationships

```
users (1) ──< (many) exclusive_sessions (driver_id)
users (1) ──< (many) intent_sessions (user_id)
users (1) ──< (1) driver_wallets (user_id PK)
users (1) ──< (many) nova_transactions (driver_user_id)
users (1) ──< (many) verified_visits (driver_id)

domain_merchants (1) ──< (many) merchant_perks (merchant_id)
domain_merchants (1) ──< (many) nova_transactions (merchant_id)
domain_merchants (1) ──< (many) stripe_payments (merchant_id)

exclusive_sessions (many) ──> (1) merchants (merchant_id)
exclusive_sessions (many) ──> (1) chargers (charger_id)
exclusive_sessions (many) ──> (1) intent_sessions (intent_session_id)

chargers (1) ──< (many) charger_merchants (charger_id) ──> (many) merchants (merchant_id)
```

**Missing Foreign Keys (Documented):**
- `nova_transactions.driver_user_id` → `users.id` (no FK constraint, enforced in code)
- `nova_transactions.merchant_id` → `domain_merchants.id` (no FK constraint)

**Evidence:** `backend/app/models/domain.py:155` comment: "transactions relationship removed - query NovaTransaction directly via driver_user_id"

---

## B. MISSION CRITICALITY

### B1. Critical Path (Revenue Loss If Down)

| Endpoint Group | Endpoints | Why Critical | Failure Impact |
|----------------|-----------|--------------|----------------|
| **Driver Activation Flow** | `POST /v1/exclusive/activate`<br>`GET /v1/exclusive/active`<br>`POST /v1/exclusive/complete` | Core revenue driver - exclusive sessions generate merchant visits | Zero revenue if drivers cannot activate exclusives |
| **Intent Capture** | `POST /v1/intent/capture` | Primary discovery mechanism - finds merchants near chargers | Users cannot discover merchants, conversion drops to zero |
| **OTP Authentication** | `POST /v1/auth/otp/start`<br>`POST /v1/auth/otp/verify` | Required for exclusive activation (phone verification) | Drivers cannot authenticate, cannot activate exclusives |
| **Merchant Nearby** | `GET /v1/drivers/merchants/nearby` | Real-time merchant discovery for charging drivers | Drivers see no merchants, cannot activate exclusives |
| **Visit Verification** | `POST /v1/exclusive/verify-visit` | Generates verification codes for merchant redemption | Merchants cannot verify visits, no redemption flow |

**Files:** `backend/app/routers/exclusive.py`, `backend/app/routers/intent.py`, `backend/app/routers/auth_domain.py`

### B2. Operationally Critical (System Safety/Control)

| Endpoint Group | Endpoints | Why Critical | Failure Impact |
|----------------|-----------|--------------|----------------|
| **Admin Overrides** | `POST /v1/admin/sessions/force-close`<br>`POST /v1/admin/overrides/emergency-pause` | Emergency controls for system-wide issues | Cannot stop runaway sessions or pause system during incidents |
| **Admin Auth** | `POST /v1/auth/admin/login` | Admin portal access (now gated) | Cannot access admin controls during incidents |
| **Nova Grants** | `POST /v1/admin/nova/grant` | Manual Nova adjustments for support cases | Cannot resolve customer balance disputes |
| **Merchant Pause/Resume** | `POST /v1/admin/merchants/{id}/pause`<br>`POST /v1/admin/merchants/{id}/resume` | Merchant account control | Cannot disable abusive merchants |
| **Audit Logs** | `GET /v1/admin/logs` | Compliance and forensics | Cannot audit admin actions or investigate incidents |

**Files:** `backend/app/routers/admin_domain.py`, `backend/app/routers/auth_domain.py`

### B3. UX Degradation (Non-Critical Features)

| Endpoint Group | Endpoints | Impact If Down |
|----------------|-----------|----------------|
| **Merchant Analytics** | `GET /v1/merchants/analytics` | Merchants lose visibility into performance |
| **Driver Activity Feed** | `GET /v1/drivers/activity` | Drivers cannot see transaction history |
| **Favorites** | `POST /v1/drivers/favorites` | Cannot save favorite merchants |
| **Merchant Share Cards** | `GET /v1/merchants/{id}/share-card` | Cannot generate social share images |

### B4. Internal-Only (Admin, Diagnostics)

| Endpoint Group | Endpoints | Purpose |
|----------------|-----------|---------|
| **Admin Overview** | `GET /v1/admin/overview` | Dashboard stats (drivers, merchants, Nova, Stripe) |
| **Admin Exclusives** | `GET /v1/admin/exclusives`<br>`POST /v1/admin/exclusives/{id}/toggle` | Exclusive management |
| **Health Checks** | `GET /healthz`<br>`GET /readyz` | Kubernetes liveness/readiness probes |
| **Metrics** | `GET /metrics` | Prometheus metrics export |

**Total API Endpoints:** ~344 routes across 103 router files (grep count)

---

## C. PERFORMANCE & SCALING

### C1. Current Latency Bottlenecks

#### Database Query Bottlenecks

**1. Admin Overview Endpoint (`GET /v1/admin/overview`)**
- **Location:** `backend/app/routers/admin_domain.py:122-160`
- **Queries:** 6 sequential queries (no joins, but multiple round-trips)
  - `db.query(User).filter(User.role_flags.contains("driver")).count()`
  - `db.query(DomainMerchant).count()`
  - `db.query(func.sum(DriverWallet.nova_balance)).scalar()`
  - `db.query(func.sum(DomainMerchant.nova_balance)).scalar()`
  - `db.query(func.sum(StripePayment.amount_usd)).filter(...).scalar()`
- **Risk:** High - Dashboard loads slowly with large user base
- **Mitigation:** Add Redis caching (1min TTL) or materialized view

**2. Exclusives List Enrichment (`GET /v1/admin/exclusives`)**
- **Location:** `backend/app/routers/admin_domain.py:835-874`
- **Pattern:** N+1 query risk
  - Query all `MerchantPerk` records
  - For each exclusive, lookup `Merchant.name` (separate query per merchant)
  - Count `ExclusiveSession` activations per merchant (separate aggregation)
- **Risk:** Medium - Degrades with merchant count
- **Mitigation:** Use `joinedload()` or batch merchant lookups

**3. Merchant Nearby Query (`GET /v1/drivers/merchants/nearby`)**
- **Location:** `backend/app/routers/drivers_domain.py:80-156`
- **Query:** Spatial query with haversine distance calculation
- **Risk:** Medium - No spatial index on `(lat, lng)` - full table scan
- **Evidence:** `backend/app/models/while_you_charge.py:51` - no PostGIS/GiST index
- **Mitigation:** Add PostGIS extension or use bounding box pre-filter

#### External API Dependencies

**1. Google Places API**
- **Usage:** Merchant enrichment, nearby search
- **Location:** `backend/app/integrations/google_places_client.py`
- **Risk:** High - Single point of failure, rate limits (unknown quota)
- **Latency:** ~200-500ms per call (network + API processing)
- **Mitigation:** Aggressive caching (`MerchantCache` table, 1h TTL)

**2. Stripe API**
- **Usage:** Checkout session creation, webhook verification
- **Location:** `backend/app/services/stripe_service.py`
- **Risk:** Medium - Payment processing blocked if Stripe down
- **Latency:** ~100-300ms per call
- **Mitigation:** Webhook idempotency (`stripe_event_id` deduplication)

**3. Square API**
- **Usage:** Merchant payment processing (optional, per-merchant)
- **Location:** `backend/app/services/square_orders.py`
- **Risk:** Low - Only affects merchants with Square connected
- **Latency:** ~200-400ms per call
- **Mitigation:** Token encryption at rest, graceful degradation

**4. Smartcar API**
- **Usage:** Vehicle telemetry (optional feature)
- **Location:** `backend/app/services/smartcar_service.py`
- **Risk:** Low - Feature-flagged (`SMARTCAR_ENABLED=false` by default)
- **Latency:** ~300-600ms per call

#### Caching Gaps

**Current Caching:**
- Redis-backed layered cache (`backend/app/cache/layers.py`)
- `MerchantCache` table for Google Places data (1h TTL)
- In-memory L1 cache (1000 entry LRU, 5min default TTL)

**Missing Caching:**
- Admin overview stats (no cache)
- Exclusives list (no cache)
- Merchant nearby queries (no cache - spatial queries expensive)
- Charger lookups (no cache)

**Evidence:** `backend/app/core/config.py:99` - `MERCHANT_CACHE_TTL_SECONDS=3600` (only for merchant enrichment)

### C2. Scaling Roadmap (Multi-Region Deployment)

#### Data Partitioning Strategy

**Geographic Partitioning (Recommended):**
- Partition `exclusive_sessions` by `charger_id` → region mapping
- Partition `intent_sessions` by `lat/lng` → region boundaries
- Partition `merchants` by `city` or `zone_slug` → region assignment
- **Challenge:** Cross-region queries (driver travels between regions)

**Sharding Strategy:**
- Shard `users` by `public_id` hash → region assignment
- Shard `domain_merchants` by `zone_slug` → region assignment
- **Challenge:** User migration between regions (rare but possible)

#### State Synchronization

**Session State:**
- `exclusive_sessions` - Active sessions must be queryable across regions
- **Solution:** Redis-backed session registry (region → session_id mapping)
- **Conflict Resolution:** Last-write-wins (session updates are idempotent)

**Nova Balance:**
- `driver_wallets.nova_balance` - Must be consistent (financial data)
- **Solution:** Single-region writes, read replicas per region
- **Conflict Resolution:** Not applicable (single writer per wallet)

**Merchant Balance:**
- `domain_merchants.nova_balance` - Must be consistent
- **Solution:** Single-region writes, read replicas

#### Data Residency Handling

**PII Data:**
- `users.email`, `users.phone` - GDPR/CCPA requires EU data in EU
- **Solution:** Partition `users` by region, enforce residency rules
- **Challenge:** User travels to different region (replicate read-only copy)

**Location Data:**
- `intent_sessions.lat/lng` - May be considered PII in EU
- **Solution:** Store in region of capture, 90-day retention policy

**Audit Logs:**
- `admin_audit_logs` - Compliance requires long-term storage
- **Solution:** Centralized audit log region (single source of truth)

#### Database Connection Pooling

**Current Configuration:**
- **PostgreSQL:** `pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`, `pool_recycle=3600`
- **SQLite (dev):** `pool_size=5`, `max_overflow=0`
- **Location:** `backend/app/db.py:63-70`

**Assessment:** Adequate for single-region (<1000 concurrent users). Will need scaling for multi-region.

---

## D. GLOBAL COMPLIANCE (GDPR/CCPA/PIPEDA)

### D1. PII Fields & Storage Locations

#### PII Tables

| Table | PII Fields | Encryption | Retention |
|-------|------------|------------|-----------|
| `users` | `email`, `phone`, `password_hash` | Password: PBKDF2-SHA256 hash | Indefinite (user account lifetime) |
| `driver_wallets` | `apple_authentication_token` | Fernet encryption at rest | Indefinite |
| `domain_merchants` | `square_access_token` | Fernet encryption at rest | Indefinite |
| `intent_sessions` | `lat`, `lng` (location = PII in EU) | None | No explicit retention (indefinite) |
| `exclusive_sessions` | `activation_lat`, `activation_lng` | None | Session expires (60min), data retained |
| `verified_visits` | `driver_id`, `merchant_id` (linkage) | None | Indefinite |
| `vehicle_onboarding` | `photo_urls` (S3 URLs), `license_plate` | None | 90 days (`expires_at` field) |
| `claim_sessions` | `email`, `phone` | None | Session expires (24h), data retained |

**Evidence:**
- Password hashing: `backend/app/core/security.py:15` - `CryptContext(schemes=["pbkdf2_sha256"])`
- Token encryption: `backend/app/services/token_encryption.py:141-167` - Fernet encryption
- Vehicle onboarding retention: `backend/app/models/vehicle_onboarding.py:42` - `expires_at` (90 days)

#### Encryption-at-Rest Coverage

**Encrypted Fields:**
- ✅ `driver_wallets.apple_authentication_token` (Fernet)
- ✅ `domain_merchants.square_access_token` (Fernet)
- ✅ `users.password_hash` (PBKDF2-SHA256 hash, one-way)

**Unencrypted PII:**
- ❌ `users.email` (plaintext, indexed)
- ❌ `users.phone` (plaintext, indexed)
- ❌ `intent_sessions.lat/lng` (plaintext)
- ❌ `exclusive_sessions.activation_lat/lng` (plaintext)
- ❌ `claim_sessions.email/phone` (plaintext)

**Risk:** Medium - Email/phone in plaintext violates GDPR "data protection by design" principle.

**Mitigation:** Consider field-level encryption for email/phone (trade-off: searchability vs. compliance).

#### Encryption-in-Transit

**HTTPS Enforcement:**
- ✅ Landing page: Security headers in `apps/landing/next.config.mjs` (HSTS preload)
- ✅ Backend: CORS middleware validates HTTPS origins in production
- ⚠️ **Gap:** CTA links were HTTP (fixed in implementation: now HTTPS)

**Evidence:** `backend/app/main.py:90-95` - CORS wildcard rejection in non-local environments

### D2. Right-to-Erasure Feasibility

#### Deletion Capabilities

**User Account Deletion:**
- **Current:** No explicit deletion endpoint
- **Required:** `DELETE /v1/users/{id}` or `POST /v1/users/{id}/delete`
- **Challenges:**
  - `nova_transactions` - Immutable ledger (cannot delete, must anonymize)
  - `admin_audit_logs` - Compliance requirement (cannot delete, must anonymize)
  - `exclusive_sessions` - Historical data (anonymize `driver_id`)

**Anonymization Strategy:**
- Replace `users.email` → `deleted_user_{id}@deleted.local`
- Replace `users.phone` → `+00000000000`
- Replace `exclusive_sessions.driver_id` → `-1` (deleted user marker)
- Keep `nova_transactions` with anonymized `driver_user_id`

**Evidence:** No deletion endpoint found in `backend/app/routers/users.py` or `backend/app/routers/account.py`

#### Audit Trail for Deletions

**Current:** `admin_audit_logs` tracks admin actions but not user-initiated deletions
**Gap:** No audit log entry when user requests account deletion
**Recommendation:** Add `log_admin_action()` call in deletion endpoint

### D3. Consent Logging & Data Minimization

#### Consent Tracking

**Current State:**
- ❌ No explicit consent logging table
- ❌ No consent withdrawal mechanism
- ⚠️ **Gap:** Phone OTP implies consent but not logged

**Evidence:** No `user_consents` table found in models

#### Data Minimization Gaps

**Over-Collection:**
- `intent_sessions` stores location data indefinitely (no retention policy)
- `exclusive_sessions` stores location data after session expiration
- `verified_visits` stores visit data indefinitely

**Recommendation:**
- Add retention policies: `intent_sessions` → 90 days, `exclusive_sessions` → 1 year (anonymized)
- Add data retention job: `DELETE FROM intent_sessions WHERE created_at < NOW() - INTERVAL '90 days'`

---

## E. TECHNICAL DEBT & RISK

### E1. Black Box Logic & Legacy Dependencies

#### Deprecated Endpoints (Still Active)

**Pilot Router (`/v1/pilot/*`):**
- **Status:** Marked `deprecated=True` but still included in `main.py`
- **Endpoints:** 6 deprecated endpoints (start_session, verify_ping, while_you_charge, session/cancel, activity)
- **Risk:** Low - Frontend migrated to `/v1/*` endpoints, but backend still serves deprecated routes
- **Blast Radius:** Low - Only affects legacy clients
- **Files:** `backend/app/routers/pilot.py`, `backend/PILOT_DEPRECATION_STATUS.md`

**Evidence:** `backend/app/routers/pilot.py:69` - `@router.post("/start_session", deprecated=True)`

#### Legacy Code Blocks

**Legacy Server Code:**
- **Location:** `backend/server/src/routes_square.py`
- **Status:** Deployment guard prevents import in production (`ENV != "local"`)
- **Risk:** Low - Guarded, but code still exists
- **Blast Radius:** None (cannot be imported in prod)

**Evidence:** `backend/server/src/routes_square.py:12-21` - RuntimeError guard

#### Duplicate Implementations

**Auth Routers:**
- `backend/app/routers/auth.py` - Legacy auth endpoints (`/auth/*`)
- `backend/app/routers/auth_domain.py` - Canonical auth endpoints (`/v1/auth/*`)
- **Status:** Both active, legacy kept for backward compatibility
- **Risk:** Low - Maintenance burden (two code paths)

**Evidence:** `backend/app/main.py:136` - "LEGACY: auth_router kept for backward compatibility"

**Merchant Routers:**
- `backend/app/routers/merchants.py` - Legacy merchant endpoints
- `backend/app/routers/merchants_domain.py` - Canonical merchant endpoints (`/v1/merchants/*`)
- **Status:** Both active, potential route conflicts
- **Risk:** Medium - Route conflicts possible

**Evidence:** `backend/PROMOTION_TO_V1_STATUS.md:14` - "Conflicts Identified: `/v1/merchants`"

### E2. Brittle Components & Over-Coupling

#### Missing Foreign Key Constraints

**NovaTransaction Relationships:**
- `nova_transactions.driver_user_id` → `users.id` (no FK, enforced in code)
- `nova_transactions.merchant_id` → `domain_merchants.id` (no FK)
- **Risk:** Medium - Data integrity relies on application logic
- **Blast Radius:** High - Financial data corruption if bug introduced

**Evidence:** `backend/app/models/domain.py:155` - Comment: "transactions relationship removed - query NovaTransaction directly"

#### Hardcoded Business Logic

**Domain Hub Hardcoding:**
- **Location:** `backend/app/routers/pilot.py:20` - `from app.domains.domain_hub import HUB_ID, HUB_NAME, DOMAIN_CHARGERS`
- **Risk:** Low - Pilot-specific, but indicates tight coupling
- **Blast Radius:** Low - Only affects pilot flow

**Zone Slug Hardcoding:**
- **Location:** `backend/app/routers/merchants_domain.py:30-32` - `DOMAIN_CENTER_LAT/LNG`, `DOMAIN_RADIUS_M`
- **Risk:** Low - Single-zone MVP, but not scalable
- **Blast Radius:** Medium - Cannot add new zones without code changes

### E3. Undocumented Flows

#### Exclusive Session State Machine

**States:** `ACTIVE`, `COMPLETED`, `EXPIRED`, `CANCELED`
**Transitions:** Not documented in code comments
**Risk:** Medium - State transition bugs difficult to debug
**Evidence:** `backend/app/models/exclusive_session.py:15-20` - Enum defined but no state machine doc

#### Nova Transaction Types

**Types:** `driver_earn`, `driver_redeem`, `merchant_topup`, `admin_grant`
**Business Rules:** Not documented (when each type is used)
**Risk:** Low - Code is readable, but no formal documentation
**Evidence:** `backend/app/models/domain.py:222` - `type = Column(String, nullable=False)`

#### Intent Capture Confidence Tiers

**Tiers:** A (<120m), B (<400m), C (no charger)
**Logic:** Documented in endpoint docstring but not in config
**Risk:** Low - Well-documented in `backend/app/routers/intent.py:45-48`

### E4. Risk Quantification

| Risk | Severity | Blast Radius | Likelihood | Mitigation Priority |
|------|----------|--------------|------------|---------------------|
| Admin portal unauthenticated access | **CRITICAL** | Entire system | **HIGH** (was P0, now fixed) | ✅ Fixed |
| Missing FK constraints on NovaTransaction | **HIGH** | Financial data integrity | **MEDIUM** | P1 - Add FK constraints |
| Google Places API dependency | **HIGH** | Merchant discovery | **MEDIUM** | P1 - Add fallback/cache |
| No data retention policies | **MEDIUM** | GDPR compliance | **HIGH** | P1 - Add retention jobs |
| Deprecated pilot endpoints still active | **LOW** | Legacy clients | **LOW** | P2 - Remove after migration |
| Duplicate auth/merchant routers | **LOW** | Maintenance burden | **MEDIUM** | P2 - Consolidate |

---

## F. CEO SUMMARY (1 Page)

### Top 5 Risks

1. **Admin Portal Was Unauthenticated** (FIXED)
   - **Status:** ✅ Fixed in implementation (auth gate added)
   - **Was:** Anyone with URL had full admin access
   - **Impact:** Could have caused data breaches, system-wide damage

2. **Missing Foreign Key Constraints on Financial Data**
   - **Location:** `nova_transactions` table
   - **Risk:** Data integrity relies on application logic (no DB-level enforcement)
   - **Impact:** Financial discrepancies if bug introduced
   - **Mitigation:** Add FK constraints in next migration

3. **Google Places API Single Point of Failure**
   - **Dependency:** Merchant discovery requires Google Places API
   - **Risk:** If API down/rate-limited, zero merchant discovery
   - **Impact:** Complete revenue loss during outage
   - **Mitigation:** Aggressive caching (1h TTL) + fallback to cached data

4. **No Data Retention Policies for Location Data**
   - **Gap:** `intent_sessions`, `exclusive_sessions` store location data indefinitely
   - **Risk:** GDPR violation (location = PII in EU)
   - **Impact:** Regulatory fines, compliance issues
   - **Mitigation:** Add 90-day retention policy + automated cleanup job

5. **Database Query Performance Degrades with Scale**
   - **Bottlenecks:** Admin overview (6 sequential queries), exclusives list (N+1 queries)
   - **Risk:** Dashboard becomes unusable with large user base
   - **Impact:** Admin productivity loss, poor UX
   - **Mitigation:** Add Redis caching, optimize queries with joins

### Top 5 Opportunities

1. **Multi-Region Deployment Ready**
   - **Strength:** Clean separation of concerns, Redis-backed caching layer exists
   - **Opportunity:** Geographic expansion (EU, Asia) with data residency compliance
   - **Value:** 10x user base expansion potential

2. **Comprehensive Audit Logging**
   - **Strength:** `admin_audit_logs` tracks all admin actions with before/after snapshots
   - **Opportunity:** Build compliance dashboard, automated anomaly detection
   - **Value:** SOC 2 / ISO 27001 certification readiness

3. **Token Encryption Infrastructure**
   - **Strength:** Fernet encryption service exists, used for Square/Apple tokens
   - **Opportunity:** Extend to email/phone encryption (field-level)
   - **Value:** Enhanced GDPR compliance, reduced breach impact

4. **Layered Caching Architecture**
   - **Strength:** L1 (memory) + L2 (Redis) cache layer implemented
   - **Opportunity:** Apply caching to admin endpoints, merchant queries
   - **Value:** 10x performance improvement, reduced database load

5. **Feature Flag System**
   - **Strength:** Feature flags exist (`FEATURE_FLAGS` in frontend, env vars in backend)
   - **Opportunity:** Build feature flag dashboard, A/B testing infrastructure
   - **Value:** Faster feature rollouts, risk-free experimentation

### What Must Be Fixed Before Public Scale

**P0 (Ship Blockers - FIXED):**
- ✅ Admin portal authentication (was unauthenticated)
- ✅ Missing backend endpoints (7 endpoints added)
- ✅ Contract mismatches (exclusives toggle fixed)

**P1 (Must Fix Before Scale):**
1. **Add FK constraints** to `nova_transactions` (financial data integrity)
2. **Implement data retention policies** (90-day cleanup for `intent_sessions`, `exclusive_sessions`)
3. **Add caching** to admin overview endpoint (Redis, 1min TTL)
4. **Optimize exclusives list query** (batch merchant lookups, avoid N+1)
5. **Add user deletion endpoint** with anonymization (GDPR right-to-erasure)

**P2 (Post-Launch Polish):**
- Remove deprecated pilot endpoints
- Consolidate duplicate auth/merchant routers
- Add PostGIS spatial indexes for merchant queries
- Build feature flag dashboard

---

## APPENDIX: File Reference Map

### Critical Files
- **Database Models:** `backend/app/models/` (18 model files)
- **API Routers:** `backend/app/routers/` (103 router files, ~344 endpoints)
- **Auth Middleware:** `backend/app/middleware/auth.py`
- **Token Encryption:** `backend/app/services/token_encryption.py`
- **Database Config:** `backend/app/db.py`
- **Admin Domain Router:** `backend/app/routers/admin_domain.py` (25 endpoints)

### Compliance Files
- **Audit Logging:** `backend/app/services/audit.py`
- **Secret Filtering:** `backend/app/services/audit.py:18-23` (SECRET_FIELDS list)
- **Token Encryption:** `backend/app/services/token_encryption.py:141-214`

### Performance Files
- **Caching:** `backend/app/cache/layers.py` (L1+L2 cache)
- **Database Pooling:** `backend/app/db.py:63-70` (PostgreSQL: pool_size=20)
- **Merchant Cache:** `backend/app/models/merchant_cache.py` (TTL-based)

---

**Report Generated:** 2026-01-27  
**Codebase Snapshot:** Post-implementation fixes (admin auth, endpoints, contracts)  
**Next Review:** After multi-region deployment planning
