# Nerava Database Schema & Paid Merchant Dashboard Blueprint

## Part 1: Current Database Schema

Nerava's backend runs on PostgreSQL (RDS) in production and SQLite in development, managed via SQLAlchemy 2 ORM with 82 Alembic migrations. There are **~60 active tables** organized into the following domains.

---

### Core User & Auth Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | All platform users (drivers, merchants, admins) | `id`, `email`, `phone`, `password_hash`, `role_flags`, `auth_provider`, `provider_sub`, `admin_role`, `vehicle_color`, `vehicle_model` |
| `refresh_tokens` | JWT refresh token rotation | `user_id`, `token_hash`, `expires_at`, `revoked`, `replaced_by` |
| `otp_challenges` | Phone OTP verification | `phone`, `code_hash`, `expires_at`, `attempts`, `consumed` |
| `user_consents` | GDPR consent tracking | `user_id`, `consent_type`, `granted_at`, `privacy_policy_version` |
| `user_notification_prefs` | Push notification preferences | `user_id`, `earned_nova`, `nearby_nova`, `wallet_reminders` |
| `admin_audit_logs` | Admin action audit trail | `actor_id`, `action`, `target_type`, `target_id`, `before_json`, `after_json` |

### Vehicle & Tesla Integration

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `tesla_connections` | Tesla OAuth tokens per user | `user_id`, `access_token` (encrypted), `refresh_token` (encrypted), `vehicle_id`, `vin`, `is_active` |
| `ev_verification_codes` | EV-XXXX codes for charging proof | `user_id`, `code`, `charger_id`, `charging_verified`, `battery_level`, `charge_rate_kw`, `status`, `expires_at` |
| `tesla_oauth_states` | OAuth state persistence (DB-backed) | `state` (PK), `data_json`, `expires_at` |
| `vehicle_accounts` | Generic vehicle provider accounts | `user_id`, `provider`, `provider_vehicle_id`, `is_active` |
| `vehicle_tokens` | Vehicle API tokens (encrypted) | `vehicle_account_id`, `access_token`, `refresh_token`, `expires_at` |
| `virtual_keys` | Tesla Fleet API virtual keys | `user_id`, `tesla_vehicle_id`, `vin`, `status`, `provisioning_token` |

### Chargers & Merchants (While You Charge)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `chargers` | EV charging stations (seeded from NREL/Overpass) | `id`, `external_id`, `name`, `network_name`, `lat`, `lng`, `connector_types` (JSON), `power_kw`, `is_public` |
| `merchants` | Businesses near chargers (enriched from Google Places) | `id`, `place_id`, `name`, `category`, `lat`, `lng`, `rating`, `photo_urls` (JSON), `ordering_url`, `is_corporate`, `nearest_charger_id`, `nearest_charger_distance_m` |
| `charger_merchants` | Charger ↔ merchant spatial associations | `charger_id`, `merchant_id`, `distance_m`, `walk_duration_s`, `is_primary`, `exclusive_title` |
| `merchant_perks` | Time-windowed merchant offers | `merchant_id`, `title`, `nova_reward`, `window_start`, `window_end`, `is_active` |
| `charger_clusters` | Named charger groupings | `name`, `charger_id`, `charger_lat`, `charger_lng`, `merchant_radius_m` |
| `favorite_merchants` | Driver saved merchants | `user_id`, `merchant_id` |
| `amenity_votes` | Driver votes on amenities (wifi/bathroom) | `merchant_id`, `user_id`, `amenity`, `vote_type` |
| `merchant_cache` | Google Places response cache | `place_id`, `merchant_data` (JSON), `cached_at`, `expires_at` |

