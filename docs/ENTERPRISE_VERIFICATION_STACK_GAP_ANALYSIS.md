# NERAVA ENTERPRISE VERIFICATION STACK: GAP ANALYSIS REPORT

**Prepared by:** Staff Engineer + Product Architect + Security Reviewer
**Date:** 2026-02-16
**Scope:** Fleet API → Toast Read → Stripe Payouts

---

## EXECUTIVE SUMMARY

1. **Fleet API integration exists as skeleton only** - Partner token generation not implemented; requires Tesla Developer Partner account approval (external dependency)

2. **Current verification is geofence-only** - No cryptographic proof of charging; spoofable with location mocking

3. **POS integration is stub-only** - Toast/Square adapters return hardcoded "unknown"; entire billing relies on driver-entered data

4. **No sponsor/budget infrastructure exists** - Current Nova system is merchant-funded credits, not sponsor-funded rewards

5. **Stripe integration is purchase-only** - No payout capability; missing Connect accounts, KYC, disbursement

6. **Fraud controls are minimal** - Device fingerprint exists but no velocity checks, pattern detection, or risk scoring

7. **Ledger is not auditable** - NovaTransaction exists but lacks escrow semantics, breakage rules, or reconciliation

8. **Can ship Fleet verification MVP in Sprint 1** - If Tesla Partner credentials are obtained

9. **Stripe Payouts requires Connect onboarding** - 2-3 week minimum for production approval

10. **Toast Read requires Partner API access** - Separate workstream; 4-6 week partnership timeline

---

## A) SYSTEM MAPPING: Current → Target

### Entities That Can Be Reused

| Current Entity | Target Use | Modifications Needed |
|----------------|------------|---------------------|
| `ArrivalSession` | `RewardSession` anchor | Add `sponsor_program_id`, `reward_status`, `verification_evidence_id` |
| `User` | Driver identity | Add `stripe_connect_account_id`, `kyc_status` |
| `VirtualKey` | Fleet API vehicle binding | Already structured correctly; needs telemetry polling |
| `BillingEvent` | Audit trail only | Keep for merchant billing; separate from driver rewards |
| `NovaTransaction` | Internal ledger reference | Extend for sponsor budget deductions |
| `Charger` | Location anchor | No changes needed |
| `Merchant` | Commerce anchor | Add `toast_restaurant_guid` if not using separate credentials table |

### Entities to Deprecate

| Entity | Reason | Migration Path |
|--------|--------|----------------|
| `DriverWallet.nova_balance` | Replaced by sponsor-funded rewards | Freeze; no new grants |
| `MerchantBalance` | Not relevant to driver payouts | Keep for legacy merchant discounts |
| `ChargeIntent` | Superseded by ArrivalSession | Already unused; delete migration |
| `StripePayment` (Nova purchases) | Reversed flow (payouts not purchases) | Keep for historical; new table for payouts |

### Entities Requiring Refactor

| Entity | Current State | Target State |
|--------|---------------|--------------|
| `VirtualKey` | Provisioning-focused | Add `last_charging_session_id`, `telemetry_state` JSONB |
| `ArrivalSession` | Order/merchant-centric | Add verification evidence linkage |
| `NovaTransaction` | Simple credit/debit | Add `sponsor_budget_id`, `reward_event_id` FK |

### Verification Definition (New Stack)

| Verification Type | Current | Target |
|-------------------|---------|--------|
| **Charging Verified** | ❌ Geofence only (spoofable) | ✅ Fleet API session data (cryptographic) |
| **Dwell Verified** | ⚠️ Location + time heuristics | ✅ Location + time + optional order |
| **Spend Verified** | ❌ Driver-entered only | ✅ Toast Read (later phase) |

---

## B) GAP ANALYSIS TABLE

