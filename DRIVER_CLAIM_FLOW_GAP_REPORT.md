# Driver Claim Flow — Gap Report & Implementation Plan

**Date:** 2026-03-17
**Status:** Planning (no code changes yet)
**Goal:** Add merchant offer claiming to the driver app flow, "Request to Join" for non-incentive merchants, and "Claim Reward" CTA for incentive merchants.

---

## Executive Summary

The driver app needs two new behaviors on the Amenities/WhileYouCharge tab:

1. **Merchants WITHOUT an incentive** → Show "Request to Join" badge/CTA
2. **Merchants WITH an incentive** → Show "Claim Reward" CTA alongside "Get Directions"

Much of the backend already exists (`/v1/rewards/claim`, `/v1/merchants/{placeId}/request-join`). The main gaps are in the driver app UI components that don't yet surface these CTAs in the right places.

---

## Current State

### What Exists Today

| Layer | Component | Status |
|-------|-----------|--------|
| **Backend** | `POST /v1/rewards/claim` | Exists in `merchant_rewards.py` — creates 2-hour claim window |
| **Backend** | `POST /v1/merchants/{placeId}/request-join` | Exists — stores driver interest tags + demand signal |
| **Backend** | `GET /v1/merchants/{placeId}/request-join/count` | Exists — returns request count + user_has_requested |
| **Backend** | `POST /v1/rewards/claims/{id}/receipt` | Exists — receipt upload + Taggun OCR |
| **Backend** | `reward_state` in merchant details response | Exists — `has_active_reward`, `join_request_count`, `user_has_requested`, `active_claim_*` |
| **Driver App** | `MerchantDetailsScreen.tsx` | Has "Claim Reward" sheet, "Request to Join" sheet, receipt upload — **but only on full detail screen** |
| **Driver App** | `MerchantDetailModal.tsx` | Only has "Get Directions" + "Activate Session" CTAs — **no claim or request buttons** |
| **Driver App** | `MerchantCarousel.tsx` | Shows "Exclusive" badge — **no "Request to Join" indicator for non-incentive merchants** |
| **Driver App** | `WhileYouChargeScreen.tsx` | Featured + secondary cards — **no claim/request CTAs** |
| **Driver App** | `api.ts` | Has `claimReward()`, `requestToJoin()`, `uploadReceipt()` mutations |

### What's Missing

The MerchantDetailsScreen (full page) already has the complete claim + request flows. But the **modal view** (MerchantDetailModal) and the **carousel cards** (WhileYouCharge, MerchantCarousel) do NOT surface these CTAs. Most drivers interact via the modal, not the full screen.

---

## Gap 1: "Request to Join" for Non-Incentive Merchants

### Current Behavior
- Merchants without exclusives look identical to merchants with exclusives in the carousel
- No visual indicator that a merchant isn't on Nerava yet
- "Request to Join" only appears deep in the full MerchantDetailsScreen

### Required Changes

#### 1A. Carousel Cards — Visual Indicator

**Files:**
- `apps/driver/src/components/MerchantCarousel/MerchantCarousel.tsx`
- `apps/driver/src/components/WhileYouCharge/FeaturedMerchantCard.tsx`
- `apps/driver/src/components/WhileYouCharge/SecondaryMerchantCard.tsx`

**Changes:**
- Add a badge or label for non-incentive merchants: "Request to Join" or "Vote to Add"
- Badge placement: where the "Exclusive" or "Sponsored" badge currently appears
- Badge styling: muted/gray to differentiate from active offers (e.g., gray pill with "Request to Join" text)
- Condition: `!merchant.exclusive_title && !merchant.badges?.includes('Exclusive') && !merchant.daily_cap_cents`

**Data dependency:**
- The carousel data comes from charger detail endpoint (`/v1/chargers/{id}/detail` → `nearby_merchants`)
- Currently returns `has_exclusive: bool` and `exclusive_title?: string`
- **No backend change needed** — we can derive "no incentive" from `has_exclusive === false && !exclusive_title`

