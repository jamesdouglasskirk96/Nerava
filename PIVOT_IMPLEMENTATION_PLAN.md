# Nerava Pivot Implementation Plan: Programmable Incentive Layer for EV Charging

**Date:** 2026-02-22
**Author:** Architecture Review (Claude Code)
**Purpose:** Detailed implementation plan for pivoting Nerava from spend-verification/merchant-centric rewards to a programmable incentive layer for EV charging behavior. Written for cross-AI review (Gemini, Claude, etc.) with full codebase context.

---

## Table of Contents

1. [Strategic Context](#1-strategic-context)
2. [Current State: Complete Codebase Architecture](#2-current-state-complete-codebase-architecture)
3. [Goal State: Programmable Incentive Layer](#3-goal-state-programmable-incentive-layer)
4. [Gap Analysis: Current vs. Goal](#4-gap-analysis-current-vs-goal)
5. [Implementation Phases](#5-implementation-phases)
6. [Data Model Changes](#6-data-model-changes)
7. [API Surface Changes](#7-api-surface-changes)
8. [Frontend Changes](#8-frontend-changes)
9. [Migration Strategy](#9-migration-strategy)
10. [Risk Assessment](#10-risk-assessment)
11. [Verification Plan](#11-verification-plan)

---

## 1. Strategic Context

### The Pivot

Nerava is moving from:
- **"Cashback on merchant spend near EV chargers"** (Upside model — transaction-dependent, card-network-reliant, thin margins)

To:
- **"Programmable incentives for EV charging behavior"** (Infrastructure model — session-dependent, sponsor-funded, behavior-steering)

### Why This Matters

| Dimension | Current (Spend Verification) | Target (Session Behavior) |
|-----------|------------------------------|---------------------------|
| Core asset | Merchant confirmation of visit | Verified charging session (start, stop, duration, location) |
| Who pays | Merchants fund rewards | Sponsors, charging networks, cities, merchants (layered) |
| Friction | Card linking, POS integration, merchant confirmation | Connect Tesla (done), charge car (automatic) |
| Scalability | Each merchant requires onboarding + POS setup | Each charger is automatic via Tesla/OCPP API |
| Valuation comp | Upside (cashback app, compressed multiples) | Infrastructure layer (platform multiples) |
| Engineering burden | Fidel integration, card brand detection, refund clawbacks | Tesla API (done), add 1 charging network |

### The Monetization Model

| Customer Type | What They Buy | Price Point | Verification Needed |
|---|---|---|---|
| Charging Networks | Utilization lift at underperforming sites | $1-3/session or monthly campaign | Charging session only |
| Sponsors (Energy cos, OEMs, Cities) | Behavior steering (off-peak, new sites, corridors) | Campaign budget ($5K-50K) | Charging session only |
| Merchants (future layer) | Verified visits during charging sessions | $1-3/visit prepaid credits | Presence during session |
| Merchants (premium upsell) | Spend-verified attribution | Higher $/visit | Card-linked (Fidel) — kept as optional tier |

---

## 2. Current State: Complete Codebase Architecture

### 2.1 Database Models (What Exists Today)

#### Core Session & Reward Models

**`arrival_sessions` table** (`backend/app/models/arrival_session.py`)
- 50+ columns tracking the full EV arrival lifecycle
- State machine: `pending_order → awaiting_arrival → arrived → merchant_notified → completed`
- Two flow types: `legacy` (geofence) and `arrival_code` (NVR-XXXX codes) and `phone_first`
- Billing fields: `platform_fee_bps` (default 2000 = 20%), `billable_amount_cents`, `billing_status`
- Vehicle snapshot: `vehicle_color`, `vehicle_model`
- Geofence data: `arrival_lat/lng`, `arrival_accuracy_m`, `arrival_distance_m`
- QR pairing: `pairing_token`, `paired_at`, `paired_phone`
- Order binding: `order_number`, `order_total_cents`, `order_source` (manual/toast/square)
- Kitchen queue: `queued_order_status` (queued → released → preparing → ready → completed)
- Code fields: `arrival_code` (NVR-XXXX), `merchant_reply_code` (4-digit)
- SMS tracking: `checkout_url_sent`, `sms_sent_at`, `sms_message_sid`
- **This model is heavily merchant-centric. Almost every field assumes merchant-driver coordination.**

**`domain_charging_sessions` table** (`backend/app/models/domain.py`)
- Simpler model: `id`, `driver_user_id`, `charger_provider`, `start_time`, `end_time`, `kwh_estimate`
- Verification: `verified` (bool), `verification_source` (tesla_api/manual_code/admin/demo)
- Event scoped: `event_id` FK to `energy_events`
- **This is closer to what we need but is scoped to "charge party events" only, not general sessions**

**`exclusive_sessions` table** (`backend/app/models/exclusive_session.py`)
- Tracks driver exclusive activation at merchant
- Fields: `driver_id`, `merchant_id`, `charger_id`, `status` (ACTIVE/COMPLETED/EXPIRED/CANCELED)
- Location capture: `activation_lat/lng`, `activation_accuracy_m`, `activation_distance_to_charger_m`
- V3 intent: `intent` (eat/work/quick-stop), `intent_metadata` (JSONB)
- Idempotency: `idempotency_key`
- **Entirely merchant-focused. "Exclusive" = merchant offer, not a charging incentive.**

#### Nova Token System

**`nova_transactions` table** (`backend/app/models/domain.py`)
- Immutable ledger: `type` (driver_earn/driver_redeem/merchant_topup/admin_grant), `amount`, `driver_user_id`, `merchant_id`
- References: `session_id`, `event_id`, `stripe_payment_id`
- Idempotency: `idempotency_key` + `payload_hash` (SHA256 truncated to 16 chars)
- Metadata: `transaction_meta` (JSON)
- **Good foundation. The ledger pattern is reusable. Needs new `type` values and a `campaign_id` reference.**

**`driver_wallets` table** (`backend/app/models/domain.py`)
- Per-driver: `user_id` (PK), `nova_balance`, `energy_reputation_score`
- Apple Wallet: `apple_authentication_token`, `wallet_pass_token`
- Google Wallet: via `google_wallet_links` table
- Balance constraint: `nova_balance >= 0` enforced at DB level (PostgreSQL CHECK, SQLite trigger)
- **Reusable as-is. Wallet is currency-agnostic.**

#### Merchant Models

**`domain_merchants` table** (`backend/app/models/domain.py`)
- Full merchant profile: name, address, lat/lng, status, zone_slug
- Nova: `nova_balance` (merchant's token balance)
- Square POS: `square_merchant_id`, `square_location_id`, `square_access_token`
- Perk config: `avg_order_value_cents`, `recommended_perk_cents`, `custom_perk_cents`, `perk_label`
- QR checkout: `qr_token`, `qr_created_at`, `qr_last_used_at`
- Stripe: FK to `stripe_payments`
- **Heavily POS-integrated. In the new model, merchants become one type of "funder" rather than the central entity.**

**`merchants` table** (`backend/app/models/while_you_charge.py`)
- Separate from `domain_merchants` — "While You Charge" discovery layer
- Google Places enrichment: `place_id`, `rating`, `photo_urls`, `hours_json`, `business_status`
- Ordering integration: `ordering_url`, `ordering_app_scheme`, `ordering_instructions`
- Short code: `short_code` (e.g., "ASADAS")
- Proximity cache: `nearest_charger_id`, `nearest_charger_distance_m`
- **Discovery metadata. Useful for the merchant layer but not for core session incentives.**

**`charger_merchants` table** (junction, `while_you_charge.py`)
- Links chargers to merchants with: `distance_m`, `walk_duration_s`, `walk_distance_m`
- Primary merchant flags: `is_primary`, `override_mode`, `suppress_others`, `exclusive_title/description`

**`merchant_perks` table** (`while_you_charge.py`)
- Active rewards: `title`, `description`, `nova_reward`, `window_start/end`, `is_active`, `expires_at`

**`merchant_balance` / `merchant_balance_ledger` tables** (`while_you_charge.py`)
- Merchant discount budget tracking with immutable ledger

**`merchant_offer_codes` table** (`while_you_charge.py`)
- Unique redemption codes: `code`, `amount_cents`, `is_redeemed`, `expires_at`

**`merchant_fee_ledger` table** (`domain.py`)
- Monthly fee tracking: `nova_redeemed_cents`, `fee_cents` (15%), `status` (accruing/invoiced/paid)

#### Tesla & EV Models

**`tesla_connections` table** (`backend/app/models/tesla_connection.py`)
- OAuth: `access_token`, `refresh_token`, `token_expires_at`
- Vehicle: `vehicle_id`, `vin`, `vehicle_name`, `vehicle_model`
- Account: `tesla_user_id`, `is_active`
- **Core infrastructure for the pivot. This is the charging session source.**

**`ev_verification_codes` table** (`tesla_connection.py`)
- Temporary codes: `code` (EV-XXXX), `user_id`, `tesla_connection_id`
- Context: `charger_id`, `merchant_place_id`, `merchant_name`
- Charging snapshot: `charging_verified`, `battery_level`, `charge_rate_kw`
- Status: `active → redeemed → expired`, 2-hour TTL

#### User & Auth Models

**`users` table** (`backend/app/models/user.py`)
- Identity: `id`, `public_id` (UUID for JWT), `email`, `phone`
- Auth: `auth_provider` (local/google/apple/phone/tesla), `provider_sub`, `password_hash`
- Profile: `display_name`, `role_flags` (driver/merchant_admin/admin)
- Vehicle cache: `vehicle_color`, `vehicle_model`

**`user_preferences` table** (`user.py`)
- `food_tags`, `max_detour_minutes`, `preferred_networks`, `typical_start/end`, `home_zip`

#### Infrastructure Models

**`chargers` table** (`while_you_charge.py`)
- Inventory: `id`, `name`, `network_name`, `lat/lng`, `connector_types`, `power_kw`, `status`
- External: `external_id` (NREL/OCM ID)

**`zones` table** (`domain.py`)
- Geographic zones: `slug`, `name`, `center_lat/lng`, `radius_m`

**`energy_events` table** (`domain.py`)
- Time-bound campaigns within zones: `slug`, `zone_slug`, `starts_at`, `ends_at`, `status`
- **This is the closest existing model to "campaigns" but is zone+time scoped only.**

#### Card-Linked Offer Models (CLO / Fidel)

**`cards` table** (via `spend_verification_service.py`, not a separate model file)
- `id`, `driver_id`, `fidel_card_id`, `last4`, `brand`, `fingerprint`, `is_active`

**`clo_transactions` table** (via `spend_verification_service.py`)
- `id`, `driver_id`, `card_id`, `merchant_id`, `offer_id`, `amount_cents`, `reward_cents`
- Status: `eligible → credited → rejected → duplicate → refunded`
- `external_id` (Fidel transaction ID), `charging_session_id`

**`merchant_offers` table** (via `spend_verification_service.py`)
- CLO offers: `merchant_id`, `min_spend_cents`, `reward_cents`, `reward_percent`, `max_reward_cents`

### 2.2 Backend Services (Business Logic Layer)

#### `CheckinService` (`backend/app/services/checkin_service.py`)
- **20+ methods** managing EV arrival code lifecycle
- Core flow: `start_checkin() → verify_checkin() → generate_code() → redeem_code() → merchant_confirm()`
- `merchant_confirm()` is the reward trigger — creates `BillingEvent`, auto-grants Nova
- Phone-first flow: `phone_start_checkin() → send_session_sms() → activate_session()`
- Constants: `CHARGER_RADIUS_M = 250`, `CODE_TTL_MINUTES = 30`, `SESSION_TTL_MINUTES = 90`
- Platform fee: `(total * fee_bps) / 10000`, capped $0.50-$5.00
- Rate limiting: 3 sessions/phone/day, 10 requests/IP/hour
- **Entirely merchant-confirmation driven. The merchant is the gatekeeper for rewards.**

#### `NovaService` (`backend/app/services/nova_service.py`)
- `grant_to_driver()` — Awards Nova with idempotency + payload hash
- `redeem_from_driver()` — Atomic debit driver / credit merchant (SELECT FOR UPDATE + atomic SQL)
- `grant_to_merchant()` — From Stripe purchase
- `get_driver_wallet()` — Gets or creates wallet
- Reputation: `energy_reputation_score += amount` on driver_earn
- Events: Emits `NovaEarnedEvent`, `NovaRedeemedEvent`
- **Solid foundation. Needs: new grant types (campaign_grant), campaign_id reference, auto_commit parameter (already added in Phase 5 hardening).**

#### `SpendVerificationService` (`backend/app/services/spend_verification_service.py`)
- Card linking: `link_card()`, `unlink_card()`, `get_linked_cards()`
- Transaction verification: `verify_transaction()` — checks min spend ($5), time window (3hr), offer validity
- Webhook processing: `process_webhook()` — Fidel events (auth/clearing/refund)
- Refund clawback: deducts reward from wallet on Fidel refund event
- Enrollment: `create_card_enrollment_session()` (Fidel Select SDK)
- **This entire service becomes a premium upsell tier, not core infrastructure.**

#### `TeslaOAuthService` (`backend/app/services/tesla_oauth.py`)
- Auth: `get_authorization_url()`, `exchange_code_for_tokens()`, `refresh_access_token()`
- Vehicles: `get_vehicles()`, `get_vehicle_data()`, `wake_vehicle()`
- Charging verification: `verify_charging()`, `verify_charging_all_vehicles()`
- Charging states: `CHARGING_STATES = {"Charging", "Starting"}`
- Retry: 3 attempts, 5s delay for 408 timeout or None charging_state
- Fleet API: `https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/`
- **Core infrastructure for the pivot. This is the session event source. Needs: continuous session tracking (not just point-in-time verification).**

#### `TeslaAuthService` (`backend/app/services/tesla_auth_service.py`)
- `verify_tesla_id_token()` — RS256 JWKS verification
- `fetch_tesla_user_profile()` — Userinfo endpoint for email/name
- **Recently created. Supports Tesla-only login.**

#### `StripeService` (`backend/app/services/stripe_service.py`)
- Checkout: `create_checkout_session()` — Nova packages ($100→1K, $450→5K, $800→10K)
- Webhook: `handle_webhook()` → `_handle_checkout_completed()` → `grant_to_merchant()`
- Reconciliation: `reconcile_payment()` — checks Stripe transfer status, handles reversals
- **Currently merchant-focused (merchants buy Nova). In new model: sponsors buy campaign credits.**

### 2.3 Backend Routers (API Surface)

| Router | File | Prefix | Endpoints | Purpose |
|--------|------|--------|-----------|---------|
| `checkin` | `routers/checkin.py` | `/v1/checkin` | 13 endpoints | EV arrival code lifecycle |
| `tesla_auth` | `routers/tesla_auth.py` | `/v1/auth/tesla` | 10 endpoints | Tesla OAuth + charging verification |
| `driver_wallet` | `routers/driver_wallet.py` | `/v1/wallet` | 7 endpoints | Balance, withdraw, Stripe Express |
| `clo` | `routers/clo.py` | `/v1/clo` | 8 endpoints | Card-linked offers (Fidel) |
| `arrival` | `routers/arrival.py` | `/v1/arrival` | 10 endpoints | EV arrival session management |
| `merchant_funnel` | `routers/merchant_funnel.py` | `/v1/merchant/funnel` | 4 endpoints | Merchant onboarding search/claim |
| `merchant_arrivals` | `routers/merchant_arrivals.py` | `/v1/merchants` | 3 endpoints | Merchant arrival notifications |
| `notifications` | `routers/notifications.py` | `/v1/notifications` | 2 endpoints | User notification prefs |
| `admin_domain` | `routers/admin_domain.py` | `/v1/admin` | 30+ endpoints | Full admin CRUD |
| `account` | `routers/account.py` | `/v1` | Account management | User profile |
| `consent` | `routers/consent.py` | `/v1` | Privacy consent | GDPR/consent |
| `charge_context` | `routers/charge_context.py` | `/v1` | Charger context | Charger discovery |
| `ev_context` | `routers/ev_context.py` | `/v1` | EV browser context | In-car detection |

**Total: ~100+ API endpoints, heavily weighted toward merchant-driver coordination.**

### 2.4 Frontend Apps

#### Driver App (`apps/driver/`)
- **State machine:** `PRE_CHARGING → CHARGING_ACTIVE → EXCLUSIVE_ACTIVE`
- **Core hook:** `useIntentCapture` — polls `/v1/intent/capture` with location, returns chargers + merchants
- **Reward trigger:** User activates exclusive → merchant confirms → Nova granted
- **Tesla integration:** EV-XXXX codes displayed when charging detected
- **Key screens:** DriverHome (carousel of chargers/merchants), ExclusiveActiveView (locked offer), WalletModal
- **Auth:** Tesla OAuth (primary), Apple/Google Sign-In, Phone OTP (all supported)
- **Native bridge:** iOS WKWebView wrapper with session state machine (IDLE → NEAR_CHARGER → ANCHORED → SESSION_ACTIVE → IN_TRANSIT → AT_MERCHANT → SESSION_ENDED)

#### Merchant Portal (`apps/merchant/`)
- **Screens:** Overview, Exclusives, Create Exclusive, Visits, EV Arrivals, Primary Experience, Billing (coming soon), Settings (coming soon), Pickup Packages (coming soon)
- **Core flow:** Create exclusive offer → driver activates → staff redeems code → visit logged
- **Auth:** Google OAuth + Phone OTP + Email magic link for claim
- **Key API calls:** `/v1/merchants/{id}/exclusives`, `/v1/merchants/{id}/visits`, `/v1/merchants/{id}/arrivals`

#### Admin Dashboard (`apps/admin/`)
- **Screens:** Dashboard, Merchants, Exclusives, Active Sessions, Overrides, Charging Locations (coming soon), Logs, Deployments
- **Critical controls:** Force-close sessions, emergency pause (system-wide), ban/verify merchants
- **Auth:** Email/password
- **Key API calls:** `/v1/admin/overview`, `/v1/admin/merchants/*`, `/v1/admin/exclusives/*`, `/v1/admin/sessions/*`

### 2.5 External Integrations

| Integration | Purpose | Status | Cost Driver |
|---|---|---|---|
| Tesla Fleet API | Charging verification, vehicle data | Active, core | API calls per verification |
| Stripe | Merchant Nova purchases, driver payouts | Active | Transaction fees |
| Twilio | Phone OTP, SMS notifications | Active | Per-SMS cost |
| Fidel | Card-linked offers, spend verification | Mock mode only | Per-transaction fee |
| Google Places | Merchant enrichment | Active | API calls per lookup |
| PostHog | Analytics | Active | Event volume |
| Sentry | Error tracking | Active | Event volume |

---

## 3. Goal State: Programmable Incentive Layer

### 3.1 Core Concept

The platform becomes a **rules engine** where **funders** define **campaigns** with **conditions**, and the system automatically matches **charging sessions** to campaigns and distributes **incentives** to drivers.

```
FUNDER creates CAMPAIGN with RULES
     ↓
DRIVER charges EV → SYSTEM creates SESSION_EVENT
     ↓
RULES ENGINE evaluates SESSION_EVENT against active CAMPAIGNS
     ↓
Matching campaigns → INCENTIVE_GRANT created → NOVA credited to driver
     ↓
CAMPAIGN budget decremented → auto-pauses when exhausted
```

### 3.2 New Data Model

#### `funders` table (NEW)
Unified entity for anyone who funds incentives:

```
funders
├── id (UUID, PK)
├── type (enum: 'charging_network' | 'sponsor' | 'merchant' | 'city' | 'oem' | 'internal')
├── name (String)
├── contact_email (String)
├── contact_phone (String, nullable)
├── billing_email (String, nullable)
├── logo_url (String, nullable)
├── status (enum: 'active' | 'paused' | 'suspended')
├── stripe_customer_id (String, nullable)  -- for billing
├── total_funded_cents (Integer, default=0)  -- lifetime funding
├── total_spent_cents (Integer, default=0)   -- lifetime spend
├── created_at (DateTime)
├── updated_at (DateTime)
└── metadata (JSON, nullable)  -- flexible per-type data
```

**Why separate from `domain_merchants`?** Funders include non-merchant entities (ChargePoint, Tesla, City of Austin DOT, Shell Recharge). The merchant layer wraps funders for backward compatibility.

#### `campaigns` table (NEW)
A time-bound, budget-capped incentive program:

```
campaigns
├── id (UUID, PK)
├── funder_id (UUID, FK → funders.id)
├── name (String)
├── description (Text, nullable)
├── campaign_type (enum: 'utilization_boost' | 'off_peak' | 'new_driver' | 'repeat_visit' | 'merchant_traffic' | 'corridor' | 'custom')
├── status (enum: 'draft' | 'active' | 'paused' | 'exhausted' | 'completed' | 'canceled')
├── budget_cents (Integer)         -- total budget
├── spent_cents (Integer, default=0) -- consumed so far
├── cost_per_session_cents (Integer) -- incentive amount per qualifying session
├── max_sessions (Integer, nullable) -- optional absolute cap
├── sessions_granted (Integer, default=0) -- count of grants
├── start_date (DateTime)
├── end_date (DateTime, nullable)   -- null = ongoing until budget exhausted
├── auto_renew (Boolean, default=False)
├── created_at (DateTime)
├── updated_at (DateTime)
├── created_by_user_id (Integer, FK → users.id, nullable)
└── metadata (JSON, nullable)
```

#### `campaign_rules` table (NEW)
Conditions that must be met for a session to qualify:

```
campaign_rules
├── id (UUID, PK)
├── campaign_id (UUID, FK → campaigns.id, ON DELETE CASCADE)
├── rule_type (enum: see below)
├── rule_operator (enum: 'in' | 'not_in' | 'eq' | 'gt' | 'lt' | 'gte' | 'lte' | 'between' | 'within_radius')
├── rule_value (JSON)  -- type-dependent value
├── created_at (DateTime)
└── updated_at (DateTime)
```

**Rule types:**
| rule_type | rule_operator | rule_value example | Meaning |
|---|---|---|---|
| `charger_ids` | `in` | `["ch_123", "ch_456"]` | Session must be at one of these chargers |
| `charger_network` | `in` | `["Tesla", "ChargePoint"]` | Session must be on this network |
| `zone_ids` | `in` | `["domain_austin", "round_rock"]` | Session must be in one of these zones |
| `geo_radius` | `within_radius` | `{"lat": 30.40, "lng": -97.72, "radius_m": 5000}` | Session within radius |
| `time_of_day` | `between` | `{"start": "22:00", "end": "06:00"}` | Off-peak hours only |
| `day_of_week` | `in` | `[1, 2, 3, 4, 5]` | Weekdays only |
| `min_duration_minutes` | `gte` | `15` | Minimum charging duration |
| `max_duration_minutes` | `lte` | `120` | Maximum charging duration |
| `driver_session_count` | `eq` | `1` | First session only (new driver acquisition) |
| `driver_session_count` | `gte` | `5` | Repeat driver reward |
| `driver_repeat_at_charger` | `gte` | `3` | Repeat at same charger |
| `connector_type` | `in` | `["CCS", "CHAdeMO"]` | Specific connector types |
| `min_power_kw` | `gte` | `50` | DC fast charging only |

**Rule evaluation:** All rules on a campaign are AND-ed. A session must satisfy every rule to qualify.

#### `session_events` table (NEW)
The atomic unit — a verified charging session:

```
session_events
├── id (UUID, PK)
├── driver_user_id (Integer, FK → users.id, indexed)
├── charger_id (String, FK → chargers.id, nullable, indexed)
├── charger_network (String, nullable)  -- "Tesla", "ChargePoint", etc.
├── zone_id (String, nullable, indexed)  -- geographic zone
├── connector_type (String, nullable)   -- "CCS", "Tesla", etc.
├── power_kw (Float, nullable)          -- charging power
├── session_start (DateTime, indexed)
├── session_end (DateTime, nullable)    -- null = still charging
├── duration_minutes (Integer, nullable) -- computed on session_end
├── kwh_delivered (Float, nullable)     -- energy delivered
├── source (enum: 'tesla_api' | 'chargepoint_api' | 'evgo_api' | 'ocpp' | 'manual' | 'demo')
├── source_session_id (String, nullable) -- external session ID from provider
├── verified (Boolean, default=False)
├── verification_method (String, nullable) -- 'api_polling' | 'webhook' | 'manual' | 'admin'
├── lat (Float, nullable)
├── lng (Float, nullable)
├── battery_start_pct (Integer, nullable)
├── battery_end_pct (Integer, nullable)
├── vehicle_id (String, nullable)       -- Tesla vehicle ID or similar
├── vehicle_vin (String, nullable)
├── created_at (DateTime, indexed)
├── updated_at (DateTime)
└── metadata (JSON, nullable)           -- provider-specific data
```

**Indexes:**
- `idx_session_events_driver_start` (driver_user_id, session_start)
- `idx_session_events_charger_start` (charger_id, session_start)
- `idx_session_events_zone_start` (zone_id, session_start)
- `idx_session_events_source` (source, source_session_id) UNIQUE — prevents duplicate imports

#### `incentive_grants` table (NEW)
Links a session event to a campaign grant:

```
incentive_grants
├── id (UUID, PK)
├── session_event_id (UUID, FK → session_events.id, indexed)
├── campaign_id (UUID, FK → campaigns.id, indexed)
├── driver_user_id (Integer, FK → users.id, indexed)
├── amount_cents (Integer)
├── status (enum: 'pending' | 'granted' | 'paid_out' | 'clawed_back')
├── nova_transaction_id (UUID, FK → nova_transactions.id, nullable) -- link to ledger
├── granted_at (DateTime, nullable)
├── created_at (DateTime)
└── metadata (JSON, nullable)
```

**Unique constraint:** `(session_event_id, campaign_id)` — one grant per session per campaign. A single session CAN earn from multiple campaigns if it matches multiple.

#### `utilization_metrics` table (NEW)
Aggregated metrics for the sales dashboard:

```
utilization_metrics
├── id (UUID, PK)
├── charger_id (String, FK → chargers.id, indexed)
├── zone_id (String, nullable, indexed)
├── period_type (enum: 'daily' | 'weekly' | 'monthly')
├── period_start (Date, indexed)
├── period_end (Date)
├── total_sessions (Integer, default=0)
├── unique_drivers (Integer, default=0)
├── total_duration_minutes (Integer, default=0)
├── avg_duration_minutes (Float, nullable)
├── total_kwh (Float, nullable)
├── peak_hour_sessions (Integer, default=0)   -- 6AM-10AM, 4PM-8PM
├── off_peak_sessions (Integer, default=0)    -- everything else
├── repeat_driver_sessions (Integer, default=0) -- drivers with 2+ sessions in period
├── new_driver_sessions (Integer, default=0)   -- first-time drivers
├── incentivized_sessions (Integer, default=0) -- sessions that earned incentives
├── non_incentivized_sessions (Integer, default=0) -- baseline sessions
├── campaign_ids (JSON, default=[])  -- which campaigns were active during this period
├── computed_at (DateTime)
└── metadata (JSON, nullable)
```

**Unique constraint:** `(charger_id, period_type, period_start)` — one metric row per charger per period.

### 3.3 New Services

#### `SessionEventService` (NEW)
- `create_from_tesla(db, driver_id, tesla_connection_id, charge_data, vehicle_info) → SessionEvent`
- `end_session(db, session_event_id) → SessionEvent`
- `get_active_session(db, driver_id) → Optional[SessionEvent]`
- `get_driver_sessions(db, driver_id, limit=50) → List[SessionEvent]`
- `get_charger_sessions(db, charger_id, since, until) → List[SessionEvent]`
- **Triggered by:** Tesla API polling (every 60s while charging), or webhook from other networks

#### `CampaignService` (NEW)
- `create_campaign(db, funder_id, name, type, budget_cents, cost_per_session_cents, rules, start_date, end_date) → Campaign`
- `update_campaign(db, campaign_id, **kwargs) → Campaign`
- `pause_campaign(db, campaign_id, reason) → Campaign`
- `resume_campaign(db, campaign_id) → Campaign`
- `get_active_campaigns(db) → List[Campaign]`
- `get_funder_campaigns(db, funder_id) → List[Campaign]`
- `check_budget(db, campaign_id) → {remaining_cents, remaining_sessions, pct_used}`

#### `IncentiveEngine` (NEW)
The rules engine that evaluates sessions against campaigns:

- `evaluate_session(db, session_event: SessionEvent) → List[IncentiveGrant]`
  1. Load all campaigns with status='active' and budget remaining
  2. For each campaign, evaluate all rules against the session
  3. For matching campaigns, create `IncentiveGrant` + call `NovaService.grant_to_driver()`
  4. Decrement `campaign.spent_cents` and `campaign.sessions_granted`
  5. If budget exhausted → set `campaign.status = 'exhausted'`
  6. Return list of grants created

- `evaluate_rule(rule: CampaignRule, session: SessionEvent) → bool`
  - Dispatches to rule-type-specific evaluators
  - `charger_ids`: `session.charger_id IN rule_value`
  - `time_of_day`: Parse session_start time, check if in window
  - `geo_radius`: Haversine distance from rule center to session lat/lng
  - `driver_session_count`: Count driver's previous sessions in DB
  - etc.

#### `UtilizationService` (NEW)
- `compute_daily_metrics(db, date: date) → List[UtilizationMetric]`
  - Aggregates session_events for each charger for the given day
  - Computes: total/unique/avg duration/peak vs off-peak/new vs repeat
  - Upserts into `utilization_metrics`
- `compute_campaign_lift(db, campaign_id) → CampaignLiftReport`
  - Compares: baseline period (before campaign) vs campaign period
  - Returns: `{baseline_sessions_per_day, campaign_sessions_per_day, lift_pct, confidence}`
- `get_charger_utilization(db, charger_id, period_type, since, until) → List[UtilizationMetric]`
- `get_zone_utilization(db, zone_id, period_type, since, until) → List[UtilizationMetric]`

### 3.4 New Routers

#### `campaigns` router (NEW) — `/v1/campaigns`
For funders to manage their campaigns:

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/` | Funder auth | Create campaign |
| GET | `/` | Funder auth | List my campaigns |
| GET | `/{id}` | Funder auth | Get campaign details |
| PUT | `/{id}` | Funder auth | Update campaign |
| POST | `/{id}/pause` | Funder auth | Pause campaign |
| POST | `/{id}/resume` | Funder auth | Resume campaign |
| GET | `/{id}/grants` | Funder auth | List grants for campaign |
| GET | `/{id}/lift` | Funder auth | Get lift report |

#### `sessions` router (NEW) — `/v1/sessions`
For drivers to see their charging history:

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/` | Driver auth | List my sessions |
| GET | `/active` | Driver auth | Get current active session |
| GET | `/{id}` | Driver auth | Get session details + grants earned |

#### `utilization` router (NEW) — `/v1/utilization`
For admin and funders:

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| GET | `/chargers/{id}` | Auth | Charger utilization metrics |
| GET | `/zones/{id}` | Auth | Zone utilization metrics |
| GET | `/overview` | Admin | Platform-wide utilization |

#### `funders` router (NEW) — `/v1/funders`
For admin to manage funders:

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/` | Admin | Create funder |
| GET | `/` | Admin | List funders |
| GET | `/{id}` | Admin | Get funder details |
| PUT | `/{id}` | Admin | Update funder |
| POST | `/{id}/fund` | Admin/Funder | Add budget (Stripe or invoice) |

### 3.5 Automated Session Detection

#### Tesla Session Polling (Enhancement to existing)
Currently: `verify_charging_all_vehicles()` is called once per driver request.
Goal: Background polling that automatically creates/updates `session_events`.

**Flow:**
1. Background task runs every 60 seconds for each active `TeslaConnection`
2. Calls `get_vehicle_data()` for the selected vehicle only (not all vehicles)
3. If `charging_state in {"Charging", "Starting"}` and no active `session_event`:
   - Create new `session_event` (source='tesla_api', verified=True)
   - Run `IncentiveEngine.evaluate_session()` to check for matching campaigns
4. If `charging_state not in {"Charging", "Starting"}` and active `session_event` exists:
   - End session: set `session_end`, compute `duration_minutes`
   - Re-evaluate for duration-based rules
5. If session still active: update `kwh_delivered`, `battery_end_pct` (telemetry)

**Implementation:** Use FastAPI `BackgroundTasks` or a lightweight task queue. For MVP, a `/v1/sessions/poll` endpoint triggered by the driver app every 60s while the app is open is simpler than a full background worker.

### 3.6 Portal Transformation

The merchant portal becomes a **Campaign Builder** that serves three customer types through one interface:

| Customer | What They See | What They Do |
|---|---|---|
| Merchant | "Boost foot traffic from EV drivers charging nearby" | Pick chargers within radius → set $/session → set budget → launch |
| Charging Network | "Boost utilization at underperforming sites" | See utilization dashboard → select sites → set incentive → monitor lift |
| Sponsor | "Run EV behavior campaigns" | Define rules (geography, time, driver segment) → set budget → track ROI |

**Auth:** Funders log in with their own credentials. Admin can create funder accounts.

---

## 4. Gap Analysis: Current vs. Goal

### 4.1 What Exists and Maps Directly

| Current | Goal Mapping | Change Needed |
|---|---|---|
| `tesla_connections` | Session event source | None (keep as-is) |
| `TeslaOAuthService` | Session detection engine | Enhance: add continuous polling, session lifecycle |
| `nova_transactions` | Incentive ledger | Add: `campaign_id` reference, new types |
| `driver_wallets` | Driver balance | None (keep as-is) |
| `NovaService` | Incentive distribution | Add: campaign-triggered grants |
| `chargers` table | Charger inventory | Add: utilization fields |
| `zones` table | Geographic scoping | None (keep as-is) |
| `users` table | Driver identity | None (keep as-is) |
| `energy_events` table | Proto-campaigns | Replace with `campaigns` (richer model) |
| `StripeService` | Payment processing | Extend: campaign funding (not just Nova packages) |
| Native bridge session states | Behavioral signal | Enhance: surface session events to driver |

### 4.2 What Exists but Becomes Secondary

| Current | New Role | Action |
|---|---|---|
| `SpendVerificationService` | Premium upsell tier | Keep but remove from critical path |
| `clo.py` router | Optional card-linking | Keep but deprioritize |
| `CheckinService` | Merchant-specific flow | Keep for merchant tier, not core |
| `arrival_sessions` | Merchant coordination | Keep for merchant tier |
| `exclusive_sessions` | Merchant activation | Keep for merchant tier |
| `merchant_funnel` router | Merchant onboarding | Keep but not growth priority |
| `merchant_perks` | Merchant offers | Reframe as campaign-funded perk |
| `merchant_fee_ledger` | Merchant billing | Generalize to funder billing |

### 4.3 What Must Be Built

| Component | Complexity | Dependencies |
|---|---|---|
| `funders` table + model | Low | None |
| `campaigns` table + model | Medium | `funders` |
| `campaign_rules` table + model | Medium | `campaigns` |
| `session_events` table + model | Medium | `users`, `chargers` |
| `incentive_grants` table + model | Medium | `session_events`, `campaigns`, `nova_transactions` |
| `utilization_metrics` table + model | Medium | `session_events`, `chargers` |
| `SessionEventService` | Medium | `TeslaOAuthService`, `session_events` |
| `CampaignService` | Medium | `campaigns`, `campaign_rules`, `funders` |
| `IncentiveEngine` (rules engine) | High | `CampaignService`, `SessionEventService`, `NovaService` |
| `UtilizationService` | Medium | `session_events`, `utilization_metrics` |
| Campaigns router | Medium | `CampaignService` |
| Sessions router | Low | `SessionEventService` |
| Utilization router | Low | `UtilizationService` |
| Funders router | Low | `funders` model |
| Campaign Builder portal | High | All new backend APIs |
| Driver app session view | Medium | Sessions router |
| Admin utilization dashboard | Medium | Utilization router |
| Second charging network (EVgo/ChargePoint) | High | OCPP or partner API |
| Background session polling | Medium | Tesla API, task queue |

---

## 5. Implementation Phases

### Phase A: Foundation (Session Events + Campaigns Data Model)
**Duration estimate: Not provided (per policy)**
**Goal:** New tables exist, migrations run, basic CRUD works.

#### A1. Create Alembic migrations
- `funders` table
- `campaigns` table
- `campaign_rules` table
- `session_events` table
- `incentive_grants` table
- `utilization_metrics` table
- Add `campaign_id` column to `nova_transactions` (nullable FK)

#### A2. Create SQLAlchemy models
- `backend/app/models/campaign.py` — Funder, Campaign, CampaignRule
- `backend/app/models/session_event.py` — SessionEvent, IncentiveGrant
- `backend/app/models/utilization.py` — UtilizationMetric

#### A3. Import models in `backend/app/models/__init__.py`

#### A4. Run migrations against dev SQLite and prod PostgreSQL

**Files created:**
- `backend/app/models/campaign.py`
- `backend/app/models/session_event.py`
- `backend/app/models/utilization.py`
- `backend/alembic/versions/xxx_add_campaign_models.py`

**Files modified:**
- `backend/app/models/__init__.py`
- `backend/app/models/domain.py` (add campaign_id to NovaTransaction)

---

### Phase B: Session Event Service (Tesla → SessionEvent Pipeline)
**Goal:** Charging sessions automatically create `session_events`.

#### B1. Create `SessionEventService`
- `create_from_tesla()` — creates session_event from Tesla charge_data
- `end_session()` — sets session_end, computes duration
- `get_active_session()` — finds open session for driver
- `get_driver_sessions()` — paginated history
- Deduplication: unique constraint on `(source, source_session_id)`

#### B2. Wire into Tesla verify-charging endpoint
- After `verify_charging_all_vehicles()` succeeds and creates EV code:
  - Also create/update `session_event` in `tesla_auth.py` router
  - If session already exists for this vehicle+charger: update it
  - If not: create new one

#### B3. Create `/v1/sessions` router
- `GET /v1/sessions/` — list driver's sessions
- `GET /v1/sessions/active` — current session
- `GET /v1/sessions/{id}` — session details

#### B4. Add session polling endpoint (MVP alternative to background worker)
- `POST /v1/sessions/poll` — driver app calls every 60s while open
  - Checks Tesla charging state
  - Creates/updates session_event
  - Returns: `{session_active, session_id, duration_minutes, incentives_earned}`

**Files created:**
- `backend/app/services/session_event_service.py`
- `backend/app/routers/sessions.py`

**Files modified:**
- `backend/app/routers/tesla_auth.py` (wire session creation into verify-charging)
- `backend/app/main_simple.py` (register sessions router)

---

### Phase C: Campaign Service + Rules Engine
**Goal:** Funders can create campaigns, rules engine evaluates sessions.

#### C1. Create `CampaignService`
- CRUD for campaigns + rules
- Budget tracking (atomic decrement)
- Status management (draft → active → paused → exhausted → completed)

#### C2. Create `IncentiveEngine`
- `evaluate_session(db, session_event)` — core matching logic
- Rule evaluators for each rule_type
- Atomic: grant Nova + decrement budget in single transaction
- Creates `incentive_grants` records
- Calls `NovaService.grant_to_driver()` with `campaign_id` reference

#### C3. Wire engine into SessionEventService
- On session creation: `IncentiveEngine.evaluate_session()`
- On session end: re-evaluate for duration-based rules

#### C4. Create `/v1/campaigns` router
- CRUD endpoints for funders
- Grant listing per campaign
- Lift report endpoint (stub — full implementation in Phase E)

#### C5. Create `/v1/funders` router (admin only)
- CRUD for funders
- Fund campaign budgets

**Files created:**
- `backend/app/services/campaign_service.py`
- `backend/app/services/incentive_engine.py`
- `backend/app/routers/campaigns.py`
- `backend/app/routers/funders.py`

**Files modified:**
- `backend/app/services/session_event_service.py` (wire incentive engine)
- `backend/app/services/nova_service.py` (add campaign_id to grant_to_driver)
- `backend/app/main_simple.py` (register routers)

---

### Phase D: Driver App Updates
**Goal:** Driver sees charging sessions and earned incentives (not just merchant offers).

#### D1. New Session Activity Screen
- Shows: active session (if charging), recent sessions
- For each session: charger name, duration, kWh, incentives earned
- Replaces/supplements the wallet view

#### D2. Update DriverHome state machine
- `CHARGING_ACTIVE` state now shows:
  - "You're earning!" banner with active session info
  - Incentive amount earned so far (from matching campaigns)
  - Nearby merchants (kept as secondary layer)
- Remove exclusive activation as primary CTA
- Add session earnings as primary CTA

#### D3. Session polling integration
- When `appChargingState === 'CHARGING_ACTIVE'`:
  - Call `POST /v1/sessions/poll` every 60s
  - Update session card with duration + earnings
- When session ends (state transitions away):
  - Show session summary with total earned

#### D4. Update wallet to show session-based earnings
- Transaction history shows: "Earned $X from Campaign Y at Charger Z"
- Balance reflects session incentives (not just merchant-confirmed Nova)

**Files created:**
- `apps/driver/src/components/Sessions/SessionActivityScreen.tsx`
- `apps/driver/src/components/Sessions/SessionCard.tsx`
- `apps/driver/src/hooks/useSessionPolling.ts`

**Files modified:**
- `apps/driver/src/App.tsx` (add session route)
- `apps/driver/src/services/api.ts` (add session endpoints)
- `apps/driver/src/components/DriverHome/DriverHome.tsx` (update CHARGING_ACTIVE view)
- `apps/driver/src/components/DriverHome/WalletModal.tsx` or equivalent (show session earnings)

---

### Phase E: Utilization Dashboard + Campaign Builder Portal
**Goal:** Funders can see utilization data and create campaigns through a web portal.

#### E1. Create `UtilizationService`
- Daily metric computation (cron or on-demand)
- Campaign lift calculation (before/after comparison)
- Charger and zone-level aggregations

#### E2. Create `/v1/utilization` router
- Charger metrics, zone metrics, platform overview

#### E3. Transform merchant portal into Campaign Builder
- **Option A:** Modify existing `apps/merchant/` to support funder role
- **Option B:** Create new `apps/funder/` portal (recommended — cleaner separation)

Campaign Builder screens:
- Dashboard: campaign performance overview
- Create Campaign: wizard with rule builder
- Campaign Detail: real-time grant feed, budget tracker, lift metrics
- Charger Explorer: map view with utilization data per charger
- Billing: campaign funding + invoice history

#### E4. Admin utilization dashboard
- Add utilization tab to `apps/admin/`
- Platform-wide metrics: total sessions, total incentives granted, active campaigns
- Per-charger drill-down with utilization charts

**Files created:**
- `backend/app/services/utilization_service.py`
- `backend/app/routers/utilization.py`
- `apps/funder/` (new app) or significant modifications to `apps/merchant/`
- Admin: new `UtilizationDashboard.tsx` component

**Files modified:**
- `backend/app/main_simple.py` (register utilization router)
- `apps/admin/src/App.tsx` (add utilization tab)
- `apps/admin/src/services/api.ts` (utilization API calls)

---

### Phase F: Second Charging Network Integration
**Goal:** Session events from non-Tesla chargers (EVgo, ChargePoint, or OCPP).

#### F1. Research partner APIs
- ChargePoint: Partner API requires business agreement
- EVgo: API access program
- OCPP: Open standard, requires OCPP server or partnership with CPO

#### F2. Create network-specific adapter
- `backend/app/services/chargepoint_adapter.py` (or evgo)
- Implements same interface as Tesla: `get_charging_status() → (is_charging, charge_data)`
- Creates `session_events` with `source='chargepoint_api'`

#### F3. Unified session detection
- Abstract charging verification behind interface
- Each adapter creates session_events in the same format
- IncentiveEngine is source-agnostic

**Files created:**
- `backend/app/services/charging_adapters/base.py`
- `backend/app/services/charging_adapters/tesla.py` (refactored from tesla_oauth.py)
- `backend/app/services/charging_adapters/chargepoint.py` (or evgo)

---

### Phase G: Deprecation of Spend Verification as Core
**Goal:** CLO/Fidel/spend verification moves to optional premium tier.

#### G1. Remove spend verification from driver app critical path
- LoginModal no longer mentions card linking
- No card linking prompts in onboarding
- CLO endpoints remain available but not surfaced in primary UI

#### G2. Create premium tier flag
- `campaigns.tier` field: 'standard' (presence-based) | 'premium' (spend-verified)
- Premium campaigns can additionally require spend verification
- Only available to merchants who specifically request ROI precision

#### G3. Update admin dashboard
- Mark CLO/Fidel as "Premium Attribution" tier
- Separate from core session incentives

**Files modified:**
- `apps/driver/src/components/DriverHome/DriverHome.tsx` (remove CLO prompts)
- `backend/app/models/campaign.py` (add tier field)
- `apps/admin/src/components/` (label premium tier)

---

## 6. Data Model Changes Summary

### New Tables (6)

| Table | Columns | Purpose |
|---|---|---|
| `funders` | ~12 columns | Who funds incentives |
| `campaigns` | ~17 columns | Incentive programs with budgets |
| `campaign_rules` | ~6 columns | Conditions for session qualification |
| `session_events` | ~22 columns | Verified charging sessions |
| `incentive_grants` | ~10 columns | Session-to-campaign grant records |
| `utilization_metrics` | ~18 columns | Aggregated charger/zone metrics |

### Modified Tables (1)

| Table | Change | Reason |
|---|---|---|
| `nova_transactions` | Add `campaign_id` (UUID, FK, nullable) | Link grants to campaigns |

### Unchanged Tables (Everything Else)

All existing tables remain. No destructive migrations. The pivot is additive.

---

## 7. API Surface Changes

### New Endpoints (~20)

| Router | Endpoint Count | Auth |
|---|---|---|
| `/v1/sessions` | 4 endpoints | Driver |
| `/v1/campaigns` | 8 endpoints | Funder |
| `/v1/funders` | 5 endpoints | Admin |
| `/v1/utilization` | 3 endpoints | Admin/Funder |

### Modified Endpoints (~3)

| Endpoint | Change |
|---|---|
| `POST /v1/auth/tesla/verify-charging` | Also creates/updates session_event |
| `POST /v1/nova/grant` | Accept optional campaign_id |
| `GET /v1/wallet/balance` | Include session-based earnings breakdown |

### Deprecated (Moved to Secondary) (~8)

| Endpoint | New Status |
|---|---|
| `POST /v1/clo/cards/link` | Premium tier only |
| `DELETE /v1/clo/cards/{id}` | Premium tier only |
| `POST /v1/clo/verify` | Premium tier only |
| `POST /v1/clo/fidel/webhook` | Premium tier only |
| Other CLO endpoints | Premium tier only |

### Unchanged (~85+)

All existing endpoints continue to work. No breaking changes.

---

## 8. Frontend Changes

### Driver App

| Change | Scope | Priority |
|---|---|---|
| Session Activity screen | New component | High |
| Session polling hook | New hook | High |
| CHARGING_ACTIVE state update | Modify DriverHome | High |
| Wallet session earnings | Modify WalletModal | Medium |
| Remove CLO card linking from primary UI | Modify settings | Low |
| EV code display enhancement (show earned amount) | Modify existing | Medium |

### Merchant Portal → Campaign Builder

| Change | Scope | Priority |
|---|---|---|
| Campaign creation wizard | New screen | High |
| Campaign performance dashboard | New screen | High |
| Charger utilization explorer | New screen | Medium |
| Rule builder UI (time, geography, driver segment) | New component | High |
| Budget tracker | New component | Medium |
| Preserve existing merchant flows | Keep as-is | N/A |

### Admin Dashboard

| Change | Scope | Priority |
|---|---|---|
| Utilization tab | New screen | High |
| Campaign monitoring | New screen | Medium |
| Funder management | New screen | Medium |
| Session event browser | New screen | Low |

---

## 9. Migration Strategy

### Database Migrations

1. **All migrations are additive** — no column drops, no table renames
2. New tables created with Alembic `revision --autogenerate`
3. `nova_transactions.campaign_id` added as nullable FK (no backfill needed)
4. Existing data untouched — backward compatibility preserved

### Backend Deployment

1. Deploy new models + migrations first (tables created but unused)
2. Deploy new services + routers (new endpoints available)
3. Wire Tesla verify-charging to create session_events (data starts flowing)
4. Deploy IncentiveEngine (campaigns start granting)
5. All existing endpoints continue to work throughout

### Frontend Deployment

1. Driver app: Add session polling + activity screen (additive)
2. Driver app: Update CHARGING_ACTIVE view (modify existing)
3. Funder portal: Deploy as new app (or modify merchant portal)
4. Admin: Add utilization tab (additive)

### Rollback Plan

- New tables can be dropped without affecting existing functionality
- `nova_transactions.campaign_id` is nullable — removing it is a clean migration
- All existing services, routers, and models remain unchanged
- Feature flags can gate new behavior: `ENABLE_SESSION_INCENTIVES=true/false`

---

## 10. Risk Assessment

### Technical Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Tesla API rate limits on continuous polling | High | Poll per-driver only when app is open (not background), cache aggressively, respect 429 |
| Rules engine performance with many campaigns | Medium | Index campaign_rules, cache active campaigns in memory, evaluate lazily |
| Race condition on budget decrement | High | Use atomic SQL: `UPDATE campaigns SET spent_cents = spent_cents + :amount WHERE spent_cents + :amount <= budget_cents` |
| Session duplication (same charge, multiple events) | Medium | Unique constraint on `(source, source_session_id)`, dedup in service layer |
| Utilization computation latency | Low | Run as batch job (nightly), not real-time |
| Second network API access | High | Requires business partnership (ChargePoint/EVgo), plan 2-3 month lead time |

### Business Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Merchant revenue disrupted during transition | Medium | Keep all merchant flows working, add campaign layer on top |
| Funders don't materialize (no demand) | High | Run pilot with one charging network partner first, build case study |
| Driver engagement drops without merchant offers | Medium | Keep merchant offers as secondary layer, session incentives compensate |
| Existing merchant relationships strained | Low | Merchants can become funders using the same portal, framed as upgrade |

### Organizational Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Scope creep (building too much before validation) | High | Phase A-C are backend-only, can be deployed in weeks, validate with manual campaigns |
| Portal complexity (Campaign Builder is large) | Medium | MVP: admin-only campaign creation, portal comes later |
| Distraction from core product (Tesla integration) | Medium | Phase B enhances Tesla integration, not separate from it |

---

## 11. Verification Plan

### Phase A Verification
```bash
# Run migrations
cd backend && python -m alembic upgrade head

# Verify tables exist
python3 -c "
from app.db import SessionLocal
from app.models.campaign import Funder, Campaign, CampaignRule
from app.models.session_event import SessionEvent, IncentiveGrant
from app.models.utilization import UtilizationMetric
db = SessionLocal()
print('All models importable')
db.close()
"
```

### Phase B Verification
```bash
# Create a session event manually
python3 -c "
from app.services.session_event_service import SessionEventService
# ... create test session
"

# Verify sessions endpoint
curl -H 'Authorization: Bearer $TOKEN' https://api.nerava.network/v1/sessions/
```

### Phase C Verification
```bash
# Create a test campaign
curl -X POST https://api.nerava.network/v1/campaigns/ \
  -H 'Authorization: Bearer $ADMIN_TOKEN' \
  -d '{
    "funder_id": "...",
    "name": "Test Boost",
    "budget_cents": 10000,
    "cost_per_session_cents": 200,
    "rules": [{"rule_type": "charger_ids", "rule_operator": "in", "rule_value": ["ch_123"]}]
  }'

# Verify a session triggers a grant
# (charge at ch_123, check driver wallet increased by 200 cents)
```

### Phase D Verification
```bash
# Build driver app
cd apps/driver && npm run build

# Verify session polling
# (Open app while charging, verify session card appears and updates)
```

### Phase E Verification
```bash
# Verify utilization metrics computed
curl -H 'Authorization: Bearer $TOKEN' \
  https://api.nerava.network/v1/utilization/chargers/ch_123?period=daily

# Verify campaign lift report
curl -H 'Authorization: Bearer $TOKEN' \
  https://api.nerava.network/v1/campaigns/{id}/lift
```

---

## Appendix: File Inventory

### Files to Create

| File | Phase | Purpose |
|---|---|---|
| `backend/app/models/campaign.py` | A | Funder, Campaign, CampaignRule models |
| `backend/app/models/session_event.py` | A | SessionEvent, IncentiveGrant models |
| `backend/app/models/utilization.py` | A | UtilizationMetric model |
| `backend/alembic/versions/xxx_add_campaign_models.py` | A | Migration |
| `backend/app/services/session_event_service.py` | B | Session lifecycle management |
| `backend/app/routers/sessions.py` | B | Driver session endpoints |
| `backend/app/services/campaign_service.py` | C | Campaign CRUD + budget management |
| `backend/app/services/incentive_engine.py` | C | Rules evaluation engine |
| `backend/app/routers/campaigns.py` | C | Campaign management endpoints |
| `backend/app/routers/funders.py` | C | Funder management endpoints |
| `apps/driver/src/components/Sessions/SessionActivityScreen.tsx` | D | Session history view |
| `apps/driver/src/components/Sessions/SessionCard.tsx` | D | Session card component |
| `apps/driver/src/hooks/useSessionPolling.ts` | D | 60s session poll hook |
| `backend/app/services/utilization_service.py` | E | Metric computation |
| `backend/app/routers/utilization.py` | E | Utilization endpoints |

### Files to Modify

| File | Phase | Change |
|---|---|---|
| `backend/app/models/__init__.py` | A | Import new models |
| `backend/app/models/domain.py` | A | Add campaign_id to NovaTransaction |
| `backend/app/main_simple.py` | B, C | Register new routers |
| `backend/app/routers/tesla_auth.py` | B | Wire session_event creation |
| `backend/app/services/nova_service.py` | C | Accept campaign_id in grants |
| `backend/app/services/session_event_service.py` | C | Wire incentive engine |
| `apps/driver/src/App.tsx` | D | Add session routes |
| `apps/driver/src/services/api.ts` | D | Add session API calls |
| `apps/driver/src/components/DriverHome/DriverHome.tsx` | D | Update CHARGING_ACTIVE view |
| `apps/admin/src/App.tsx` | E | Add utilization tab |
| `apps/admin/src/services/api.ts` | E | Add utilization API calls |

### Files Unchanged (Remain Functional)

All existing routers, services, models, and frontend components continue to work as-is. The pivot is purely additive. No breaking changes.

---

*End of document. This plan is designed for cross-AI review and can be executed phase-by-phase with verification at each step.*
