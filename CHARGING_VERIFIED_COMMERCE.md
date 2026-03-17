# Charging Verified Commerce: Implementation Plan & Gap Analysis

## What This Is

Nerava already knows when a driver is charging and where. This plan wraps that verified state into an opaque token that any merchant's checkout system can validate via a single API call. This eliminates receipt scanning, QR codes, and staff training entirely.

**The primitive:** `verified EV driver presence`

**The billing event:** Claim + Presence (driver claims an offer while verified charging nearby)

---

## Architecture Overview

Three actors, three data flows:

1. **Driver** — taps "Claim Offer" in Amenities tab → sees confirmation sheet with offer details → taps "Order Online" → gets redirected to merchant's ordering URL with verification token appended
2. **Merchant's checkout** — calls `POST /v1/verify-charging` with the token (public endpoint, token IS the auth) → gets back `{ verified: true, distance_m, session_duration_min }` → applies discount
3. **Nerava backend** — issues tokens, verifies them, records claims, decrements campaign budgets

```
Driver App                    Nerava Backend                Merchant Checkout
    |                              |                              |
    |-- POST /verification-tokens->|                              |
    |<-- { token: nrv_vt_... } ----|                              |
    |                              |                              |
    |-- Opens merchant URL --------|------- ?nrv_token=... ------>|
    |                              |                              |
    |                              |<-- POST /verify-charging ----|
    |                              |-- { verified: true } ------->|
    |                              |                              |
    |-- POST /commerce/claim ----->|                              |
    |<-- { claim_id, offer } ------|                              |
```

---

## Gap Analysis: What Exists vs What's Needed

### Backend — What Exists

| Component | File | Reusable? | Gap |
|-----------|------|-----------|-----|
| `SessionEvent` model | `backend/app/models/session_event.py` | Yes — source of truth for "is driver charging?" | None |
| `Campaign` model | `backend/app/models/campaign.py` | Partial — has budget, targeting, lifecycle | Missing commerce-specific fields (AOV bracket, offer description, geo radius) |
| `IncentiveEngine` | `backend/app/services/incentive_engine.py` | Pattern only — runs on session END | Commerce claims happen DURING session, not at end |
| `CampaignService.decrement_budget_atomic()` | `backend/app/services/campaign_service.py` | Yes — atomic budget tracking | None |
| `DomainMerchant` | `backend/app/models/domain.py` | Partial — has `avg_order_value_cents` (nullable, unused) | Missing: ordering URL, AOV bracket, commerce_enabled flag |
| `ExclusiveSession` | `backend/app/models/exclusive_session.py` | Pattern — activation + countdown + lifecycle | Commerce claims are simpler (no countdown timer) |
| `RewardClaim` | `backend/app/models/merchant_reward.py` | No — too coupled to receipt upload flow | Need new `CommerceClaim` model |
| `PartnerAPIKey` auth | `backend/app/dependencies/partner_auth.py` | Pattern for Phase 2 | Phase 1 is token-only (no merchant API keys) |
| `EV verification codes` | `backend/app/models/tesla_connection.py` | Pattern — `EV-XXXX` codes, 2hr TTL | Verification tokens follow same pattern |
| Haversine distance | `backend/app/services/incentive_engine.py` | Yes | None |

### Frontend — What Exists