### Domain / Charge Party MVP

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `zones` | Geographic zones (e.g., "domain_austin") | `slug` (PK), `name`, `center_lat`, `center_lng`, `radius_m` |
| `energy_events` | Charge party events with time windows | `slug`, `zone_slug`, `starts_at`, `ends_at`, `status` |
| `domain_merchants` | Merchant records with owner + Nova balance | `name`, `google_place_id`, `lat`, `lng`, `owner_user_id`, `nova_balance`, `square_merchant_id`, `perk_label`, `qr_token` |
| `nova_transactions` | Nova currency ledger (earn/spend/topup) | `type`, `driver_user_id`, `merchant_id`, `amount`, `campaign_id`, `idempotency_key` |
| `domain_charging_sessions` | Verified charging sessions | `driver_user_id`, `charger_provider`, `start_time`, `end_time`, `kwh_estimate`, `verified` |
| `stripe_payments` | Stripe Checkout for Nova purchases | `stripe_session_id`, `merchant_id`, `amount_usd`, `nova_issued`, `status` |
| `merchant_redemptions` | Driver redemptions at merchants | `merchant_id`, `driver_user_id`, `nova_spent_cents`, `square_order_id`, `idempotency_key` |
| `merchant_rewards` | Predefined rewards (e.g., "300 Nova = Free Coffee") | `merchant_id`, `nova_amount`, `title`, `is_active` |
| `merchant_fee_ledger` | Platform fee tracking per merchant | `merchant_id`, `period_start`, `nova_redeemed_cents`, `fee_cents`, `status` |

### Driver Wallet & Payouts (Stripe Express)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `driver_wallets` | Driver wallet with Nova + Stripe Express | `user_id`, `balance_cents`, `stripe_account_id`, `stripe_onboarding_complete` — **CHECK constraint: `balance_cents >= 0`** |
| `wallet_ledger` | All wallet transactions | `wallet_id`, `amount_cents`, `balance_after_cents`, `transaction_type`, `reference_type` |
| `payouts` | Stripe Express payouts | `driver_id`, `amount_cents`, `stripe_transfer_id`, `status`, `idempotency_key` |

### Exclusive Sessions & Intent

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `exclusive_sessions` | Driver ↔ merchant exclusive activations | `driver_id`, `merchant_id`, `charger_id`, `status`, `activated_at`, `expires_at`, `completed_at`, `idempotency_key` |
| `intent_sessions` | Charging intent captures (location signals) | `user_id`, `lat`, `lng`, `charger_id`, `charger_distance_m`, `confidence_tier` |
| `perk_unlocks` | Perk unlock records | `user_id`, `perk_id`, `merchant_id`, `dwell_time_seconds` |

### EV Arrival Sessions

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `arrival_sessions` | Full EV arrival lifecycle | `driver_id`, `merchant_id`, `charger_id`, `arrival_type`, `fulfillment_type`, `order_number`, `order_total_cents`, `vehicle_color`, `vehicle_model`, `status`, `arrival_code` |
| `queued_orders` | Merchant order queue | `arrival_session_id`, `merchant_id`, `status`, `ordering_url`, `order_number` |
| `verified_visits` | Verified charging visits (used in merchant preview) | `merchant_id`, `driver_id`, `verification_code`, `verified_at` |
| `merchant_notification_config` | SMS/email notification preferences per merchant | `merchant_id`, `notify_sms`, `sms_phone`, `email_address` |

### Campaign & Incentive System (Sponsor)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `campaigns` | Sponsor campaigns with budgets and targeting rules | `sponsor_name`, `budget_cents`, `spent_cents`, `cost_per_session_cents`, `status`, `rule_charger_ids` (JSON), `rule_geo_center_lat/lng`, `rule_time_start/end`, `rule_min_duration_minutes` |
| `session_events` | Verified charging sessions for incentive evaluation | `driver_user_id`, `charger_id`, `session_start`, `session_end`, `kwh_delivered`, `verified`, `quality_score` |
| `incentive_grants` | Campaign rewards granted to drivers | `session_event_id`, `campaign_id`, `driver_user_id`, `amount_cents`, `status` |

