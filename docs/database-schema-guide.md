# Nerava Database Schema Guide

**Database:** PostgreSQL 15 on AWS RDS
**Date:** 2026-01-30

---

## What is Nerava?

Nerava is a platform that connects EV (electric vehicle) drivers with nearby restaurants and businesses while they charge. Think of it like this:

1. A driver pulls up to a Tesla Supercharger
2. The app detects their location and shows nearby restaurants
3. The driver picks a restaurant and gets an exclusive deal (like a free drink)
4. A 60-minute countdown timer starts
5. The driver walks to the restaurant, shows a code to the host, and enjoys their meal
6. The session completes and we capture feedback

The database tracks every step of this journey.

---

## How to Read This Guide

Each section describes a group of related tables. For each table, you'll see:

- **What it stores** — plain English description
- **Columns** — every field with its type and what it means
- **How it connects** — which other tables it links to (and how to join them)

**Key terms:**
- **Primary Key (PK):** The unique identifier for each row. Like a Social Security number for a database record.
- **Foreign Key (FK):** A column that points to a row in another table. It's how tables are connected. For example, if `exclusive_sessions.driver_id` is a FK to `users.id`, that means every exclusive session belongs to one user.
- **UUID:** A random 36-character string like `a1b2c3d4-5678-90ab-cdef-1234567890ab`. Used as IDs instead of counting numbers so they can't be guessed.
- **Nullable:** The field can be empty (NULL). If a column is NOT nullable, every row must have a value.
- **Index:** A performance optimization that makes searching by that column fast. If you see "indexed" it means queries filtering on that column will be fast.

---

## The Core Tables

These are the most important tables. Start here.

### `users` — Every person who has ever used Nerava

This is the central table. Almost everything connects back to a user.