#### 1B. MerchantDetailModal — "Request to Join" CTA

**Files:**
- `apps/driver/src/components/MerchantDetail/MerchantDetailModal.tsx`

**Changes:**
- When merchant has no exclusive/incentive, replace or supplement the "Activate Session" button with "Request to Join Nerava"
- On click: open bottom sheet with interest tag selection (Coffee, Food, Discount, Workspace, Safety Stop, Shopping)
- After submission: show confirmation with request count ("You and 42 other drivers have requested this merchant")
- Reuse the existing `RequestToJoinSheet` component from MerchantDetailsScreen

**Data dependency:**
- Need `join_request_count` and `user_has_requested` in the modal
- Option A: Fetch from `/v1/merchants/{placeId}/request-join/count` when modal opens (extra API call)
- Option B: Include in charger detail response `nearby_merchants[]` (backend change, but cleaner)
- **Recommendation:** Option A first (no backend change), optimize to Option B later

**CTA layout when merchant has NO incentive:**
```
┌─────────────────────────────────┐
│  [Request to Join]  [Directions]│
└─────────────────────────────────┘
```

**CTA layout when merchant has already been requested by this driver:**
```
┌─────────────────────────────────┐
│  [✓ Requested (42)]  [Directions]│
└─────────────────────────────────┘
```

---

## Gap 2: "Claim Reward" CTA for Incentive Merchants

### Current Behavior
- Incentive merchants show "Activate Session" in the modal (starts exclusive timer)
- "Claim Reward" only exists on the full MerchantDetailsScreen
- The modal's "Activate Session" starts the exclusive flow (walk to merchant, show code) — this is the **old flow**
- The **new billing model** (Claim + Presence) is: driver claims offer while charging → visits merchant → verified

### Required Changes

#### 2A. MerchantDetailModal — "Claim Reward" CTA

**Files:**
- `apps/driver/src/components/MerchantDetail/MerchantDetailModal.tsx`

**Changes:**
- For merchants with an active incentive/reward, add "Claim Reward" as primary CTA
- "Get Directions" becomes secondary CTA
- On click: open `ClaimRewardSheet` (reuse from MerchantDetailsScreen)
- After claiming: show 2-hour countdown, link to receipt upload

**CTA layout when merchant HAS incentive:**
```
┌──────────────────────────────────┐
│  [Claim Reward]    [Directions]  │
└──────────────────────────────────┘
```

**CTA layout when reward already claimed (pending receipt):**
```
┌──────────────────────────────────┐
│  [Upload Receipt]  [Directions]  │
└──────────────────────────────────┘
```

**CTA layout when receipt uploaded (under review):**
```
┌──────────────────────────────────┐
│  [Under Review ⏳] [Directions]  │
└──────────────────────────────────┘
```

**Data dependency:**
- Need `reward_state` (has_active_reward, active_claim_id, active_claim_status) in the modal
- Currently only available from `/v1/merchants/{merchant_id}` (full detail endpoint)
- The modal currently only has carousel-level data (MerchantSummary)
- **Backend option:** Add `has_active_reward` to `NearbyMerchantResponse` in charger detail
- **Frontend option:** Fetch merchant detail when modal opens (adds latency)
- **Recommendation:** Add `has_active_reward: bool` to `NearbyMerchantResponse` (small backend change), fetch full `reward_state` on modal open for claim details

#### 2B. Carousel Badge for Claimable Rewards

**Files:**
- `apps/driver/src/components/MerchantCarousel/MerchantCarousel.tsx`
- `apps/driver/src/components/WhileYouCharge/FeaturedMerchantCard.tsx`
- `apps/driver/src/components/WhileYouCharge/SecondaryMerchantCard.tsx`

**Changes:**
- Add a reward badge for merchants with claimable rewards (e.g., green pill "Earn $2.00")
- This already partially exists: `campaign_reward_cents > 0` shows earn badge on featured cards
- Extend to show on secondary cards as well
- Add visual distinction between "has exclusive only" vs "has claimable reward"

