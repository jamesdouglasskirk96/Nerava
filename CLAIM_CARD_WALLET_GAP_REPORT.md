# Claim Active Card in Wallet — Gap Report & Implementation Plan

**Date:** 2026-03-24
**Feature:** Add a "Claim Active" card to the Wallet screen showing active exclusive sessions, with tap-through to claim details (directions, QR code, offer info)
**Branch:** `claude/add-claim-card-wallet-5kTRE`

---

## 1. Feature Summary

When a driver has an active claim (exclusive session), the Wallet screen should display a prominent "Claim Active" card — similar to the green "Visit Active" popup currently shown on the Charger Detail amenities tab. This card provides at-a-glance status and, when tapped, navigates to a dedicated Claim Details screen with directions, offer details, countdown timer, and a QR code for merchant verification.

Claims should expire **1 hour after the associated charging session ends** (not 1 hour from activation as currently implemented).

---

## 2. Current State Analysis

### What Exists Today

| Component | Location | Status |
|-----------|----------|--------|
| **Wallet screen** | `apps/driver/src/components/Wallet/WalletModal.tsx` | Live — shows balance, withdrawal, recent transactions |
| **ActiveVisitTracker** | `apps/driver/src/components/ChargerDetail/ChargerDetailSheet.tsx` (L923-984) | Live — floating green card on charger detail amenities tab |
| **ClaimConfirmModal** | `apps/driver/src/components/ChargerDetail/ChargerDetailSheet.tsx` (L861-919) | Live — confirms claim before activation |
| **useExclusiveSessionState** | `apps/driver/src/hooks/useExclusiveSessionState.ts` | Live — localStorage-persisted state, countdown timer |
| **ExclusiveActiveView** | `apps/driver/src/components/ExclusiveActiveView/ExclusiveActiveView.tsx` | Live — full-screen active exclusive with countdown, directions, "I'm at the Merchant" button |
| **ExclusiveSession model** | `backend/app/models/exclusive_session.py` | Live — ACTIVE/COMPLETED/EXPIRED/CANCELED statuses |
| **POST /v1/exclusive/activate** | `backend/app/routers/exclusive.py` (L144-472) | Live — creates session, expires_at = now + 60min |
| **POST /v1/exclusive/verify** | `backend/app/routers/exclusive.py` (L761-942) | Live — generates verification code (ATX-ASADAS-023 format) |
| **GET /v1/exclusive/active** | `backend/app/routers/exclusive.py` (L639-687) | Live — returns current ACTIVE session or null |

### What's Missing (Gaps)

#### Gap 1: No Claim Card on Wallet Screen
The wallet (`WalletModal.tsx`) has no awareness of active exclusive sessions. It only shows balance, withdrawal flow, and transaction history. There is no visual indicator that a claim is active.

**Impact:** Drivers who navigate to the wallet during an active claim lose visibility of their claim status. They must go back to the charger detail screen to see their active visit.

#### Gap 2: No Dedicated Claim Details Screen
The `ExclusiveActiveView` exists but is embedded in the charger detail flow. There is no standalone route/screen for claim details that can be navigated to from the wallet.

**Impact:** No deep-link target for the wallet card tap. The claim details (directions, QR code, offer info) are scattered across `ExclusiveActiveView` and `ChargerDetailSheet`.

#### Gap 3: No QR Code for Merchant Verification
The `POST /v1/exclusive/verify` endpoint generates a text verification code (e.g., `ATX-ASADAS-023`), but there is no QR code rendered in the driver app. The "Walk to and show this screen" text in the ExclusiveActiveView suggests this was planned but not implemented.

**Impact:** Merchant POS verification requires manual code entry. A scannable QR code would streamline redemption.

#### Gap 4: Expiry Tied to Activation, Not Charging Session End
Currently, `expires_at = activated_at + 60 minutes` (set at activation time in `exclusive.py` L390). The requirement is for claims to expire **1 hour after the charging session ends**.

**Impact:** If a driver activates a claim 5 minutes into a 45-minute charge, the claim expires at minute 65 — only 20 minutes after charging ends. The new behavior should give a full 60 minutes post-charge to visit the merchant.