| # | Capability | Current Status | Needed Changes | Risk | Effort | Dependencies |
|---|------------|----------------|----------------|------|--------|--------------|
| **1** | **Fleet API Auth** | Missing | Implement partner token flow, OAuth for vehicles | High | M | Tesla Partner account approval |
| **2** | **Fleet API Data Model** | Partial (`VirtualKey` exists) | Add `fleet_sessions` table, telemetry JSONB | Med | S | #1 |
| **3** | **Fleet API Polling** | Missing | Background task polling vehicle charge state | Med | M | Redis/Celery, #1 |
| **4** | **Fleet API Webhooks** | Stub only | Implement webhook receiver, signature validation | Med | S | Tesla webhook registration |
| **5** | **Fleet API Rate Limits** | Missing | Implement token bucket, backoff, caching | Low | S | Redis |
| **6** | **Charging Session Verification Logic** | Missing | Define thresholds, edge cases, evidence capture | High | M | Product decision |
| **7** | **Fraud: Location Binding** | Partial (accuracy tracked) | Cross-check Fleet location vs app location | Med | S | #1 |
| **8** | **Fraud: Replay Prevention** | Missing | Signed payloads, nonce, timestamp validation | High | M | - |
| **9** | **Fraud: Velocity Checks** | Missing | N rewards in T hours limit per user | Med | S | Redis |
| **10** | **Fraud: Device Binding** | Partial (fingerprint) | Persistent device registry, attestation | Med | M | - |
| **11** | **Sponsor Model** | Missing | `sponsors`, `sponsor_programs`, `sponsor_budgets` tables | High | M | - |
| **12** | **Reward Events Ledger** | Missing | `reward_events` table with full evidence | High | M | #6, #11 |
| **13** | **Budget Escrow Logic** | Missing | Reserve → confirm → release/refund pattern | High | M | #11 |
| **14** | **Breakage Rules** | Missing | Expiry, forfeiture, rollover logic | Med | S | Product decision |
| **15** | **Reward Issuance Rules** | Missing | Eligibility checks, caps, frequency limits | High | M | #11 |
| **16** | **Stripe Connect Setup** | Missing | Create Connect accounts for drivers | High | L | Stripe approval, KYC flow |
| **17** | **Stripe Payout Batching** | Missing | Batch payouts, min thresholds, scheduling | Med | M | #16 |
| **18** | **Stripe Webhook (Payouts)** | Missing | Handle payout.paid, payout.failed events | Med | S | #16 |
| **19** | **PostHog Events** | Partial | Add reward funnel events, verification outcomes | Low | S | - |
| **20** | **Audit Trail** | Partial | Immutable event log, admin action logging | Med | M | - |
| **21** | **Admin: Dispute Resolution** | Missing | View evidence, manual override, clawback | Med | M | #12 |
| **22** | **Admin: Budget Management** | Missing | Fund/pause/adjust sponsor budgets | Med | S | #11 |
| **23** | **Toast Read Integration** | Stub only | Implement Partner API, order lookup | Med | L | Toast Partner approval |
| **24** | **Square Read Integration** | Stub only | Implement order lookup | Low | M | Square API key |

### Risk Legend
- **High**: Blocks launch or creates liability
- **Med**: Degrades experience or creates operational burden
- **Low**: Nice-to-have for v1

### Effort Legend
- **S**: < 2 days
- **M**: 2-5 days
- **L**: > 5 days

---

## C) DATA MODEL CHANGES (Proposed Migrations)

### New Tables