| Component | File | Reusable? | Gap |
|-----------|------|-----------|-----|
| `ChargerDetailSheet` | `apps/driver/.../ChargerDetail/ChargerDetailSheet.tsx` | Modify — Amenities tab is read-only flat list | Need: offer badges, "Claim Offer" button, "Request to Join" |
| `ClaimRewardSheet` | `apps/driver/.../MerchantDetails/ClaimRewardSheet.tsx` | Adapt — modal for claiming (currently says "upload receipt within 2 hours") | Change copy + flow for instant verification |
| `RequestToJoinSheet` | `apps/driver/.../MerchantDetails/RequestToJoinSheet.tsx` | Wire in — exists but orphaned from charger context | Import into AmenitiesTab |
| `MerchantActionSheet` | Inline in `ChargerDetailSheet.tsx` | Extend — only has Call/Website/Directions | Add: "Order Online", "Claim Offer", "Request to Join" |
| `PrimaryFilters` | `apps/driver/.../shared/PrimaryFilters.tsx` | Wire in — 5 category buttons, not used in charger detail | Import into AmenitiesTab |
| `SearchBar` | `apps/driver/.../shared/SearchBar.tsx` | Wire in — not used in charger detail | Import into AmenitiesTab |
| `ChargerDetailNearbyMerchant` | `apps/driver/src/services/api.ts` | Extend — missing commerce fields | Add: commerce_offer, campaign_id, claim_url, is_nerava_merchant, join_request_count |

### Merchant Portal — What Exists

| Component | File | Reusable? | Gap |
|-----------|------|-----------|-----|
| Exclusives CRUD | `apps/merchant/app/components/Exclusives.tsx` | Pattern — toggle on/off, daily cap, inline edit | Commerce campaigns follow same UX pattern |
| `CreateExclusive` form | `apps/merchant/app/components/CreateExclusive.tsx` | Pattern — name, description, daily cap | Extend for AOV bracket, budget, ordering URL |
| EV Arrivals dashboard | `apps/merchant/app/components/EVArrivals.tsx` | Pattern — session code input, active/completed tabs | Commerce claims dashboard follows same structure |
| Billing | `apps/merchant/app/components/Billing.tsx` | Extend — has Stripe checkout, invoice history | Add budget top-up for commerce campaigns |
| Insights | `apps/merchant/app/components/Insights.tsx` | Pattern — charts, Pro-gated detail | Commerce analytics follow same pattern |
| Dashboard layout | `apps/merchant/app/components/DashboardLayout.tsx` | Extend — sidebar with 10 nav items | Add "Campaigns" nav item |

### Data Interface Gap

`ChargerDetailNearbyMerchant` is currently:
```typescript
{
  place_id, name, photo_url, distance_m, walk_time_min,
  has_exclusive, phone?, website?, category?, lat?, lng?, exclusive_title?
}
```

Needs to become:
```typescript
{
  // existing fields...
  is_nerava_merchant: boolean        // has active campaign
  commerce_offer?: string            // "10% off your order"
  commerce_campaign_id?: string      // for claim API call
  commerce_claim_url?: string        // merchant's ordering URL
  join_request_count: number         // social proof for non-Nerava merchants
  driver_has_active_claim?: boolean  // if driver already claimed this merchant
}
```

---

## Phase 1: Minimum Viable Verification Flow

**Goal:** End-to-end loop — driver claims offer in Amenities tab, merchant verifies via API, budget decremented. Campaigns created via admin initially.

### 1.1 New Model: `VerificationToken`

**File:** `backend/app/models/verification_token.py`

```
Table: verification_tokens
- id (UUIDType, PK)
- token (String(64), unique, indexed) — format: nrv_vt_{40_hex_chars}
- driver_user_id (Integer, FK users.id, not null, indexed)
- session_event_id (UUIDType, FK session_events.id, not null)
- charger_id (String, FK chargers.id, nullable)
- charger_lat (Float, nullable)
- charger_lng (Float, nullable)
- merchant_id (String, nullable) — if pre-bound to specific merchant
- status (String, default "active") — active | claimed | expired | revoked
- claimed_at (DateTime, nullable)
- claim_merchant_place_id (String, nullable)
- expires_at (DateTime, not null)
- created_at (DateTime, not null)
```

Design decisions:
- **DB table, not Redis.** Tokens need audit trails for billing disputes. Low volume (one per active charging session per driver). Redis can serve as a hot cache in Phase 3.
- **Status lifecycle:** `active` → `claimed` (merchant verifies + driver confirms) or `expired` (session ends or 2hr TTL)
- **One active token per driver** at a time (enforced in service layer)

