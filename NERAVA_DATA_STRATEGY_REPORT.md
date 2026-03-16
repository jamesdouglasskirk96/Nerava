# Nerava Data Strategy: Verified EV Charging Behavior Intelligence

**Prepared for:** Gemini (Growth Team)
**Date:** February 28, 2026
**Confidential — Internal Use Only**

---

## Executive Summary

Nerava sits at a unique intersection: we verify that an EV is physically plugged in and charging via the Tesla Fleet API, then continuously track the driver's phone GPS throughout the session. This gives us something no one else has — **verified dwell-time behavioral data tied to a known charging location**. We know exactly where a driver goes, how long they stay, and what they do while their car charges. This is the foundation of a merchant data subscription product.

---

## 1. What We Collect (The Data Asset)

### 1.1 Verified Charging Session Data

Every charging session creates a `SessionEvent` record with:

| Data Point | Source | Update Frequency |
|-----------|--------|-----------------|
| Session start/end timestamps | Tesla Fleet API | On state change |
| Duration (minutes) | Computed | On session end |
| kWh delivered | Tesla Fleet API | Every 30s |
| Charger power (kW) | Tesla Fleet API | Every 30s |
| Battery start/end % | Tesla Fleet API | Start + end |
| Charger ID + network | Matched from DB | On session start |
| Connector type | Tesla Fleet API | On session start |
| Vehicle ID + VIN | Tesla Fleet API | On session start |
| Session quality score (0-100) | Anti-fraud heuristics | On session end |
| Verification method | System | On session start |

**Key differentiator:** Every session is **cryptographically verified** through the Tesla OAuth token chain. We don't rely on self-reported data — we have API-level proof the car is charging.

### 1.2 Continuous Location Trail

Starting with v2.7 (deployed today), every active charging session records a **GPS breadcrumb trail** from the driver's phone:

```
session_metadata.location_trail = [
  { "lat": 30.3621, "lng": -97.7382, "ts": "2026-02-28T14:30:00" },
  { "lat": 30.3625, "lng": -97.7389, "ts": "2026-02-28T14:30:30" },
  { "lat": 30.3632, "lng": -97.7401, "ts": "2026-02-28T14:31:00" },
  ...up to 120 points (~60 min at 30s intervals)
]
```

- **Collection method:** `navigator.geolocation.watchPosition()` with `enableHighAccuracy: true`
- **Frequency:** Every 30 seconds (matches poll interval)
- **Max points:** 120 per session (capped to control storage)
- **Accuracy:** High-accuracy GPS mode, typically 5-15m radius

This trail shows us: did the driver walk to a coffee shop? Browse a retail store? Sit in a restaurant for 40 minutes? Walk around a mall?

### 1.3 Driver Profile & Preferences

| Field | Description |
|-------|-------------|
| `vehicle_model` | Make/model (e.g., "Tesla Model 3") |
| `vehicle_color` | Vehicle color |
| `home_zip` | Home zip code |
| `food_tags` | Cuisine preferences (JSON array: ["coffee", "tacos"]) |
| `max_detour_minutes` | Willingness to walk/drive for dining |
| `preferred_networks` | Charger network preferences |
| `typical_start` / `typical_end` | Habitual charging windows |
| `energy_reputation_score` | Engagement tier (Bronze → Platinum) |

### 1.4 Merchant Interaction Data

| Event | Data Captured |
|-------|---------------|
| **Merchant shown** | Which merchants appeared in results, in what order, walk distance |
| **Exclusive activation** | Which merchant was selected, intent (eat/work/quick-stop), party size |
| **Visit verification** | GPS proof of arrival at merchant, accuracy in meters |
| **Merchant confirmation** | POS order total, order number, confirmation timestamp |
| **Amenity votes** | Upvote/downvote on wifi, bathroom availability |
| **Feedback** | Rating (up/down), reason, freeform comment |

### 1.5 Wallet & Spending Data

- Total lifetime earnings from charging rewards
- Payout history (amounts, frequency, method)
- Campaign reward redemptions (which sponsors, how much)
- Energy reputation tier and streak data

