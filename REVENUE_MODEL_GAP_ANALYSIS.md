# Nerava Revenue Model Gap Analysis

**Date:** 2026-03-22
**Purpose:** Map Parker's unified monetization framework against what's actually built in the codebase. Identify gaps that block each revenue layer from going live.

---

## The System

Nerava is a **verified behavior layer monetized at every point money touches that behavior.**

One driver action (charges EV + visits merchant) can generate 3-4 revenue streams simultaneously. The layers reinforce each other: fleet locks in infrastructure, merchants drive behavior, utilities fund the system, data extracts long-term value.

**At 1M active drivers (target model):**

| Layer | Revenue Driver | Monthly | Annual |
|-------|---------------|---------|--------|
| Fleet/EVject | $3/vehicle/mo avg | $3M | $36M |
| Reimbursement | 2 txn/mo x $2 | $4M | $48M |
| Merchant | 1 visit/mo x $3 | $3M | $36M |
| Utility | $2/driver/mo | $2M | $24M |
| Data/Enterprise | Contracts | $400K | $5M |
| **Total** | | **$12.4M** | **$149M** |

---

## Layer 1: Fleet / EVject SaaS (Foundation)

**Model:** $4/vehicle/month + $0.10/session
**Margin:** 80%+ (pure software)
**Role:** Predictable recurring revenue, locks in infrastructure

### What's Built (60%)

| Component | File | Status |
|-----------|------|--------|
| Partner API (full CRUD) | `backend/app/routers/partner_api.py` | Done |
| Partner session ingest (idempotent) | `backend/app/services/partner_session_service.py` | Done |
| Admin partner management | `backend/app/routers/admin_partners.py` | Done |
| API key auth (SHA-256, `nrv_pk_` prefix) | `backend/app/dependencies/partner_auth.py` | Done |
| Trust tier system (1-3) | `backend/app/models/partner.py` | Done |
| Shadow driver resolution | `partner_session_service.py` | Done |
| Webhook delivery (HMAC-SHA256, retries) | `backend/app/services/webhook_delivery.py` | Done |
| Campaign matching with partner controls | `backend/app/services/incentive_engine.py` | Done |
| Charger quality scoring (0-100) | `backend/app/services/charger_score.py` | Done |
| Session telemetry (30+ fields) | `backend/app/models/session_event.py` | Done |
| 19 integration tests | `backend/tests/test_partner_api.py` | Done |

### What's Missing

| Gap | Priority | Effort | Impact |
|-----|----------|--------|--------|
| **Fleet dashboard UI** — no console for EVject/partners to view vehicle metrics, session history, fleet health | P0 | 2-3 weeks | Blocks EVject pilot |
| **Anomaly detection service** — no ML/heuristic logic for flagging suspicious sessions (power spikes, location jumps, early stops, battery inconsistencies) | P1 | 1-2 weeks | Core fleet value prop |
| **Real-time session alerts** — no webhook/push for anomalous sessions as they happen | P1 | 1 week | Fleet operators expect this |
| **Charger reliability scoring API** — quality_score exists but no uptime %, failure rate, or compatibility matrix exposed via API | P2 | 1 week | Acquirer/data value |
| **Per-vehicle billing infrastructure** — no metering for $4/vehicle/month; no Stripe usage-based billing for partners | P1 | 1-2 weeks | Revenue collection |
| **Smartcar session integration** — Smartcar OAuth works but NOT wired to SessionEvent creation | P0 | 2-3 weeks | Blocks non-Tesla vehicles |

### EVject Economics

| Party | Per Vehicle/Month | Per Session |
|-------|------------------|-------------|
| Nerava charges EVject | $4 | $0.10 |
| EVject charges fleet operator | $10-20 | Pass-through |
| **EVject margin** | **$6-16 (60-80%)** | |

EVject says yes because Nerava is **revenue expansion**, not cost.

### Scale Projections

| Vehicles | Monthly SaaS | Monthly Sessions | Total/Month | Annual |
|----------|-------------|-----------------|-------------|--------|
| 1,000 | $4K | $1-2K | $5-6K | $60-72K |
| 10,000 | $40K | $10-20K | $50-60K | $600-720K |
| 100,000 | $400K | $100-200K | $500-600K | $6-7.2M |

---

## Layer 2: Lyft / Reimbursement Flow (Volume Engine)

**Model:** $2 per transaction (~20% on $10 flow)
**Margin:** 70-75%
**Role:** Drives transaction volume, creates platform stickiness

### What's Built (15%)

