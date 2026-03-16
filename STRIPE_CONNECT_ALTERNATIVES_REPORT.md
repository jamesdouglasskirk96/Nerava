# Stripe Connect Alternatives for Nerava Driver Payouts

## Current State: Nerava's Stripe Connect Express Implementation

The current payout system uses:

- **Express accounts** created per driver with `transfers` capability
- **Stripe Transfer** from Nerava's platform account to the driver's Express connected account
- **Webhook-driven** lifecycle: `transfer.paid` confirms completion, `transfer.failed` triggers fund reversal
- **Business rules**: $20 minimum withdrawal, 3/day max, $1,000/week cap, 20% platform fee (2000 BPS)
- **Double-entry ledger** via `WalletLedger` model tracks every credit/debit
- **Idempotency** via unique keys on `Payout.idempotency_key`

The `Payout` model is tightly coupled to Stripe with `stripe_transfer_id` and `stripe_payout_id` columns, meaning any migration requires schema changes or an adapter layer.

---

## 1. Stripe Connect Express (Current)

**What it is:** Stripe's marketplace payment infrastructure. Each driver gets an Express connected account. Nerava transfers funds to the connected account, which Stripe then pays out to the driver's bank/debit card.

**Pricing:**
- **Per payout to connected account:** 0.25% + $0.25
- **Active account fee:** $2.00/month per Express account with payout activity
- **Instant payouts (to debit card):** 1% of amount (min $0.50, max $9,999)
- **Standard payouts (to bank):** Free once funds are in the connected account (T+2 business days)
- **1099 tax filing:** $2.99 per IRS e-file, $1.49 per state e-file, $2.99 per mail
- **No charge:** Transfers between platform and connected accounts

**Cost at scale (10K drivers, avg $30 payout, ~25K payouts/month):**
- Transfer fees: 25K x ($0.25 + 0.25% of $30) = 25K x $0.325 = ~$8,125/mo
- Active account fees: 10K x $2 = $20,000/mo
- **Total: ~$28,125/month ($337,500/year)**

**Cost at 100K drivers (~250K payouts/month):**
- Transfer fees: ~$81,250/mo
- Active account fees: ~$200,000/mo
- **Total: ~$281,250/month ($3.375M/year)**

**Driver onboarding friction:** MEDIUM-HIGH
- Drivers are redirected to Stripe's hosted onboarding page
- Must provide: legal name, date of birth, last 4 SSN (full SSN may be required later), home address, bank account or debit card
- Takes 3-5 minutes; some drivers may be asked for government-issued ID
- Stripe handles all KYC/identity verification

**Payout speed:**
- Standard: 2 business days
- Instant (to debit card): minutes, but costs 1%

**1099 compliance:** EXCELLENT — Stripe auto-generates 1099s, handles e-filing with IRS/states, e-delivery to connected accounts. You opt in via Dashboard. $2.99/form for federal, $1.49/form for state.

**API quality:** Best-in-class. Excellent documentation, SDKs for every language, webhooks, idempotency keys, test mode.

**Pros:**
- Already integrated (zero migration cost)
- Mature, battle-tested platform
- Built-in KYC, 1099, and fraud prevention
- Instant payout option exists
- Excellent developer experience

**Cons:**
- $2/month per active account is extremely expensive at scale (this is the dominant cost driver)
- Onboarding friction loses drivers (they see "Stripe" branding, not Nerava)
- Express accounts are semi-opaque — limited control over the driver experience
- Drivers who don't complete onboarding can't withdraw

**Key risk:** The $2/month per active account fee scales linearly and will dominate costs. At 100K drivers, that's $200K/month just in account fees before any transactions.

---

## 2. PayPal Payouts / Hyperwallet (Enterprise Payouts)

**What it is:** PayPal's mass payout API sends funds to PayPal accounts, Venmo, bank accounts, or debit cards. Hyperwallet (now "Enterprise Payouts") is PayPal's white-label payout infrastructure for enterprise-scale disbursements.

**Pricing:**
- **PayPal Payouts API (domestic, to PayPal wallet):** $0.25 flat per payment
- **PayPal Payouts API (international):** 2% of amount, max $20 cap
- **Hyperwallet/Enterprise Payouts:** ~1-2% for bank transfers (custom negotiated)
- **No monthly per-account fee** (critical difference from Stripe)
- **Recipient pays no fee** on PayPal Payouts

**Cost at scale (10K drivers, avg $30, ~25K payouts/month):**
- PayPal Payouts: 25K x $0.25 = $6,250/mo
- **No active account fee**
- **Total: ~$6,250/month ($75,000/year)**

**Cost at 100K drivers:**
- **Total: ~$62,500/month ($750,000/year)** — 78% cheaper than Stripe