```sql
-- Migration 067: Create sponsors table
CREATE TABLE sponsors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    legal_entity_name VARCHAR(255),
    billing_email VARCHAR(255) NOT NULL,
    stripe_customer_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active', -- active, paused, suspended
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Migration 068: Create sponsor_programs table
CREATE TABLE sponsor_programs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sponsor_id UUID NOT NULL REFERENCES sponsors(id),
    name VARCHAR(255) NOT NULL,
    program_type VARCHAR(50) NOT NULL, -- charging_reward, dwell_reward, spend_match

    -- Eligibility rules (JSONB for flexibility)
    eligibility_rules JSONB DEFAULT '{}',
    -- e.g., {"min_charge_kwh": 5, "min_dwell_minutes": 15, "merchant_categories": ["restaurant"]}

    -- Reward configuration
    reward_amount_cents INTEGER NOT NULL,
    reward_type VARCHAR(50) DEFAULT 'cash', -- cash, credit
    max_rewards_per_user_per_day INTEGER DEFAULT 1,
    max_rewards_per_user_total INTEGER,

    -- Geographic restrictions
    geo_restriction JSONB, -- {"type": "radius", "center_lat": 30.26, "center_lng": -97.74, "radius_m": 50000}

    -- Time restrictions
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    active_hours JSONB, -- {"mon": ["11:00-14:00", "17:00-21:00"], ...}

    status VARCHAR(50) DEFAULT 'active', -- draft, active, paused, exhausted, expired
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sponsor_programs_sponsor ON sponsor_programs(sponsor_id);
CREATE INDEX idx_sponsor_programs_status ON sponsor_programs(status);

-- Migration 069: Create sponsor_budgets table
CREATE TABLE sponsor_budgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sponsor_id UUID NOT NULL REFERENCES sponsors(id),
    program_id UUID REFERENCES sponsor_programs(id), -- NULL = sponsor-level budget

    funded_amount_cents BIGINT NOT NULL,
    reserved_amount_cents BIGINT DEFAULT 0, -- pending verification
    spent_amount_cents BIGINT DEFAULT 0, -- confirmed rewards

    -- Breakage tracking
    expired_amount_cents BIGINT DEFAULT 0,
    forfeited_amount_cents BIGINT DEFAULT 0,

    funding_source VARCHAR(50), -- stripe_invoice, wire, prepaid
    stripe_payment_intent_id VARCHAR(255),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_sponsor_budgets_sponsor ON sponsor_budgets(sponsor_id);
CREATE INDEX idx_sponsor_budgets_program ON sponsor_budgets(program_id);

-- Migration 070: Create reward_events table (core ledger)
CREATE TABLE reward_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Linkages
    user_id UUID NOT NULL REFERENCES users(id),
    sponsor_program_id UUID NOT NULL REFERENCES sponsor_programs(id),
    sponsor_budget_id UUID NOT NULL REFERENCES sponsor_budgets(id),
    arrival_session_id UUID REFERENCES arrival_sessions(id),

    -- Reward details
    amount_cents INTEGER NOT NULL,
    reward_type VARCHAR(50) NOT NULL, -- cash, credit

    -- Lifecycle
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending → verified → issued → paid (or: rejected, expired, clawed_back)

    -- Verification evidence
    verification_method VARCHAR(50), -- fleet_api, geofence_dwell, toast_order
    verification_evidence_id UUID REFERENCES verification_evidence(id),
    verified_at TIMESTAMP,

    -- Issuance
    issued_at TIMESTAMP,

    -- Payout
    payout_id UUID REFERENCES payouts(id),
    paid_at TIMESTAMP,

    -- Audit
    rejection_reason VARCHAR(255),
    clawback_reason VARCHAR(255),
    admin_notes TEXT,

    -- Idempotency
    idempotency_key VARCHAR(255) UNIQUE,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_reward_events_user ON reward_events(user_id);
CREATE INDEX idx_reward_events_program ON reward_events(sponsor_program_id);
CREATE INDEX idx_reward_events_status ON reward_events(status);
CREATE INDEX idx_reward_events_created ON reward_events(created_at);

-- Migration 071: Create verification_evidence table
CREATE TABLE verification_evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source identification
    verification_type VARCHAR(50) NOT NULL, -- fleet_session, geofence, toast_order

    -- Fleet API evidence
    fleet_session_id VARCHAR(255),
    fleet_vehicle_id VARCHAR(255),
    charge_start_time TIMESTAMP,
    charge_end_time TIMESTAMP,
    energy_added_kwh DECIMAL(10, 3),
    charger_id_from_fleet VARCHAR(255),

    -- Geofence evidence
    app_lat DECIMAL(10, 7),
    app_lng DECIMAL(10, 7),
    app_accuracy_m DECIMAL(10, 2),
    app_timestamp TIMESTAMP,

    -- Location cross-check
    fleet_lat DECIMAL(10, 7),
    fleet_lng DECIMAL(10, 7),
    location_delta_m DECIMAL(10, 2),

    -- Toast evidence
    toast_order_guid VARCHAR(255),
    toast_order_total_cents INTEGER,
    toast_order_items JSONB,

    -- Device binding
    device_fingerprint VARCHAR(64),
    device_attestation JSONB, -- iOS DeviceCheck / Android SafetyNet

    -- Raw payloads (for audit)
    raw_fleet_response JSONB,
    raw_toast_response JSONB,

    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_verification_evidence_fleet_session ON verification_evidence(fleet_session_id);
CREATE INDEX idx_verification_evidence_type ON verification_evidence(verification_type);

-- Migration 072: Create payouts table
CREATE TABLE payouts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Amounts
    gross_amount_cents INTEGER NOT NULL,
    fee_amount_cents INTEGER DEFAULT 0,
    net_amount_cents INTEGER NOT NULL,

    -- Stripe
    stripe_payout_id VARCHAR(255),
    stripe_transfer_id VARCHAR(255),
    stripe_connect_account_id VARCHAR(255) NOT NULL,

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- pending → processing → paid → (failed, reversed)

    -- Metadata
    reward_event_count INTEGER,
    period_start TIMESTAMP,
    period_end TIMESTAMP,

    -- Audit
    initiated_at TIMESTAMP,
    completed_at TIMESTAMP,
    failed_at TIMESTAMP,
    failure_reason VARCHAR(255),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_payouts_user ON payouts(user_id);
CREATE INDEX idx_payouts_status ON payouts(status);
CREATE INDEX idx_payouts_stripe ON payouts(stripe_payout_id);

-- Migration 073: Create vehicle_identities table
CREATE TABLE vehicle_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),

    -- Provider
    provider VARCHAR(50) NOT NULL, -- tesla, smartcar (future)
    provider_vehicle_id VARCHAR(255) NOT NULL,
    vin VARCHAR(17),

    -- OAuth tokens (encrypted)
    access_token_encrypted TEXT,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMP,

    -- Vehicle metadata
    vehicle_name VARCHAR(255),
    vehicle_model VARCHAR(255),
    vehicle_year INTEGER,

    -- Virtual key linkage
    virtual_key_id UUID REFERENCES virtual_keys(id),

    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, revoked, expired
    last_telemetry_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(provider, provider_vehicle_id)
);
CREATE INDEX idx_vehicle_identities_user ON vehicle_identities(user_id);
CREATE INDEX idx_vehicle_identities_provider ON vehicle_identities(provider, provider_vehicle_id);

-- Migration 074: Create fleet_sessions table (cached Fleet API data)
CREATE TABLE fleet_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_identity_id UUID NOT NULL REFERENCES vehicle_identities(id),

    -- Fleet API identifiers
    fleet_session_id VARCHAR(255) UNIQUE,

    -- Session data
    charger_id VARCHAR(255),
    charger_name VARCHAR(255),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,

    -- Charging metrics
    energy_added_kwh DECIMAL(10, 3),
    max_charge_rate_kw DECIMAL(10, 2),
    start_battery_percent INTEGER,
    end_battery_percent INTEGER,

    -- Location
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),

    -- Status
    charging_state VARCHAR(50), -- Charging, Complete, Disconnected, Stopped

    -- Linkage
    arrival_session_id UUID REFERENCES arrival_sessions(id),

    -- Raw
    raw_response JSONB,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_fleet_sessions_vehicle ON fleet_sessions(vehicle_identity_id);
CREATE INDEX idx_fleet_sessions_time ON fleet_sessions(start_time);
```

