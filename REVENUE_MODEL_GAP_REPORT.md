# Nerava Revenue Model Gap Report

**Date:** 2026-03-22
**Scope:** Merchant incentives, utility integration, enterprise data capabilities, partner API

---

## Executive Summary

Nerava has a strong foundation for **charging outcome monetization** (live today) and **merchant traffic monetization** (partially built). However, significant gaps remain in **utility/grid integration** (stub only), **enterprise data licensing** (designed but no paywall), and **commerce verification** (designed but not coded). This report catalogs what exists, what's missing, and prioritized recommendations.

---

## 1. Campaign & Incentive System — FULLY IMPLEMENTED

### What Exists

| Component | File | Status |
|-----------|------|--------|
| Campaign model (budget, targeting, lifecycle) | `backend/app/models/campaign.py` | Live |
| Incentive engine (session → grant matching) | `backend/app/services/incentive_engine.py` | Live |
| Campaign CRUD + lifecycle | `backend/app/services/campaign_service.py` | Live |
| Session event service | `backend/app/services/session_event_service.py` | Live |
| Nova transaction ledger | `backend/app/services/nova_service.py` | Live |
| Energy reputation system | `backend/app/services/reputation.py` | Live |
| Driver wallet + Stripe payouts | `backend/app/services/payout_service.py` | Live |

**Campaign targeting rules** (all AND-ed):
- Charger IDs, networks, connector types
- Zone IDs, geographic radius (haversine)
- Time-of-day windows, day-of-week
- Min/max duration, min power (kW)
- Driver session count bounds, driver allowlists
- Per-driver caps (daily/weekly/total)
- Partner controls: `allow_partner_sessions`, `rule_partner_ids`, `rule_min_trust_tier`

**Campaign types** (documented in model): `utilization_boost`, `off_peak`, `new_driver`, `repeat_visit`, `merchant_traffic`, `corridor`, `loyalty`, `custom`

**Grant logic:**
- One session = one grant max per type (highest priority campaign wins)
- Grants created only on session END
- Atomic budget decrement prevents overruns
- Idempotent via `session_event_id` + `grant_type` uniqueness constraint
- `reward_destination` routes: `nerava_wallet`, `partner_managed`, `deferred`

### What's Missing

**Three outcome categories are architectured but only one is live:**

| Outcome Type | Campaign Type | Status |
|-------------|---------------|--------|
| Charging (driver charges at right place/time) | `session` | **LIVE** |
| Spend (receipt-verified merchant purchase) | `receipt` | Partially built |
| Data (driver submits feedback/survey/photos) | `data` | Planned only |

The `grant_type` field and `(session_event_id, grant_type)` constraint support stacking one grant per type per session, but the `receipt` and `data` campaign types have no end-to-end flow yet.

---

## 2. Merchant Traffic Monetization — PARTIAL

### What Exists

**Claim-Based Billing Model** (design complete, partially coded):
- Core billing event: **Claim + Presence** = active charging session + within 250-350m + driver taps "Claim Offer"
- AOV-based dynamic pricing:

| AOV Bracket | Claim Cost (4% of AOV) |
|------------|----------------------|
| Under $10 | $0.40 |
| $10-25 | $1.00 |
| $25-50 | $2.00 |
| $50-100 | $4.00 |

**Toast POS Integration** (`backend/app/services/toast_pos_service.py`) — **FULL**:
- OAuth flow, order fetch, 30-day rolling AOV calculation
- Mock mode for development (`TOAST_MOCK_MODE=true`)
- Endpoints: `/v1/merchant/pos/toast/connect`, `/callback`, `/status`, `/disconnect`, `/aov`

**Exclusive Session System** (`backend/app/models/exclusive_session.py`) — **LIVE**:
- Merchant deal activation with countdown timer (default 60 min)
- Statuses: ACTIVE → VERIFIED → COMPLETED / EXPIRED / REJECTED
- Driver claim flow deployed 2026-03-18

**Merchant Reward System** (`backend/app/services/merchant_reward_service.py`) — **LIVE**:
- `RewardClaim` model with 2-hour expiry
- `ReceiptSubmission` model with Taggun OCR integration
- Request-to-Join flow for non-Nerava merchants (demand signal)