| Component | File | Status |
|-----------|------|--------|
| Driver wallet (balance, pending, Stripe Express) | `backend/app/services/payout_service.py` | Done |
| Double-entry wallet ledger | `backend/app/models/driver_wallet.py` | Done |
| Stripe Express payouts | `backend/app/routers/stripe_api.py` | Done |
| Withdrawal fee structure ($0.25 + 0.25% under $20) | `payout_service.py` | Done |
| Platform fee config (20% / 2000 BPS) | `backend/app/core/config.py` | Done |
| Payment idempotency | `stripe_webhooks.py` | Done |

### What's Missing

| Gap | Priority | Effort | Impact |
|-----|----------|--------|--------|
| **Lyft API integration** — zero code for driver detection, ride history, or reimbursement linking | P2 | 3-4 weeks | Blocks Lyft revenue entirely |
| **Reimbursement-specific API** — no endpoints for submitting/verifying reimbursement claims | P2 | 2 weeks | |
| **Receipt OCR (Taggun)** — `ocr_provider` field exists in model but no actual API integration | P2 | 1 week | Receipt verification |
| **Card-linked verification (Fidel API)** — Phase 2 plan only, zero code | P3 | 3-4 weeks | Automatic receipt matching |
| **Multi-party payment routing** — no split payment support (driver portion + reimbursement portion) | P2 | 2 weeks | |
| **Ride-share driver verification** — no way to verify someone is a Lyft/Uber driver | P2 | 1 week | |

### Scale Projections

| Transactions/Month | Revenue | Cost | Profit |
|--------------------|---------|------|--------|
| 100K | $200K | $50K | $150K |
| 1M | $2M | $500K | $1.5M |

**Note:** This is the least-built layer. Requires Lyft partnership or direct ride-share driver targeting to activate. Lower priority than Fleet and Merchant.

---

## Layer 3: Merchant Incentives (Growth Loop)

**Model:** $2-4 per verified claim (4% of AOV)
**Margin:** 60-70%
**Role:** Drives driver engagement, shapes behavior, creates local network effects

### What's Built (70%)

| Component | File | Status |
|-----------|------|--------|
| Exclusive session system (activate, countdown, complete) | `backend/app/routers/exclusive.py` | Done |
| Verified visit tracking with redemption codes | `backend/app/models/exclusive_session.py` | Done |
| ChargerMerchant links (exclusive_title, distance) | `backend/app/models/while_you_charge.py` | Done |
| Toast POS OAuth + mock mode | `backend/app/services/toast_pos_service.py` | Done |
| AOV calculation from Toast orders | `toast_pos_service.py` | Done |
| Reconciliation API (summaries, daily breakdown, CSV export) | `backend/app/routers/merchant_reconciliation.py` | Done |
| Merchant acquisition funnel (find, preview, claim) | `apps/merchant/` | Done |
| Merchant portal (exclusives CRUD, billing, settings) | `apps/merchant/` | Done |
| Campaign budget management (atomic decrement, auto-pause) | `backend/app/services/campaign_service.py` | Done |
| Promo codes (NERAVA100 = $100 free credit) | `campaign_service.py` | Done |
| Driver claim flow (charging check + eligibility + visit tracking) | `apps/driver/ChargerDetailSheet.tsx` | Done |
| Push notification on nearby merchant while charging | `backend/app/services/push_service.py` | Done |
| Toast discount attribution ("Nerava Margarita" in POS) | Live in production | **Verified 2026-03-18** |

### What's Missing

| Gap | Priority | Effort | Impact |
|-----|----------|--------|--------|
| **Dynamic AOV-based pricing** — campaigns have fixed `cost_per_session_cents`, no bracket pricing ($0.40 for <$10 AOV, $1 for $10-25, $2 for $25-50, $4 for $50-100) | P1 | 1 week | Revenue optimization |
| **GPS proximity validation** — no 250-350m distance check in claim activation (server-side) | P0 | 2-3 days | Anti-fraud, billing integrity |
| **Verification token system** — `nrv_vt_` tokens described in CHARGING_VERIFIED_COMMERCE.md but NOT built. No CommerceClaim model. | P1 | 1 week | Clean billing events |
| **handleCompleteClaim API call** — driver app "I'm Done" button only updates UI state, doesn't call `POST /v1/exclusive/complete` or create VerifiedVisit | P0 | 2-3 days | Claim doesn't persist to backend |
| **Merchant-funded campaign creation flow** — merchants can't self-serve create AOV-based campaigns via portal | P1 | 2 weeks | Merchant self-service |
| **Real Taggun OCR** — receipt model stubbed, no actual API calls | P2 | 1 week | Receipt dispute evidence |

### Asadas Grill Test (2026-03-18) — What Worked