### Modifications to Existing Tables

```sql
-- Migration 075: Add columns to users
ALTER TABLE users ADD COLUMN stripe_connect_account_id VARCHAR(255);
ALTER TABLE users ADD COLUMN stripe_connect_status VARCHAR(50); -- pending, active, restricted
ALTER TABLE users ADD COLUMN kyc_status VARCHAR(50) DEFAULT 'not_started'; -- not_started, pending, approved, rejected
ALTER TABLE users ADD COLUMN kyc_completed_at TIMESTAMP;
ALTER TABLE users ADD COLUMN lifetime_rewards_cents BIGINT DEFAULT 0;
ALTER TABLE users ADD COLUMN pending_payout_cents INTEGER DEFAULT 0;

-- Migration 076: Add columns to arrival_sessions
ALTER TABLE arrival_sessions ADD COLUMN sponsor_program_id UUID REFERENCES sponsor_programs(id);
ALTER TABLE arrival_sessions ADD COLUMN reward_event_id UUID REFERENCES reward_events(id);
ALTER TABLE arrival_sessions ADD COLUMN verification_evidence_id UUID REFERENCES verification_evidence(id);
ALTER TABLE arrival_sessions ADD COLUMN fleet_session_id UUID REFERENCES fleet_sessions(id);

-- Migration 077: Add columns to virtual_keys (if not already present)
ALTER TABLE virtual_keys ADD COLUMN last_charging_session_id VARCHAR(255);
ALTER TABLE virtual_keys ADD COLUMN telemetry_state JSONB; -- cached last known state
ALTER TABLE virtual_keys ADD COLUMN telemetry_fetched_at TIMESTAMP;
```

### Entity Relationships Diagram

```
sponsors
    └── sponsor_programs (1:N)
            └── sponsor_budgets (1:N)
            └── reward_events (1:N)
                    └── verification_evidence (1:1)
                    └── payouts (N:1)
                    └── arrival_sessions (1:1)

users
    └── vehicle_identities (1:N)
            └── virtual_keys (1:1)
            └── fleet_sessions (1:N)
    └── reward_events (1:N)
    └── payouts (1:N)

arrival_sessions
    └── fleet_sessions (1:1)
    └── verification_evidence (1:1)
    └── reward_events (1:1)
```

---

## D) VERIFICATION SPEC: Fleet API First

### What Constitutes a Verified Charging Session

#### Required Signals

| Signal | Source | Required | Threshold |
|--------|--------|----------|-----------|
| `charging_state` | Fleet API | ✅ | Must be `Charging` or `Complete` |
| `charge_start_time` | Fleet API | ✅ | Must exist |
| `energy_added_kwh` | Fleet API | ✅ | ≥ 1.0 kWh |
| `session_duration` | Computed | ✅ | ≥ 5 minutes |
| `app_location` | Driver app | ✅ | Within 500m of charger |
| `fleet_location` | Fleet API | ⚠️ Optional | If available, within 500m of charger |
| `device_fingerprint` | Driver app | ✅ | Must match session creator |

#### Verification Algorithm

