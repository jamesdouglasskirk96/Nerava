# Campaign Money Flow Audit Report

**Date:** April 2, 2026
**Author:** James Kirk / Claude Code
**Status:** CRITICAL — Must fix before accepting 6-figure sponsor deposits

---

## THE BUG: Why 19 Grants Were Made Against a $1.60 Budget

### What Happened

The "New-User-Campaign" has a **$1.60 reward budget** (after 20% platform fee on a $2 deposit), **0 sessions granted** shown in the console UI, yet there are **19 grants at $0.40 each = $7.60 spent** — a 4.75x budget overrun.

### Root Cause

The incentive engine reads campaign budget state ONCE (stale ORM cache), then processes multiple sessions against it without re-checking the live database value.

**The flow that causes the overrun:**

1. `get_active_campaigns()` returns Campaign with `spent_cents=0, budget_cents=160` (stale read)
2. Session evaluation loop processes sessions sequentially
3. Each session calls `decrement_budget_atomic()` — raw SQL: `UPDATE campaigns SET spent_cents = spent_cents + :amount WHERE spent_cents + :amount <= budget_cents AND status = 'active'`
4. The raw SQL correctly increments `spent_cents` each time (0→40→80→120→160)
5. **After `spent_cents` hits 160, the WHERE clause should reject further updates — but the campaign object in memory is stale and still passes the application-level budget check**
6. The auto-pause status transition (`exhausted`) happens AFTER the grant is created, in a separate non-atomic step

**Result:** 19 grants x $0.40 = **$7.60 spent against a $1.60 budget**

### Secondary Bug: Console UI Shows Wrong Numbers

The Campaign Console shows "Sessions Granted: 0" and "Spent: $0" even though 19 grants exist. The console reads from the Campaign model's `sessions_granted` and `spent_cents` fields (ORM cache), not from a `SUM()` of the actual `incentive_grants` table. These counters drifted from reality.

---

## Code Locations

| Component | File | Lines | Issue |
|-----------|------|-------|-------|
| Stale campaign read | `app/services/incentive_engine.py` | ~55 | `CampaignService.get_active_campaigns(db)` returns cached objects |
| Budget decrement | `app/services/campaign_service.py` | 320-364 | `decrement_budget_atomic()` — SQL is correct but called from stale context |
| Auto-pause (too late) | `app/services/campaign_service.py` | 355-357 | Status set to `exhausted` AFTER grant created, not atomically |
| Campaign counters | `app/models/campaign.py` | `spent_cents`, `sessions_granted` | Counters not reconciled against actual grants |
| Console display | `apps/console` | Campaign detail page | Reads stale model fields instead of computing from grants |

---

## CRITICAL FIXES NEEDED BEFORE 6-FIGURE DEPOSITS

### Priority 1: Fix Budget Overrun (BLOCKING — Must fix before ANY real money)

| # | Issue | Fix | Effort |
|---|-------|-----|--------|
| 1 | Stale campaign read allows overspend | Add `SELECT FOR UPDATE` row lock when reading campaign for evaluation | 1 day |
| 2 | No atomic check-then-grant | Move budget check INTO the atomic decrement — if `rowcount=0`, skip grant creation entirely (never create grant first) | 1 day |
| 3 | Campaign not auto-pausing | After atomic decrement, immediately check `spent_cents >= budget_cents` and set `status='exhausted'` within same transaction | 1 day |
| 4 | `sessions_granted` / `spent_cents` drift from actual grants | Add reconciliation: compute from `SUM(incentive_grants.amount_cents)` instead of trusting the counter | 3 days |

### Priority 2: Money Flow Integrity (Required for production sponsor campaigns)

| # | Issue | Current State | Required |
|---|-------|--------------|----------|
| 5 | Budget enforcement | Soft check via raw SQL WHERE clause, bypassable under concurrent load | Hard enforcement: `SELECT FOR UPDATE` + atomic decrement + auto-pause in single transaction |
| 6 | Deposit tracking | `budget_cents` set on campaign creation, no link to Stripe payment | Must link campaign budget to a verified Stripe payment. No campaign activates until funds clear. |
| 7 | Platform fee storage | Computed client-side (console shows "Platform Fee 20%: $0.4") but not stored on Campaign model | Store `gross_deposit_cents`, `platform_fee_cents`, `net_budget_cents` separately |
| 8 | Refund flow | Does not exist | If campaign pauses with remaining budget, sponsor needs refund mechanism |
| 9 | Audit trail | No ledger for sponsor deposits | Create `CampaignLedger` table: deposit, fee, grant, refund entries (mirrors wallet_ledger pattern) |
| 10 | Max grant per session | `cost_per_session_cents` is trusted without cap | Add `max_grant_cents` field — no single grant can exceed this regardless of cost_per_session |

### Priority 3: Campaign Referral System (Required for Trident deal structure)

From the Trident partnership proposal — Nerava offers 5-10% referral fees on revenue from buyers partners introduce.

| # | Capability | Current State | Required |
|---|------------|--------------|----------|
| 11 | Driver referral | Exists: $5 credit via referral code (`referral_codes` table) | Works, keep as-is |
| 12 | Partner/buyer referral | Does not exist | New `PartnerReferral` model: tracks which partner introduced which buyer, computes perpetual revenue share |
| 13 | Revenue share calculation | Does not exist | Track all revenue from a referred buyer, compute 5% (standard) or 10% (enhanced year 1) share |
| 14 | Referral attribution | Does not exist | When a campaign is created, tag it with `referred_by_partner_id`. All grants from that campaign attribute revenue to the referrer. |
| 15 | Referral payout | Does not exist | Monthly computation of referral fees, visible in partner dashboard |