| Step | Status |
|------|--------|
| Charging detected at nearby Tesla Supercharger | Verified |
| Driver claim modal ("Claim reward at Asadas Grill?") | Working |
| Charging eligibility check | Working |
| "Nerava Margarita" discount applied in Toast POS | Verified ($5.00 discount) |
| Discount shows in Toast reports (Discount Summary tab) | Verified |
| Session shows in driver app (55 min, 50.9 kWh, +$0.40 reward) | Verified |
| Walking route map (charger to merchant) | Verified |

### Scale Projections

| Visits/Month | Avg Claim | Revenue | Margin |
|-------------|-----------|---------|--------|
| 50K | $3 | $150K | $90-105K |
| 500K | $3 | $1.5M | $900K-1.05M |

---

## Layer 4: Utility Incentives (Profit Engine)

**Model:** 10-25% of utility incentive spend
**Margin:** 80%+
**Role:** High-margin revenue funded by external budget (rate-payer funds, demand response programs)

### What's Built (40%)

| Component | File | Status |
|-----------|------|--------|
| Time-of-day targeting (rule_time_start/end, overnight spans) | `backend/app/models/campaign.py` | Done |
| Day-of-week targeting (rule_days_of_week JSON) | `campaign.py` | Done |
| Zone/geo targeting (center lat/lng + radius) | `campaign.py` + `incentive_engine.py` | Done |
| Charger network filtering (Tesla, ChargePoint, EVgo) | `campaign.py` | Done |
| Min power (kW) for DC fast charging | `campaign.py` | Done |
| Connector type targeting (CCS, Tesla, CHAdeMO) | `campaign.py` | Done |
| Campaign types include "off_peak", "utilization_boost" | `campaign.py` | Done |
| Budget management + auto-pause on exhaustion | `campaign_service.py` | Done |
| Sponsor console for campaign management | `apps/console/` | Done |

### What's Missing

| Gap | Priority | Effort | Impact |
|-----|----------|--------|--------|
| **Utility-specific onboarding** — no utility customer flow, no rate-payer program enrollment | P2 | 2-3 weeks | Blocks utility partnerships |
| **Real-time grid signal integration** — no API connection to ISO/RTO signals (CAISO, ERCOT, PJM) for dynamic demand response | P3 | 4-6 weeks | Dynamic pricing |
| **kWh-based rewards** — campaigns price per-session, not per-kWh. Utilities care about energy shifted, not session count | P1 | 1 week | Utility value alignment |
| **Utility reporting dashboard** — no UI showing: kWh shifted off-peak, peak reduction %, charger utilization deltas | P2 | 2-3 weeks | Utility proof of value |
| **Dynamic campaign pricing** — campaigns are static; no price adjustment based on grid load or TOU rates | P3 | 3-4 weeks | Demand response |
| **Utility billing/invoicing** — no system for billing utilities on % of incentive spend | P2 | 1-2 weeks | Revenue collection |

### Scale Projections

| Utility Spend/Year | Nerava Take (15%) | Margin |
|--------------------|-------------------|--------|
| $5M | $750K | $600K+ |
| $50M | $7.5M | $6M+ |

**Key insight:** Utility programs have existing budgets. You're not creating demand — you're redirecting existing rate-payer funds through a more efficient channel. The campaign infrastructure already handles the targeting; what's missing is the utility-facing wrapper.

---

## Layer 5: Data / Enterprise (Strategic Moat)

**Model:** $50K-250K/year contracts
**Margin:** 90%+
**Role:** Defensibility, long-term value extraction, competitive moat

### What's Built (35%)

| Component | File | Status |
|-----------|------|--------|
| Merchant reporting (K-anonymity protected) | `backend/app/routers/merchant_reports.py` | Done |
| Insights API (events, merchants) | `backend/app/routers/insights_api.py` | Done |
| CSV export (claims data) | `merchant_reconciliation.py` | Done |
| PostHog analytics across all apps | `packages/analytics` | Done |
| Server-side analytics service | `backend/app/services/analytics.py` | Done |
| Charger quality scoring (0-100) | `backend/app/services/charger_score.py` | Done |
| Rich session telemetry (30+ columns) | `session_event.py` | Done |
| K-anonymity threshold (min 5 drivers) | `merchant_reports.py` | Done |

### What's Missing