### 1.2 New Model: `CommerceClaim`

**File:** `backend/app/models/commerce_claim.py`

```
Table: commerce_claims
- id (UUIDType, PK)
- driver_user_id (Integer, FK users.id, not null, indexed)
- session_event_id (UUIDType, FK session_events.id, not null)
- verification_token_id (UUIDType, FK verification_tokens.id, not null)
- campaign_id (UUIDType, FK campaigns.id, nullable, indexed)
- merchant_id (String, nullable)
- merchant_place_id (String, nullable)
- merchant_name (String, not null)
- distance_m (Float, nullable) — charger-to-merchant at claim time
- aov_bracket (String, nullable) — merchant's self-reported AOV bracket
- claim_cost_cents (Integer, not null) — AOV midpoint * 4%
- status (String, default "verified") — verified | billed | refunded
- offer_description (String, nullable)
- created_at (DateTime, not null)
- idempotency_key (String, unique, indexed) — "claim_{token_id}_{merchant_place_id}"
```

Separate from `RewardClaim` because that model is tightly coupled to the receipt upload flow. This is a cleaner abstraction.

### 1.3 Extend `Campaign` Model

Add columns to existing `campaigns` table (all nullable with defaults, zero risk to existing data):

```python
commerce_enabled = Column(Boolean, default=False)
commerce_offer_description = Column(String, nullable=True)     # "10% off your order"
commerce_aov_bracket = Column(String, nullable=True)           # "low_10", "mid_25", "high_50", "premium_100"
commerce_cost_bps = Column(Integer, default=400)               # 4% = 400 bps
commerce_daily_cap = Column(Integer, nullable=True)            # max claims/day
commerce_merchant_ids = Column(JSON, nullable=True)            # restrict to specific merchants
commerce_geo_radius_m = Column(Integer, default=1000)          # max charger-to-merchant distance
commerce_ordering_url = Column(String, nullable=True)          # merchant's online ordering URL
```

AOV bracket cost table:
| Bracket | AOV Midpoint | Cost per claim (4%) |
|---------|-------------|-------------------|
| `low_10` | $10 | $0.40 |
| `mid_25` | $25 | $1.00 |
| `high_50` | $50 | $2.00 |
| `premium_100` | $100 | $4.00 |

### 1.4 New Service: `VerificationTokenService`

**File:** `backend/app/services/verification_token_service.py`

Methods:
- `create_token(db, driver_user_id, session_event_id)` — validates active session, revokes existing active token for this driver, generates `nrv_vt_{secrets.token_hex(20)}`, sets TTL to min(session estimated end, now + 2h)
- `verify_token(db, token_string, merchant_lat, merchant_lng)` — looks up token, checks status == "active" and session still active, computes haversine distance, returns verification result. Read-only (does NOT mutate status)
- `revoke_for_session(db, session_event_id)` — marks all active tokens for session as "expired". Called on session end.

Verify response:
```json
{
  "verified": true,
  "distance_m": 342.5,
  "session_duration_min": 28,
  "charger_network": "Tesla",
  "confidence": "high"
}
```

No PII exposed. No driver name, email, or phone.

### 1.5 New Service: `CommerceClaimService`

**File:** `backend/app/services/commerce_claim_service.py`

Methods:
- `create_claim(db, driver_user_id, token_id, merchant_place_id, merchant_name, campaign_id)` — validates token, computes claim_cost_cents from AOV bracket, calls `CampaignService.decrement_budget_atomic()`, marks token as "claimed", creates claim row
- `get_daily_claim_count(db, campaign_id, date)` — for daily cap enforcement
- `list_claims_for_merchant(db, merchant_id, limit, offset)` — for merchant dashboard

### 1.6 New Router: Commerce Verification