```python
def verify_charging_session(
    fleet_session: FleetSession,
    arrival_session: ArrivalSession,
    app_location: Location,
    device_fingerprint: str
) -> VerificationResult:

    errors = []
    warnings = []

    # 1. Charging state check
    if fleet_session.charging_state not in ['Charging', 'Complete']:
        errors.append(f"Invalid charging state: {fleet_session.charging_state}")

    # 2. Energy threshold
    MIN_ENERGY_KWH = 1.0
    if fleet_session.energy_added_kwh < MIN_ENERGY_KWH:
        errors.append(f"Insufficient energy: {fleet_session.energy_added_kwh} kWh < {MIN_ENERGY_KWH}")

    # 3. Duration threshold
    MIN_DURATION_MINUTES = 5
    duration_minutes = (fleet_session.end_time - fleet_session.start_time).total_seconds() / 60
    if duration_minutes < MIN_DURATION_MINUTES:
        errors.append(f"Session too short: {duration_minutes:.1f} min < {MIN_DURATION_MINUTES}")

    # 4. Location binding (app vs charger)
    MAX_DISTANCE_M = 500
    charger = get_charger(arrival_session.charger_id)
    app_distance = haversine(app_location, charger.location)
    if app_distance > MAX_DISTANCE_M:
        errors.append(f"App location too far: {app_distance:.0f}m > {MAX_DISTANCE_M}m")

    # 5. Location cross-check (Fleet vs app) - warning only
    if fleet_session.latitude and fleet_session.longitude:
        fleet_location = Location(fleet_session.latitude, fleet_session.longitude)
        cross_check_distance = haversine(app_location, fleet_location)
        if cross_check_distance > 1000:  # 1km tolerance
            warnings.append(f"Fleet/app location mismatch: {cross_check_distance:.0f}m")

    # 6. Device binding
    if device_fingerprint != arrival_session.device_fingerprint:
        errors.append("Device fingerprint mismatch")

    # 7. Time freshness (session must be recent)
    MAX_SESSION_AGE_HOURS = 4
    session_age_hours = (now() - fleet_session.end_time).total_seconds() / 3600
    if session_age_hours > MAX_SESSION_AGE_HOURS:
        errors.append(f"Session too old: {session_age_hours:.1f}h > {MAX_SESSION_AGE_HOURS}h")

    # 8. Idempotency - session not already rewarded
    if reward_exists_for_fleet_session(fleet_session.fleet_session_id):
        errors.append("Session already rewarded")

    return VerificationResult(
        verified=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        evidence=create_evidence(fleet_session, app_location, device_fingerprint)
    )
```

#### Edge Cases

| Scenario | Detection | Handling |
|----------|-----------|----------|
| **Idle (plugged, not charging)** | `charging_state` = `Stopped` or `NoPower` | Reject: not actively charging |
| **Interrupted session** | `end_time` is NULL or `charging_state` = `Disconnected` early | Accept if ≥ 1 kWh added before interrupt |
| **Multiple short sessions** | Same vehicle, multiple sessions < 5min | Reject each; no aggregation in v1 |
| **Location spoofing** | App location far from Fleet location | Flag for review; hard reject if > 5km delta |
| **Time spoofing** | App timestamp differs from server time | Use server receive time; reject if > 5 min skew |
| **Token replay** | Same session ID submitted twice | Idempotency check; return existing result |

#### Idempotency Keys

```
Format: reward:{user_id}:{fleet_session_id}
Example: reward:usr_abc123:ts_sess_xyz789

TTL: 7 days (in Redis)
Storage: Also persisted in reward_events.idempotency_key
```

#### Anti-Fraud Constraints

| Constraint | Implementation | Bypass Risk |
|------------|----------------|-------------|
| Device binding | SHA256(IP + UA + Accept-Lang) stored at session start | Medium (can be faked) |
| Token freshness | OAuth token must be < 1 hour old | Low (we control refresh) |
| Location proximity | App location within 500m of charger | Medium (GPS spoof) |
| Fleet cross-check | Fleet location within 1km of app | Low (hard to spoof Tesla) |
| Rate limit | Max 3 rewards/user/day | Low |
| Velocity check | Max 1 reward/user/2 hours | Low |

---

## E) IMPLEMENTATION PLAN (2 Sprints)

### Sprint 1: Fleet Verification MVP + Internal Ledger + Mock Payouts
**Duration:** 5 working days

#### Day 1-2: Data Model + Fleet Service

**Backend Changes:**

| File | Changes |
|------|---------|
| `backend/alembic/versions/067_*.py` through `077_*.py` | Create all migrations from Section C |
| `backend/app/models/sponsor.py` | New: `Sponsor`, `SponsorProgram`, `SponsorBudget` |
| `backend/app/models/reward.py` | New: `RewardEvent`, `VerificationEvidence`, `Payout` |
| `backend/app/models/vehicle_identity.py` | New: `VehicleIdentity`, `FleetSession` |
| `backend/app/models/__init__.py` | Export new models |
| `backend/app/services/tesla_fleet_api.py` | Implement `get_vehicle_data()`, `get_charging_session()` |
| `backend/app/services/fleet_verification_service.py` | New: Core verification logic from spec |

**Verification Service Implementation:**

```python
# backend/app/services/fleet_verification_service.py
class FleetVerificationService:
    async def verify_charging_session(
        self,
        user_id: UUID,
        arrival_session_id: UUID,
        app_location: Location,
        device_fingerprint: str
    ) -> VerificationResult:
        # 1. Get user's vehicle identity
        vehicle = await self.get_active_vehicle(user_id)

        # 2. Fetch recent Fleet sessions
        fleet_sessions = await self.fleet_api.get_recent_sessions(
            vehicle.provider_vehicle_id,
            vehicle.access_token_encrypted  # decrypt before use
        )

        # 3. Find matching session (time overlap with arrival)
        arrival = await self.get_arrival_session(arrival_session_id)
        matching_session = self.find_matching_session(fleet_sessions, arrival)

        # 4. Run verification checks
        result = self.verify(matching_session, arrival, app_location, device_fingerprint)

        # 5. Store evidence
        evidence = await self.store_evidence(result, matching_session, app_location)

        return result
```