**Driver onboarding friction:** LOW
- If paying to PayPal: driver just provides their PayPal email. No additional KYC by Nerava.
- If paying to bank via Hyperwallet: driver must create a Hyperwallet account, provide bank details. More friction.
- Venmo payout: driver provides Venmo handle.

**Payout speed:**
- To PayPal wallet: instant
- To bank from PayPal: 1-3 business days
- Hyperwallet direct to bank: 1-3 business days

**1099 compliance:** POOR-MEDIUM. PayPal issues 1099-K for payments above thresholds going through their payment network, but for Payouts API specifically, the platform (Nerava) is responsible for 1099 filing. You would need a separate tax filing solution.

**Pros:**
- No per-account monthly fee (massive savings at scale)
- Low per-transaction cost ($0.25 flat)
- Most US consumers already have PayPal/Venmo (low friction)
- Batch payouts simplify operations
- Instant delivery to PayPal wallet

**Cons:**
- 1099 filing not included; you need a third-party solution
- Drivers without PayPal must create an account
- No RTP/FedNow for instant bank delivery

**Key risk:** 1099 compliance gap is the biggest concern. At the $600 threshold, nearly every active driver will need a 1099.

---

## 3. Dwolla (ACH-Focused)

**What it is:** API-first ACH payment platform. Excellent for programmatic bank-to-bank transfers. Supports Standard ACH, Same Day ACH, and real-time payments via push-to-debit.

**Pricing:**
- **Start Plan (pay-as-you-go):** 0.5% per transaction (min $0.05, max $5.00), no monthly fee
- **Scale Plan:** Starts at $1,000/month, custom per-transaction pricing (typically $0.10-$0.25 per ACH)
- **Custom Plan:** $2,000+/month, negotiated rates
- **Same Day ACH:** Additional fee (typically $0.50-$1.00 on top)

**Cost at scale (10K drivers, avg $30, ~25K payouts/month):**
- Start Plan: 25K x min($5.00, 0.5% of $30) = 25K x $0.15 = $3,750/mo
- Scale Plan: $1,000/mo base + 25K x $0.15 = ~$4,750/mo
- **Total: ~$3,750-$4,750/month ($45,000-$57,000/year)**

**Cost at 100K drivers (~250K payouts/month):**
- Negotiated rates likely $0.10-$0.15/txn: 250K x $0.12 = $30,000 + $2,000 base = ~$32,000/mo
- **Total: ~$32,000/month ($384,000/year)** — 89% cheaper than Stripe

**Driver onboarding friction:** MEDIUM
- Drivers must provide bank account and routing number
- Dwolla supports Plaid for instant bank verification (better UX) or micro-deposit verification (2-3 days)
- White-labeled — drivers see Nerava branding, not Dwolla
- KYC handled by Dwolla via their "Verified Customer" flow (name, DOB, last 4 SSN, address)

