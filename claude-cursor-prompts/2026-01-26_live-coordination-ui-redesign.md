# Live Coordination UI Redesign — Staff Engineer Implementation Prompt

You are a Staff Engineer doing a code-level design-to-implementation analysis for Nerava's Driver web app.

---

## Goal

Turn the current driver app UI from a passive discovery tool into **live coordination infrastructure**:

1. Replace passive discovery language with live, urgent, actionable copy.
2. Promote social proof to the primary visual layer (sessions, active drivers).
3. Replace the "Wallet" metaphor with "Sessions" / "Active Session" coordination.
4. Improve charger availability with visual stall indicators + recency timestamps.
5. Reduce friction in the reservation flow (less sequential modal chain).
6. Elevate the "Show This Screen" / "Reservation Ticket" as the signature interaction.

---

## Input Assets

### 1. Monorepo

`/Users/jameskirk/Desktop/Nerava` (assume opened in this workspace).

### 2. Figma Export (the canonical design target)

**Directory:** `Nerava-Figma-With-Amenities/`

Feature components to reference:

| Figma Component | Path | Purpose |
|---|---|---|
| `App.tsx` | `Nerava-Figma-With-Amenities/app/App.tsx` | App shell, screen orchestration |
| `ChargerList.tsx` | `Nerava-Figma-With-Amenities/app/components/ChargerList.tsx` | Charger list with stall indicators |
| `LiveStallIndicator.tsx` | `Nerava-Figma-With-Amenities/app/components/LiveStallIndicator.tsx` | Visual dot-row stall availability |
| `SingleChargerCard.tsx` | `Nerava-Figma-With-Amenities/app/components/SingleChargerCard.tsx` | Individual charger card |
| `MerchantCarousel.tsx` | `Nerava-Figma-With-Amenities/app/components/MerchantCarousel.tsx` | Merchant carousel with likes |
| `SingleMerchantCarousel.tsx` | `Nerava-Figma-With-Amenities/app/components/SingleMerchantCarousel.tsx` | Single-merchant carousel variant |
| `MerchantDetails.tsx` | `Nerava-Figma-With-Amenities/app/components/MerchantDetails.tsx` | Full merchant detail screen |
| `FeaturedMerchantCard.tsx` | `Nerava-Figma-With-Amenities/app/components/FeaturedMerchantCard.tsx` | Featured merchant card |
| `NearbyMerchantCard.tsx` | `Nerava-Figma-With-Amenities/app/components/NearbyMerchantCard.tsx` | Nearby merchant card |
| `SocialProofBadge.tsx` | `Nerava-Figma-With-Amenities/app/components/SocialProofBadge.tsx` | Session count + active drivers pulse |
| `AmenityVotes.tsx` | `Nerava-Figma-With-Amenities/app/components/AmenityVotes.tsx` | Community amenity voting (WiFi, bathroom) |
| `PrimaryFilters.tsx` | `Nerava-Figma-With-Amenities/app/components/PrimaryFilters.tsx` | Category filter bar |
| `RefuelIntentModal.tsx` | `Nerava-Figma-With-Amenities/app/components/RefuelIntentModal.tsx` | Intent capture (eat/work/quick-stop) |
| `SpotSecuredModal.tsx` | `Nerava-Figma-With-Amenities/app/components/SpotSecuredModal.tsx` | Reservation confirmation ticket |
| `ActiveExclusive.tsx` | `Nerava-Figma-With-Amenities/app/components/ActiveExclusive.tsx` | Active session view with verification |
| `OTPModal.tsx` | `Nerava-Figma-With-Amenities/app/components/OTPModal.tsx` | Phone OTP authentication |
| `WalletModal.tsx` | `Nerava-Figma-With-Amenities/app/components/WalletModal.tsx` | Active + expired exclusives list |
| `AccountPage.tsx` | `Nerava-Figma-With-Amenities/app/components/AccountPage.tsx` | User profile page |