**Current expiry logic:**
```python
# backend/app/routers/exclusive.py ~L390
expires_at = datetime.now(timezone.utc) + timedelta(minutes=EXCLUSIVE_DURATION_MIN)
```

**Required:** Expiry should be dynamically extended: `max(activated_at + 60min, charging_session_end + 60min)`. This requires linking the `ExclusiveSession` to the active `SessionEvent`.

#### Gap 5: No Charging Session → Exclusive Session Link
The `ExclusiveSession` model has no FK to `session_events`. There's no way to know when the associated charging session ended, which is needed for the "1 hour after charge ends" expiry.

**Impact:** Cannot implement the new expiry rule without linking these two entities.

#### Gap 6: Wallet Badge Not Reflecting Active Claims
The bottom nav shows a wallet badge (`$2` in the screenshot), but it only reflects balance. An active claim should add a visual indicator (e.g., green dot, "1 Active" badge) to make the wallet tab more discoverable during a claim.

---

## 3. Implementation Plan

### Phase 1: Backend — Link Sessions & Update Expiry

#### Task 1.1: Add `charging_session_id` to ExclusiveSession
- **File:** `backend/app/models/exclusive_session.py`
- **Change:** Add nullable FK column `charging_session_id → session_events.id`
- **Migration:** New Alembic migration
- **Why:** Links the claim to the charging session for expiry calculation

#### Task 1.2: Populate `charging_session_id` on Activation
- **File:** `backend/app/routers/exclusive.py` (POST /activate)
- **Change:** When creating an `ExclusiveSession`, query for the driver's current active `SessionEvent` and store its ID
- **Fallback:** If no active session found (edge case), use current behavior (60min from activation)

#### Task 1.3: Update Expiry Logic
- **File:** `backend/app/routers/exclusive.py`
- **Change:** Add a new endpoint or modify `GET /v1/exclusive/active` to dynamically compute `effective_expires_at`:
  - If charging session is still active: `expires_at = session_end (unknown) + 60min` → show "Expires 1hr after charge ends"
  - If charging session has ended: `expires_at = session_ended_at + 60min`
  - If no linked session: fall back to `activated_at + 60min`
- **Also:** Add a background/on-demand check in `GET /active` that updates `expires_at` when the linked session ends

#### Task 1.4: Extend GET /v1/exclusive/active Response
- **File:** `backend/app/routers/exclusive.py`
- **Change:** Include additional fields in the response:
  ```json
  {
    "exclusive_session": {
      "id": "uuid",
      "merchant_id": "string",
      "merchant_name": "string",
      "merchant_place_id": "string",
      "charger_id": "string",
      "charger_name": "string",
      "exclusive_title": "Free Drink with Sandwich",
      "expires_at": "ISO8601",
      "activated_at": "ISO8601",
      "remaining_seconds": 3420,
      "charging_active": true,
      "charging_session_ended_at": null,
      "verification_code": "ATX-SCHLTZ-007",
      "merchant_lat": 30.123,
      "merchant_lng": -97.456,
      "merchant_distance_m": 199,
      "merchant_walk_time_min": 3,
      "merchant_category": "fast_food",
      "merchant_photo_url": "https://..."
    }
  }
  ```
- **Why:** The wallet card and claim details screen need merchant info, offer title, distance, and coordinates without a separate API call

#### Task 1.5: Auto-generate Verification Code on Activation
- **File:** `backend/app/routers/exclusive.py`
- **Change:** Call the verify/code generation logic at activation time (not just on explicit verify call) so the QR code is immediately available
- **Store:** `verification_code` column on `ExclusiveSession` (new migration)

### Phase 2: Frontend — Claim Active Card on Wallet

#### Task 2.1: Create `ClaimActiveCard` Component
- **File:** `apps/driver/src/components/Wallet/ClaimActiveCard.tsx` (new)
- **Design:** Green card matching the "Visit Active" popup style:
  ```
  ┌─────────────────────────────────────┐
  │ ● Claim Active          ⏱ 47:23    │
  │                                     │
  │ ⚡ Charger ─────────────── 🏪 Merchant │
  │   Schlotzsky's Supercharger  199m   │
  │                                     │
  │ 🎁 Free Drink with Sandwich         │
  │                                     │
  │    [ View Claim Details → ]         │
  └─────────────────────────────────────┘
  ```
