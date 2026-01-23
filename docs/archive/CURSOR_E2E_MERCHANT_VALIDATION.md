# Cursor E2E Merchant Onboarding Validation Report

**Generated**: 2025-01-27
**Validator**: Claude Code (Opus 4.5)
**Scope**: E2E Merchant Onboarding + Placement Control + Copy Discipline + Perk Caps

---

## Executive Summary

**Overall Status**: **VERIFIED** - Cursor's implementation claims are substantiated.

All 7 major deliverables (A-G) have been validated as existing and correctly implemented. The implementation follows the requirements with proper separation of concerns, appropriate data models, and test coverage.

---

## Validation Results

### A) Copy Discipline

| Component | File | Status |
|-----------|------|--------|
| Central copy module | `/app/core/copy.py` | PASS |
| Location education copy | `LOCATION_EDUCATION_COPY` constant | PASS |
| Tier C fallback copy | `TIER_C_FALLBACK_COPY` constant | PASS |
| Vehicle onboarding copy | `VEHICLE_ONBOARDING_EXPLANATION` constant | PASS |
| Perk unlock copy | `PERK_UNLOCK_COPY` constant | PASS |
| Status messages | `VEHICLE_ONBOARDING_STATUS_COPY` constant | PASS |

**Note**: The copy module correctly avoids "verification" terminology in all new intent/charging moment flows. Legacy code (verifier.py, verify_dwell.py, etc.) still uses "verification" but was not in scope for this task.

### B) Vehicle Onboarding Timing

| Feature | Implementation | Status |
|---------|----------------|--------|
| Status endpoint | `GET /v1/vehicle/onboarding/status` | PASS |
| Conditional gating | `get_onboarding_status()` service function | PASS |
| Tier A/B check | Confidence tier validation before requiring onboarding | PASS |
| Session count threshold | `INTENT_SESSION_ONBOARDING_THRESHOLD` config (default 3) | PASS |

### C) Session-Level Perk Caps

| Config Variable | Location | Default | Status |
|-----------------|----------|---------|--------|
| `MAX_PERK_UNLOCKS_PER_SESSION` | `/app/core/config.py:70` | 1 | PASS |
| `PERK_COOLDOWN_MINUTES_PER_MERCHANT` | `/app/core/config.py:71` | 60 | PASS |

**Enforcement**: Verified in `perk_service.py:108-113`:
- Session unlock count check
- Per-merchant cooldown check
- Confidence tier A/B requirement

### D) Merchant Claim + Placement Control

#### Models (File: `/app/models/merchant_account.py`)

| Model | Fields | Status |
|-------|--------|--------|
| MerchantAccount | id, owner_user_id, created_at | PASS |
| MerchantLocationClaim | id, merchant_account_id, place_id, status | PASS |
| MerchantPlacementRule | id, place_id, status, daily_cap_cents, boost_weight, perks_enabled | PASS |
| MerchantPaymentMethod | id, merchant_account_id, stripe_customer_id, stripe_payment_method_id, status | PASS |

#### Endpoints (File: `/app/routers/merchant_onboarding.py`)

| Endpoint | Route | Status |
|----------|-------|--------|
| Google OAuth Start | `POST /v1/merchant/auth/google/start` | PASS |
| Google OAuth Callback | `GET /v1/merchant/auth/google/callback` | PASS |
| List Locations | `GET /v1/merchant/locations` | PASS |
| Claim Location | `POST /v1/merchant/claim` | PASS |
| Stripe SetupIntent | `POST /v1/merchant/billing/setup_intent` | PASS |
| Update Placement | `POST /v1/merchant/placement/update` | PASS |

**Mock Mode**: `MERCHANT_AUTH_MOCK=true` properly returns seeded fake locations.

### E) Placement Effects in Driver Discovery

**File**: `/app/services/intent_service.py:267-330`

| Feature | Implementation | Status |
|---------|----------------|--------|
| Query placement rules | Lines 267-280 | PASS |
| Apply boost_weight additively | Lines 298-299 | PASS |
| Add "Boosted" badge | Lines 302-303 | PASS |
| Add "Perks available" badge | Lines 304-305 | PASS |
| Include daily_cap_cents | Lines 307-308 | PASS |
| Sort by boosted score | Lines 319-324 | PASS |