**Shared interfaces defined in Figma components:**
- `Merchant` — `id, name, category, walkTime, imageUrl, badge, isFeatured, neravaSessionsCount, activeDriversCount, amenities, experiences, rating`
- `Charger` — `id, name, walkTime, imageUrl, availableStalls, totalStalls, experiences, network, power`
- `RefuelDetails` — `intent: 'eat' | 'work' | 'quick-stop', partySize?, needsPowerOutlet?, isToGo?`

**UI library:** 48 shadcn/ui components in `Nerava-Figma-With-Amenities/app/components/ui/`

### 3. Current Driver App (the code to modify)

**Root:** `apps/driver/src/`

| Current Component | Path | Maps To |
|---|---|---|
| `DriverHome` | `apps/driver/src/components/DriverHome/DriverHome.tsx` | Main orchestrator (all states) |
| `MerchantCarousel` | `apps/driver/src/components/MerchantCarousel/MerchantCarousel.tsx` | Discovery carousel |
| `PreChargingScreen` | `apps/driver/src/components/PreCharging/PreChargingScreen.tsx` | Pre-charge browse |
| `NearbyExperiences` | `apps/driver/src/components/PreCharging/NearbyExperiences.tsx` | Nearby merchant list |
| `ChargerCard` | `apps/driver/src/components/PreCharging/ChargerCard.tsx` | Charger card |
| `WhileYouChargeScreen` | `apps/driver/src/components/WhileYouCharge/WhileYouChargeScreen.tsx` | Charging-active browse |
| `FeaturedMerchantCard` | `apps/driver/src/components/WhileYouCharge/FeaturedMerchantCard.tsx` | Featured card |
| `MerchantDetailModal` | `apps/driver/src/components/MerchantDetail/MerchantDetailModal.tsx` | Merchant detail |
| `MerchantDetailsScreen` | `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx` | Full details + activation |
| `HeroImageHeader` | `apps/driver/src/components/MerchantDetails/HeroImageHeader.tsx` | Merchant hero |
| `DistanceCard` | `apps/driver/src/components/MerchantDetails/DistanceCard.tsx` | Walk time display |
| `RefuelIntentModal` | `apps/driver/src/components/RefuelIntentModal/RefuelIntentModal.tsx` | V3 intent capture |
| `SpotSecuredModal` | `apps/driver/src/components/SpotSecuredModal/SpotSecuredModal.tsx` | V3 reservation confirmation |
| `ActivateExclusiveModal` | `apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx` | OTP activation (legacy) |
| `ExclusiveActiveView` | `apps/driver/src/components/ExclusiveActiveView/ExclusiveActiveView.tsx` | Active session view |
| `VerificationCodeModal` | `apps/driver/src/components/VerificationCode/VerificationCodeModal.tsx` | Verification code display |
| `ArrivalConfirmationModal` | `apps/driver/src/components/ArrivalConfirmationModal/ArrivalConfirmationModal.tsx` | Arrival confirmation |

**State Management:**
- `DriverSessionContext` — location, session ID, charging state (`PRE_CHARGING | CHARGING_ACTIVE | EXCLUSIVE_ACTIVE`)
- `FavoritesContext` — liked merchants with backend sync
- `useExclusiveSessionState()` — 60-min timer, localStorage persistence
- `useChargingState()` — state machine transitions
- React Query hooks: `useIntentCapture()`, `useActiveExclusive()`, `useMerchantsForCharger()`

**Existing Feature Flags** (in `apps/driver/src/config/featureFlags.ts`):
```typescript
SECURE_A_SPOT_V3: import.meta.env.VITE_SECURE_A_SPOT_V3 === 'true'
```

**Routes** (in `apps/driver/src/App.tsx`):
```
/         → DriverHome
/driver   → DriverHome
/wyc      → WhileYouChargeScreen
/m/:id    → MerchantDetailsScreen
```

---

## PHASE 0 — Inventory + Truth

### A) Figma Export Inventory