---

## 2. Why This Data Is Unique

### 2.1 Verified Dwell Time (No Other Platform Has This)

Google Maps knows where people go. Foursquare/Placer.ai estimates foot traffic. But **none of them can verify that a person is physically stationary for 20-60 minutes** with the same confidence we can. We have:

1. **Tesla API proof** that the car is plugged in and charging
2. **Continuous phone GPS** showing the driver's movement during that verified window
3. **Merchant-level granularity** — we know which specific business they walked to

This creates a dataset where every observation is anchored to a **verified, high-confidence dwell event**. The driver isn't just passing through — they are guaranteed to be in the area for the duration of their charge.

### 2.2 Intent Signal

When a driver activates an exclusive session, they explicitly tell us their intent:
- `eat` — looking for food/dining
- `work` — looking for a workspace
- `quick-stop` — just grabbing something fast

Combined with `food_tags` preferences, this is a declared intent signal at the moment of highest purchase likelihood.

### 2.3 Cross-Validated Location

We have **two independent location sources** for every session:
- **Tesla vehicle GPS** — where the car is physically charging
- **Device GPS** — where the driver's phone is, updated every 30 seconds

This cross-validation eliminates spoofing and provides confidence scores that location-only platforms can't match.

---

## 3. The Merchant Data Product

### 3.1 Product: "Nerava Insights" — EV Driver Behavior Subscriptions

A monthly SaaS subscription for merchants near EV chargers, providing:

**Dashboard Features:**
- How many EV drivers charge within walking distance of your business per day/week/month
- What % of those drivers walk to your area vs. stay at their car
- Average dwell time of EV drivers in your vicinity
- Peak charging hours (when to staff up / run promotions)
- Competitive benchmarking (anonymized: "drivers in your zone also visit X category")
- Foot traffic heatmaps derived from location trails
- Conversion funnel: shown in app → activated → visited → confirmed

**Data Delivery:**
- Real-time dashboard (web portal)
- Weekly email digest
- Monthly PDF report with trends
- Raw data API access (Enterprise tier only)

### 3.2 What Merchants Get at Each Tier

#### Starter — $49/month
- Monthly EV foot traffic report (aggregated, anonymized)
- Charging volume near your location (sessions/day, avg duration)
- Peak hours breakdown (morning/afternoon/evening/night)
- Category-level competitor view ("35% of nearby EV drivers visited coffee shops")
- 1 location

#### Growth — $149/month
- Everything in Starter
- Weekly reports instead of monthly
- Dwell time distribution (what % of drivers stay 15 min, 30 min, 45 min, 60+ min)
- Walk pattern heatmap (aggregated trails showing foot traffic flow)
- Driver preference breakdown (cuisine tags, intent signals — anonymized aggregate)
- Conversion metrics (how many drivers saw your listing vs. activated vs. visited)
- Promotional slot: feature your deal to drivers charging nearby
- Up to 3 locations

#### Enterprise — $399/month per location
- Everything in Growth
- Daily reporting cadence
- Real-time dashboard with live session count nearby
- API access to anonymized aggregate data
- Custom geofence alerts ("notify me when 5+ drivers are charging within 0.5mi")
- Cross-location comparison (for multi-unit operators)
- Dedicated account manager
- Custom reports on request

### 3.3 Add-On: Sponsored Campaigns

Beyond the data subscription, merchants can run **campaigns** through our existing campaign engine:

| Campaign Type | Pricing |
|--------------|---------|
| **Per-session reward** | $1.00 - $5.00 per verified visit (merchant sets amount) |
| **Time-targeted** | +20% premium for peak-hour targeting |
| **New driver acquisition** | +30% premium for first-visit-only campaigns |
| **Minimum budget** | $100/month |
| **Platform fee** | 15% of campaign spend |

The campaign system is already built and deployed (`campaigns` table, `IncentiveEngine`, sponsor console at `apps/console`).

---

## 4. Pricing Justification

### 4.1 Comparable Market Rates