**Payout speed:**
- Standard ACH: 3-4 business days
- Same Day ACH: Same business day (cutoff ~2pm ET)
- Push-to-debit: Near-instant (if supported by driver's bank)

**1099 compliance:** NONE built in. Dwolla is purely a payment rail. You must handle all tax reporting separately.

**Pros:**
- Cheapest per-transaction costs at scale
- No per-account monthly fees
- White-labeled (Nerava-branded experience)
- Multiple speed tiers (standard, same-day, real-time)
- Plaid integration for smooth bank linking

**Cons:**
- Zero tax/1099 support
- ACH returns need robust handling
- No PayPal/Venmo payout option
- US only
- Standard ACH is slow (3-4 days)

**Key risk:** ACH returns require robust handling. No 1099 support means pairing with another vendor.

---

## 4. Square Payouts

**What it is:** Square's payout API for transferring funds to sellers/recipients. Already relevant because Nerava uses Square for merchant POS integration.

**Pricing:**
- **Standard transfer (next business day):** Free
- **ACH bank transfer via API:** 1% per transfer ($1 min, $5 cap)
- **Instant transfer (to debit card):** 1.5-1.95% per transfer

**Cost at scale (10K drivers, avg $30, ~25K payouts/month):**
- ACH: 25K x min($5.00, 1% of $30) = 25K x $1.00 = $25,000/mo
- **Total: ~$25,000/month ($300,000/year)**

**Driver onboarding friction:** MEDIUM-HIGH. Drivers would need a Square account. Square's API is designed for merchants, not gig workers.

**1099 compliance:** LIMITED. Square issues 1099-K for merchants on their platform, but tax responsibility falls on Nerava for driver disbursements.

**Verdict:** Not designed for mass consumer payouts. The $1 minimum per ACH is expensive for small payouts. **Not recommended** unless consolidating to Square for other reasons.

---

## 5. Marqeta / Visa Direct / Mastercard Send (Push-to-Card)

**What it is:** Push funds directly to a driver's existing debit card in real-time via Visa Direct or Mastercard Send networks. Marqeta can also issue Nerava-branded debit cards with instant load.

**Pricing (Visa Direct via processor):**
- **Per transaction:** $0.25-$1.00 per push (negotiated)
- **Visa Direct network fee:** ~$0.01-$0.05 per OCT
- **Processor markup:** $0.25-$0.75 per transaction

**Pricing (Marqeta card issuing):**
- **Platform fee:** Custom ($10K-$50K+/month minimum commitment)
- **Per-card issuance:** $0.50-$3.00 per physical card
- **Revenue opportunity:** Interchange revenue sharing when drivers spend on their Nerava-branded card

**Cost at scale (10K drivers, Visa Direct only):**
- 25K x $0.50 (estimated all-in) = $12,500/mo
- **Total: ~$12,500/month ($150,000/year)**

**Driver onboarding friction:** VERY LOW (Visa Direct — just a debit card number) / LOW (Marqeta virtual card)

**Payout speed:** Real-time. Funds available in seconds.

**1099 compliance:** NONE. Must pair with tax vendor.

**Pros:**
- Best-in-class speed (real-time)
- Lowest driver friction
- Marqeta card creates branded experience + interchange revenue

**Cons:**
- Visa Direct requires licensed processor
- Marqeta has high minimum commitments (not viable at <10K drivers)
- No 1099 support

---

## 6. Tremendous

**What it is:** Rewards and payouts platform. Recipients choose how to receive funds: gift cards, prepaid Visa, PayPal, Venmo, Cash App, bank transfer, or 2,000+ brand gift cards.

**Pricing:**
- **Gift cards, prepaid cards:** FREE (Tremendous earns from brand partnerships)
- **Monetary options (PayPal, Venmo, Cash App, ACH, instant debit):** 4% added to order total (sender pays) OR 6% deducted from recipient (min $1.00, max $25.00)
- **No monthly platform fee**

**Cost at scale (10K drivers, avg $30, ~25K payouts/month, sender-pays):**
- Monetary (70% of payouts): 17.5K x 4% x $30 = $21,000/mo
- Gift cards (30%): $0
- **Total: ~$21,000/month ($252,000/year)**

**Driver onboarding friction:** VERY LOW. Tremendous sends a "claim link" — driver clicks and chooses payout method.

**1099 compliance:** GOOD. Automates W-9 collection and helps with 1099 preparation.

**Pros:**
- Zero platform cost for gift cards
- Recipient choice model (drivers pick how they want to be paid)
- Lowest engineering effort to integrate
- Aligns with Nerava's rewards semantics

**Cons:**
- 4-6% fee on monetary payouts is expensive
- Less "professional" than direct bank deposit
- Tremendous-branded claim flow

---

## 7. Trolley (formerly PaymentRails)

**What it is:** Mass payout platform purpose-built for internet economy payouts with first-class 1099/1042-S tax compliance.

**Pricing:**
- **Starter Plan:** $49/month
- **Growth/Scale:** Custom pricing
- **Per-payment fees:** ~$0.25-$1.00 for domestic ACH (estimated)
- **1099 filing:** Included in platform

**Cost at scale (10K drivers, avg $30, ~25K payouts/month):**
- Platform: $49-$500/mo
- ACH: 25K x $0.50 = $12,500/mo
- Tax filing: 10K x $3 = $30,000/year ($2,500/mo)
- **Total: ~$15,000/month ($180,000/year)**

**Driver onboarding friction:** LOW-MEDIUM. White-labeled tax form collection (W-9). Requires name, address, SSN/TIN.

**1099 compliance:** BEST-IN-CLASS. Automated W-9/W-8BEN collection, TIN validation, auto-generates and e-files 1099s with IRS and states.

**Cons:**
- No instant/real-time payouts
- Opaque pricing
- ACH-only for domestic speed

---

## 8. BaaS Platforms: Unit / Treasury Prime

**What it is:** Banking-as-a-Service platforms that let you embed FDIC-insured bank accounts and debit cards directly into Nerava.

**Pricing (Unit):**
- **Platform fee:** $5K-$25K+/month (scaling with features)
- **Per-account:** ~$0.10-$1.00/month
- **ACH transfers:** ~$0.10-$0.25 per transaction
- **Revenue share:** Interchange from card transactions

**Cost at 100K drivers:**
- Gross: ~$70,000-$100,000/month
- Net (after interchange offset): Could approach break-even or profitability

**Payout speed:** INSTANT within system (ledger entry), 1-3 days for external ACH

**1099 compliance:** PARTIAL. You still handle 1099 for reward payouts.

**Key consideration:** This is a 6-12 month build and a major strategic investment. Only consider if Nerava's roadmap includes becoming a financial product for EV drivers.

---

## 9. Dots (Emerging Contender)

**What it is:** Modern payouts infrastructure purpose-built for marketplaces and gig platforms. Combines instant payouts, 1099 compliance, and global coverage.

**Pricing:**
- **Core Plan:** $19/month + $2/domestic ACH, 3.9%+$2 international
- **Scale Plan:** $999/month + $1/domestic ACH, 2.9%+$1 international
- **Instant payouts:** Included (uses RTP/FedNow)
- **1099 filing:** $3.50-$5.00 per form

**Cost at scale (10K drivers, Scale Plan):**
- Platform: $999/mo
- ACH: 25K x $1.00 = $25,000/mo
- 1099: $2,917/mo
- **Total: ~$28,916/month ($347,000/year)**

**Why it matters:** Only platform combining instant payouts (via RTP/FedNow) with built-in 1099 compliance.

---

## Recommendation Matrix

| Criterion | Stripe (Current) | PayPal | Dwolla | Visa Direct | Tremendous | Trolley | BaaS (Unit) | Dots |
|---|---|---|---|---|---|---|---|---|
| **Cost at 10K drivers/mo** | $28K | $6K | $4-5K | $12-30K | $21K | ~$15K | $15-20K | $29K |
| **Cost at 100K drivers/mo** | $281K | $63K | $32K | $125K | $210K | ~$150K | $70-100K | ~$260K |
| **Driver UX friction** | Med-High | Low | Medium | Very Low | Very Low | Low-Med | Medium | Low |
| **Payout speed** | 2 days (instant @1%) | Instant to PayPal | 3-4 days | Real-time | Near-instant | 2-4 days | Instant (in-app) | Instant (RTP) |
| **1099 compliance** | Excellent | Poor | None | None | Good | Best | Partial | Good |
| **Engineering effort** | Zero (done) | 2-4 weeks | 4-8 weeks | 6-12 weeks | 1-2 weeks | 4-6 weeks | 6-12 months | 4-6 weeks |

---

## Recommended Strategy by Stage

### Near-term (0-6 months, <10K drivers): Stay with Stripe Connect
The $2/account/month cost is not yet material. Stripe's 1099 compliance, instant payouts, and proven reliability are worth the premium. Zero migration risk.

**Estimated cost at 1K drivers: ~$3K/month**

### Medium-term (6-18 months, 10K-50K drivers): Migrate to Dwolla + Trolley (or Dots)

**Option A — Dwolla + Trolley:**
- Dwolla handles ACH payouts at $0.10-$0.25/txn
- Trolley handles W-9 collection and 1099 filing
- **Estimated: $5K-$15K/month at 10K drivers (70-80% savings vs Stripe)**

**Option B — Dots (all-in-one):**
- Single vendor for ACH, instant payouts (RTP/FedNow), and 1099
- **Estimated: $26K-$29K/month at 10K drivers**
- Simpler integration, newer company

**Option C — PayPal Payouts:**
- $0.25/payment with instant to PayPal wallets
- **Estimated: $6K/month at 10K drivers (cheapest)**
- Must handle 1099 separately

### Long-term (18+ months, 50K+ drivers): Evaluate BaaS (Unit)
If Nerava's vision includes becoming a financial platform for EV drivers, a BaaS integration creates a competitive moat and interchange revenue. At 100K+ drivers, interchange can offset costs entirely.

---

## Migration Considerations from Current Codebase

1. **Database schema:** `Payout` model has Stripe-specific columns. Add generic `external_transfer_id` and `payout_provider` column.
2. **Service abstraction:** `PayoutService` directly calls Stripe. Introduce a `PayoutProvider` interface.
3. **Webhook refactoring:** Current handler is Stripe-specific. Each provider needs its own webhook handler.
4. **Driver onboarding:** `WalletModal.tsx` has Stripe Account Link flow. New provider needs equivalent UX.
5. **Gradual migration:** Use feature flag to route new drivers to new provider while keeping existing Stripe accounts active. Dual-run for 3-6 months.

---

## Sources

- [Stripe Connect Pricing](https://stripe.com/connect/pricing)
- [Stripe Connect 1099](https://stripe.com/connect/1099)
- [PayPal Payouts Fees](https://developer.paypal.com/docs/payouts/standard/reference/fees/)
- [Dwolla Pricing](https://www.dwolla.com/pricing)
- [Tremendous Pricing](https://www.tremendous.com/pricing/)
- [Trolley Pricing](https://trolley.com/trolley-pricing/)
- [Marqeta Platform](https://www.marqeta.com/)
- [Unit Embedded Finance](https://www.unit.co/)
- [Dots Pricing](https://usedots.com/pricing/)

---

*Report generated March 2, 2026*