Read and catalog every component in `Nerava-Figma-With-Amenities/app/components/`. For each, note:
- The component name and its props interface.
- Which Figma screen it represents (discover, detail, modal, etc.).
- Whether it has a direct equivalent in `apps/driver/src/`.

### B) Figma-to-Code Mapping Table

Produce a complete table:

| Figma Component | Current Code Equivalent | Status |
|---|---|---|
| `ChargerList.tsx` | `PreCharging/ChargerCard.tsx` | partial — no stall dots |
| `LiveStallIndicator.tsx` | *(none)* | missing |
| `SocialProofBadge.tsx` | *(none)* | missing |
| `AmenityVotes.tsx` | *(none)* | missing |
| `PrimaryFilters.tsx` | *(none)* | missing |
| `MerchantCarousel.tsx` | `MerchantCarousel/MerchantCarousel.tsx` | partial |
| `MerchantDetails.tsx` | `MerchantDetails/MerchantDetailsScreen.tsx` | partial |
| `FeaturedMerchantCard.tsx` | `WhileYouCharge/FeaturedMerchantCard.tsx` | partial |
| `NearbyMerchantCard.tsx` | `PreCharging/NearbyExperiences.tsx` | partial |
| `RefuelIntentModal.tsx` | `RefuelIntentModal/RefuelIntentModal.tsx` | match (V3) |
| `SpotSecuredModal.tsx` | `SpotSecuredModal/SpotSecuredModal.tsx` | match (V3) |
| `ActiveExclusive.tsx` | `ExclusiveActiveView/ExclusiveActiveView.tsx` | partial |
| `OTPModal.tsx` | `ActivateExclusiveModal/ActivateExclusiveModal.tsx` | partial |
| `WalletModal.tsx` | *(no standalone modal)* | missing |
| `AccountPage.tsx` | `Account/AccountPage.tsx` | partial |

**Verify this table by reading both directories.** Do not trust this draft — confirm every cell.

---

## PHASE 1 — Gap Analysis (Critique Requirements)

For each requirement, search the codebase first, then propose concrete changes.

### 1) Headline Language: Urgency + Agency (CRITICAL)

**Problem:** Current copy reads passive. Likely strings:
- "Find a charger near experiences"
- "What to do while you charge"
- "While You Charge"
- "Nearby Experiences"
- "Pre-Charging"

**Target copy (dynamic, live intel):**
- "3 chargers with open stalls near you"
- "Updated 3 min ago . 2 drivers charging"
- "Lock in your spot while you charge"
- "Asadas Grill . 4 min walk . Live now"

**Deliverable:**
1. Run: `rg -n "Find a charger|What to do while you charge|While You Charge|Pre-Charging|Nearby Experiences|nearby experiences" apps/driver/src/`
2. List every passive headline with file, line number, and current text.
3. Propose replacement copy for each. Where copy needs data (charger count, stall count, timestamp), identify the data source or mark as TODO.
4. Provide the exact edits.

### 2) Social Proof Prominence (HIGH)

**Problem:** Session counts and active driver counts are small metadata or missing entirely. They should be primary UI elements.

**Target (from Figma):**
- `SocialProofBadge.tsx` renders `neravaSessionsCount` and `activeDriversCount` with a pulsing "Live" indicator.
- Props: `{ neravaSessionsCount?, activeDriversCount? }`
- Pulse animation when `activeDriversCount > 0`.

**Deliverable:**
1. Run: `rg -n "sessionCount\|session_count\|neravaSession\|activeDriver\|drivers visited\|sessions" apps/driver/src/`
2. Identify where these fields exist in the data model (`MerchantSummary`, `MerchantForCharger`, API response).
3. Port `SocialProofBadge` from Figma into `apps/driver/src/components/shared/SocialProofBadge.tsx`.
4. Integrate it into `FeaturedMerchantCard`, `MerchantDetailModal`, and `MerchantDetailsScreen`.
5. Add CSS keyframe pulse animation (pure CSS, no new dependencies).

### 3) Replace "Wallet" with "Sessions" (HIGH)