**File:** `backend/app/routers/commerce_verify.py`

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `POST /v1/verification-tokens` | JWT (driver) | Generate token tied to active session |
| `POST /v1/verify-charging` | None (token IS auth) | Merchant validates driver's charging status |
| `POST /v1/commerce/claim` | JWT (driver) | Record claim, decrement budget |
| `GET /v1/commerce/claims/active` | JWT (driver) | Driver's active claims |

The verify endpoint is intentionally public. The token is a short-lived bearer credential. Rate limited by IP via existing middleware.

### 1.7 Extend Charger Detail API

**File:** `backend/app/routers/chargers.py`

Extend `NearbyMerchantResponse` and the `charger_detail` endpoint to query active commerce campaigns targeting nearby merchants and inject offer data.

### 1.8 Session End Hook

**File:** `backend/app/services/session_event_service.py`

In `end_session()`, `end_session_manual()`, and `_close_stale_session()`: call `VerificationTokenService.revoke_for_session()`. Wrap in try/except to not break the hot path if revocation fails.

### 1.9 Driver App: Amenities Tab Enhancement

**File:** `apps/driver/src/components/ChargerDetail/ChargerDetailSheet.tsx`

**AmenitiesTab changes:**
- Merchants with `commerce_offer`: show offer badge + "Claim Offer" button
- Merchants without `is_nerava_merchant`: show "Request to Join" link (wire existing `RequestToJoinSheet`)
- Show `join_request_count` as social proof

**New: CommerceOfferSheet (confirmation sheet)**
- Shows: merchant name, offer description, walk time, session time remaining
- CTA: "Order Online" → generates token → opens `{merchant.commerce_claim_url}?nrv_token={token}`
- Secondary CTA: "Just Directions" → opens Maps

**MerchantActionSheet changes:**
- Add "Order Online" (if commerce_claim_url exists)
- Add "Request to Join" (if not is_nerava_merchant)

### 1.10 Driver App: Search & Filter in Amenities

**File:** `apps/driver/src/components/ChargerDetail/ChargerDetailSheet.tsx`

- Import `PrimaryFilters` from `shared/PrimaryFilters.tsx` into AmenitiesTab
- Add category filtering (food, coffee, grocery, etc.) to the merchant list
- Import `SearchBar` from `shared/SearchBar.tsx` for name search

### 1.11 Migration

**File:** `backend/alembic/versions/111_commerce_verify.py`

- Create `verification_tokens` table
- Create `commerce_claims` table
- Add `commerce_*` columns to `campaigns` table
- Add `ordering_url` column to `merchants` table (or `domain_merchants`)

### 1.12 Tests

**File:** `backend/tests/test_commerce_verify.py`

Test cases:
1. Token creation with active session succeeds
2. Token creation without active session fails (400)
3. Token creation revokes previous active token
4. Verify returns verified=true when session active + merchant nearby
5. Verify returns verified=false when session ended
6. Verify returns verified=false when merchant too far (>geo_radius_m)
7. Verify expired token returns verified=false
8. Claim with valid token succeeds, decrements budget
9. Claim is idempotent (same token + merchant = existing claim)
10. Claim fails when budget exhausted (auto-pause)
11. Claim fails when daily cap reached
12. Session end revokes active tokens
13. Rate limiting on verify endpoint

---

## Phase 2: Merchant Portal Self-Serve

### 2.1 Campaign Creation

**New route:** `/campaigns/create` in `apps/merchant/`

Form fields:
- Offer description (e.g., "10% off your order", "Free drink with entree")
- AOV bracket selector (Under $10 / $10-25 / $25-50 / $50-100 / $100+)
- Online ordering URL
- Budget (prepaid via Stripe Checkout — reuse existing billing pattern)
- Daily claim cap (optional)
- Geo radius (advanced, default 1000m)

Show real-time pricing: "At your AOV bracket ($25), each verified EV claim costs $1.00. Your $150 budget gets ~150 claims."