### Merchant Account & Onboarding

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `merchant_accounts` | Merchant owner accounts | `owner_user_id` |
| `merchant_location_claims` | Google Business Profile claims | `merchant_account_id`, `place_id`, `status` |
| `merchant_placement_rules` | Boost/cap/perk config per location | `place_id`, `daily_cap_cents`, `boost_weight`, `perks_enabled` |
| `merchant_payment_methods` | Stripe card on file | `merchant_account_id`, `stripe_customer_id`, `stripe_payment_method_id` |
| `claim_sessions` | Merchant claim flow state | `merchant_id`, `email`, `phone`, `phone_verified`, `email_verified`, `magic_link_token` |
| `merchant_pos_credentials` | Toast/Square POS tokens (encrypted) | `merchant_id`, `pos_type`, `access_token_encrypted` |

### Misc / Supporting

| Table | Purpose |
|-------|---------|
| `feature_flags` | Feature flag system (`key`, `enabled`, `env`) |
| `credit_ledger` | Generic credit tracking |
| `follows` / `reward_events` / `community_periods` | Social/community features |
| `challenges` / `participations` | Group charging challenges |
| `hubspot_outbox` | CRM event queue |
| `billing_events` | Arrival billing events |

---

### Entity Relationship Summary

```
Users ──┬── tesla_connections ── ev_verification_codes
        ├── driver_wallets ──┬── wallet_ledger
        │                    └── payouts
        ├── exclusive_sessions ── merchants ── charger_merchants ── chargers
        ├── intent_sessions ── perk_unlocks
        ├── arrival_sessions ── queued_orders
        ├── session_events ── incentive_grants ── campaigns
        └── nova_transactions ── domain_merchants ── merchant_redemptions

Campaigns (sponsors) ── incentive_grants ── session_events (drivers)
                                         └── nova_transactions (payouts)

Merchants ──┬── charger_merchants ── chargers
            ├── merchant_perks
            ├── merchant_notification_config
            ├── arrival_sessions
            ├── verified_visits
            └── exclusive_sessions
```

---

## Part 2: Building the Paid Merchant Dashboard

### What Exists Today (Free Tier)

The merchant portal (`apps/merchant/`) currently offers:

| Feature | Status | Data Source |
|---------|--------|-------------|
| Business search + claim flow | Live | Google Places API + `claim_sessions` |
| Overview dashboard (activations, visits, conversion rate) | Live | `exclusive_sessions`, `verified_visits` |
| Create/manage exclusive offers | Live | `exclusive_sessions`, `charger_merchants` |
| View verified visits (table with filters) | Live | `verified_visits` |
| EV arrival alerts + code redemption | Live | `arrival_sessions`, `merchant_notification_config` |
| SMS/email notification config | Live | `merchant_notification_config` |
| Merchant preview page (HMAC-signed links) | Live | `merchants`, `verified_visits` |
| **Billing / Payments** | **Stub — "Coming Soon"** | — |
| **Settings** | **Stub** | — |
| **Primary Experience (charger positioning)** | **Stub** | — |

### Merchant Auth Flow

Merchants authenticate via a **claim flow**:
1. Search for business on `/find` (Google Places)
2. Preview page with HMAC-signed URL (7-day TTL)
3. Claim: email + phone → OTP verification (Twilio) → magic link email (15 min TTL)
4. Creates `User` with `role_flags="merchant_admin"` and sets `DomainMerchant.owner_user_id`
5. JWT stored in `localStorage`, used as `Authorization: Bearer` on all API calls

Alternative: Google Business Profile OAuth for national expansion.

### Backend APIs Available

| Router | Prefix | Purpose |
|--------|--------|---------|
| `merchant_funnel.py` | `/v1/merchant/funnel/` | Public search, resolve, preview, text link SMS |
| `merchant_claim.py` | `/v1/merchant/claim/` | Claim flow (start → verify phone → magic link → verify token) |
| `merchant_analytics.py` | `/v1/merchant/` | Summary stats, insights |
| `merchant_arrivals.py` | `/v1/merchant/arrivals/` | Arrival sessions + notification config CRUD |
| `merchant_balance.py` | `/v1/merchants/{id}/balance` | Balance ledger (get, credit, debit) |
| `merchant_reports.py` | `/v1/merchants/{id}/report` | Period-based reports (week/30d) |
| `merchant_api.py` | `/v1/merchant/` | API key auth + analytics summary |
| `merchant_onboarding.py` | `/v1/merchant/` | GBP OAuth + placement rules |