- **Data source:** `useExclusiveSessionState` hook + enriched `GET /active` response
- **Behavior:** Rendered between the balance card and "How it works" section
- **Tap:** Navigates to `/claim/:sessionId` (new route)

#### Task 2.2: Integrate ClaimActiveCard into WalletModal
- **File:** `apps/driver/src/components/Wallet/WalletModal.tsx`
- **Change:** Import and render `ClaimActiveCard` when `activeExclusive !== null`
- **Position:** Below the blue balance card, above "How it works"
- **Data:** Use `useActiveExclusive()` React Query hook (already polls every 30s)

#### Task 2.3: Create Claim Details Screen
- **File:** `apps/driver/src/components/ClaimDetails/ClaimDetailsScreen.tsx` (new)
- **Route:** `/claim/:sessionId`
- **Sections:**
  1. **Header:** "Claim Active" badge + countdown timer (large, prominent)
  2. **Offer Card:** Merchant name, exclusive title, category, photo
  3. **QR Code:** Generated from `verification_code` using a lightweight QR library (e.g., `qrcode.react`)
     - Text below: "Show this to the merchant" + human-readable code (ATX-SCHLTZ-007)
  4. **Distance & Directions:** Walking distance, estimated time, "Get Directions" button (opens Maps)
  5. **Charger Info:** Which charger you're at, charging status
  6. **Action Buttons:**
     - "Get Directions" (outline, opens native maps with merchant lat/lng)
     - "I'm at the Merchant — Done" (solid green, completes the claim)
  7. **Expiry Notice:** "This claim expires 1 hour after your charge ends" or countdown if charge already ended

#### Task 2.4: Add Route to App.tsx
- **File:** `apps/driver/src/App.tsx`
- **Change:** Add `<Route path="/claim/:sessionId" element={<ClaimDetailsScreen />} />`

#### Task 2.5: Update useExclusiveSessionState for Enriched Data
- **File:** `apps/driver/src/hooks/useExclusiveSessionState.ts`
- **Change:** Store additional fields from the enriched `GET /active` response (merchant name, offer title, verification code, lat/lng, distance)
- **Why:** The wallet card and claim details screen need this data

### Phase 3: Frontend — QR Code & Polish

#### Task 3.1: Add QR Code Library
- **Command:** `cd apps/driver && npm install qrcode.react`
- **Why:** Lightweight React component for QR code generation. No backend changes needed — the verification code string is encoded client-side.

#### Task 3.2: Create QR Code Component
- **File:** `apps/driver/src/components/ClaimDetails/ClaimQRCode.tsx` (new)
- **Input:** Verification code string (e.g., `ATX-SCHLTZ-007`)
- **Output:** QR code image + human-readable code below
- **Size:** 200x200px, high error correction (L level sufficient for short codes)

#### Task 3.3: Wallet Tab Badge for Active Claim
- **File:** `apps/driver/src/components/shared/BottomNav.tsx` (or equivalent)
- **Change:** Add a green dot or "1" badge on the wallet tab icon when an active claim exists
- **Data:** Read from `useExclusiveSessionState` or `useActiveExclusive`

#### Task 3.4: Update Charging Session Polling to Extend Claim Expiry
- **File:** `apps/driver/src/hooks/useSessionPolling.ts`
- **Change:** When a charging session ends (detected via poll), notify the exclusive session state to recalculate expiry based on `session_ended_at + 60min`
- **Backend sync:** `GET /v1/exclusive/active` returns the updated `expires_at` on next poll

### Phase 4: Testing

#### Task 4.1: Backend Tests
- **File:** `backend/tests/test_exclusive_claim_expiry.py` (new)
- **Tests:**
  - Activation links to current charging session
  - Expiry extends when charging session ends (1hr post-charge)
  - `GET /active` returns enriched merchant data
  - Verification code generated at activation
  - Expiry auto-marks session EXPIRED when charge ended > 1hr ago

