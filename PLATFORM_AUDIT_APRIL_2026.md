# Nerava Platform Audit — April 2, 2026

**Audited by:** Claude Code with direct production DB access
**Production DB stats as of audit:**
- 80,330 chargers | 215,403 merchants | 798,789 charger-merchant links
- 32 users | 94 sessions | 20 grants | 20 wallets | 15 payouts
- 10 Tesla connections | 6 device tokens (iOS only, 5 active)

---

## SECTION 1: Campaign Money Flow Audit (Updated with DB Evidence)

### The Bug — Confirmed with Production Data

**Campaign:** New-User-Campaign (ID: `004a944e-...`)
- `budget_cents = 160` ($1.60)
- `spent_cents = 0` (counter never incremented — **stale**)
- `sessions_granted = 0` (counter never incremented — **stale**)
- **Actual grants in `incentive_grants` table: 20 grants, totaling 800 cents ($8.00)**
- **Budget overrun: 5x** ($8.00 granted against $1.60 budget)

### Root Causes (Confirmed)

1. **`spent_cents` field never updates.** All 10 campaigns show `spent_cents = 0` regardless of actual grants. The `decrement_budget_atomic()` function's raw SQL UPDATE may be failing silently, or the ORM cache is never flushed.

2. **`sessions_granted` field never updates.** Same issue — the counter stays at 0 while 20 grants were actually created.

3. **No budget exhaustion.** The campaign is still `status = 'active'` despite being 5x over budget. The auto-pause logic depends on `spent_cents >= budget_cents` which never triggers because `spent_cents` stays at 0.

### Wallet Impact (Driver 3 — James)

| Source | Value |
|--------|-------|
| Wallet `balance_cents` | 270 |
| Wallet `total_earned_cents` | 520 |
| Wallet `total_withdrawn_cents` | 0 |
| Ledger `SUM(amount_cents)` | -1,449 |

**Discrepancy:** Ledger sum is -1,449 cents but wallet shows 270 balance. The ledger includes withdrawal debits + fee debits that failed (Stripe insufficient funds) but the balance was restored incorrectly (the fee-loss bug we fixed earlier). The `total_withdrawn_cents = 0` despite 15 payout attempts confirms payouts are all failing/processing.

### Payout Issues (Driver 3)

| Count | Status |
|-------|--------|
| 1 | `processing` (stuck since 3/27) |
| 14 | `failed` (all "Insufficient funds in Stripe account") |

The `processing` payout from 3/27 has been stuck for 6 days. It should be reconciled — either mark as failed and restore balance, or check if Stripe actually processed it.

### All Campaigns in DB

| Name | Status | Budget | Spent (field) | Actual Grants | Actual Spent | Issue |
|------|--------|--------|---------------|---------------|-------------|-------|
| New-User-Campaign | active | $1.60 | $0 | 20 | $8.00 | **5x OVERRUN** |
| Nerava-Dev-Campaign (x2) | draft | $10,000 | $0 | 0 | $0 | Duplicate |
| Q2 EVject Birthday | draft | $10,000 | $0 | 0 | $0 | OK |
| EVject birthday | draft | $10,000 | $0 | 0 | $0 | Duplicate of above? |
| (unnamed) | draft | $10,000 | $0 | 0 | $0 | No name |
| Daniel-Test | draft | $5.00 | $0 | 0 | $0 | Test data |
| Miami Charge Party | draft | $100 | $0 | 0 | $0 | OK |
| Nerava-New-User-Campaign | paused | $5.00 | $0 | 0 | $0 | OK |
| Asadas Grill | draft | $100 | $0 | 0 | $0 | OK |