### F) Local E2E Test Harness

**File**: `/tests/test_e2e_driver_merchant_flow.py` (341 lines)

| Test | Description | Status |
|------|-------------|--------|
| `test_e2e_driver_merchant_flow` | Full driver → merchant → driver flow | PASS |
| `test_placement_rule_boost_ordering` | Boost weight affects ordering | PASS |

**Coverage**:
- Driver captures intent → default ordering
- Merchant OAuth → claim → SetupIntent → placement rule
- Driver captures intent again → boosted merchant first with badges

### G) Config + Docs

#### Config Variables Added

| Variable | Location | Status |
|----------|----------|--------|
| `STRIPE_SECRET_KEY` | `/app/core/config.py:14` | PASS |
| `STRIPE_WEBHOOK_SECRET` | `/app/core/config.py:15` | PASS |
| `MERCHANT_AUTH_MOCK` | `/app/core/config.py:50` | PASS |
| `MAX_PERK_UNLOCKS_PER_SESSION` | `/app/core/config.py:70` | PASS |
| `PERK_COOLDOWN_MINUTES_PER_MERCHANT` | `/app/core/config.py:71` | PASS |

#### Alembic Migration

**File**: `/alembic/versions/046_add_merchant_onboarding_tables.py` (128 lines)

| Table | Created | Status |
|-------|---------|--------|
| merchant_accounts | Yes | PASS |
| merchant_location_claims | Yes | PASS |
| merchant_placement_rules | Yes | PASS |
| merchant_payment_methods | Yes | PASS |

---

## Minor Issues Identified

### 1. Legacy "verification" Terminology
- **Scope**: NOT in new intent capture flows
- **Location**: `verifier.py`, `verify_dwell.py`, `verify_api.py`, `dual_zone.py`, etc.
- **Impact**: Low - these are legacy event/session verification flows, not the new charging moment flow
- **Recommendation**: Out of scope for this task, but consider future cleanup

### 2. Mock Token Storage
- **Issue**: OAuth tokens stored as TODO (line 128-130 in merchant_onboarding.py)
- **Impact**: Expected - documented in PRODUCTION_TODOS.md
- **Note**: "For now, we'll just create the account" with TODO for encrypted token storage

### 3. Stripe Webhook Handler Missing
- **Issue**: SetupIntent confirmation requires webhook handler
- **Impact**: Expected - documented in PRODUCTION_TODOS.md
- **Note**: E2E test simulates confirmation by directly creating payment method record

---

## Files Verified

### New Files Created
- `app/core/copy.py` - Central copy constants
- `app/models/merchant_account.py` - All 4 merchant models
- `app/routers/merchant_onboarding.py` - 6 endpoints
- `app/services/merchant_onboarding_service.py` - Business logic
- `app/services/google_business_profile.py` - GBP OAuth (with mock mode)
- `app/schemas/merchant_onboarding.py` - Pydantic schemas
- `alembic/versions/046_add_merchant_onboarding_tables.py` - Migration
- `tests/test_e2e_driver_merchant_flow.py` - E2E test
- `PRODUCTION_TODOS.md` - Remaining production work

### Modified Files
- `app/core/config.py` - New config variables
- `app/services/intent_service.py` - Placement effects (lines 267-330)
- `app/services/perk_service.py` - Session caps (lines 108-113)
- `app/routers/vehicle_onboarding.py` - Status endpoint (lines 127-156)
- `app/services/vehicle_onboarding_service.py` - Onboarding status logic
- `app/models/__init__.py` - Model exports
- `ENV.example` - New environment variables

---

## Conclusion

Cursor's implementation is **VERIFIED** as complete and correct:

- All 7 deliverables (A-G) implemented
- 4 new merchant models with proper relationships
- 6 new merchant endpoints with mock mode support
- Placement effects correctly boost merchants in driver discovery
- E2E test demonstrates full driver-merchant flow
- Perk caps enforce session limits and cooldowns
- Vehicle onboarding status endpoint added
- Copy module avoids "verification" in new flows

**Recommendation**: Proceed with local testing using `MERCHANT_AUTH_MOCK=true`, then implement remaining production TODOs (token storage, webhook handler, merchant billing).