#### Task 4.2: Frontend Tests
- **File:** `apps/driver/src/components/Wallet/ClaimActiveCard.test.tsx` (new)
- **Tests:**
  - Card renders when active claim exists
  - Card hidden when no active claim
  - Countdown timer displays correctly
  - Tap navigates to claim details
  - Card shows merchant name and offer title

#### Task 4.3: E2E Test
- **File:** `apps/driver/e2e/claim-wallet-card.spec.ts` (new)
- **Flow:** Activate claim → navigate to wallet → verify card visible → tap → verify details screen

---

## 4. Data Flow Diagram

```
Driver activates claim (Charger Detail → Amenities → Claim Reward)
          │
          ▼
POST /v1/exclusive/activate
  ├── Creates ExclusiveSession (ACTIVE)
  ├── Links to active SessionEvent (charging_session_id)
  ├── Generates verification_code
  └── Returns enriched response
          │
          ▼
useExclusiveSessionState stores full claim data (localStorage)
          │
          ├──────────────────────────────┐
          ▼                              ▼
   Charger Detail Sheet            Wallet Screen
   (ActiveVisitTracker)          (ClaimActiveCard)
          │                              │
          │                              ▼ (tap)
          │                     /claim/:sessionId
          │                     (ClaimDetailsScreen)
          │                        ├── QR Code
          │                        ├── Directions
          │                        ├── Offer Details
          │                        └── "I'm Done" CTA
          │                              │
          ▼                              ▼
POST /v1/exclusive/complete ◄────────────┘
          │
          ▼
   Session marked COMPLETED
   Wallet card disappears
```

---

## 5. Expiry Logic (New)

```
if charging_session is still active:
    effective_expires_at = "TBD — 1hr after charge ends"
    show: "Expires 1 hour after your charge ends"

elif charging_session has ended:
    effective_expires_at = charging_session.ended_at + 60 minutes
    show: countdown timer (MM:SS remaining)

elif no linked charging session:
    effective_expires_at = activated_at + 60 minutes  (legacy fallback)
    show: countdown timer (MM:SS remaining)
```

Backend cron/on-demand check: When `GET /active` is called, if `charging_session.ended_at` is set and `ended_at + 60min < now()`, auto-mark the exclusive session as EXPIRED.

---

## 6. Dependencies & Risks

| Risk | Mitigation |
|------|-----------|
| `qrcode.react` adds bundle size (~12KB gzipped) | Lazy-load the claim details screen via `React.lazy()` |
| Charging session may end while app is backgrounded | `GET /active` recalculates expiry server-side on each call; frontend syncs on app resume via `refetchOnWindowFocus` |
| Multiple charger-merchant variants (WYC gotcha) | Reuse existing `_find_all_charger_merchant_links()` resolution logic |
| ExclusiveSession has no FK to session_events | New nullable column + migration (zero risk to existing data) |
| Verification code format may conflict across merchants | Already handled by daily reset + per-merchant counter in `POST /verify` |

---

## 7. Estimated Scope

| Phase | Tasks | Files Changed | Files Created |
|-------|-------|---------------|---------------|
| Phase 1 (Backend) | 5 | 3 | 1 migration |
| Phase 2 (Frontend) | 5 | 3 | 2 components |
| Phase 3 (Polish) | 4 | 2 | 1 component |
| Phase 4 (Testing) | 3 | 0 | 3 test files |
| **Total** | **17** | **8** | **7** |

---

## 8. Open Questions

1. **Should the claim card appear on the wallet even if the driver navigated away from the charger?** (Recommended: Yes — the card persists via localStorage until expiry or completion)
2. **Should we show the QR code immediately or only after "I'm at the Merchant"?** (Recommended: Immediately — reduces friction at the merchant counter)
3. **Should expired claims show a "Claim Expired" state briefly or just disappear?** (Recommended: Show expired state for 5 seconds with message, then remove)
4. **What happens if a driver has multiple active claims?** (Current model: only one ACTIVE session at a time — enforced in POST /activate. No change needed.)