#### Day 3: Sponsor + Budget Service

**Backend Changes:**

| File | Changes |
|------|---------|
| `backend/app/services/sponsor_service.py` | New: CRUD for sponsors, programs, budgets |
| `backend/app/services/budget_ledger_service.py` | New: Reserve/confirm/release pattern |
| `backend/app/routers/admin_sponsors.py` | New: Admin endpoints for sponsor management |

**Budget Ledger Pattern:**

```python
# backend/app/services/budget_ledger_service.py
class BudgetLedgerService:
    async def reserve(
        self,
        budget_id: UUID,
        amount_cents: int,
        reward_event_id: UUID
    ) -> ReservationResult:
        """Atomic: increment reserved_amount, fail if insufficient"""
        async with self.db.begin():
            budget = await self.db.execute(
                select(SponsorBudget)
                .where(SponsorBudget.id == budget_id)
                .with_for_update()  # Row lock
            )
            available = budget.funded_amount_cents - budget.reserved_amount_cents - budget.spent_amount_cents
            if available < amount_cents:
                raise InsufficientBudgetError()
            budget.reserved_amount_cents += amount_cents
            # Link to reward_event
            return ReservationResult(success=True, reservation_id=...)

    async def confirm(self, reservation_id: UUID):
        """Move from reserved to spent"""
        # reserved -= amount, spent += amount

    async def release(self, reservation_id: UUID):
        """Cancel reservation, return to available"""
        # reserved -= amount
```

#### Day 4: Reward Issuance + Mock Payout

**Backend Changes:**

| File | Changes |
|------|---------|
| `backend/app/services/reward_service.py` | New: Issuance logic, eligibility checks |
| `backend/app/services/payout_service.py` | New: Mock payout creation (no Stripe yet) |
| `backend/app/routers/rewards.py` | New: Driver reward endpoints |

**Driver Endpoints:**

```python
# backend/app/routers/rewards.py

@router.get("/v1/rewards/balance")
async def get_reward_balance(user: User = Depends(get_current_user)):
    """Get driver's pending and lifetime rewards"""
    return {
        "pending_cents": user.pending_payout_cents,
        "lifetime_cents": user.lifetime_rewards_cents,
        "available_for_payout": user.pending_payout_cents >= MIN_PAYOUT_CENTS
    }

@router.get("/v1/rewards/history")
async def get_reward_history(user: User = Depends(get_current_user)):
    """List reward events for driver"""
    # Paginated list of reward_events

@router.post("/v1/rewards/request-payout")
async def request_payout(user: User = Depends(get_current_user)):
    """Request payout of pending rewards"""
    # Creates payout record, returns status
```

#### Day 5: Integration + Tests

**Test Plan:**

| Test Type | File | Coverage |
|-----------|------|----------|
| Unit | `tests/test_fleet_verification_service.py` | Verification algorithm, edge cases |
| Unit | `tests/test_budget_ledger_service.py` | Reserve/confirm/release, race conditions |
| Integration | `tests/integration/test_reward_flow.py` | Full flow: arrival → verify → reward |
| API | `tests/api/test_rewards_router.py` | Endpoint contracts |

**Frontend Changes (Sprint 1):**

| File | Changes |
|------|---------|
| `apps/driver/src/components/Rewards/RewardsScreen.tsx` | New: Balance display, history list |
| `apps/driver/src/components/Rewards/PendingPayout.tsx` | New: Payout request UI (disabled until Sprint 2) |
| `apps/driver/src/services/api.ts` | Add reward endpoints |

---

### Sprint 2: Stripe Payouts Production + Admin Tools + Monitoring
**Duration:** 5 working days

#### Day 1-2: Stripe Connect Integration

**Backend Changes:**

| File | Changes |
|------|---------|
| `backend/app/services/stripe_connect_service.py` | New: Account creation, onboarding links |
| `backend/app/services/stripe_payout_service.py` | New: Create transfers, handle webhooks |
| `backend/app/routers/stripe_connect.py` | New: Onboarding endpoints |
| `backend/app/routers/stripe_webhooks.py` | Extend: Payout webhooks |

**Stripe Connect Flow:**

```python
# backend/app/services/stripe_connect_service.py
class StripeConnectService:
    async def create_express_account(self, user: User) -> str:
        """Create Stripe Express account for driver"""
        account = stripe.Account.create(
            type="express",
            country="US",
            email=user.email,
            capabilities={
                "transfers": {"requested": True}
            },
            metadata={
                "nerava_user_id": str(user.id)
            }
        )
        user.stripe_connect_account_id = account.id
        user.stripe_connect_status = "pending"
        return account.id

    async def create_onboarding_link(self, user: User) -> str:
        """Generate onboarding link for driver"""
        link = stripe.AccountLink.create(
            account=user.stripe_connect_account_id,
            refresh_url=f"{settings.app_url}/rewards/onboarding/refresh",
            return_url=f"{settings.app_url}/rewards/onboarding/complete",
            type="account_onboarding"
        )
        return link.url

# backend/app/services/stripe_payout_service.py
class StripePayoutService:
    async def create_payout(self, payout: Payout) -> str:
        """Transfer funds to driver's Connect account"""
        transfer = stripe.Transfer.create(
            amount=payout.net_amount_cents,
            currency="usd",
            destination=payout.stripe_connect_account_id,
            metadata={
                "nerava_payout_id": str(payout.id),
                "nerava_user_id": str(payout.user_id)
            }
        )
        payout.stripe_transfer_id = transfer.id
        payout.status = "processing"
        return transfer.id
```