**Merchant Funding Model** — **LIVE**:
- Free trial via promo codes (`NERAVA100` → $100 balance, fee waived)
- Paid deposits via Stripe Checkout → 20% platform fee → net credited
- Auto-pause when balance < reward amount

### What's Missing

**Verification Token System** — DESIGNED, NO CODE:
- Per `CHARGING_VERIFIED_COMMERCE.md` Phase 1.1:
  - `VerificationToken` model: format `nrv_vt_{40_hex_chars}`, 2-hour TTL
  - Status lifecycle: active → claimed → expired/revoked
  - Public endpoint: `POST /v1/verify-charging` (token IS the auth)
  - Response: `{ verified: true, distance_m, session_duration_min }`
- **Impact:** Blocks merchant-side checkout integration (merchant can't verify driver is charging)

**CommerceClaim Model** — DESIGNED, NO CODE:
- Separate from `RewardClaim` (which is coupled to receipt upload)
- Would track: driver, session, verification token, campaign, merchant, distance, AOV bracket, claim cost
- Idempotency via `idempotency_key: claim_{token_id}_{merchant_place_id}`

**Commerce Campaign Fields** — NOT ADDED TO MODEL:
- Design calls for: `commerce_enabled`, `commerce_offer_description`, `commerce_aov_bracket`, `commerce_cost_bps` (default 400), `commerce_daily_cap`, `commerce_merchant_ids`, `commerce_geo_radius_m`, `commerce_ordering_url`
- Only documented in `CHARGING_VERIFIED_COMMERCE.md`

---

## 3. Receipt Verification & OCR — PARTIALLY BUILT

### What Exists

**Taggun OCR** (`backend/app/services/merchant_reward_service.py`):
- `process_receipt_ocr()` submits receipt image URL to Taggun API ($0.04/scan)
- Extracts: merchant name, total amount (cents), transaction date, confidence
- Auto-approves if confidence >= 0.7 and total_cents > 0
- Mock mode returns realistic fake data
- Stores OCR response in `ReceiptSubmission.ocr_raw_response` (JSON)

**Receipt Upload Flow:**
1. Driver uploads receipt as base64
2. Creates `ReceiptSubmission` record
3. Validates claim status (must be CLAIMED)
4. Processes OCR
5. Updates claim: CLAIMED → RECEIPT_UPLOADED → APPROVED/REJECTED
6. Creates wallet ledger entry on approval

### What's Missing

- **Receipt ↔ Campaign Grant link:** `ReceiptSubmission` is not wired to `IncentiveGrant`. Receipt approval doesn't trigger campaign budget decrement.
- **Card-linked verification (Fidel API):** Phase 2 design exists — automatic verification without driver upload. Not started.
- **Receipt campaign type in IncentiveEngine:** Engine only evaluates `session` type. No `receipt` evaluation path.

---

## 4. Utility / Grid Integration — STUB ONLY

### What Exists

**Grid Intelligence Router** (`backend/app/routers/grid.py`):
- Endpoints: `/v1/grid/metrics/current`, `/v1/grid/metrics/time-series`
- Returns KPI aggregations from `RewardEvent` table:
  - Total rewards (cents), kWh delivered, CO2 kg
  - Hardcoded coefficients: `KWH_PER_CENT = 0.1`, `CO2_PER_KWH = 0.4`
- **This is purely informational — no active grid control or demand-side management**

**Energy Reputation System** (`backend/app/services/reputation.py`):
- Gamified tier system: Bronze → Silver → Gold → Platinum
- Points 1:1 with Nova earned; streak tracking
- **Gamification only — not grid-tied**

### What's Completely Missing

| Feature | Impact | Effort |
|---------|--------|--------|
| Time-of-use (TOU) rate integration | Lets campaigns target off-peak hours with real utility data | 4-6 weeks |
| Demand response signaling | Trigger/incentivize charging shifts for grid balancing | 8-12 weeks |
| Ancillary services contracts | Frequency response, voltage support revenue | 12+ weeks |
| Renewable energy targeting | Peak solar/wind hour campaigns | 2-3 weeks |
| Utility billing integration | Bill utility companies for verified load shifting | 6-8 weeks |
| Utility-specific campaign rules | TOU period targeting in IncentiveEngine | 2-3 weeks |

**Assessment:** The `off_peak` campaign type exists as a label but has no utility data backing. Campaigns can target time-of-day windows, which is a rough proxy for TOU periods, but there's no real grid signal integration.

---

## 5. Enterprise Data & Analytics — EMERGING

### What Exists

**Charger Reliability Score** (`backend/app/services/charger_score.py`):
- Nerava Score (0-100) based on: completion rate (40%), recency (30%), driver diversity (20%), duration (10%)
- Returns None if < 5 sessions (insufficient data)
- Ready for partner/enterprise consumption but not exposed as a product

**Merchant Insights** (`backend/app/services/merchant_insights.py`):
- `/v1/merchants/{id}/report`: EV visits, unique drivers, Nova awarded, rewards
- `/v1/merchants/me/insights`: Self-service — nearby chargers, foot traffic heatmaps, conversion funnel
- K-anonymity enforcement (min 5 unique drivers)
- Weekly merchant report worker: `backend/app/workers/weekly_merchant_report.py`

**Corporate Classifier** (`backend/app/services/corporate_classifier.py`):
- Multi-layer: denylist → domain → franchise pattern → type heuristic
- ~100+ corporate domains, ~80 chain patterns
- Outputs: `local`, `corporate`, `review`

**Data Collection in Place:**
- Location trails (GPS breadcrumbs in `session_metadata`)
- Intent signals, dwell times, foot traffic patterns
- Session telemetry (kWh, battery %, power, connector)
- Charger cable/brand data from Tesla charge_state

### What's Missing

**Data Licensing Product** (designed in `NERAVA_DATA_STRATEGY_REPORT.md`, not built):

| Tier | Price | Features | Status |
|------|-------|----------|--------|
| Starter Insights | $49/mo | Monthly foot traffic, peak hours, competitors | Not built |
| Growth Insights | $149/mo | Real-time dashboard, weekly email, heatmap, intent | Not built |
| Enterprise Insights | $299+/mo | Raw data API, custom reports, dedicated analyst | Not built |

**Missing infrastructure:**
- No tiering/paywall logic
- No API rate limiting per data tier
- No metering or usage tracking
- No raw session data export endpoints (only aggregated)
- No data licensing contracts or revenue sharing terms
- No insurance/risk data products (charger safety ratings)

---

## 6. Partner Incentive API — FULLY IMPLEMENTED

### What Exists

| Component | Endpoint/File | Status |
|-----------|--------------|--------|
| Partner model + trust tiers | `backend/app/models/partner.py` | Live |
| API key auth (`nrv_pk_` prefix) | `backend/app/dependencies/partner_auth.py` | Live |
| Session ingest | `POST /v1/partners/sessions` | Live |
| Session CRUD | `GET/PATCH /v1/partners/sessions/{id}` | Live |
| Grant listing | `GET /v1/partners/grants` | Live |
| Campaign discovery | `GET /v1/partners/campaigns/available` | Live |
| Partner profile | `GET /v1/partners/me` | Live |
| Admin CRUD | `/v1/admin/partners/*` | Live |
| Shadow driver resolution | `partner_session_service.py` | Live |

**Trust tiers:** 1=hardware-verified (+20 quality), 2=api-verified (+10), 3=app-reported (-10)

**19 tests** covering full flow, auth, idempotency, campaign matching, partner controls.

---

## 7. Session Quality & Anti-Fraud — FULLY IMPLEMENTED

**SessionEvent** (`backend/app/models/session_event.py`):
- `quality_score` (0-100) computed on session end
- `ended_reason`: unplugged, full, moved, timeout, unknown
- Full telemetry: battery %, power (kW), connector type, vehicle details
- Partner fields: `signal_confidence` (0-1), `partner_status`
- GPS breadcrumb trail (capped at 120 points)

---

## Summary: Feature Status Matrix

| Feature | Status | Revenue Impact | Build Effort |
|---------|--------|---------------|-------------|
| Campaign system (session type) | **LIVE** | Active revenue | — |
| Merchant exclusive claims | **LIVE** | Active revenue | — |
| Partner incentive API | **LIVE** | Partner revenue | — |
| Nova + wallet + payouts | **LIVE** | Driver retention | — |
| Energy reputation | **LIVE** | Engagement | — |
| Toast POS (AOV calculation) | **LIVE** | Pricing accuracy | — |
| Receipt OCR (Taggun) | **BUILT** | Blocked (not wired to grants) | 2-3 weeks |
| Corporate classifier | **BUILT** | Discovery quality | — |
| Charger reliability score | **BUILT** | Not monetized yet | 1-2 weeks |
| Merchant insights | **BUILT** | Not monetized yet | 2-4 weeks |
| Verification token system | **DESIGNED ONLY** | Blocks commerce revenue | 2-3 weeks |
| CommerceClaim model | **DESIGNED ONLY** | Blocks commerce revenue | 1-2 weeks |
| Commerce campaign fields | **DESIGNED ONLY** | Blocks commerce revenue | 1 week |
| Data licensing product | **DESIGNED ONLY** | $49-300+/mo SaaS | 4-6 weeks |
| Receipt → campaign grant link | **MISSING** | Blocks receipt revenue | 2-3 weeks |
| Card-linked verification (Fidel) | **MISSING** | Passive receipt verification | 3-4 weeks |
| Utility TOU integration | **MISSING** | Grid revenue stream | 4-6 weeks |
| Demand response signaling | **MISSING** | Grid revenue stream | 8-12 weeks |
| Utility billing integration | **MISSING** | Grid revenue stream | 6-8 weeks |
| Enterprise data API + paywall | **MISSING** | Data licensing revenue | 4-6 weeks |

---

## Prioritized Recommendations

### P0 — Unblock Commerce Revenue (4-6 weeks)

1. **Build Verification Token System** — Merchants need to verify a driver is charging before giving a discount. This is the single biggest blocker to merchant-side monetization.
2. **Build CommerceClaim model + commerce campaign fields** — Enable AOV-based billing events.
3. **Wire receipt OCR to campaign grants** — Receipt approval should trigger `IncentiveGrant` creation and budget decrement.

### P1 — Monetize Existing Data (4-6 weeks)

4. **Ship Merchant Insights as paid product** — Data collection and aggregation already exist. Add tiering, paywall, and Stripe subscription billing.
5. **Expose Charger Reliability Score to partners** — Charging networks would pay for crowd-sourced reliability data.

### P2 — Utility Revenue (8-12 weeks, post-Series A)

6. **Add TOU rate integration** — Let campaigns target real utility off-peak windows instead of hardcoded time ranges.
7. **Build demand response triggers** — Partner with utilities to incentivize load shifting.

### P3 — Scale & Automate (3-4 weeks each)

8. **Card-linked verification (Fidel API)** — Eliminates receipt upload friction for spend verification.
9. **Enterprise data API tier** — Raw data export with rate limiting and metering for large partners.

---

## Revenue Model Summary

| Revenue Stream | Status | Est. Revenue Potential |
|---------------|--------|----------------------|
| Charging campaigns (session grants) | **LIVE** | Core revenue today |
| Merchant claim billing (AOV-based) | **Blocked** (needs verification tokens) | $0.40-4.00 per qualified lead |
| Merchant prepaid deposits | **LIVE** | 20% platform fee on deposits |
| Partner session fees | **LIVE** | Per-session or rev-share |
| Data licensing (insights tiers) | **Not built** | $49-300+/mo per subscriber |
| Utility demand response | **Not built** | Per-kWh shifted or contract-based |
| Receipt verification campaigns | **Partially built** | Per-verified-purchase |

**Bottom line:** Nerava's charging outcome monetization is solid and live. The highest-ROI next step is building the Verification Token System to unlock merchant commerce revenue — the design is complete, the claim flow is deployed, and this is the missing link between driver demand and merchant billing.