---

### Paid Dashboard: What to Build

#### Tier Structure

| | Free | Pro ($49/mo) | Premium ($149/mo) |
|-|------|-------------|-------------------|
| Overview dashboard | Yes | Yes | Yes |
| Exclusive management | 1 active | Unlimited | Unlimited |
| Verified visits table | Last 7 days | Full history | Full history + export |
| EV arrival alerts | SMS only | SMS + email | SMS + email + POS |
| Analytics | Basic counts | Charts + trends | Advanced + benchmarks |
| Revenue tracking | No | Yes | Yes |
| ROI calculator | No | Yes | Yes |
| Custom reports | No | No | Yes (CSV/PDF export) |
| Multi-location | No | No | Yes |
| API access | No | No | Yes |
| Priority support | No | No | Yes |

#### New Database Tables Needed

```sql
-- Merchant subscriptions (Stripe Billing)
CREATE TABLE merchant_subscriptions (
    id UUID PRIMARY KEY,
    merchant_id UUID REFERENCES domain_merchants(id),
    owner_user_id INTEGER REFERENCES users(id),
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    plan_tier VARCHAR(20) NOT NULL DEFAULT 'free',  -- free, pro, premium
    status VARCHAR(20) NOT NULL DEFAULT 'active',   -- active, past_due, canceled, trialing
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    trial_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Merchant analytics snapshots (materialized daily)
CREATE TABLE merchant_analytics_daily (
    id UUID PRIMARY KEY,
    merchant_id UUID REFERENCES domain_merchants(id),
    date DATE NOT NULL,
    total_activations INTEGER DEFAULT 0,
    total_completions INTEGER DEFAULT 0,
    total_arrivals INTEGER DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    total_revenue_cents INTEGER DEFAULT 0,   -- from arrival_sessions.order_total_cents
    total_nova_redeemed INTEGER DEFAULT 0,
    unique_drivers INTEGER DEFAULT 0,
    repeat_drivers INTEGER DEFAULT 0,
    avg_dwell_minutes FLOAT,
    peak_hour INTEGER,                        -- 0-23
    conversion_rate FLOAT,                    -- completions / activations
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(merchant_id, date)
);

-- Merchant invoices (for audit trail)
CREATE TABLE merchant_invoices (
    id UUID PRIMARY KEY,
    merchant_id UUID REFERENCES domain_merchants(id),
    stripe_invoice_id VARCHAR(255) UNIQUE,
    amount_cents INTEGER NOT NULL,
    status VARCHAR(20),  -- draft, open, paid, void
    period_start TIMESTAMP,
    period_end TIMESTAMP,
    pdf_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### New Backend Endpoints

```
# Subscription management
POST   /v1/merchant/subscription/checkout    → Create Stripe Checkout for plan upgrade
POST   /v1/merchant/subscription/portal      → Create Stripe Billing Portal session
GET    /v1/merchant/subscription              → Current plan details
POST   /v1/merchant/subscription/webhook      → Stripe Billing webhooks

# Enhanced analytics (Pro+)
GET    /v1/merchant/{id}/analytics/daily      → Daily metrics for date range
GET    /v1/merchant/{id}/analytics/trends     → Week-over-week / month-over-month trends
GET    /v1/merchant/{id}/analytics/drivers    → Driver cohort analysis (new vs repeat)
GET    /v1/merchant/{id}/analytics/roi        → ROI calculation (rewards cost vs revenue)
GET    /v1/merchant/{id}/analytics/peak-hours → Hourly heatmap data

# Reports (Premium)
GET    /v1/merchant/{id}/reports/export       → CSV/PDF export
GET    /v1/merchant/{id}/reports/custom       → Custom date range + metric selection