---

## Correct Money Flow (How It Should Work)

### Sponsor Deposits a Campaign Budget

```
Sponsor deposits $10,000 via Stripe
  → Stripe payment intent confirmed
  → Campaign created with:
      gross_deposit_cents = 1_000_000
      platform_fee_cents  =   200_000  (20%)
      net_budget_cents     =   800_000  (available for driver rewards)
      spent_cents          =         0
      status               = "active"
  → CampaignLedger entry: type="deposit", amount=1_000_000
  → CampaignLedger entry: type="platform_fee", amount=-200_000
```

### Session Triggers Grant

```
Driver charges at eligible charger
  → IncentiveEngine.evaluate_session()
  → SELECT campaign FOR UPDATE WHERE status='active' AND spent + cost <= budget
  → If found:
      UPDATE campaigns SET spent_cents = spent_cents + cost WHERE ...
      → If rowcount == 0: SKIP (budget exhausted, race condition caught)
      → If rowcount == 1:
          Create IncentiveGrant
          Credit driver wallet
          CampaignLedger entry: type="grant", amount=-cost, grant_id=X
  → If spent >= budget:
      UPDATE campaigns SET status='exhausted' (same transaction)
```

### Campaign Exhausted / Paused

```
Budget runs out OR sponsor pauses
  → status → "exhausted" or "paused"
  → No more grants created
  → Remaining budget visible to sponsor
  → Sponsor can request refund of remaining balance
```

### Refund Flow (Not Yet Built)

```
Sponsor requests refund of remaining budget
  → remaining = net_budget_cents - spent_cents
  → Stripe refund for: remaining + (remaining * platform_fee_rate) [optional: refund fee too]
  → CampaignLedger entry: type="refund", amount=remaining
  → Campaign status → "refunded"
```

---

## Database Schema Changes Needed

### New: `campaign_ledger` Table

```sql
CREATE TABLE campaign_ledger (
    id UUID PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES campaigns(id),
    entry_type VARCHAR(30) NOT NULL,  -- deposit, platform_fee, grant, refund
    amount_cents INTEGER NOT NULL,     -- positive for deposits, negative for fees/grants/refunds
    balance_after_cents INTEGER NOT NULL,
    reference_type VARCHAR(30),        -- stripe_payment, incentive_grant, stripe_refund
    reference_id VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP NOT NULL
);
```

### New Columns on `campaigns` Table

```sql
ALTER TABLE campaigns ADD COLUMN gross_deposit_cents INTEGER DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN platform_fee_cents INTEGER DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN net_budget_cents INTEGER DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN max_grant_cents INTEGER;
ALTER TABLE campaigns ADD COLUMN referred_by_partner_id UUID REFERENCES partners(id);
ALTER TABLE campaigns ADD COLUMN stripe_payment_intent_id VARCHAR(255);
```

### New: `partner_referrals` Table

```sql
CREATE TABLE partner_referrals (
    id UUID PRIMARY KEY,
    partner_id UUID NOT NULL REFERENCES partners(id),
    referred_entity_type VARCHAR(30) NOT NULL,  -- campaign, merchant, sponsor
    referred_entity_id UUID NOT NULL,
    referral_rate_bps INTEGER NOT NULL DEFAULT 500,  -- 500 = 5%
    enhanced_rate_bps INTEGER,  -- 1000 = 10% for year 1
    enhanced_rate_expires_at TIMESTAMP,
    total_revenue_attributed_cents INTEGER DEFAULT 0,
    total_referral_paid_cents INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

---

## Recommended Build Order

### Week 1: Budget Safety (MUST complete before any real deposit)
- Fix #1: `SELECT FOR UPDATE` on campaign read
- Fix #2: Atomic check-then-grant (no grant if decrement fails)
- Fix #3: Auto-pause in same transaction
- Fix #6: Link campaign activation to Stripe payment confirmation
- Fix #7: Store gross/fee/net separately

### Week 2: Audit Trail
- Fix #4: Reconciliation of counters vs actual grants
- Fix #9: Campaign ledger table
- Fix #5: Hard budget enforcement end-to-end test suite

### Week 3: Referral System
- Fix #12-15: Partner referral tracking, attribution, revenue share computation

### Week 4: Refund + Polish
- Fix #8: Refund flow
- Fix #10: Max grant cap
- Campaign reconciliation dashboard in admin portal

---

## Test Cases to Validate Fix

1. **Budget exhaustion**: Create campaign with $1 budget, $0.40/session. After 2 grants ($0.80), third session should NOT create a grant.
2. **Concurrent evaluation**: Submit 10 sessions simultaneously against a $2 budget. Total grants should never exceed $2.
3. **Auto-pause**: Campaign should transition to `exhausted` immediately when last grant depletes budget.
4. **Console accuracy**: Console should show correct spent/remaining by querying actual grants, not cached counters.
5. **Deposit verification**: Campaign should not activate until Stripe payment intent succeeds.
6. **Refund**: Paused campaign with remaining budget should allow refund.