#### Day 3: Admin Tools

**Backend Changes:**

| File | Changes |
|------|---------|
| `backend/app/routers/admin_rewards.py` | New: Dispute resolution, manual override |
| `backend/app/routers/admin_sponsors.py` | Extend: Budget funding, pause/resume |
| `backend/app/services/audit_service.py` | New: Immutable action logging |

**Admin Endpoints:**

```python
# backend/app/routers/admin_rewards.py

@router.get("/v1/admin/rewards/{reward_id}")
async def get_reward_details(reward_id: UUID, admin: User = Depends(require_admin)):
    """Get full reward details including evidence"""

@router.post("/v1/admin/rewards/{reward_id}/approve")
async def approve_reward(reward_id: UUID, admin: User = Depends(require_admin)):
    """Manually approve a flagged reward"""

@router.post("/v1/admin/rewards/{reward_id}/reject")
async def reject_reward(
    reward_id: UUID,
    reason: str,
    admin: User = Depends(require_admin)
):
    """Reject reward, release budget reservation"""

@router.post("/v1/admin/rewards/{reward_id}/clawback")
async def clawback_reward(
    reward_id: UUID,
    reason: str,
    admin: User = Depends(require_admin)
):
    """Clawback already-paid reward (creates negative balance)"""
```

**Frontend Changes:**

| File | Changes |
|------|---------|
| `apps/admin/src/components/Rewards.tsx` | New: Reward management dashboard |
| `apps/admin/src/components/Sponsors.tsx` | New: Sponsor/budget management |
| `apps/admin/src/components/Disputes.tsx` | New: Dispute queue |

#### Day 4: Monitoring + Observability

**Backend Changes:**

| File | Changes |
|------|---------|
| `backend/app/services/analytics.py` | Extend: Reward funnel events |
| `backend/app/middleware/metrics.py` | Extend: Reward-specific metrics |

**PostHog Events:**

```python
REWARD_EVENTS = [
    "reward_eligible",      # User qualifies for program
    "reward_verification_started",
    "reward_verification_success",
    "reward_verification_failed",
    "reward_issued",
    "reward_payout_requested",
    "reward_payout_completed",
    "reward_payout_failed"
]
```

**Prometheus Metrics:**

```python
rewards_issued_total = Counter("rewards_issued_total", "Total rewards issued", ["program_id"])
rewards_amount_cents = Counter("rewards_amount_cents", "Total reward amount in cents", ["program_id"])
verification_latency = Histogram("verification_latency_seconds", "Verification time")
payout_success_rate = Gauge("payout_success_rate", "Payout success rate (7d rolling)")
```

#### Day 5: Rollout + Kill Switch

**Rollout Plan:**

| Stage | Users | Duration | Criteria to Advance |
|-------|-------|----------|---------------------|
| Internal | 5 team members | 2 days | Zero errors, payouts succeed |
| Alpha | 20 beta users | 3 days | < 5% failure rate, no fraud signals |
| Beta | 100 users | 5 days | < 2% failure rate, budget tracking accurate |
| GA | All users | - | Monitoring stable |

**Kill Switch Implementation:**

```python
# backend/app/dependencies/feature_flags.py
class FeatureFlags:
    REWARDS_ENABLED = "rewards_enabled"
    FLEET_VERIFICATION_ENABLED = "fleet_verification_enabled"
    STRIPE_PAYOUTS_ENABLED = "stripe_payouts_enabled"

# Usage in router
@router.post("/v1/rewards/request-payout")
async def request_payout(
    user: User = Depends(get_current_user),
    flags: FeatureFlags = Depends(get_feature_flags)
):
    if not flags.is_enabled(FeatureFlags.STRIPE_PAYOUTS_ENABLED):
        raise HTTPException(503, "Payouts temporarily disabled")
    # ... proceed
```

**Environment Variables:**

```bash
# Kill switches
REWARDS_ENABLED=true
FLEET_VERIFICATION_ENABLED=true
STRIPE_PAYOUTS_ENABLED=false  # Enable after Sprint 2 Day 2

# Rollout percentage
REWARDS_ROLLOUT_PERCENT=0  # 0-100
```

---

## F) DECISIONS + OPEN QUESTIONS

### Must Decide NOW