**Problem:** "Wallet" implies loyalty/coupons. The UX is about live session coordination.

**Rename map:**
| Current | Target |
|---|---|
| "Wallet" (nav icon/label) | "Sessions" |
| "Active Exclusives" | "Active Session" |
| "Expired Exclusives" | "Past Visits" |
| Wallet icon (if wallet-shaped) | Activity/clock icon |

**Deliverable:**
1. Run: `rg -rn "Wallet\|Active Exclusive\|Expired Exclusive\|wallet" apps/driver/src/`
2. List every occurrence with file and line.
3. Identify nav/header components, routing references, analytics event names.
4. Provide exact edits for each. Update analytics event names to match (e.g., `wallet_opened` → `sessions_opened`).
5. Verify no API endpoints reference "wallet" in a way that would break.

### 4) Charger Availability Hierarchy (MEDIUM)

**Problem:** "3/5 stalls available" is plain text. Should be a visual dot row with color coding.

**Target (from Figma):**
- `LiveStallIndicator.tsx` — props: `{ availableStalls: number, totalStalls: number }`
- Renders filled/empty dots with color states:
  - Green (`bg-green-500`): 3+ available
  - Yellow (`bg-yellow-500`): 1-2 available
  - Red (`bg-red-500`): 0 available
  - Empty dots: `bg-gray-300`

**Deliverable:**
1. Read `Nerava-Figma-With-Amenities/app/components/LiveStallIndicator.tsx` — understand exact implementation.
2. Find charger card components: `rg -n "stall\|available\|ChargerCard\|charger.*card" apps/driver/src/`
3. Port `LiveStallIndicator` into `apps/driver/src/components/shared/LiveStallIndicator.tsx`.
4. Integrate into `ChargerCard` and any charger list views.
5. Add "Updated X min ago" line. Check if `last_updated` or `updated_at` exists in charger data. If not, add a `// TODO: Backend - add last_updated to charger response` comment and conditionally hide the line.

### 5) Modal Flow Momentum (MEDIUM)

**Problem:** Activation flow is a sequential modal chain: OTP → intent → secured → active. Each step is a full-screen interruption.

**Target:** Reduce to fewer surfaces with progressive disclosure.

**Changes:**
- Default intent to "Dining, Party of 2" with a "Change" link (skip intent modal for returning users).
- Prefill from `localStorage` using the user's last intent selection.
- If user is already authenticated, skip OTP entirely (current code may already do this — verify).

**Deliverable:**
1. Read `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx` — find the activation flow state machine (`flowState`, modal show/hide flags, `handleSecureSpot`, `handleActivateWithIntent`).
2. Read `apps/driver/src/components/RefuelIntentModal/RefuelIntentModal.tsx` — understand current props and behavior.
3. Add `localStorage` prefill:
   - On confirm: `localStorage.setItem('nerava_last_intent', JSON.stringify(details))`
   - On open: read and pre-select previous choices.
4. Add progressive disclosure: if `localStorage` has previous intent, show a compact summary ("Dining, Party of 2") with "Change" button instead of the full modal by default.
5. Gate behind feature flag `VITE_LIVE_COORDINATION_UI_V1` if this changes existing behavior.

### 6) Signature Interaction: "Show This Screen" Ticket (BOLD)

**Problem:** The reservation ticket (SpotSecuredModal) is a dismissible modal. It should be the hero moment.

**Target (from Figma):**
- `SpotSecuredModal.tsx` — current prop `onViewWallet` (rename to `onContinue`).
- `ActiveExclusive.tsx` — has verification code display, remaining time, "Show Host" button.

**Changes:**
- Add a "Show Host" button that transitions to a fullscreen ticket view (no nav chrome, large code, merchant name, time remaining).
- Add "Copy Code" button that copies the reservation ID to clipboard.
- Add subtle shimmer animation on the reservation code.