**Action items:**
1. **CRITICAL:** Fix `spent_cents` counter — it never increments. Debug `decrement_budget_atomic()`.
2. **CRITICAL:** Add hard budget enforcement — `SELECT FOR UPDATE` before grant creation.
3. **CLEANUP:** Delete duplicate/test campaigns (Daniel-Test, unnamed, duplicate Dev/EVject).
4. **CLEANUP:** Pause New-User-Campaign immediately (it's 5x over budget and still active).
5. **RECONCILE:** Mark stuck `processing` payout as failed and restore balance.

---

## SECTION 2: Driver App Feature Audit

### Features to REMOVE Before Production

| Feature | Location | Issue |
|---------|----------|-------|
| **Test Push Notification button** | `AccountPage.tsx` lines 717-746 | Visible to ALL users. Orange button that leaks diagnostic info (device count, APNs status). Must remove. |
| **Demo mode toggle** | `?demo=1` URL param | Gated but shouldn't be in production builds. Strip in build process or remove entirely. |

### Features That Work Correctly

| Feature | Status | Notes |
|---------|--------|-------|
| Favorites (merchants + chargers) | WORKS | Syncs with backend, navigation works |
| Search bar | WORKS | Falls back to Austin TX when no location |
| Share button (ExclusiveActiveView) | WORKS | Web Share API + clipboard fallback |
| Session history | WORKS | Shows up to 50 sessions |
| Wallet withdrawal | WORKS | Proper Stripe onboarding flow |
| Account deletion | WORKS | Confirmation dialog + backend call |
| Profile editing (name/email) | WORKS | Saves to backend |
| Earnings screen | WORKS | Full transaction ledger |
| SessionExpiredModal | WORKS | Triggers on 401 |
| EV Code overlay | WORKS | Shows verification code |
| Referral codes | WORKS | QR code, share link, $5 credit |
| Mock Charging toggle | WORKS | Properly gated to test user (6318 only) |

### Features NOT IMPLEMENTED

| Feature | Expected | Actual |
|---------|----------|--------|
| **Vehicle Promos tab (EVject cards)** | Two EVject product cards with discount links on Vehicle page Promos tab | Tab/cards don't exist in code. The screenshots from earlier showing EVject promos were from the Chargeway app, not Nerava. |
| **Real-time charger availability in UI** | Show available/occupied on charger cards | Backend has TomTom + Google Places data but frontend doesn't display it |
| **Dynamic pricing on charger cards** | Show $/kWh from Tesla/NREL | Backend has data but frontend shows static pricing |
| **EVject discount in charger detail** | Contextual adapter promo on non-Tesla chargers | Not implemented |

---

## SECTION 3: Data Integrity Issues

### Stale/Zombie Sessions

| Driver | Session Start | Duration | kWh | Issue |
|--------|-------------|----------|-----|-------|
| 25 | 2026-03-14 | Never ended | 5.9 | Zombie — 19 days without end |
| 19 | 2026-03-08 | Never ended | 0.9 | Zombie — 25 days without end |

**Action:** Force-close these sessions via admin endpoint.

### Anomalous Sessions

| Duration | kWh | Quality | Issue |
|----------|-----|---------|-------|
| 3,839 min (2.7 days) | 17.64 | 100 | Session lasted 2.7 days — likely stale cleanup missed it |
| 3,988 min (2.8 days) | 9.02 | 100 | Same issue — multi-day "session" |
| 2,687 min (1.9 days) | 40.64 | 100 | Your recent session 3/31-4/2 |
| 1,328 min (22 hrs) | 37.0 | 100 | Unusually long |

**Quality score of 100 on multi-day sessions is wrong.** The quality scoring algorithm should penalize sessions longer than ~2 hours (most charging sessions are 20-60 min). A 2.7-day "session" with 17 kWh is clearly a stale cleanup failure, not a real charging session.

### Duplicate Verification Codes

Verified visits table shows codes with random suffixes (`ATX-THEHEI-002-86`, `ATX-THEHEI-001-66`) from the duplicate code bug we fixed. These should be cleaned up.

### Tesla Connection Anomalies

- Users 22 and 23 have Tesla connections with `vehicle_id = None` and `vin = None` — failed OAuth flows that weren't cleaned up
- Users 3 and 4 share the same `vehicle_id` (`374458273718615`) — this is your Tesla connected to two accounts

---

## SECTION 4: Admin Portal Gaps (What to Add)

Based on the DB audit, these are the most impactful additions:

### P0 — Must Have

| Feature | Why | Effort |
|---------|-----|--------|
| **Campaign budget reconciliation** | Show actual grants vs budget field. Alert on discrepancies. The `spent_cents=0` bug proves we can't trust the counter. | 2 days |
| **Payout monitoring page** | 14 failed payouts, 1 stuck in processing. Need visibility. | 2 days |
| **Session anomaly detector** | Flag sessions >4 hours, quality=100 on long sessions, zombie sessions with no end | 1 day |
| **User detail page** | Click a user to see their sessions, wallet, Tesla connection, payouts, grants | 3 days |
| **Force-close session button** | Close zombie sessions from admin | 1 day |

### P1 — Should Have

| Feature | Why | Effort |
|---------|-----|--------|
| **Tesla connection health** | Show which connections have valid tokens, which need re-auth, which have null vehicle_id | 2 days |
| **Wallet reconciliation** | Compare `balance_cents` vs `SUM(ledger)` for every wallet. Flag mismatches. | 2 days |
| **Campaign cleanup tools** | Delete/archive test campaigns, duplicate campaigns | 1 day |
| **Device token dashboard** | Only 6 tokens (all iOS). Need to know who has push enabled. | 1 day |
| **Charger coverage map** | Heatmap of charger density by state/region | 2 days |
| **Merchant coverage stats** | What % of chargers have merchants linked? By state? | 1 day |

### P2 — Nice to Have

| Feature | Why | Effort |
|---------|-----|--------|
| **Internal analytics (replace PostHog)** | Retention cohorts, funnels, acquisition source | 2 weeks |
| **Charger availability dashboard** | Show TomTom polling data, occupancy heatmaps | 3 days |
| **Partner management UI** | Frontend for existing backend partner API | 3 days |

---

## SECTION 5: Production Health Summary

### What's Healthy
- 80K chargers seeded across all 50 states
- 215K merchants with 799K links (and growing — seed running)
- Session detection working (94 real sessions)
- Wallet credits working (20 grants delivered)
- Stripe Express onboarding working (3 users completed)
- Push notifications working (5 active iOS tokens)
- Tesla OAuth working (10 connections, 6 with valid vehicle IDs)
- Referral system working (codes generated)

### What's Broken
- **Campaign budget enforcement** — `spent_cents` never updates, no auto-pause
- **Payouts** — 14/15 failed (Stripe platform balance empty), 1 stuck in processing
- **Session quality scoring** — gives 100 to multi-day sessions
- **Stale session cleanup** — 2 zombie sessions open for 19-25 days
- **Nova balance** — all drivers show `nova_balance = 0` despite earning grants

### What's Missing
- No Android users (0 Android device tokens — Play Store still rejecting)
- No real-time availability in driver app UI
- No dynamic pricing display
- Vehicle Promos tab not implemented
- No campaign deposit verification via Stripe
- No campaign refund flow
- No partner referral tracking for Trident deal

---

## SECTION 6: Recommended Priority Actions

### This Week
1. **Fix campaign `spent_cents` counter** — debug why `decrement_budget_atomic()` isn't updating
2. **Pause New-User-Campaign** — it's 5x over budget
3. **Close zombie sessions** — force-end the 2 sessions open for 19+ days
4. **Remove Test Push button** — before any more users sign up
5. **Reconcile stuck payout** — the `processing` payout from 3/27
6. **Get Android approved** — submit v1.0.4 with the Playwright-verified fix

### Next Week
7. **Add hard budget enforcement** — `SELECT FOR UPDATE` + atomic grant
8. **Build payout monitoring in admin**
9. **Build user detail page in admin**
10. **Fix session quality scoring** for multi-day sessions

### This Month
11. **Campaign ledger table** — every money event tracked
12. **Wallet reconciliation** — automated balance vs ledger check
13. **Partner referral tracking** — for Trident deal
14. **Internal analytics dashboard** — replace PostHog dependency