| # | Decision | Options | Recommended Default | Rationale |
|---|----------|---------|---------------------|-----------|
| 1 | **Rewards: Cash or Credits?** | Cash (bank payout) / Credits (in-app only) | **Cash** | Higher driver motivation; credits add redemption complexity |
| 2 | **Who pays transfer fees?** | Nerava / Driver / Sponsor | **Nerava absorbs** (for now) | Simplifies UX; revisit at scale |
| 3 | **Minimum payout threshold** | $5 / $10 / $25 | **$10** | Balances Stripe fees (~$0.25 + 0.25%) vs driver expectation |
| 4 | **KYC threshold** | $0 / $600 / $20,000 | **$600/year** | IRS 1099-K threshold; collect W-9 at $600 |
| 5 | **Reward expiry** | Never / 30 days / 90 days / 1 year | **1 year** | Balance breakage revenue vs user trust |
| 6 | **Clawback policy** | Never / Fraud only / Any dispute | **Fraud only** (within 30 days) | Protect integrity without alienating drivers |
| 7 | **Sponsor reporting cadence** | Real-time / Daily / Weekly | **Daily email + real-time dashboard** | Sponsors want visibility without noise |
| 8 | **Fleet API polling frequency** | 1min / 5min / 15min / On-demand | **On-demand** (when driver claims) | Rate limits; polling is expensive |

### Requires External Approval

| # | Dependency | Owner | Timeline | Blocker Level |
|---|------------|-------|----------|---------------|
| 1 | Tesla Developer Partner account | Tesla | 2-4 weeks | **Critical** - blocks Fleet API |
| 2 | Stripe Connect approval | Stripe | 1-2 weeks | **Critical** - blocks payouts |
| 3 | Toast Partner API access | Toast | 4-6 weeks | **Non-blocking** - parallel workstream |
| 4 | Square API access | Square | 1-2 weeks | **Non-blocking** - parallel workstream |

### Legal/Compliance Questions

| # | Question | Needs Answer From | Impact |
|---|----------|-------------------|--------|
| 1 | Do we need money transmitter license? | Legal counsel | If yes, use Stripe Connect Express (they hold license) |
| 2 | 1099 reporting obligations? | Tax advisor | Must issue 1099-K if driver earns > $600/year |
| 3 | State-specific payout regulations? | Legal counsel | Some states have unclaimed property laws |
| 4 | Sponsor contract template? | Legal counsel | Need standard terms for budget, liability, reporting |

### What Can Ship THIS WEEK

| Capability | Can Ship | Dependency |
|------------|----------|------------|
| Data model migrations | ✅ Yes | None |
| Sponsor/Budget admin UI (internal) | ✅ Yes | None |
| Mock verification flow (no Fleet) | ✅ Yes | None |
| Reward ledger service | ✅ Yes | None |
| Driver rewards UI (balance display) | ✅ Yes | None |
| Fleet API verification | ❌ No | Tesla Partner credentials |
| Stripe payouts | ❌ No | Connect approval |
| Toast order verification | ❌ No | Partner API access |

---

## APPENDIX: File Change Summary

### New Files (Backend)

```
backend/app/models/sponsor.py
backend/app/models/reward.py
backend/app/models/vehicle_identity.py
backend/app/services/fleet_verification_service.py
backend/app/services/sponsor_service.py
backend/app/services/budget_ledger_service.py
backend/app/services/reward_service.py
backend/app/services/payout_service.py
backend/app/services/stripe_connect_service.py
backend/app/services/stripe_payout_service.py
backend/app/services/audit_service.py
backend/app/routers/rewards.py
backend/app/routers/admin_rewards.py
backend/app/routers/admin_sponsors.py
backend/app/routers/stripe_connect.py
backend/alembic/versions/067_create_sponsors.py
backend/alembic/versions/068_create_sponsor_programs.py
backend/alembic/versions/069_create_sponsor_budgets.py
backend/alembic/versions/070_create_reward_events.py
backend/alembic/versions/071_create_verification_evidence.py
backend/alembic/versions/072_create_payouts.py
backend/alembic/versions/073_create_vehicle_identities.py
backend/alembic/versions/074_create_fleet_sessions.py
backend/alembic/versions/075_add_user_stripe_columns.py
backend/alembic/versions/076_add_arrival_session_columns.py
backend/alembic/versions/077_add_virtual_key_columns.py
```

### Modified Files (Backend)

```
backend/app/models/__init__.py
backend/app/services/tesla_fleet_api.py
backend/app/services/analytics.py
backend/app/middleware/metrics.py
backend/app/routers/stripe_webhooks.py (extend)
backend/app/dependencies/feature_flags.py
```

### New Files (Frontend - Driver)

```
apps/driver/src/components/Rewards/RewardsScreen.tsx
apps/driver/src/components/Rewards/RewardHistory.tsx
apps/driver/src/components/Rewards/PendingPayout.tsx
apps/driver/src/components/Rewards/StripeOnboarding.tsx
```

### New Files (Frontend - Admin)

```
apps/admin/src/components/Rewards.tsx
apps/admin/src/components/Sponsors.tsx
apps/admin/src/components/Disputes.tsx
```

---

**End of Report**