# Multi-location (Premium)
GET    /v1/merchant/locations                 → All claimed locations
GET    /v1/merchant/locations/compare         → Cross-location comparison
```

#### New Frontend Pages

| Page | Route | Tier | Description |
|------|-------|------|-------------|
| Analytics | `/analytics` | Pro+ | Charts: daily activations, revenue trend, driver cohorts, peak hours heatmap |
| Revenue | `/revenue` | Pro+ | Revenue tracking: order totals, Nova redeemed value, net revenue, ROI calculator |
| Reports | `/reports` | Premium | Custom date range reports with CSV/PDF export |
| Locations | `/locations` | Premium | Multi-location management and comparison |
| Billing | `/billing` | All | Subscription management, invoices, payment method (Stripe Billing Portal) |
| Settings | `/settings` | All | Notification prefs, business hours, team members |

#### Implementation Approach

**Phase 1: Subscription Infrastructure (1-2 days)**
1. Create `merchant_subscriptions` table + Alembic migration
2. Build Stripe Billing integration:
   - Products/prices in Stripe Dashboard (Pro $49/mo, Premium $149/mo)
   - Checkout session creation endpoint
   - Billing Portal session endpoint
   - Webhook handler for `customer.subscription.created/updated/deleted`
3. Add `plan_tier` check middleware/dependency for gating features
4. Build `/billing` page with plan selection + Stripe Checkout redirect

**Phase 2: Analytics Engine (2-3 days)**
1. Create `merchant_analytics_daily` table + migration
2. Build daily aggregation job (cron or scheduled task):
   - Query `exclusive_sessions` + `arrival_sessions` + `verified_visits` per merchant per day
   - Insert/update `merchant_analytics_daily` rows
3. Build analytics API endpoints with date range filtering
4. Build `/analytics` page with Recharts charts:
   - Line chart: daily activations + completions over time
   - Bar chart: revenue by day/week
   - Pie chart: driver breakdown (new vs repeat)
   - Heatmap: activity by hour of day

**Phase 3: Revenue & ROI (1-2 days)**
1. Aggregate `arrival_sessions.order_total_cents` per merchant
2. Calculate ROI: `(total_revenue - rewards_cost) / rewards_cost * 100`
3. Build `/revenue` page with KPI cards + trend charts
4. Add export endpoint for CSV download

**Phase 4: Polish & Launch (1 day)**
1. Feature gate all Pro/Premium pages with subscription check
2. Add upgrade prompts on gated pages for free tier
3. Trial period support (14-day free trial of Pro)
4. Email notifications for trial expiry, payment failures

#### Data Already Available for Analytics

All the data needed for a rich merchant dashboard **already exists** in the database:

| Metric | Source Table | Column/Query |
|--------|------------|--------------|
| Activations | `exclusive_sessions` | `COUNT WHERE merchant_id = ? AND status = 'activated'` |
| Completions | `exclusive_sessions` | `COUNT WHERE status = 'completed'` |
| Conversion rate | `exclusive_sessions` | `completed / activated * 100` |
| EV arrivals | `arrival_sessions` | `COUNT WHERE merchant_id = ?` |
| Order revenue | `arrival_sessions` | `SUM(order_total_cents)` |
| Verified visits | `verified_visits` | `COUNT WHERE merchant_id = ?` |
| Unique drivers | `exclusive_sessions` | `COUNT(DISTINCT driver_id)` |
| Repeat drivers | `exclusive_sessions` | `COUNT(driver_id) HAVING COUNT > 1` |
| Nova redeemed | `nova_transactions` | `SUM(amount) WHERE merchant_id = ? AND type = 'redemption'` |
| Peak hours | `exclusive_sessions` | `EXTRACT(HOUR FROM activated_at) GROUP BY hour` |
| Dwell time | `exclusive_sessions` | `AVG(completed_at - activated_at)` |
| Rewards cost | `incentive_grants` | `SUM(amount_cents) WHERE campaign merchant matches` |

No new data collection is needed — just aggregation queries and a materialized daily snapshot for performance.
