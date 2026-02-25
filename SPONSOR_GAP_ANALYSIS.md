# Sponsor Persona Gap Analysis

> Generated 2026-02-19 from a full audit of the Nerava monorepo.

---

## 1. Hardcoded Restaurant UI That Needs Abstraction

The merchant portal is **~85% generic** already. Only a handful of components carry restaurant-specific assumptions.

### HIGH priority

| File | Line(s) | Issue |
|------|---------|-------|
| `apps/merchant/app/components/EVArrivals.tsx` | 253, 257, 293 | Arrival types hardcoded as `"Dine-In"` vs `"EV Curbside"`. A Credit Sponsor has neither concept. |
| `apps/merchant/app/components/EVArrivals.tsx` | 11-12 | References `Order #` (`session.order_number`) and `order_total_cents` — restaurant order tracking that doesn't apply to sponsors. |

### MEDIUM priority

| File | Line(s) | Issue |
|------|---------|-------|
| `apps/merchant/app/components/CreatePickupPackage.tsx` | 50 | Placeholder text `"e.g., Coffee & Pastry Bundle"` and the feature name "Pickup Packages" assumes food-service. |
| `apps/merchant/app/components/DashboardLayout.tsx` | nav items | Sidebar label "Pickup Packages" would confuse a sponsor. Consider renaming or hiding based on merchant type. |

### LOW priority (cosmetic)

| File | Line(s) | Issue |
|------|---------|-------|
| `apps/merchant/app/components/CreateExclusive.tsx` | 98 | Placeholder `"e.g., Free Pastry with Coffee"` — cosmetic only, not enforced. |
| `apps/merchant/app/components/SelectLocation.tsx` | 11, 18 | Mock/demo location names reference "Downtown Coffee Shop". |
| `apps/merchant/app/components/PrimaryExperience.tsx` | 90 | Word "reservation" used in upcoming-feature text. |

### Already generic (no changes needed)

- Exclusives/Offers creation flow (`CreateExclusive.tsx`) — fields are name, description, daily cap, eligibility.
- Visits tracking (`Visits.tsx`) — shows timestamp, offer, driver, status, duration.
- Overview dashboard (`Overview.tsx`) — metrics are "Activations Today", "Completed Visits", "Conversion Rate".
- Onboarding (`ClaimBusiness.tsx`) — collects business name, email, phone. No restaurant-specific fields.
- Billing and Settings pages.

---

## 2. Missing DB Fields & Models

### 2a. Fields to add to `domain_merchants`

| Field | Type | Purpose |
|-------|------|---------|
| `merchant_type` | `String` (enum: `restaurant`, `sponsor`, `service`) | Distinguish persona at the data layer. Controls which dashboard features are shown, which API fields are returned, and how the driver app renders the entity. |
| `sponsor_credit_balance_cents` | `Integer`, default 0 | Separate from `nova_balance`. Tracks remaining pre-paid session credits purchased via a bundle. Decremented on each driver session drawdown. |

> **Existing field that helps:** `nova_balance` (Integer) is already on `DomainMerchant` and updated atomically by `NovaService.grant_to_merchant()`. A sponsor's bundle credits could reuse this column if the team decides one balance is sufficient.

### 2b. New table: `sponsor_credit_bundles`

```
id                  UUID   PK
sponsor_merchant_id UUID   FK → domain_merchants.id
name                String            e.g. "25K Starter Bundle"
total_credits_cents Integer           e.g. 2_500_000  ($25,000)
platform_fee_cents  Integer           e.g. 500_000    ($5,000 @ 20%)
net_session_pool    Integer           e.g. 2_000_000  ($20,000 available for sessions)
sessions_included   Integer           e.g. 4_000      (@ $5/session)
remaining_sessions  Integer           starts = sessions_included
stripe_payment_id   String  FK → stripe_payments.id
status              String            pending | active | exhausted | expired
purchased_at        DateTime
expires_at          DateTime nullable
```

### 2c. Extend `NovaTransaction.type` enum

Current values: `driver_earn`, `driver_redeem`, `merchant_topup`, `admin_grant`.

Add:
- `sponsor_bundle_purchase` — recorded when Stripe webhook confirms the $25K checkout.
- `sponsor_session_drawdown` — recorded each time a driver charging session consumes credits from a bundle.