| Gap | Priority | Effort | Impact |
|-----|----------|--------|--------|
| **Data retention policy** — session_events grow unbounded. At 100K drivers: ~1M rows/month, ~100GB/year. No archival, no partitioning. | **P0 CRITICAL** | 1-2 weeks | DB cost explosion, query degradation |
| **Data warehouse export** — no BigQuery, Snowflake, or S3 Parquet pipeline | P2 | 2-3 weeks | Enterprise data contracts |
| **Charger reliability API** — quality_score exists but no uptime %, failure rate, charger compatibility, or safety metrics exposed | P1 | 2 weeks | Core data product |
| **Survey/review campaigns** — campaign_type "data" exists but no infrastructure for driver-submitted reviews, photos, or structured survey responses | P2 | 3-4 weeks | Data outcome campaigns |
| **Enterprise self-serve portal** — no UI for enterprise customers to query data, build reports, or set up alerts | P3 | 4-6 weeks | Scale beyond manual contracts |
| **Anonymized dataset API** — no bulk export of anonymized charging behavior for research/analysis customers | P2 | 2 weeks | Research contracts |

### Data Moat: What Accumulates

Every session adds to a proprietary dataset that gets harder to replicate over time:

| Data Asset | Source | Defensibility |
|-----------|--------|--------------|
| Charging session patterns (by location, time, vehicle) | SessionEvent | High — requires install base |
| Charger reliability scores | Aggregated sessions | High — requires volume |
| Merchant conversion data (claim → visit → spend) | ExclusiveSession + Toast | Very high — requires both sides |
| Driver behavior profiles (frequency, duration, preferred chargers) | SessionEvent + NovaTransaction | High — requires engagement |
| Cable/adapter detection (EVject hardware) | Tesla API telemetry | Unique — only with hardware partner |

---

## Cross-Layer Revenue Stacking

**One driver action = 3-4 revenue streams:**

```
Driver charges at charger (near merchant, during off-peak)
│
├── Fleet/EVject: $0.10 session fee (if EVject vehicle)
├── Merchant: $3 claim fee (driver walks to restaurant)
├── Utility: $0.40 (15% of $2.67 off-peak incentive)
├── Data: session adds to charger reliability + behavior dataset
│
└── Total captured per action: ~$3.50
    Total if reimbursement involved: ~$5.50
```

---

## The $50 EVject CAC Strategy

**Wrong:** $50 off EVject hardware (one-time discount, no retention, no data)

**Right:** $50 EVject Safety Credit, unlocked via behavior:

| Milestone | Unlock | What You Capture |
|-----------|--------|-----------------|
| Verify EV (connect Tesla/Smartcar) | $10 | Vehicle data, connected user |
| Complete 2 charging sessions | $10 | Session data, charger reliability signal |
| Visit a merchant during charging | $10 | Commerce conversion data |
| Complete safety monitoring setup | $20 | Ongoing engagement, push notification consent |

**EVject pays $50 CAC. You convert it into:**
- Engaged user generating sessions
- Merchant visits generating claim revenue
- Data generating enterprise value
- Ongoing safety subscription ($2-4/mo value)

The $50 is not a cost — it's a multi-layer revenue engine.

---

## Priority Roadmap (Next 30 Days)

### Week 1-2: Close Merchant Loop (Highest Revenue Velocity)
- [ ] Wire `handleCompleteClaim` to `POST /v1/exclusive/complete` (P0)
- [ ] Add GPS proximity validation in claim activation (P0)
- [ ] Dynamic AOV-based pricing brackets (P1)
- [ ] Merchant portal cleanup (drop dead pages, consolidate) (P1)

### Week 2-3: Fleet/EVject Pilot Ready
- [ ] Smartcar → SessionEvent integration (P0)
- [ ] Basic fleet dashboard (partner can view their sessions + vehicles) (P0)
- [ ] Anomaly detection v1 (heuristic: early stops, low power, duration outliers) (P1)
- [ ] Per-vehicle billing metering (P1)

### Week 3-4: Data Foundation
- [ ] Data retention policy (partition session_events, archive >90 days to S3) (P0 CRITICAL)
- [ ] Charger reliability API (expose quality_score + failure metrics) (P1)
- [ ] kWh-based campaign rewards (P1)

### Deferred (30-60 days)
- Utility reporting dashboard
- Enterprise data warehouse export
- Lyft/reimbursement API integration
- Survey/review campaigns
- Real-time grid signal integration

---

## Critical Path to Revenue

| Layer | First Revenue | Blocking Gap |
|-------|-------------|-------------|
| **Merchant** | **Now (Asadas verified 3/18)** | Complete claim API call, proximity check |
| **Fleet/EVject** | 30-60 days | Smartcar integration, fleet dashboard, billing |
| **Utility** | 60-90 days | kWh rewards, utility reporting, partnerships |
| **Data** | 90-120 days | Retention policy, reliability API, contracts |
| **Reimbursement** | 120+ days | Lyft partnership, full integration |

**Bottom line:** Merchant is live and generating verifiable transactions TODAY. Fleet is 60% built and needs Smartcar + dashboard to pilot with EVject. Everything else stacks on top of those two foundations.