| Column | Type | What It Means |
|---|---|---|
| `id` | Integer (PK) | Auto-incrementing number. The internal user ID. |
| `public_id` | String | A public-facing ID like `usr_abc123`. Safe to expose in APIs. |
| `email` | String | Email address (nullable — phone-only users won't have one) |
| `phone` | String | Phone number in `+1XXXXXXXXXX` format (nullable — email-only users) |
| `display_name` | String | Whatever name the user chose (nullable) |
| `hashed_password` | String | Encrypted password (nullable — OTP users don't have passwords) |
| `auth_provider` | String | How they signed up: `"phone_otp"`, `"google"`, `"apple"`, `"email"` |
| `is_active` | Boolean | Whether the account is enabled |
| `role` | String | `"driver"`, `"merchant_admin"`, or `"admin"` |
| `admin_role` | String | For admin users: `"super_admin"`, `"zone_manager"`, `"support"`, `"analyst"` |
| `google_id` | String | Google OAuth ID (nullable) |
| `apple_id` | String | Apple Sign-In ID (nullable) |
| `analytics_consent` | Boolean | Whether they consented to analytics tracking |
| `consent_ip` | String | IP address when they gave consent (for GDPR compliance) |
| `consent_at` | DateTime | When they consented |
| `privacy_policy_version` | String | Which version of the privacy policy they agreed to |
| `created_at` | DateTime | When the account was created |
| `updated_at` | DateTime | Last modification time |

**Common queries:**
```sql
-- How many users signed up this month?
SELECT COUNT(*) FROM users WHERE created_at >= '2026-01-01';

-- How many users by auth provider?
SELECT auth_provider, COUNT(*) FROM users GROUP BY auth_provider;

-- How many drivers vs merchants vs admins?
SELECT role, COUNT(*) FROM users GROUP BY role;
```

---

### `chargers` — EV charging stations

Each row is a physical charging station (like a Tesla Supercharger location).

| Column | Type | What It Means |
|---|---|---|
| `id` | String (PK) | Unique charger ID like `"canyon_ridge_tesla"` |
| `name` | String | Human name: `"Tesla Supercharger - Canyon Ridge"` |
| `lat` | Float | Latitude coordinate |
| `lng` | Float | Longitude coordinate |
| `network_name` | String | Charging network: `"Tesla"`, `"ChargePoint"`, `"EVgo"` |
| `is_public` | Boolean | Whether it's publicly accessible |
| `address` | String | Street address |
| `total_stalls` | Integer | Number of charging plugs |
| `available_stalls` | Integer | Currently open plugs (nullable) |
| `stall_power_kw` | Float | Power output per stall in kilowatts |
| `primary_merchant_id` | String (FK → merchants) | The "featured" nearby merchant |
| `primary_merchant_override_id` | String (FK → merchants) | Manual override for the featured merchant |
| `created_at` | DateTime | When added to our database |

**Common queries:**
```sql
-- All chargers and their featured merchant
SELECT c.name as charger, m.name as featured_merchant
FROM chargers c
LEFT JOIN merchants m ON c.primary_merchant_id = m.id;

-- Chargers by network
SELECT network_name, COUNT(*) FROM chargers GROUP BY network_name;
```

---

### `merchants` — Businesses near chargers

Each row is a restaurant, cafe, or business that's been linked to a charger.

| Column | Type | What It Means |
|---|---|---|
| `id` | String (PK) | Unique merchant ID like `"asadas_grill_canyon_ridge"` |
| `name` | String | Business name: `"Asadas Grill"` |
| `google_place_id` | String | Google Maps Place ID (used to fetch hours, photos, reviews) |
| `address` | String | Street address |
| `lat` | Float | Latitude |
| `lng` | Float | Longitude |
| `category` | String | Business type: `"Mexican Restaurant"`, `"Coffee Shop"` |
| `phone` | String | Business phone number |
| `website` | String | Business website URL |
| `rating` | Float | Google rating (1.0 to 5.0) |
| `user_ratings_total` | Integer | Number of Google reviews |
| `price_level` | Integer | Price range: 1 ($) to 4 ($$$$) |
| `hours_json` | JSON | Operating hours by day |
| `photo_urls` | JSON | Array of photo URLs |
| `is_active` | Boolean | Whether the merchant is visible to drivers |
| `created_at` | DateTime | When added |

**How merchants connect to chargers:** Through the `charger_merchants` linking table (see below).

---

### `charger_merchants` — Which merchants are near which chargers

This is a "linking table" (also called a junction table or bridge table). It connects chargers to merchants in a many-to-many relationship. One charger can have multiple nearby merchants, and one merchant could be near multiple chargers.

| Column | Type | What It Means |
|---|---|---|
| `id` | Integer (PK) | Row ID |
| `charger_id` | String (FK → chargers) | Which charger |
| `merchant_id` | String (FK → merchants) | Which merchant |
| `distance_m` | Float | Walking distance in meters |
| `walk_time_minutes` | Integer | Estimated walking time |
| `is_primary` | Boolean | Whether this is the "featured" merchant for this charger |
| `sort_order` | Integer | Display order (lower = shown first) |

**How to use it:**
```sql
-- All merchants within walking distance of a charger
SELECT m.name, cm.distance_m, cm.walk_time_minutes
FROM charger_merchants cm
JOIN merchants m ON cm.merchant_id = m.id
WHERE cm.charger_id = 'canyon_ridge_tesla'
ORDER BY cm.sort_order;

-- Which chargers are near Asadas Grill?
SELECT c.name, cm.distance_m
FROM charger_merchants cm
JOIN chargers c ON cm.charger_id = c.id
WHERE cm.merchant_id = 'asadas_grill_canyon_ridge';
```

---

## The User Journey Tables

These tables track what happens as a driver goes through the app flow.

### `intent_sessions` — "A driver opened the app near a charger"

Created when a driver's GPS coordinates are sent to the server. This is the starting point of every user session.

| Column | Type | What It Means |
|---|---|---|
| `id` | UUID (PK) | Session ID |
| `user_id` | Integer (FK → users) | Which driver (null for anonymous users) |
| `lat` | Float | Driver's latitude when the session started |
| `lng` | Float | Driver's longitude |
| `accuracy_m` | Float | GPS accuracy in meters (lower = more precise) |
| `charger_id` | String (FK → chargers) | Nearest charger found |
| `charger_distance_m` | Float | How far the driver was from the charger |
| `confidence_tier` | String | `"A"` (within 120m), `"B"` (within 400m), `"C"` (no charger) |
| `source` | String | `"web"` or `"mobile"` |
| `created_at` | DateTime | When the session started |

**Why it matters:** This tells you how many people opened the app, where they were, and whether they were near a charger. The `confidence_tier` is key — Tier A/B users saw merchants, Tier C got a "no chargers nearby" message.

```sql
-- Daily intent captures by confidence tier
SELECT DATE(created_at) as day, confidence_tier, COUNT(*)
FROM intent_sessions
GROUP BY day, confidence_tier
ORDER BY day DESC;

-- Average GPS accuracy
SELECT AVG(accuracy_m) FROM intent_sessions WHERE accuracy_m IS NOT NULL;
```

---

### `exclusive_sessions` — "A driver secured an exclusive deal"

This is the main business event. Created when a driver taps "Activate Exclusive" and starts the 60-minute countdown.

| Column | Type | What It Means |
|---|---|---|
| `id` | UUID (PK) | Session ID |
| `driver_id` | Integer (FK → users) | Which driver |
| `merchant_id` | String (FK → merchants) | Which merchant they chose |
| `charger_id` | String (FK → chargers) | Which charger they were at |
| `intent_session_id` | UUID (FK → intent_sessions) | Links back to the original GPS capture |
| `status` | Enum | `"ACTIVE"`, `"COMPLETED"`, `"EXPIRED"`, `"CANCELED"` |
| `activated_at` | DateTime | When the timer started |
| `expires_at` | DateTime | When the timer runs out (60 min after activation) |
| `completed_at` | DateTime | When the driver completed the session (null if expired/canceled) |
| `activation_lat` | Float | Driver's exact location at activation |
| `activation_lng` | Float | Driver's exact location at activation |
| `activation_distance_to_charger_m` | Float | How close they were to the charger |
| `intent` | String | `"eat"`, `"work"`, `"quick-stop"` — what they planned to do |
| `intent_metadata` | JSON | Extra info: `{"party_size": 2, "is_to_go": false}` |
| `idempotency_key` | String | Prevents duplicate activations from double-taps |
| `created_at` | DateTime | Row creation time |

**This is your most important analytics table.** Every row is a "conversion" — someone who went from browsing to committing.

```sql
-- Daily activations
SELECT DATE(activated_at) as day, COUNT(*) as activations
FROM exclusive_sessions
GROUP BY day ORDER BY day DESC;

-- Completion rate (what % of activated sessions were completed vs expired)
SELECT status, COUNT(*),
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
FROM exclusive_sessions
GROUP BY status;

-- Average time from activation to completion
SELECT AVG(EXTRACT(EPOCH FROM completed_at - activated_at) / 60) as avg_minutes
FROM exclusive_sessions
WHERE status = 'COMPLETED';

-- Most popular merchants
SELECT m.name, COUNT(*) as activations
FROM exclusive_sessions es
JOIN merchants m ON es.merchant_id = m.id
GROUP BY m.name ORDER BY activations DESC;

-- Intent breakdown
SELECT intent, COUNT(*) FROM exclusive_sessions GROUP BY intent;

-- Party size distribution (from JSON column)
SELECT intent_metadata->>'party_size' as party_size, COUNT(*)
FROM exclusive_sessions
WHERE intent_metadata->>'party_size' IS NOT NULL
GROUP BY party_size;
```

---

### `verified_visits` — "A driver actually showed up at the merchant"

Created when the driver taps "I'm at the Merchant" and shows their code. This is the strongest signal that the driver physically visited the business.

| Column | Type | What It Means |
|---|---|---|
| `id` | String (PK) | UUID |
| `verification_code` | String | Human-readable code shown to the host: `"ATX-ASADAS-023"` |
| `region_code` | String | Region prefix: `"ATX"` (Austin) |
| `merchant_code` | String | Merchant abbreviation: `"ASADAS"` |
| `visit_number` | Integer | Sequential visit count for this merchant |
| `merchant_id` | String | Which merchant |
| `driver_id` | Integer (FK → users) | Which driver |
| `exclusive_session_id` | String (FK → exclusive_sessions) | Links to the exclusive session |
| `charger_id` | String | Which charger they came from |
| `verified_at` | DateTime | When they verified arrival |
| `verification_lat` | Float | GPS at verification time |
| `verification_lng` | Float | GPS at verification time |
| `redeemed_at` | DateTime | When the merchant confirmed the redemption (nullable) |
| `order_reference` | String | POS order number from the merchant (nullable) |
| `visit_date` | DateTime | Calendar date of the visit |

```sql
-- Total verified visits by merchant
SELECT merchant_id, COUNT(*) as visits
FROM verified_visits
GROUP BY merchant_id ORDER BY visits DESC;

-- Time from exclusive activation to verified arrival
SELECT AVG(EXTRACT(EPOCH FROM vv.verified_at - es.activated_at) / 60) as avg_minutes_to_arrive
FROM verified_visits vv
JOIN exclusive_sessions es ON vv.exclusive_session_id = es.id;

-- Redemption rate (how many verified visits also have a POS order)
SELECT COUNT(CASE WHEN redeemed_at IS NOT NULL THEN 1 END) as redeemed,
       COUNT(*) as total,
       ROUND(100.0 * COUNT(CASE WHEN redeemed_at IS NOT NULL THEN 1 END) / COUNT(*), 1) as redemption_pct
FROM verified_visits;
```

---

## User Profile & Preferences Tables

### `user_preferences` — What the driver likes

| Column | Type | What It Means |
|---|---|---|
| `id` | UUID (PK) | Row ID |
| `user_id` | Integer (FK → users) | Which user |
| `cuisine_preferences` | JSON | Array of preferred cuisines: `["mexican", "italian"]` |
| `dietary_restrictions` | JSON | `["vegetarian", "gluten-free"]` |
| `max_walk_distance_m` | Integer | How far they're willing to walk |
| `preferred_amenities` | JSON | `["wifi", "outdoor_seating"]` |
| `created_at` | DateTime | When preferences were saved |

### `favorite_merchants` — Merchants the driver "hearted"

| Column | Type | What It Means |
|---|---|---|
| `id` | Integer (PK) | Row ID |
| `user_id` | Integer (FK → users) | Which driver |
| `merchant_id` | String (FK → merchants) | Which merchant they favorited |
| `created_at` | DateTime | When they tapped the heart |

```sql
-- Most favorited merchants
SELECT m.name, COUNT(*) as favorites
FROM favorite_merchants fm
JOIN merchants m ON fm.merchant_id = m.id
GROUP BY m.name ORDER BY favorites DESC;
```

### `amenity_votes` — Crowdsourced merchant amenity info

Drivers can upvote or downvote whether a merchant has good WiFi or a bathroom.

| Column | Type | What It Means |
|---|---|---|
| `id` | Integer (PK) | Row ID |
| `merchant_id` | String (FK → merchants) | Which merchant |
| `user_id` | Integer (FK → users) | Who voted |
| `amenity` | String | `"bathroom"` or `"wifi"` |
| `vote_type` | String | `"up"` or `"down"` |
| `created_at` | DateTime | When they voted |

```sql
-- Amenity scores by merchant
SELECT m.name, av.amenity,
  SUM(CASE WHEN av.vote_type = 'up' THEN 1 ELSE 0 END) as upvotes,
  SUM(CASE WHEN av.vote_type = 'down' THEN 1 ELSE 0 END) as downvotes
FROM amenity_votes av
JOIN merchants m ON av.merchant_id = m.id
GROUP BY m.name, av.amenity;
```

---

## Wallet & Rewards Tables

### `driver_wallets` — Driver's reward balance

Each driver has one wallet. The balance is in "Nova" — Nerava's internal currency.

| Column | Type | What It Means |
|---|---|---|
| `user_id` | Integer (PK, FK → users) | One wallet per user |
| `nova_balance` | Integer | Current Nova balance (smallest unit, like cents) |
| `energy_reputation_score` | Integer | Reputation score based on charging activity |
| `charging_detected` | Boolean | Whether the system has detected active EV charging |
| `created_at` | DateTime | When the wallet was created |

### `user_reputation` — Driver's loyalty tier

| Column | Type | What It Means |
|---|---|---|
| `user_id` | String (PK) | Which user |
| `score` | Integer | Reputation points earned |
| `tier` | String | `"Bronze"`, `"Silver"`, `"Gold"` |
| `streak_days` | Integer | Consecutive days with activity |
| `followers_count` | Integer | Social followers on Nerava |
| `following_count` | Integer | How many they follow |

```sql
-- Tier distribution
SELECT tier, COUNT(*) FROM user_reputation GROUP BY tier;
```

---

## Merchant Business Tables

### `merchant_perks` — Deals offered by merchants

| Column | Type | What It Means |
|---|---|---|
| `id` | Integer (PK) | Perk ID |
| `merchant_id` | String (FK → merchants) | Which merchant offers it |
| `title` | String | `"Free Beverage with Meal"` |
| `description` | String | Details of the perk |
| `perk_type` | String | `"discount"`, `"freebie"`, `"upgrade"` |
| `value_cents` | Integer | Dollar value in cents (e.g., 500 = $5.00) |
| `is_active` | Boolean | Whether the perk is currently available |
| `max_daily_redemptions` | Integer | Cap on how many times it can be used per day |
| `created_at` | DateTime | When created |

### `perk_unlocks` — When a driver unlocked a perk

| Column | Type | What It Means |
|---|---|---|
| `id` | UUID (PK) | Unlock ID |
| `user_id` | Integer (FK → users) | Which driver |
| `perk_id` | Integer (FK → merchant_perks) | Which perk |
| `merchant_id` | String (FK → merchants) | Which merchant |
| `unlock_method` | String | `"dwell_time"` (waited long enough) or `"user_confirmation"` (tapped button) |
| `intent_session_id` | UUID (FK → intent_sessions) | Links to the intent session |
| `dwell_time_seconds` | Integer | How long they dwelled before unlock |
| `unlocked_at` | DateTime | When it was unlocked |

```sql
-- Perk unlock rate by method
SELECT unlock_method, COUNT(*) FROM perk_unlocks GROUP BY unlock_method;
```

---

## Authentication & Security Tables

### `refresh_tokens` — Active login sessions

| Column | Type | What It Means |
|---|---|---|
| `id` | UUID (PK) | Token ID |
| `user_id` | Integer (FK → users) | Which user |
| `token_hash` | String | SHA-256 hash of the refresh token (not the token itself — for security) |
| `expires_at` | DateTime | When the token expires |
| `revoked_at` | DateTime | When it was logged out (null if still active) |
| `created_at` | DateTime | When the login happened |

### `otp_challenges` — Phone verification codes

| Column | Type | What It Means |
|---|---|---|
| `id` | String (PK) | Challenge ID |
| `phone` | String | Phone number the code was sent to |
| `code_hash` | String | Hashed version of the 6-digit code |
| `expires_at` | DateTime | Code expiration (typically 10 minutes) |
| `attempts` | Integer | How many times the user tried to verify |
| `max_attempts` | Integer | Maximum allowed attempts (default 5) |
| `consumed` | Boolean | Whether the code was successfully used |
| `ip_address` | String | IP address of the requester |
| `user_agent` | String | Browser/device info |
| `created_at` | DateTime | When the code was sent |

```sql
-- OTP success rate
SELECT
  COUNT(CASE WHEN consumed = true THEN 1 END) as verified,
  COUNT(*) as total,
  ROUND(100.0 * COUNT(CASE WHEN consumed = true THEN 1 END) / COUNT(*), 1) as success_pct
FROM otp_challenges;
```

---

## Compliance Tables

### `user_consents` — GDPR/CCPA consent records

Every time a user grants or revokes consent, a NEW row is created (not updated). This preserves the full audit trail for legal compliance.

| Column | Type | What It Means |
|---|---|---|
| `id` | UUID (PK) | Consent record ID |
| `user_id` | Integer (FK → users) | Which user |
| `consent_type` | String | `"analytics"`, `"marketing"`, `"functional"` |
| `granted` | Boolean | `true` = gave consent, `false` = revoked |
| `ip_address` | String | IP when consent was given/revoked |
| `privacy_policy_version` | String | Which version they agreed to |
| `created_at` | DateTime | When this consent action happened |

**To find current consent status:** Always use the MOST RECENT row per user per consent_type:

```sql
-- Current consent status for each user
SELECT DISTINCT ON (user_id, consent_type)
  user_id, consent_type, granted, created_at
FROM user_consents
ORDER BY user_id, consent_type, created_at DESC;
```

---

## Domain/Zone Tables (Charge Party System)

These tables power the "charge party" feature — organized charging events at specific locations.

### `zones` — Geographic regions

| Column | Type | What It Means |
|---|---|---|
| `slug` | String (PK) | Zone identifier: `"domain_austin"` |
| `name` | String | Human name: `"The Domain, Austin"` |
| `center_lat` | Float | Zone center latitude |
| `center_lng` | Float | Zone center longitude |
| `radius_m` | Integer | Zone radius in meters |

### `domain_merchants` — Merchants participating in charge parties

Similar to `merchants` but for the domain/charge-party system. Includes payment integration.

Key unique columns:
- `nova_balance` — How much Nova currency the merchant has
- `square_merchant_id` / `square_access_token` — Square POS integration for payment processing
- `avg_order_value_cents` — Average order value (used to calibrate perk amounts)
- `qr_token` — QR code for in-store redemption

### `nova_transactions` — All Nova currency movements

Every Nova earn, spend, and transfer is recorded here.

| Column | Type | What It Means |
|---|---|---|
| `id` | UUID (PK) | Transaction ID |
| `type` | String | `"driver_earn"`, `"driver_redeem"`, `"merchant_topup"`, `"admin_grant"` |
| `driver_user_id` | Integer (FK → users) | The driver involved |
| `merchant_id` | String (FK → domain_merchants) | The merchant involved |
| `amount` | Integer | Always positive. Direction determined by `type`. |
| `idempotency_key` | String | Prevents duplicate transactions |
| `created_at` | DateTime | When the transaction occurred |

```sql
-- Total Nova earned vs redeemed
SELECT type, SUM(amount) as total_nova
FROM nova_transactions
GROUP BY type;
```

---

## How Tables Connect — The Full Picture

Here's how the key tables relate to each other in the main user flow:

```
users
  │
  ├── intent_sessions (user opens app near a charger)
  │     │
  │     └── exclusive_sessions (user activates a deal)
  │           │
  │           └── verified_visits (user arrives at merchant)
  │
  ├── driver_wallets (user's reward balance)
  │
  ├── user_preferences (what they like)
  │
  ├── favorite_merchants (merchants they hearted)
  │
  ├── otp_challenges (phone verification codes)
  │
  └── user_consents (privacy consent records)

chargers
  │
  └── charger_merchants (links chargers to nearby merchants)
        │
        └── merchants
              │
              ├── merchant_perks (deals the merchant offers)
              │     │
              │     └── perk_unlocks (when a driver unlocked a deal)
              │
              └── amenity_votes (WiFi/bathroom ratings)
```

---

## Key Queries for Analysis

### Funnel Analysis

```sql
-- Full funnel: Intent → Activation → Verification → Completion
WITH funnel AS (
  SELECT
    (SELECT COUNT(DISTINCT user_id) FROM intent_sessions
     WHERE created_at >= '2026-01-01') as intent_users,
    (SELECT COUNT(DISTINCT driver_id) FROM exclusive_sessions
     WHERE activated_at >= '2026-01-01') as activated_users,
    (SELECT COUNT(DISTINCT driver_id) FROM verified_visits
     WHERE verified_at >= '2026-01-01') as verified_users,
    (SELECT COUNT(DISTINCT driver_id) FROM exclusive_sessions
     WHERE status = 'COMPLETED' AND completed_at >= '2026-01-01') as completed_users
)
SELECT * FROM funnel;
```

### Cohort Retention

```sql
-- Monthly cohorts: when did users first activate, and did they come back?
SELECT
  DATE_TRUNC('month', first_activation) as cohort_month,
  COUNT(DISTINCT driver_id) as cohort_size,
  COUNT(DISTINCT CASE WHEN second_activation IS NOT NULL THEN driver_id END) as returned
FROM (
  SELECT driver_id,
    MIN(activated_at) as first_activation,
    (SELECT MIN(activated_at) FROM exclusive_sessions es2
     WHERE es2.driver_id = es.driver_id
     AND es2.activated_at > MIN(es.activated_at) + INTERVAL '7 days') as second_activation
  FROM exclusive_sessions es
  GROUP BY driver_id
) cohorts
GROUP BY cohort_month
ORDER BY cohort_month;
```

### Merchant Performance

```sql
-- Merchant scorecard
SELECT
  m.name,
  COUNT(DISTINCT es.id) as total_activations,
  COUNT(DISTINCT vv.id) as total_verified_visits,
  ROUND(100.0 * COUNT(DISTINCT vv.id) / NULLIF(COUNT(DISTINCT es.id), 0), 1) as visit_rate_pct,
  COUNT(DISTINCT es.driver_id) as unique_drivers,
  AVG(EXTRACT(EPOCH FROM vv.verified_at - es.activated_at) / 60) as avg_minutes_to_arrive
FROM merchants m
LEFT JOIN exclusive_sessions es ON m.id = es.merchant_id
LEFT JOIN verified_visits vv ON es.id = vv.exclusive_session_id
GROUP BY m.name
ORDER BY total_activations DESC;
```

### Driver Engagement

```sql
-- Driver engagement summary
SELECT
  u.public_id,
  u.auth_provider,
  u.created_at as signup_date,
  COUNT(DISTINCT es.id) as total_sessions,
  COUNT(DISTINCT CASE WHEN es.status = 'COMPLETED' THEN es.id END) as completed_sessions,
  COUNT(DISTINCT vv.id) as verified_visits,
  ur.tier as reputation_tier,
  ur.score as reputation_score
FROM users u
LEFT JOIN exclusive_sessions es ON u.id = es.driver_id
LEFT JOIN verified_visits vv ON u.id = vv.driver_id
LEFT JOIN user_reputation ur ON CAST(u.id AS TEXT) = ur.user_id
WHERE u.role = 'driver'
GROUP BY u.public_id, u.auth_provider, u.created_at, ur.tier, ur.score
ORDER BY total_sessions DESC;
```

---

## Table Counts (for reference)

The database has **78 tables total**:

- **Core tables** (described above): ~20 tables
- **Domain/charge-party tables**: ~10 tables
- **Vehicle integration tables**: 4 tables (vehicle_accounts, vehicle_tokens, vehicle_telemetry, vehicle_onboarding)
- **Wallet/pass tables**: 5 tables (driver_wallets, apple_pass_registrations, google_wallet_links, wallet_pass_state, wallet_pass_states)
- **Merchant onboarding tables**: 5 tables (merchant_accounts, merchant_location_claims, merchant_placement_rules, merchant_payment_methods, claim_sessions)
- **Feature scaffold tables**: ~30 tables (built but not yet active — things like fleet management, IoT links, AI suggestions, green hour deals)

For day-to-day analysis, you'll primarily work with: `users`, `intent_sessions`, `exclusive_sessions`, `verified_visits`, `chargers`, `merchants`, `charger_merchants`, and `merchant_perks`.

---

*Last updated: 2026-01-30*