**Badge hierarchy (highest priority wins):**
1. Active claim in progress → "Claimed ✓" (blue)
2. Claimable reward → "Earn $X.XX" (green)
3. Exclusive offer → "Exclusive" (yellow/gold)
4. Sponsored → "Sponsored" (gray)
5. No incentive → "Request to Join" (muted gray)

---

## Gap 3: Claim + Presence Validation

### Current State
The claim endpoint (`POST /v1/rewards/claim`) doesn't currently enforce the "Claim + Presence" billing rules:
1. Driver must be in an **active charging session** (Tesla/Smartcar verified)
2. Driver must be **within 250-350m** of the merchant (GPS verified)
3. Driver taps **"Claim Offer"** (explicit intent)

### Required Backend Changes

**File:** `backend/app/routers/merchant_rewards.py`

**Changes:**
- On `POST /v1/rewards/claim`, validate:
  - Driver has an active `SessionEvent` (not ended, created within reasonable timeframe)
  - Driver's GPS coordinates (from request body) are within 350m of the merchant (haversine)
  - No duplicate active claim for this merchant (already exists via idempotency)
- Return 400 with clear error if validation fails:
  - `"not_charging"` → "Start charging to claim this reward"
  - `"too_far"` → "Get closer to {merchant_name} to claim"

**Frontend handling:**
- Show appropriate error messages in ClaimRewardSheet
- Disable "Claim Reward" button if not actively charging (check via `useSessionPolling` hook)
- Gray out button with tooltip: "Available while charging"

---

## Gap 4: Merchant Detail Modal Data Enrichment

### Problem
The `MerchantDetailModal` receives `MerchantSummary` data from the carousel, which lacks:
- `reward_state` (claim info)
- `join_request_count`
- `user_has_requested`
- `has_active_reward`

### Options

**Option A: Lazy fetch on modal open (recommended for v1)**
- When modal opens, fire `GET /v1/merchants/{placeId}/request-join/count`
- If merchant has incentive, also fetch reward state from detail endpoint
- Show loading skeleton for CTA area while fetching
- Pro: No backend changes. Con: Extra API call per modal open.

**Option B: Enrich charger detail response (recommended for v2)**
- Add to `NearbyMerchantResponse`:
  - `has_active_reward: bool`
  - `reward_amount_cents?: int`
  - `join_request_count?: int`
  - `user_has_requested?: bool`
- Pro: No extra API calls. Con: Heavier charger detail response, requires auth context in charger endpoint.

---

## Implementation Order

### Phase 1: "Request to Join" (smallest change, high signal value)

1. Add "Request to Join" badge to carousel cards for non-incentive merchants
2. Add "Request to Join" CTA to MerchantDetailModal (reuse RequestToJoinSheet)
3. Fetch request count on modal open
4. Show confirmation state after request

**Estimated scope:** ~4 frontend files, 0 backend files
**Risk:** Low — uses existing endpoints

### Phase 2: "Claim Reward" CTA in Modal

1. Add "Claim Reward" button to MerchantDetailModal for incentive merchants
2. Integrate ClaimRewardSheet into modal flow
3. Show claim status (countdown, upload receipt link)
4. Add `has_active_reward` to NearbyMerchantResponse (backend)

**Estimated scope:** ~3 frontend files, 1 backend file
**Risk:** Low — reuses existing components

### Phase 3: Claim + Presence Validation

1. Add charging session validation to `POST /v1/rewards/claim`
2. Add GPS proximity check to claim endpoint
3. Disable "Claim Reward" in UI when not charging
4. Add error handling for validation failures

**Estimated scope:** ~2 frontend files, 1 backend file
**Risk:** Medium — new validation logic, needs testing with real sessions

### Phase 4: Carousel Visual Polish

1. Implement badge hierarchy (claimed > earn > exclusive > sponsored > request)
2. Extend earn badge to secondary cards
3. Add "Claimed ✓" badge for active claims
4. Visual differentiation between incentive tiers