Add nullable FK: `bundle_id → sponsor_credit_bundles.id`.

### 2d. Extend `User.role_flags`

Current roles are comma-separated in `role_flags`: `driver`, `merchant_admin`, `admin`.

Add: `sponsor_admin` — grants access to the sponsor-specific dashboard views.

### 2e. Existing models that can be leveraged

| Model | File | How it helps |
|-------|------|-------------|
| `MerchantCreditLedger` | `backend/app/models/extra.py:162-169` | Already has `merchant_id`, `delta_credits`, `price_cents`, `reason` (purchase/spend/refund). Could track per-session drawdowns. |
| `MerchantFeeLedger` | `backend/app/services/merchant_fee.py` | Tracks periodic fees with `status` (accruing → invoiced → paid). Could track the 20% platform fee on bundles. |
| `DriverWallet` | `backend/app/models/domain.py:129-164` | Has `nova_balance`. If sponsored sessions grant Nova to drivers, this is the target. |

---

## 3. Necessary Stripe Checkout Metadata for the $25K Transaction

### Current Stripe implementation

- **Mode:** `payment` (one-time, not subscription).
- **Packages:** `NOVA_PACKAGES` dict in `backend/app/services/stripe_service.py:17-22`:
  - `nova_100` → $100 / 1,000 Nova
  - `nova_500` → $450 / 5,000 Nova (10% discount)
  - `nova_1000` → $800 / 10,000 Nova (20% discount)
- **Webhook:** Listens for `checkout.session.completed`, then atomically grants Nova via `NovaService.grant_to_merchant()` with idempotency key.
- **Metadata sent today:** `merchant_id`, `nova_amount`, `package_id`, `payment_id`.

### What to add for the $25K bundle

**1. New package entry:**

```python
"sponsor_25k": {
    "usd_cents":       2_500_000,   # $25,000
    "nova_amount":     2_000_000,   # $20,000 net credits (after fee)
    "sessions":        4_000,       # @ $5/session
    "platform_fee_bps": 2000,       # 20%
    "bundle_type":     "25k_starter",
}
```

**2. Stripe Checkout session metadata:**

```json
{
  "merchant_id":   "<uuid>",
  "payment_id":    "<uuid>",
  "package_id":    "sponsor_25k",
  "bundle_type":   "25k_starter",
  "sessions":      "4000",
  "platform_fee_cents": "500000",
  "net_credit_cents":   "2000000"
}
```

> All values must be strings (Stripe metadata constraint). Total must stay under 1,000 characters.

**3. Webhook fulfillment additions:**

After `checkout.session.completed`:
1. Create `sponsor_credit_bundles` row (status=`active`).
2. Update `domain_merchants.sponsor_credit_balance_cents += net_session_pool`.
3. Create `NovaTransaction` with type=`sponsor_bundle_purchase`, `bundle_id` set.
4. (Optional) Send confirmation email to sponsor.

**4. Platform fee tracking:**

Current fee model (`PLATFORM_FEE_BPS = 1500`, 15%) is applied on **redemptions** (when drivers spend Nova), not on purchases. The sponsor bundle uses a different model — 20% deducted **at purchase time**.

Options:
- **Recommended:** Store `platform_fee_cents` directly on `sponsor_credit_bundles`. Fee is collected implicitly (Stripe charges $25K, Nerava keeps $5K, credits $20K to the bundle pool).
- **Alternative:** Use Stripe Connect destination charges with `application_fee_amount` for automatic split — but this requires the sponsor to have a Stripe Connected Account, which adds onboarding friction.

---

## 4. Driver Experience Gaps

### Current charging flow

```
PRE_CHARGING → browse chargers + see primary merchant
    ↓
CHARGING_ACTIVE → carousel of nearby merchants with exclusives
    ↓
Tap merchant → MerchantDetailsScreen (ExclusiveOfferCard)
    ↓
"Activate Exclusive" → ExclusiveActiveView (countdown + verification code)
    ↓
Walk to merchant → show code → "Done"
```

### What exists for "sponsored"