| Competitor | Product | Price |
|-----------|---------|-------|
| Placer.ai | Foot traffic analytics | $500-2,000/mo |
| Adentro (formerly ListenFirst) | Walk-in analytics | $200-500/mo |
| Foursquare Pilgrim | Location intelligence API | $0.01-0.05 per query |
| Near Intelligence | Audience intelligence | Custom ($1,000+/mo) |
| Bluedot | Geofencing triggers | $500+/mo |

Our pricing ($49-399) is intentionally **below** these incumbents because:
1. We're starting from zero and need adoption
2. Our dataset is currently Tesla-only (expanding)
3. We can upsell to campaigns which have much higher margin
4. The data subscription is a **lead-gen tool** for campaign sales

### 4.2 Unit Economics

**Cost to serve per merchant subscription:**

| Cost Component | Monthly | Notes |
|---------------|---------|-------|
| RDS storage (merchant's data slice) | $0.02 | Negligible — shared DB |
| Compute (report generation) | $0.50 | Lambda or scheduled job |
| Email delivery (reports) | $0.10 | SendGrid |
| Dashboard hosting | $0.20 | Static site, shared infra |
| **Total COGS** | **~$0.82** | |

| Tier | Revenue | COGS | Gross Margin |
|------|---------|------|-------------|
| Starter ($49) | $49 | $0.82 | 98.3% |
| Growth ($149) | $149 | $1.50 | 99.0% |
| Enterprise ($399) | $399 | $5.00 | 98.7% |

Software margins. The data is a byproduct of our core charging session loop — we're already collecting it.

### 4.3 Revenue Projections

**Assumptions:**
- Market: Merchants within 0.5 mi of EV chargers in Nerava-covered zones
- Austin metro alone: ~200 charger locations, avg 8 walkable merchants each = 1,600 addressable merchants
- Conversion: 5% Year 1, 15% Year 2 (merchant acquisition funnel already built)

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| Addressable merchants | 1,600 | 5,000 | 15,000 |
| Subscribers | 80 | 750 | 3,000 |
| Avg revenue/merchant/mo | $99 | $129 | $149 |
| **Subscription MRR** | **$7,920** | **$96,750** | **$447,000** |
| Campaign attach rate | 20% | 35% | 40% |
| Avg campaign spend/mo | $300 | $400 | $500 |
| **Campaign MRR** | **$4,800** | **$105,000** | **$600,000** |
| **Total MRR** | **$12,720** | **$201,750** | **$1,047,000** |
| **Total ARR** | **$152,640** | **$2,421,000** | **$12,564,000** |

---

## 5. Data Privacy & Compliance

### 5.1 What We Share vs. What We Keep

**NEVER shared with merchants (kept internal):**
- Individual driver identity (name, phone, email)
- Individual GPS trails or coordinates
- Individual vehicle VIN or ID
- Individual wallet balances or earnings
- Raw session-level data

**Shared with merchants (aggregated + anonymized):**
- Aggregate foot traffic counts (min cohort size: 5 drivers)
- Distribution curves (dwell time, visit frequency)
- Category-level preferences (% who like coffee, % who like tacos)
- Time-of-day patterns (aggregate)
- Heatmaps (min 10 data points per cell, blurred to 50m resolution)

### 5.2 Compliance Framework

- **Driver consent:** Location permission is already requested for core functionality (charger matching, session detection). Data usage for anonymized analytics should be covered by Terms of Service update.
- **CCPA:** Drivers can request data deletion. Anonymized/aggregated data is exempt.
- **GDPR (if expanding to EU):** Need explicit opt-in for analytics beyond core service. Aggregated data with k-anonymity ≥ 5 is compliant.
- **Action item:** Legal review of ToS to ensure "anonymized aggregate analytics for merchant partners" is covered.

### 5.3 k-Anonymity Standard

All merchant-facing reports enforce a **minimum cohort of 5 unique drivers** before any data point is shown. If fewer than 5 drivers charged near a merchant in a given time window, that data point is suppressed or merged with adjacent time windows.

---

## 6. Data Collection at Scale — Cost Impact

From the cost analysis we ran earlier, here's how the data storage scales:

| Driver Count | Sessions/Month | Location Points/Month | Storage Cost/Month | Total Data Infra Cost/Month |
|-------------|---------------|----------------------|-------------------|-----------------------------|
| 1,000 | 4,000 | 480,000 | $0.08 | $45 |
| 10,000 | 40,000 | 4,800,000 | $0.80 | $180 |
| 100,000 | 400,000 | 48,000,000 | $8.00 | $850 |
| 1,000,000 | 4,000,000 | 480,000,000 | $80.00 | $4,500 |

The location trail (120 JSON points per session, ~4KB each) adds approximately **16 bytes per data point** or **1.9 KB per session**. At 1M drivers doing 4 sessions/month, that's ~7.6 GB/month of location trail data — about **$0.87/month in RDS storage**. The data is essentially free to store.

---

## 7. Technical Architecture (Already Built)

### What's Live in Production Today

| Component | Status | Purpose |
|-----------|--------|---------|
| Tesla Fleet API integration | LIVE | Verified charging detection |
| GPS location trail collection | LIVE (v2.7) | 30s breadcrumb tracking |
| Session event pipeline | LIVE | Full session lifecycle |
| Campaign engine | LIVE | Sponsor targeting + payouts |
| Incentive evaluation | LIVE | Rule-based reward matching |
| Merchant proximity matching | LIVE | Walk distance/time calc |
| Charger-merchant mapping | LIVE | Pre-computed relationships |
| Driver preference capture | LIVE | Food tags, intent signals |
| Exclusive session verification | LIVE | GPS-verified merchant visits |
| Energy reputation system | LIVE | Driver engagement scoring |
| Stripe payouts | LIVE | Driver reward disbursement |
| Merchant acquisition funnel | LIVE | `/find` → `/preview` → `/claim` |
| Merchant dashboard | LIVE | Basic visit/activation metrics |

### What Needs to Be Built for Data Subscriptions

| Component | Effort | Priority |
|-----------|--------|----------|
| Aggregate analytics engine (SQL views + caching) | ~30 min | P0 |
| Merchant insights dashboard (extend `apps/merchant`) | 2-3 hours | P0 |
| Weekly/monthly email report generator (SendGrid) | ~1 hour | P1 |
| Heatmap visualization from location trails | 1-2 hours | P1 |
| Subscription billing (Stripe recurring — already integrated) | ~1 hour | P0 |
| API access layer (Enterprise tier) | ~1 hour | P2 |
| k-anonymity enforcement layer | ~30 min | P0 |
| Admin controls for data access tiers | ~30 min | P1 |

**Total estimated build time: 6-8 hours across 1-2 working sessions**

---

## 8. Competitive Moat

1. **Verified dwell = verified attention.** No other platform can guarantee a consumer is stationary for 20-60 minutes with the same confidence.

2. **Intent at point of highest purchase likelihood.** The driver just parked. They have 30-60 minutes. They told us what they want (eat/work/quick-stop). This is the highest-value commercial intent signal in physical retail.

3. **Cross-validated location.** Tesla GPS + phone GPS + charger network ID = three independent location confirmations per session. No spoofing, no estimation.

4. **Data gets better with scale.** More drivers = denser trails = better heatmaps = more accurate predictions. Network effects compound.

5. **Campaign engine is the upsell.** The data subscription is the foot in the door. The real money is in campaigns where merchants pay $1-5 per verified visit. Data subscription → campaign conversion is the growth flywheel.

---

## 9. Immediate Next Steps

1. **Legal review** — Update Terms of Service to cover anonymized aggregate data sharing with merchant partners
2. **Aggregate analytics SQL views** — Build the queries that power merchant dashboards
3. **Merchant insights MVP** — Extend existing merchant portal with Starter-tier metrics
4. **Pricing page** — Add data subscription pricing to merchant acquisition funnel
5. **Pilot program** — Offer 10 merchants near Domain/Mueller chargers free 90-day trials, convert to paid

---

*This document describes Nerava's current technical capabilities and proposed data strategy. All projections are estimates. Pricing is subject to market testing.*