**Deliverable:**
1. Read the Figma `ActiveExclusive.tsx` and `SpotSecuredModal.tsx` to understand the target UX.
2. Find current ticket rendering: `rg -n "verificationCode\|reservationId\|reservation_id\|Reservation ID\|Show Host\|Copy Code" apps/driver/src/`
3. Implement a `FullScreenTicket` component (or extend `SpotSecuredModal`) with:
   - Fullscreen presentation (position: fixed, z-50, white background).
   - Large reservation code with CSS shimmer keyframe.
   - "Copy Code" button using `navigator.clipboard.writeText()`.
   - "Show Host" button that triggers fullscreen mode.
   - Tap-to-dismiss (exit fullscreen).
4. Integrate into `ExclusiveActiveView` or `DriverHome` depending on where the active session is displayed.

---

## PHASE 2 — Implementation Plan + Diffs

### A) Prioritized Checklist

| Priority | Change | Files |
|---|---|---|
| **P0** | Headline copy: passive → live intel | `PreChargingScreen`, `WhileYouChargeScreen`, `NearbyExperiences`, `DriverHome` |
| **P0** | Social proof badge (port from Figma) | New: `shared/SocialProofBadge.tsx`; modify: `FeaturedMerchantCard`, `MerchantDetailsScreen` |
| **P0** | Rename Wallet → Sessions | Nav components, `WalletSuccessModal`, analytics events |
| **P1** | Stall indicator (port from Figma) | New: `shared/LiveStallIndicator.tsx`; modify: `ChargerCard` |
| **P1** | Active Session banner on discover screen | Modify: `DriverHome` — add banner when `EXCLUSIVE_ACTIVE` |
| **P1** | Intent prefill + progressive disclosure | Modify: `RefuelIntentModal`, `MerchantDetailsScreen` |
| **P2** | Full-screen ticket "Show Host" + Copy Code | New: `shared/FullScreenTicket.tsx`; modify: `SpotSecuredModal`, `ExclusiveActiveView` |
| **P2** | Shimmer animation on reservation code | CSS keyframes in `index.css` or component-level |
| **P2** | Microcopy sweep (remaining passive text) | All screens |

### B) Concrete Diffs

Provide patch-style diffs for each P0 item:

1. **Discover screen headline + copy** — replace all passive strings with live-intel equivalents.
2. **Merchant card layout** — add `SocialProofBadge` with `neravaSessionsCount` and `activeDriversCount`. Show "Live Now" pulse when active.
3. **Charger card stall indicator** — replace text availability with `LiveStallIndicator` dot row.
4. **Nav rename** — Wallet → Sessions icon and label change.
5. **Active Session banner** — when `appChargingState === 'EXCLUSIVE_ACTIVE'`, render a sticky banner: "Asadas Grill . 42 min left . Tap to view".
6. **Ticket full-screen** — "Show Host" button + "Copy Code" clipboard integration.

### C) Missing Data Dependencies

If the UI needs fields not currently in the API response, list them:

| Field Needed | Used By | Current API Source | Status |
|---|---|---|---|
| `neravaSessionsCount` | SocialProofBadge | `MerchantSummary`? | Verify |
| `activeDriversCount` | SocialProofBadge, headline | `MerchantSummary`? | Verify |
| `availableStalls` | LiveStallIndicator | Charger data? | Verify |
| `totalStalls` | LiveStallIndicator | Charger data? | Verify |
| `lastUpdatedAt` | "Updated X min ago" | Charger data? | Likely missing |

For each missing field:
- Identify the backend file that would supply it.
- Provide a minimal fallback (hide the element, use a placeholder, derive from existing data).
- Mark with `// TODO: Backend - add {field} to {endpoint}`.

---

## PHASE 3 — Acceptance Tests

### Verification Checklist