- `FeaturedMerchantCard.tsx:103-108` renders a small `"⚡ Sponsored"` badge (top-right corner) when `badges` array contains `"Sponsored"`.
- Mock data (`mockMerchants.ts`) has an `isSponsored` flag.
- **No special behavior, incentive copy, or credit flow** is attached to this badge.

### Gaps for "Sponsored Charging" as primary incentive

| Gap | Where | What's needed |
|-----|-------|--------------|
| **No incentive description** | API response from `/v1/intent/capture` and `/v1/merchants/{id}` | Add `sponsored_charging` object: `{ sponsor_name, incentive_copy, credit_amount_cents }`. |
| **Badge is too subtle** | `FeaturedMerchantCard.tsx` (corner badge) | Promote to hero-level treatment: full-width banner or card background change (green gradient = savings). |
| **ExclusiveOfferCard doesn't handle sponsored type** | `ExclusiveOfferCard.tsx` | Add conditional rendering: if `is_sponsored_charging`, show "Charging Powered by [Sponsor]" with distinct green/teal styling vs. amber perk styling. |
| **No credit/savings display** | `ExclusiveActiveView.tsx` | Add "Your charging is sponsored by [Name]" banner. Post-session, show credits earned. |
| **No driver wallet UI** | Entire driver app | Backend has `DriverWallet.nova_balance` but the main flow never surfaces it. Need a balance indicator (header pill or post-session summary). |
| **Pre-charge screen doesn't mention sponsorship** | `PreChargingScreen.tsx` | When a charger has a sponsor, show "Charge for free at [location] — powered by [Sponsor]". |
| **No distinct sponsored API endpoint/field** | Backend schemas | `/v1/intent/capture` returns `MerchantSummary` with `badges: string[]`. Need structured `sponsored_charging` field, not just a string badge. |

### Proposed driver-side touchpoints

1. **Charger list / map:** Sponsored chargers get a visual marker (green pin or "$0" tag).
2. **Pre-Charging screen:** Hero text: "Free charging — powered by [Sponsor Name]".
3. **FeaturedMerchantCard:** Replace subtle badge with prominent sponsored banner.
4. **MerchantDetailsScreen:** New `SponsoredChargingCard` component above `ExclusiveOfferCard`.
5. **ExclusiveActiveView:** Top banner: "Your charging is sponsored by [Name]".
6. **Post-session:** Summary card: "You saved $X.XX on this session, thanks to [Sponsor]."

---

## 5. Summary: What to Build

### Phase 1 — Data layer (backend)

- [ ] Add `merchant_type` enum to `domain_merchants` + Alembic migration.
- [ ] Create `sponsor_credit_bundles` table + model.
- [ ] Extend `NovaTransaction.type` with `sponsor_bundle_purchase` and `sponsor_session_drawdown`.
- [ ] Add `bundle_id` FK to `NovaTransaction`.
- [ ] Add `sponsor_admin` to user role flags.

### Phase 2 — Payment (backend)

- [ ] Add `sponsor_25k` (and any other tiers) to `NOVA_PACKAGES`.
- [ ] Extend `StripeService.create_checkout_session()` to accept bundle metadata.
- [ ] Extend webhook handler to create `sponsor_credit_bundles` row and credit balance on payment.
- [ ] Add `GET /v1/sponsor/bundles` and `POST /v1/sponsor/bundles/{id}/checkout` endpoints.
- [ ] Implement session drawdown service: decrement `remaining_sessions` + create `NovaTransaction` per driver session.

### Phase 3 — Merchant portal

- [ ] Read `merchant_type` and conditionally hide restaurant-only nav items (Pickup Packages, EV Arrivals Dine-In/Curbside).
- [ ] Add "Bundle Overview" dashboard card for sponsors: total credits, remaining sessions, drawdown chart.
- [ ] Rename/abstract arrival types (or hide EVArrivals page entirely for sponsors).

### Phase 4 — Driver app

- [ ] Extend `/v1/intent/capture` and `/v1/merchants/{id}` responses with `sponsored_charging` object.
- [ ] Build `SponsoredChargingCard` component (green/teal, distinct from amber ExclusiveOfferCard).
- [ ] Promote sponsored badge from corner to hero-level in `FeaturedMerchantCard`.
- [ ] Add "Sponsored by [Name]" banner to `ExclusiveActiveView`.
- [ ] Surface driver balance/savings post-session.