### 2.2 Claims Dashboard

**New route:** `/campaigns/claims` in `apps/merchant/`

Real-time view:
- EV Driver Claims Today: 7
- Average Walk Time: 2.8 min
- Average Session Remaining: 31 min
- Budget Remaining: $89.50
- Estimated Claims Left: 10

Table: Recent claims with timestamp, anonymized driver ID, distance, cost, offer

### 2.3 Campaign Management

**New route:** `/campaigns` in `apps/merchant/`

- List active/paused/exhausted campaigns
- Toggle on/off
- Edit offer description, daily cap
- Budget top-up (Stripe Checkout)
- Campaign performance chart (claims over time)

### 2.4 Dashboard Sidebar Update

Add "Campaigns" nav item to `DashboardLayout.tsx` sidebar.

---

## Phase 3: Refinements

### 3.1 Merchant API Keys (Optional)
For merchants who want deeper integration (server-side verification, webhooks). Reuse `PartnerAPIKey` pattern with `partner_type: "merchant"`.

### 3.2 POS Read-Only Integration
Toast/Square read-only connection to:
- Auto-calibrate AOV from real order data
- Track claim → order conversion ("42 claims, 28 converted, 67% conversion rate")
- Show merchants: "EV drivers who claimed spent an average of $38.50"

### 3.3 Driver Rewards
Commerce campaigns can optionally reward the driver too (dual-sided). Add `commerce_driver_reward_cents` to Campaign. Driver earns Nova points + cash when claiming.

### 3.4 Merchant Webhook Notifications
Push notifications to merchant when claims happen. Reuse webhook delivery patterns from partner API.

### 3.5 Analytics Events
Add to `apps/driver/src/analytics/events.ts`:
- `COMMERCE_TOKEN_CREATED`
- `COMMERCE_OFFER_VIEWED` (confirmation sheet opened)
- `COMMERCE_OFFER_CLAIMED`
- `COMMERCE_ORDER_OPENED` (redirected to merchant URL)
- `COMMERCE_MERCHANT_REQUESTED` (Request to Join tapped)

### 3.6 Feature Flag
Gate behind `FEATURE_COMMERCE_VERIFY` in `backend/app/routers/flags.py`. Initially dev/staging only.

---

## File-by-File Change Summary

### New Files (Phase 1)