**Estimated scope:** ~4 frontend files, 0 backend files
**Risk:** Low — purely visual

---

## File Inventory

### Frontend Files to Modify

| File | Phase | Changes |
|------|-------|---------|
| `apps/driver/src/components/MerchantDetail/MerchantDetailModal.tsx` | 1, 2 | Add "Request to Join" and "Claim Reward" CTAs |
| `apps/driver/src/components/MerchantCarousel/MerchantCarousel.tsx` | 1, 4 | Add request/claim badges to cards |
| `apps/driver/src/components/WhileYouCharge/FeaturedMerchantCard.tsx` | 1, 4 | Add request badge, earn badge |
| `apps/driver/src/components/WhileYouCharge/SecondaryMerchantCard.tsx` | 1, 4 | Add request badge |
| `apps/driver/src/components/MerchantDetails/ClaimRewardSheet.tsx` | 2 | May need minor props adjustment for modal context |
| `apps/driver/src/components/MerchantDetails/RequestToJoinSheet.tsx` | 1 | May need minor props adjustment for modal context |
| `apps/driver/src/services/api.ts` | 1, 2 | Already has mutations — may need React Query hook wrappers |

### Backend Files to Modify

| File | Phase | Changes |
|------|-------|---------|
| `backend/app/routers/chargers.py` | 2 | Add `has_active_reward` to NearbyMerchantResponse |
| `backend/app/routers/merchant_rewards.py` | 3 | Add charging session + proximity validation |

### No Changes Needed

| Component | Reason |
|-----------|--------|
| `MerchantDetailsScreen.tsx` | Already has full claim + request flows |
| `ExclusiveActiveView.tsx` | Separate flow, not affected |
| `RequestToJoinSheet.tsx` | Already built, just needs to be imported into modal |
| `ClaimRewardSheet.tsx` | Already built, just needs to be imported into modal |
| `ReceiptUploadModal.tsx` | Already built, opens from claim flow |
| Backend claim/request endpoints | Already exist and work |

---

## Data Flow Diagram

```
DRIVER OPENS AMENITIES TAB
         │
         ▼
  ┌─────────────┐
  │ Carousel     │ ← GET /v1/chargers/{id}/detail (nearby_merchants)
  │ renders      │
  │ merchants    │
  └──────┬──────┘
         │
    has_exclusive?
    ┌────┴────┐
    NO        YES
    │         │
    ▼         ▼
  "Request   "Exclusive" or
  to Join"   "Earn $X" badge
  badge
         │
   Driver taps card
         │
         ▼
  ┌─────────────┐
  │ Modal opens  │ ← Lazy fetch: /request-join/count + /merchants/{id} (reward_state)
  └──────┬──────┘
         │
    has_incentive?
    ┌────┴────┐
    NO        YES
    │         │
    ▼         ▼
  [Request   [Claim      [Get
  to Join]   Reward]     Directions]
    │         │
    ▼         ▼
  Interest   ClaimRewardSheet
  tag picker  (2-hour window)
    │         │
    ▼         ▼
  Confirm    Receipt upload
  + count    + OCR verification
```

---

## Open Questions

1. **Should "Request to Join" show for ALL non-incentive merchants or only those within walking distance?**
   - Recommendation: Only within walking distance (same filter as current carousel)

2. **Should "Claim Reward" require active charging or allow pre-claim?**
   - Recommendation: Require active charging (aligns with billing model: Claim + Presence)

3. **Should we show the reward amount on the "Claim Reward" button?**
   - Recommendation: Yes — "Claim $2.00 Reward" is more compelling than "Claim Reward"

4. **Should "Request to Join" count as a conversion metric for the merchant acquisition funnel?**
   - Recommendation: Yes — high request count = strong signal for merchant outreach team

5. **How do we handle merchants with BOTH an exclusive AND a claimable reward?**
   - Recommendation: Show "Claim Reward" as primary (it's the billing event), "Activate Session" as secondary