- [ ] All passive headlines replaced with live-intel copy.
- [ ] `SocialProofBadge` renders on merchant cards with `neravaSessionsCount`.
- [ ] Live pulse CSS animation appears when `activeDriversCount > 0`.
- [ ] `LiveStallIndicator` renders correct dot count and color state (green/yellow/red).
- [ ] "Wallet" renamed to "Sessions" in all UI text, nav labels, and analytics events.
- [ ] Active Session banner appears on discover screen when exclusive is active.
- [ ] "Show Host" opens fullscreen ticket view.
- [ ] "Copy Code" copies reservation ID to clipboard.
- [ ] Old UI works correctly with `VITE_LIVE_COORDINATION_UI_V1=false`.
- [ ] TypeScript compiles: `cd apps/driver && npm run typecheck`
- [ ] Build succeeds: `cd apps/driver && npm run build`

### Playwright Tests (if `e2e/` or Playwright config exists in repo)

Propose 5 specs:

1. **Social proof renders:** Navigate to discover, verify merchant card shows "X drivers visited" text with hierarchy above category/distance.
2. **Live pulse:** Mock API to return `activeDriversCount: 3`, verify element with `animation` CSS property is present.
3. **Stall dots:** Render charger card with `available: 2, total: 5`, verify 2 green dots + 3 gray dots rendered.
4. **Sessions nav:** Click nav item formerly labeled "Wallet", verify URL is `/sessions` and header text is "Sessions".
5. **Copy Code:** Activate exclusive, open ticket, click "Copy Code", verify `navigator.clipboard` was called with the reservation ID string.

---

## Repo Search Commands (run these, don't guess)

```bash
# Passive headlines to replace
rg -n "Find a charger|What to do while you charge|While You Charge|Pre-Charging|Nearby Experiences|nearby experiences" apps/driver/src/

# Wallet references to rename
rg -rn "Wallet|Active Exclusive|Expired Exclusive|wallet" apps/driver/src/

# Social proof fields
rg -n "sessionCount|session_count|neravaSession|activeDriver|drivers.visited" apps/driver/src/

# Charger availability
rg -n "stall|availableStall|totalStall|available.*charger" apps/driver/src/

# Activation flow state machine
rg -n "flowState|setFlowState|handleActivate|handleSecure|showModal|showRefuel|showSpot" apps/driver/src/components/MerchantDetails/

# Feature flags
rg -n "FEATURE_FLAGS|VITE_.*=" apps/driver/src/

# Nav / header / routing
rg -n "Sidebar|BottomNav|TabBar|Header|Navigation|<Route" apps/driver/src/

# Verification code / ticket
rg -n "verificationCode|reservationId|reservation_id|Reservation.ID|Show.Host|Copy.Code" apps/driver/src/
```

---

## Hard Constraints

1. **Incremental changes.** Do not rewrite components from scratch. Modify existing files in place.
2. **No new heavy dependencies.** Only use packages already in `apps/driver/package.json`. Check before adding anything.
3. **Feature flag:** Gate all visual changes behind `VITE_LIVE_COORDINATION_UI_V1`. Add it to `apps/driver/src/config/featureFlags.ts`:
   ```typescript
   LIVE_COORDINATION_UI_V1: import.meta.env.VITE_LIVE_COORDINATION_UI_V1 === 'true',
   ```
4. **Preserve existing flags.** `VITE_SECURE_A_SPOT_V3` must continue to work independently.
5. **No broken builds:**
   ```bash
   cd apps/driver && npm run typecheck && npm run build
   ```

---

## Execution Order

1. Read `Nerava-Figma-With-Amenities/app/App.tsx` to understand the Figma screen flow.
2. Read every component in `Nerava-Figma-With-Amenities/app/components/` — build the definitive Figma inventory.
3. Read key driver app components (`DriverHome`, `MerchantCarousel`, `PreChargingScreen`, `WhileYouChargeScreen`, `MerchantDetailsScreen`) — build the code inventory.
4. Produce the verified Figma-to-Code mapping table (Phase 0B).
5. Run all search commands and identify every string/component that needs changing (Phase 1).
6. Produce the prioritized implementation plan and diffs (Phase 2).
7. Write acceptance tests (Phase 3).

**Start with Phase 0. Do not skip to diffs until the mapping table is verified by reading both codebases.**