| File | Purpose |
|------|---------|
| `backend/app/models/verification_token.py` | VerificationToken ORM model |
| `backend/app/models/commerce_claim.py` | CommerceClaim ORM model |
| `backend/app/services/verification_token_service.py` | Token creation, verification, revocation |
| `backend/app/services/commerce_claim_service.py` | Claim creation, budget decrement, daily caps |
| `backend/app/routers/commerce_verify.py` | Router: /v1/verification-tokens, /v1/verify-charging, /v1/commerce/* |
| `backend/app/schemas/commerce.py` | Pydantic request/response schemas |
| `backend/alembic/versions/111_commerce_verify.py` | Migration for new tables + campaign columns |
| `backend/tests/test_commerce_verify.py` | Full test suite (13 test cases) |

### Modified Files (Phase 1)

| File | Change |
|------|--------|
| `backend/app/models/campaign.py` | Add 8 `commerce_*` columns |
| `backend/app/routers/chargers.py` | Extend `NearbyMerchantResponse` with commerce fields; add campaign lookup in `charger_detail` |
| `backend/app/services/session_event_service.py` | Call `VerificationTokenService.revoke_for_session()` on session end (3 methods) |
| `backend/app/main_simple.py` | Register `commerce_verify.router` |
| `apps/driver/src/services/api.ts` | Add commerce fields to `ChargerDetailNearbyMerchant`, add new API hooks |
| `apps/driver/src/components/ChargerDetail/ChargerDetailSheet.tsx` | Enhance AmenitiesTab: offer badges, claim button, request-to-join, search/filter |

### New Files (Phase 2)

| File | Purpose |
|------|---------|
| `apps/merchant/app/components/Campaigns.tsx` | Campaign list view |
| `apps/merchant/app/components/CreateCampaign.tsx` | Campaign creation form |
| `apps/merchant/app/components/CampaignClaims.tsx` | Claims dashboard |

### Modified Files (Phase 2)

| File | Change |
|------|--------|
| `apps/merchant/app/App.tsx` | Add campaign routes |
| `apps/merchant/app/components/DashboardLayout.tsx` | Add "Campaigns" sidebar nav |
| `apps/merchant/app/services/api.ts` | Add campaign + claims API functions |

---

## Build & Deploy Sequencing

### Phase 1 Order:
1. Migration (models + columns) — no dependencies
2. Services (token service first, then claim service) — depends on models
3. Schemas (Pydantic) — parallel with services
4. Router — depends on services + schemas
5. Register router in `main_simple.py`
6. Session end hook in `session_event_service.py`
7. Backend tests — verify all logic
8. Frontend API types + hooks — can parallel with backend tests
9. Frontend UI (AmenitiesTab, confirmation sheet, action sheet) — depends on API hooks
10. Feature flag gating

### Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Session end hook breaks hot path | Medium | Wrap `revoke_for_session()` in try/except; log but don't raise |
| Token security (bearer credential) | Low | Short-lived (2hr max), session-bound, no PII exposed, rate limited |
| Campaign budget race conditions | Low | Reuse existing `decrement_budget_atomic()` which handles this |
| Charger detail endpoint latency | Low | Commerce campaign lookup is one additional batched query |
| New tables break existing tests | None | All additive, no existing schema changes |

---

## What This Replaces

| Old Approach | Status | Replacement |
|--------------|--------|-------------|
| Receipt OCR (Taggun) | Planned, never built | Verification token — $0 per verification vs $0.04-0.08/scan |
| QR code merchant verification | Partially built | Verification token — no physical QR scanning needed |
| Staff training for deal redemption | Required | Token-based — zero staff involvement |
| POS integration for verification | Complex, multi-month | Token-only in Phase 1 — zero merchant integration needed |
| `RewardClaim` with receipt upload | Built, receipt flow orphaned | `CommerceClaim` — clean model, no receipt fields |

---

## Identity Solution

The verification token IS the identity layer. Flow:

1. Driver is authenticated in Nerava app (JWT)
2. Driver taps merchant → app calls `POST /v1/verification-tokens` (authenticated)
3. App opens merchant URL: `https://merchant.com/order?nrv_token=nrv_vt_abc123`
4. Merchant's checkout calls `POST /v1/verify-charging` with just the token
5. Token proves: driver exists, is charging, is nearby — without exposing any PII

No login on merchant site. No new account. No deep integration. The token is ephemeral, scoped to one session, and proves presence without exposing driver data. This mirrors how existing `EV-XXXX` codes work.

---

## Billing Model Summary

**The billing event:** Driver claims offer while verified charging nearby

**Three conditions (all must be true):**
1. Driver has active charging session (Tesla API / Smartcar verified)
2. Driver is within campaign's geo radius of merchant (GPS verified)
3. Driver taps "Claim Offer" (explicit intent)

**Pricing:** AOV bracket × 4% (configurable via `commerce_cost_bps`)

**Budget mechanics:**
- Prepaid via Stripe Checkout
- Atomic budget decrement on claim (reuses existing `decrement_budget_atomic`)
- Daily cap enforcement
- Auto-pause when budget exhausted
- Budget top-up via merchant portal

This is a stronger signal than Google Ads clicks ($1-5/click, no proximity guarantee) or Yelp leads ($2-8, phone call that might not convert). Nerava's charging lead is physically nearby, has 20-45 minutes of dwell time, and explicitly chose to engage.
