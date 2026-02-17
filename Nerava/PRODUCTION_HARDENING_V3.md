# Nerava iOS Shell App - Production Hardening V3

## Overview

V3 extends V2 production hardening with the **"Secure a Spot" activation flow** for the driver app. The old "Activate Exclusive" flow remains available behind a feature flag for backward compatibility.

**Scope:** Partial UI parity (P0 only). P1/P2 features (PrimaryFilters, SocialProofBadge, AmenityVotes) are explicitly deferred to V4.

This document covers:

1. **Mandatory Decisions** (must choose before implementation)
2. Feature Flag Strategy (gradual rollout)
3. Web App Changes (new components and flow updates)
4. Backend API Changes (intent capture fields)
5. iOS Native Changes (SKIP for V3)

---

## ⚠️ Decisions + Flags (MUST CHOOSE BEFORE IMPLEMENTATION)

**STOP.** These three decisions must be made explicitly. Do not proceed until each has a clear answer.

### Decision 1: Backward Compatibility Strategy

**Options:**
- **A) Feature Flag Dual-Path (CHOSEN):** Both flows exist. `VITE_SECURE_A_SPOT_V3=false` uses old flow, `=true` uses new flow.
- **B) Replace Old Flow:** Remove old flow entirely. No backward compatibility.

**V3 Choice: Option A (Feature Flag Dual-Path)**

This means:
- `handleAddToWallet()` (old flow) MUST remain in codebase
- `handleSecureSpot()` (new flow) is additive
- Button click is gated by `FEATURE_FLAGS.SECURE_A_SPOT_V3`
- Old flow is tested in CI with `flag=false`
- Rollback = set flag to false and redeploy frontend (build-time env in Vite)

**Enforcement:**
```typescript
// CORRECT: Dual-path
onClick={FEATURE_FLAGS.SECURE_A_SPOT_V3 ? handleSecureSpot : handleAddToWallet}

// WRONG: Removing old flow
onClick={handleSecureSpot}  // ❌ No fallback
```

---

### Decision 2: Location Handling

**Options:**
- **A) Location Required:** Fail activation if geolocation unavailable.
- **B) Location Optional (CHOSEN):** Accept `null` and proceed. Backend stores null.

**V3 Choice: Option B (Location Optional)**

This means:
- TypeScript: `lat: number | null`, `lng: number | null`
- Backend Pydantic: `lat: Optional[float] = None`, `lng: Optional[float] = None`
- **NEVER use 0 as fallback.** Zero is a valid coordinate (null island). Use `null`.
- Database stores `NULL` for both columns when unavailable.
- Analytics/geofence logic must handle null (V4 TODO).

**Enforcement:**
```typescript
// CORRECT: null when unavailable
let lat: number | null = null
let lng: number | null = null

// WRONG: Zero fallback (creates sessions at null island)
let lat = 0  // ❌ NEVER
let lng = 0  // ❌ NEVER

// WRONG: Omitting from request (Pydantic may reject)
{ charger_id, merchant_id }  // ❌ Missing lat/lng
```

---

### Decision 3: Confirmation Button Action

**Options:**
- **A) Navigate to Wallet:** Button opens wallet view/route.
- **B) Close and Continue (CHOSEN):** Button closes modal, transitions to walking state.

**V3 Choice: Option B (Close and Continue)**

This means:
- Button label is **"Continue"** (NOT "View Wallet")
- `onContinue` calls `setShowSpotSecuredModal(false)` then `setFlowState('walking')`
- Wallet does not exist in V3. "View Wallet" would be a lie.
- V4 TODO: Implement wallet route, rename button to "View Wallet"

**Enforcement:**
```typescript
// CORRECT: V3 button
<button onClick={onContinue}>Continue</button>

// WRONG: Promising wallet that doesn't exist
<button onClick={openWallet}>View Wallet</button>  // ❌ Wallet route doesn't exist
```

---

## Pre-Implementation Verification

**CRITICAL:** Verify all referenced files exist before starting implementation.

### Verification Commands

```bash
cd /Users/jameskirk/Desktop/Nerava

# Verify files to be modified exist
ls -la apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx
ls -la apps/driver/src/components/ActivateExclusiveModal/ActivateExclusiveModal.tsx
ls -la apps/driver/src/services/api.ts

# Verify component directories exist (will create RefuelIntentModal, SpotSecuredModal inside)
ls -d apps/driver/src/components

# Verify utils directory exists (will create verificationCode.ts inside)
ls -d apps/driver/src/utils || mkdir -p apps/driver/src/utils

# Verify backend files to modify
ls -la backend/app/routers/exclusive.py
ls -la backend/app/models/exclusive_session.py

# Check latest migration number (expect 053)
ls backend/alembic/versions/*.py | tail -3

# Detect Pydantic version (CRITICAL for validator syntax)
cd backend && python -c "import pydantic; print(f'Pydantic v{pydantic.VERSION}')" && cd ..
# If v2.x: use @field_validator
# If v1.x: use @validator

# Verify Figma reference components exist
ls src_figma_ev_waze/app/components/RefuelIntentModal.tsx
ls src_figma_ev_waze/app/components/SpotSecuredModal.tsx
```

**IF ANY VERIFICATION FAILS:**
- Do not proceed with implementation
- Update file paths in this plan
- Re-verify before starting

---

## Feature Flag Strategy

### Flag Definition

**Flag Name:** `VITE_SECURE_A_SPOT_V3`
**Type:** Boolean (string "true" or "false")
**Default:** `"false"` (old flow active)

### Behavior by Flag Value

| Flag Value | Button Text | Flow |
|------------|-------------|------|
| `"false"` (default) | "Activate Exclusive" | Old flow: OTP → Activate → ExclusiveActivatedModal |
| `"true"` | "Secure a Spot" | New flow: RefuelIntentModal → OTP → Activate with intent → SpotSecuredModal |

### Environment Configuration

```bash
# .env.local (development)
VITE_SECURE_A_SPOT_V3=true

# .env.staging
VITE_SECURE_A_SPOT_V3=true

# .env.production (initially)
VITE_SECURE_A_SPOT_V3=false

# .env.production (after validation)
VITE_SECURE_A_SPOT_V3=true
```

### Flag Usage in Code

```typescript
// apps/driver/src/config/featureFlags.ts (create this file)
export const FEATURE_FLAGS = {
  SECURE_A_SPOT_V3: import.meta.env.VITE_SECURE_A_SPOT_V3 === 'true',
} as const
```

This allows gradual rollout. Rollback requires changing the environment variable and redeploying (Vite bakes `import.meta.env` at build time).

---

## Priority Matrix

### P0 (V3 Scope - Must Implement)
- [ ] **F0-A**: RefuelIntentModal (intent capture before activation)
- [ ] **F0-B**: SpotSecuredModal (new confirmation UX with Reservation ID)
- [ ] **F0-C**: Verification code generation utility (ATX-{MERCHANT}-{DAY})
- [ ] **F0-D**: Update activation flow in MerchantDetailsScreen (behind feature flag)
- [ ] **F0-E**: Update TypeScript interface in api.ts (**CRITICAL BLOCKER**)
- [ ] **F0-F**: Update backend Pydantic schema in routers/exclusive.py (**CRITICAL BLOCKER**)
- [ ] **F0-G**: Update backend SQLAlchemy model in models/exclusive_session.py (**CRITICAL BLOCKER**)
- [ ] **F0-H**: Create and run migration 054 (**CRITICAL BLOCKER**)
- [ ] **F0-I**: Feature flag configuration file

### P1/P2 (Deferred to V4)
- PrimaryFilters on merchant carousel
- SocialProofBadge on merchant cards
- AmenityVotes on merchant detail screen
- WalletModal enhancements
- Wallet navigation from SpotSecuredModal
- Backend verification code validation

---

## V3 Design Decisions (Implementation Details)

> **Note:** Core decisions (backward compat, location, button action) are in the **"Decisions + Flags"** section above. This section covers secondary implementation choices.

### Reservation IDs are Informational Only

The Reservation ID (e.g., `ATX-ASADAS-025`) is for **display purposes only**. Backend does NOT validate these codes in V3.

**V4 TODO:** Add backend endpoint to generate/validate Reservation IDs for merchant verification.

### Reservation ID Stability

**Requirement:** Once generated, a Reservation ID must NOT change for the duration of an active session.

**Problem:** If stored only in React state, component unmount/remount (navigation, refresh, React error boundary) regenerates it. If the day changes mid-session, the new ID will have a different day code.

**Solution (V3):** Persist to `localStorage` keyed by `exclusive_session.id`:
```typescript
const storageKey = `reservation_id_${sessionId}`
let id = localStorage.getItem(storageKey)
if (!id) {
  id = generateReservationId(merchantName)
  localStorage.setItem(storageKey, id)
}
```

**Cleanup:** Remove from localStorage when:
- Session expires (`remaining_seconds <= 0`)
- User transitions out of session state (e.g., `flowState` changes from 'walking' to 'idle')
- Session is completed

**V3 Implementation:** Add cleanup `useEffect` hooks in MerchantDetailsScreen to remove reservation IDs when sessions expire or state transitions occur. While orphaned keys are small and acceptable short-term, explicit cleanup prevents localStorage bloat if sessions are resumed or if the app runs for extended periods.

**V4 TODO:** Store Reservation ID in backend `exclusive_session` record for true persistence.

### Hardcoded Location Code

The `generateReservationId` function defaults to `'ATX'` for all merchants. Dynamic location codes deferred to V4.

### merchant_place_id Source

**CRITICAL:** `merchant_place_id` must come from `merchantData.merchant.place_id`, NOT from `merchantId`.

```typescript
// CORRECT: Use actual place_id from merchant data
merchant_place_id: merchantData.merchant.place_id ?? null

// WRONG: Using merchantId (poisons database with incorrect place IDs)
merchant_place_id: merchantId  // ❌ NEVER - this is a UUID, not a Google Place ID
```

**Why this matters:** `merchantId` is our internal UUID. `place_id` is Google's identifier. Confusing them corrupts the database and breaks all Google-dependent features (photos, reviews, hours).

---

## 🚨 Data Integrity Rules (P0 - Non-Negotiable)

These rules are **non-negotiable**. Violating any of them corrupts the database and breaks downstream features. Every code review must verify compliance.

### Rule 1: Never Fabricate Place IDs

```typescript
// ✅ CORRECT: Use actual Google Place ID from merchant data
merchant_place_id: merchantData.merchant.place_id ?? null

// ❌ WRONG: Using our internal UUID (poisons database)
merchant_place_id: merchantId  // NEVER - this is a UUID, not a Google Place ID

// ❌ WRONG: Hardcoding a fake Place ID
merchant_place_id: "fake-place-id"  // NEVER
```

**Why:** `place_id` is Google's identifier for a location. Our `merchantId` is a UUID. Confusing them breaks:
- Google Places API enrichment (photos, reviews, hours)
- Analytics join queries
- Geofencing features
- Any future Google-dependent features

**How to detect:** Google Place IDs start with `ChIJ` (e.g., `ChIJN1t_tDeuEmsRUsoyG83frY4`). If you see a UUID in `merchant_place_id`, it's wrong.

### Rule 2: Never Use Zero as Location Fallback

```typescript
// ✅ CORRECT: Use null when location unavailable
let lat: number | null = null
let lng: number | null = null

// ❌ WRONG: Zero fallback (creates sessions at null island, 0°N 0°E)
let lat = userLat ?? 0  // NEVER
let lng = userLng ?? 0  // NEVER

// ❌ WRONG: Default parameter with zero
function activate(lat = 0, lng = 0) { ... }  // NEVER
```

**Why:** `(0, 0)` is a real location in the Atlantic Ocean called "Null Island." Sessions there:
- Corrupt geofence calculations
- Pollute location analytics
- Break distance-based features
- Are impossible to distinguish from intentional (0,0) coordinates

**How to detect:** Query `SELECT COUNT(*) FROM exclusive_sessions WHERE lat = 0 AND lng = 0`. Should be 0.

### Rule 3: Button Labels Must Match Behavior

```typescript
// ✅ CORRECT: V3 button closes modal and continues
<button onClick={handleContinue}>Continue</button>

// ❌ WRONG: Label promises wallet but doesn't deliver
<button onClick={handleContinue}>View Wallet</button>  // Wallet doesn't exist in V3!
```

**Why:** UX trust. Users click "View Wallet" expecting to see their wallet. If it does something else, they lose trust in the app.

### Rule 4: All New Flows Behind Feature Flag

```typescript
// ✅ CORRECT: Feature flag controls which flow runs
onClick={FEATURE_FLAGS.SECURE_A_SPOT_V3 ? handleSecureSpot : handleAddToWallet}

// ❌ WRONG: Replacing flow with no rollback path
onClick={handleSecureSpot}  // Old flow deleted - can't rollback!
```

**Why:** Fast rollback. If production breaks, flip flag and redeploy frontend. Old flow is restored without code changes.

### Rule 5: Migration + Model + Handler = Complete

A database change requires ALL THREE:
1. **Migration** - Adds columns to database
2. **Model** - SQLAlchemy knows about columns
3. **Handler** - Endpoint writes to columns

```python
# ❌ INCOMPLETE: Migration only (columns exist but are always NULL)
# Migration: ✅ adds intent column
# Model: ❌ missing intent attribute
# Handler: ❌ doesn't set session.intent

# ✅ COMPLETE: All three updated
# Migration: ✅ adds intent column
# Model: ✅ has intent = Column(String(50))
# Handler: ✅ sets session.intent = request.intent
```

**How to detect:** After activation, query `SELECT intent FROM exclusive_sessions WHERE id = ?`. If NULL when intent was sent, handler isn't writing.

---

## F0-E: Update TypeScript Interface (CRITICAL - DO FIRST)

**File:** `apps/driver/src/services/api.ts`

**FIND (line 269-278):**
```typescript
export interface ActivateExclusiveRequest {
  merchant_id?: string
  merchant_place_id?: string
  charger_id: string
  charger_place_id?: string
  intent_session_id?: string
  lat: number
  lng: number
  accuracy_m?: number
}
```

**REPLACE WITH:**
```typescript
export interface ActivateExclusiveRequest {
  merchant_id?: string
  merchant_place_id?: string | null
  charger_id: string
  charger_place_id?: string
  intent_session_id?: string
  lat: number | null  // V3: null allowed when location unavailable
  lng: number | null  // V3: null allowed when location unavailable
  accuracy_m?: number
  // NEW: Intent capture fields (V3)
  intent?: 'eat' | 'work' | 'quick-stop'
  party_size?: number
  needs_power_outlet?: boolean
  is_to_go?: boolean
}
```

### MANDATORY GATE: TypeScript Verification

**STOP-THE-LINE:** After this change, immediately run:

```bash
cd /Users/jameskirk/Desktop/Nerava/apps/driver
npm run typecheck
```

**If typecheck fails:** Do not proceed. Fix all type errors before continuing.

**Verification that fields are forwarded:**
1. Search for `activateExclusive.mutateAsync` usage
2. Confirm the request object construction includes the new fields
3. If using a request builder/transformer, verify it does not strip unknown fields

### MANDATORY GATE: Request Payload Verification (Pre-Merge)

**STOP-THE-LINE:** Before merging, you MUST verify the actual HTTP request payload includes null values correctly.

**Why:** TypeScript types don't guarantee runtime behavior. Your API client may:
- Strip `null` values during serialization
- Use a Zod schema that rejects `null`
- Have a `cleanUndefined()` helper that also removes `null`
- Transform the payload before sending

**Verification steps:**

1. **Run the app locally with V3 flag enabled:**
   ```bash
   cd /Users/jameskirk/Desktop/Nerava/apps/driver
   VITE_SECURE_A_SPOT_V3=true npm run dev
   ```

2. **Trigger an activation with location denied** (or mock geolocation failure)

3. **Open browser DevTools → Network tab → find the `/activate` request**

4. **Verify request payload contains:**
   ```json
   {
     "lat": null,
     "lng": null,
     "intent": "eat",
     "party_size": 2
   }
   ```

5. **Verify backend response is 200** (not 422 validation error)

6. **Query database to confirm NULL stored:**
   ```sql
   SELECT lat, lng, intent FROM exclusive_sessions ORDER BY created_at DESC LIMIT 1;
   -- Expected: lat=NULL, lng=NULL, intent='eat'
   ```

**If any of these fail:** Do not merge. Fix the serialization/validation issue first.

**Checklist item to add to PR:**
- [ ] Verified request payload includes `"lat": null, "lng": null` (not omitted, not 0)
- [ ] Verified backend returns 200 (not 422)
- [ ] Verified database stores NULL (not 0)

---

## F0 Changes (Must Implement)

### F0-I: Feature Flag Configuration

**New File:** `apps/driver/src/config/featureFlags.ts`

```typescript
/**
 * Feature flags for gradual rollout.
 * Controlled via environment variables.
 */
export const FEATURE_FLAGS = {
  /**
   * V3 "Secure a Spot" flow with intent capture.
   * When false: uses legacy "Activate Exclusive" flow.
   * When true: uses new RefuelIntentModal → SpotSecuredModal flow.
   */
  SECURE_A_SPOT_V3: import.meta.env.VITE_SECURE_A_SPOT_V3 === 'true',
} as const

export type FeatureFlags = typeof FEATURE_FLAGS
```

---

### F0-A: RefuelIntentModal

**New File:** `apps/driver/src/components/RefuelIntentModal/RefuelIntentModal.tsx`

```typescript
import { Coffee, Utensils, Laptop } from 'lucide-react'
import { useState } from 'react'

export type RefuelIntent = 'eat' | 'work' | 'quick-stop'

export interface RefuelDetails {
  intent: RefuelIntent
  partySize?: number
  needsPowerOutlet?: boolean
  isToGo?: boolean
}

interface RefuelIntentModalProps {
  merchantName: string
  isOpen: boolean
  onConfirm: (details: RefuelDetails) => void
  onClose: () => void
}

export function RefuelIntentModal({ merchantName, isOpen, onConfirm, onClose }: RefuelIntentModalProps) {
  const [selectedIntent, setSelectedIntent] = useState<RefuelIntent | null>(null)
  const [partySize, setPartySize] = useState(1)
  const [needsPowerOutlet, setNeedsPowerOutlet] = useState(false)
  const [isToGo, setIsToGo] = useState(false)

  if (!isOpen) return null

  const handleContinue = () => {
    if (!selectedIntent) return

    const details: RefuelDetails = {
      intent: selectedIntent,
      ...(selectedIntent === 'eat' && { partySize }),
      ...(selectedIntent === 'work' && { needsPowerOutlet }),
      ...(selectedIntent === 'quick-stop' && { isToGo }),
    }

    onConfirm(details)
  }

  const intentOptions = [
    {
      id: 'eat' as const,
      icon: Utensils,
      title: 'Eat',
      description: 'Dine-in or grab a meal',
    },
    {
      id: 'work' as const,
      icon: Laptop,
      title: 'Work',
      description: 'Need a workspace or WiFi',
    },
    {
      id: 'quick-stop' as const,
      icon: Coffee,
      title: 'Quick Stop',
      description: 'Coffee, restroom, or to-go',
    },
  ]

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="refuel-intent-title"
    >
      <div className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl">
        {/* Header */}
        <div className="mb-6">
          <h2 id="refuel-intent-title" className="text-2xl text-center mb-2">
            How are you refueling?
          </h2>
          <p className="text-sm text-[#65676B] text-center">
            This helps {merchantName} prepare for your arrival
          </p>
        </div>

        {/* Intent Options */}
        <div className="space-y-3 mb-6" role="radiogroup" aria-label="Refuel intent options">
          {intentOptions.map((option) => {
            const Icon = option.icon
            const isSelected = selectedIntent === option.id

            return (
              <button
                key={option.id}
                onClick={() => setSelectedIntent(option.id)}
                role="radio"
                aria-checked={isSelected}
                className={`w-full p-4 rounded-2xl border-2 transition-all text-left ${
                  isSelected
                    ? 'border-[#1877F2] bg-[#1877F2]/5'
                    : 'border-[#E4E6EB] hover:border-[#1877F2]/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                    isSelected ? 'bg-[#1877F2]' : 'bg-[#F7F8FA]'
                  }`}>
                    <Icon className={`w-5 h-5 ${
                      isSelected ? 'text-white' : 'text-[#65676B]'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-base mb-1">{option.title}</h3>
                    <p className="text-sm text-[#65676B]">{option.description}</p>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {/* Sub-options based on intent */}
        {selectedIntent === 'eat' && (
          <div className="mb-6 bg-[#F7F8FA] rounded-2xl p-4">
            <label className="text-sm font-medium mb-3 block" id="party-size-label">Party Size</label>
            <div className="flex gap-2" role="group" aria-labelledby="party-size-label">
              {[1, 2, 3, 4, 5].map((size) => (
                <button
                  key={size}
                  onClick={() => setPartySize(size)}
                  aria-pressed={partySize === size}
                  className={`flex-1 py-2 px-3 rounded-xl font-medium transition-all ${
                    partySize === size
                      ? 'bg-[#1877F2] text-white'
                      : 'bg-white text-[#050505] border border-[#E4E6EB]'
                  }`}
                >
                  {size === 5 ? '5+' : size}
                </button>
              ))}
            </div>
          </div>
        )}

        {selectedIntent === 'work' && (
          <div className="mb-6 bg-[#F7F8FA] rounded-2xl p-4">
            <button
              onClick={() => setNeedsPowerOutlet(!needsPowerOutlet)}
              aria-pressed={needsPowerOutlet}
              className={`w-full py-3 rounded-xl font-medium transition-all ${
                needsPowerOutlet
                  ? 'bg-[#1877F2] text-white'
                  : 'bg-white text-[#050505] border border-[#E4E6EB]'
              }`}
            >
              {needsPowerOutlet ? '✓ ' : ''}Need Power Outlet
            </button>
          </div>
        )}

        {selectedIntent === 'quick-stop' && (
          <div className="mb-6 bg-[#F7F8FA] rounded-2xl p-4">
            <button
              onClick={() => setIsToGo(!isToGo)}
              aria-pressed={isToGo}
              className={`w-full py-3 rounded-xl font-medium transition-all ${
                isToGo
                  ? 'bg-[#1877F2] text-white'
                  : 'bg-white text-[#050505] border border-[#E4E6EB]'
              }`}
            >
              {isToGo ? '✓ ' : ''}To-Go Order
            </button>
          </div>
        )}

        {/* Action Buttons */}
        <div className="space-y-3">
          <button
            onClick={handleContinue}
            disabled={!selectedIntent}
            className={`w-full py-4 rounded-2xl font-medium transition-all ${
              selectedIntent
                ? 'bg-[#1877F2] text-white hover:bg-[#166FE5] active:scale-[0.98]'
                : 'bg-[#E4E6EB] text-[#65676B] cursor-not-allowed'
            }`}
          >
            Continue
          </button>
          <button
            onClick={onClose}
            className="w-full py-4 bg-white border-2 border-[#E4E6EB] text-[#050505] rounded-2xl font-medium hover:bg-[#F7F8FA] active:scale-[0.98] transition-all"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
```

**Barrel Export:** `apps/driver/src/components/RefuelIntentModal/index.ts`

```typescript
export { RefuelIntentModal } from './RefuelIntentModal'
export type { RefuelIntent, RefuelDetails } from './RefuelIntentModal'
```

---

### F0-B: SpotSecuredModal

**New File:** `apps/driver/src/components/SpotSecuredModal/SpotSecuredModal.tsx`

```typescript
import { CheckCircle } from 'lucide-react'
import type { RefuelDetails } from '../RefuelIntentModal'

interface SpotSecuredModalProps {
  merchantName: string
  merchantBadge?: string
  refuelDetails: RefuelDetails
  remainingMinutes: number
  reservationId: string  // NOTE: UI calls this "Reservation ID", not "verification code"
  isOpen: boolean
  onContinue: () => void  // NOTE: "Continue" not "View Wallet" for V3
}

export function SpotSecuredModal({
  merchantName,
  merchantBadge,
  refuelDetails,
  remainingMinutes,
  reservationId,
  isOpen,
  onContinue,
}: SpotSecuredModalProps) {
  if (!isOpen) return null

  const getIntentLabel = (): string => {
    switch (refuelDetails.intent) {
      case 'eat':
        return `Dining (Party of ${refuelDetails.partySize || 1})`
      case 'work':
        return `Work Session${refuelDetails.needsPowerOutlet ? ' + Power Outlet' : ''}`
      case 'quick-stop':
        return `Quick Stop${refuelDetails.isToGo ? ' (To-Go)' : ''}`
    }
  }

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-end justify-center z-50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="spot-secured-title"
    >
      <div
        className="bg-white rounded-3xl p-8 max-w-md w-full shadow-2xl"
        style={{ marginBottom: 'calc(2rem + env(safe-area-inset-bottom, 0px))' }}
      >
        {/* Icon */}
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <CheckCircle className="w-8 h-8 text-green-600" aria-hidden="true" />
        </div>

        {/* Title */}
        <h2 id="spot-secured-title" className="text-2xl text-center mb-3">Spot Secured</h2>

        {/* Time remaining */}
        <div className="flex justify-center mb-4">
          <div className="bg-[#1877F2]/10 rounded-full px-4 py-2">
            <p className="text-sm text-[#1877F2] font-medium">
              Active for the next {remainingMinutes} {remainingMinutes === 1 ? 'minute' : 'minutes'}
            </p>
          </div>
        </div>

        {/* Description */}
        <p className="text-center text-[#65676B] mb-6">
          Your spot is secured while you're charging.<br />
          Show this at {merchantName}.
        </p>

        {/* Reservation Card */}
        <div className="bg-[#F7F8FA] rounded-2xl p-4 mb-6 border border-[#E4E6EB]">
          <div className="mb-3">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium">{merchantName}</h3>
              {merchantBadge && (
                <div className="px-2.5 py-1 bg-yellow-500/10 rounded-full border border-yellow-500/20">
                  <span className="text-xs text-yellow-700">{merchantBadge}</span>
                </div>
              )}
            </div>
            <p className="text-sm text-[#65676B]">{getIntentLabel()}</p>
          </div>

          {/* Reservation ID - V3: Informational only, no backend validation */}
          <div className="bg-white rounded-xl p-3 border border-[#E4E6EB]">
            <p className="text-xs text-[#65676B] mb-1 text-center">Reservation ID</p>
            <p
              className="text-lg font-mono font-medium text-center tracking-wider"
              aria-label={`Reservation ID: ${reservationId.split('-').join(' ')}`}
            >
              {reservationId}
            </p>
          </div>
        </div>

        {/* Continue Button - V3: No wallet navigation, just continue to walking state */}
        <button
          onClick={onContinue}
          className="w-full py-4 bg-[#1877F2] text-white rounded-2xl font-medium hover:bg-[#166FE5] active:scale-[0.98] transition-all"
        >
          Continue
        </button>
      </div>
    </div>
  )
}
```

**Barrel Export:** `apps/driver/src/components/SpotSecuredModal/index.ts`

```typescript
export { SpotSecuredModal } from './SpotSecuredModal'
```

---

### F0-C: Reservation ID Generation

**New File:** `apps/driver/src/utils/reservationId.ts`

```typescript
/**
 * Generate a Reservation ID in the format: {LOCATION}-{MERCHANT}-{DAY}
 * Example: ATX-ASADAS-025
 *
 * Properties:
 * - Resets daily (based on day of year)
 * - Unique per merchant per day (within location)
 * - Human-readable and easy to communicate verbally
 * - Generated client-side (no backend call required)
 *
 * V3 LIMITATION: IDs are informational only. Backend does NOT validate them.
 * V4 TODO: Add backend endpoint to generate/validate Reservation IDs.
 *
 * COLLISION WARNING: Two merchants with same first 6 letters (e.g., "Starbucks Downtown"
 * and "Starbucks Airport") will have same merchant code. Acceptable for V3 demo.
 *
 * @param merchantName - Merchant display name (e.g., "Asadas Grill")
 * @param locationCode - 3-letter location code (default: "ATX" for Austin)
 * @returns Formatted Reservation ID (e.g., "ATX-ASADAS-025")
 */
export function generateReservationId(merchantName: string, locationCode = 'ATX'): string {
  // V4 TODO: Get locationCode from backend merchant data or user's geolocation

  // Extract letters from merchant name (uppercase, letters only)
  const lettersOnly = merchantName.toUpperCase().replace(/[^A-Z]/g, '')

  // Ensure minimum 3 characters, maximum 6
  // If name has < 3 letters, pad with 'X'
  // Examples: "A1 Diner" -> "ADINER", "42" -> "XXX", "Jo's" -> "JOSXXX"
  const merchantCode = lettersOnly.length >= 3
    ? lettersOnly.substring(0, 6)
    : lettersOnly.padEnd(3, 'X')

  // Get day of year (1-366) for daily reset
  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 0)
  const diff = now.getTime() - start.getTime()
  const oneDay = 1000 * 60 * 60 * 24
  const dayOfYear = Math.floor(diff / oneDay)

  // Format as 3-digit string (001-366)
  const dailyNumber = String(dayOfYear).padStart(3, '0')

  return `${locationCode}-${merchantCode}-${dailyNumber}`
}

/**
 * Parse a Reservation ID to extract components.
 * Useful for future backend validation.
 *
 * @param id - Reservation ID string
 * @returns Parsed components or null if invalid format
 */
export function parseReservationId(id: string): {
  locationCode: string
  merchantCode: string
  dayOfYear: number
} | null {
  const parts = id.split('-')
  if (parts.length !== 3) return null

  const [locationCode, merchantCode, dayStr] = parts

  // Validate location code (3 uppercase letters)
  if (!/^[A-Z]{3}$/.test(locationCode)) return null

  // Validate merchant code (3-6 uppercase letters)
  if (!/^[A-Z]{3,6}$/.test(merchantCode)) return null

  const dayOfYear = parseInt(dayStr, 10)
  if (isNaN(dayOfYear) || dayOfYear < 1 || dayOfYear > 366) return null

  return { locationCode, merchantCode, dayOfYear }
}

/**
 * Check if a Reservation ID was generated today.
 *
 * @param id - Reservation ID to validate
 * @returns true if ID was generated today
 */
export function isReservationIdFromToday(id: string): boolean {
  const parsed = parseReservationId(id)
  if (!parsed) return false

  const now = new Date()
  const start = new Date(now.getFullYear(), 0, 0)
  const diff = now.getTime() - start.getTime()
  const oneDay = 1000 * 60 * 60 * 24
  const todayDayOfYear = Math.floor(diff / oneDay)

  return parsed.dayOfYear === todayDayOfYear
}
```

---

### F0-D: Update Activation Flow in MerchantDetailsScreen

**File:** `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`

**NEW FLOW (behind feature flag):**
```
User taps "Secure a Spot" → RefuelIntentModal → OTP (if not authenticated) → Activate with intent → SpotSecuredModal → Continue → walking state
```

---

#### Step 1: Add Imports (top of file)

**FIND (around line 1-15, import section):**

**ADD:**
```typescript
import { FEATURE_FLAGS } from '../../config/featureFlags'
import { RefuelIntentModal, type RefuelDetails } from '../RefuelIntentModal'
import { SpotSecuredModal } from '../SpotSecuredModal'
import { generateReservationId } from '../../utils/reservationId'
import { ApiError } from '../../services/api'
```

---

#### Step 2: Add State Variables

**FIND (around line 38-43):**
```typescript
  const [flowState, setFlowState] = useState<FlowState>('idle')
  const [showActivateModal, setShowActivateModal] = useState(false)
```

**ADD AFTER:**
```typescript
  // V3: Intent capture state (only used when SECURE_A_SPOT_V3 is enabled)
  const [showRefuelIntentModal, setShowRefuelIntentModal] = useState(false)
  const [showSpotSecuredModal, setShowSpotSecuredModal] = useState(false)
  const [refuelDetails, setRefuelDetails] = useState<RefuelDetails | null>(null)
  const [reservationId, setReservationId] = useState<string | null>(null)
```

---

#### Step 3: Add Validation Check for place_id

**ADD after merchantData fetch (around line 32):**
```typescript
  // V3: Validate merchant data has required fields
  useEffect(() => {
    if (merchantData && !merchantData.merchant.place_id) {
      console.warn('[V3] Merchant missing place_id, sending merchant_place_id=null')
    }
  }, [merchantData])
```

---

#### Step 4: Add Intent Capture Handlers

**ADD NEW FUNCTIONS (after handleAddToWallet, around line 210):**
```typescript
  // ============================================
  // V3: "Secure a Spot" flow handlers
  // Only active when FEATURE_FLAGS.SECURE_A_SPOT_V3 is true
  // ============================================

  const handleSecureSpot = () => {
    // Show intent capture modal first
    setShowRefuelIntentModal(true)
  }

  const handleIntentConfirm = (details: RefuelDetails) => {
    setRefuelDetails(details)
    setShowRefuelIntentModal(false)

    // Proceed to authentication if needed
    if (!isAuthenticated) {
      setShowActivateModal(true)
    } else {
      handleActivateWithIntent(details)
    }
  }

  const handleActivateWithIntent = async (details: RefuelDetails) => {
    if (!merchantId || !merchantData) {
      alert('Missing merchant data')
      return
    }

    // Get location (OPTIONAL for V3)
    let lat: number | null = null
    let lng: number | null = null
    let accuracy_m: number | undefined

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 5000,
          maximumAge: 60000
        })
      })
      lat = position.coords.latitude
      lng = position.coords.longitude
      accuracy_m = position.coords.accuracy || undefined
      console.log('[V3] Location acquired:', { lat, lng, accuracy_m })
    } catch (err) {
      // V3: Location is optional, proceed without it
      console.log('[V3] Location unavailable, proceeding with null:', err)
    }

    try {
      const response = await activateExclusive.mutateAsync({
        merchant_id: merchantId,
        // CORRECT: Use actual place_id from merchant data, not merchantId
        merchant_place_id: merchantData.merchant.place_id ?? null,
        charger_id: chargerId,
        lat,  // V3: Can be null
        lng,  // V3: Can be null
        accuracy_m,
        // V3: Intent capture fields
        intent: details.intent,
        party_size: details.partySize,
        needs_power_outlet: details.needsPowerOutlet,
        is_to_go: details.isToGo,
      })

      const sessionId = response.exclusive_session.id
      setExclusiveSessionId(sessionId)
      setRemainingSeconds(response.exclusive_session.remaining_seconds)

      // Generate Reservation ID (V3: client-side only, informational)
      // IMPORTANT: Persist to localStorage keyed by session ID to survive remounts
      const storageKey = `reservation_id_${sessionId}`
      let id = localStorage.getItem(storageKey)
      if (!id) {
        id = generateReservationId(merchantData.merchant.name)
        localStorage.setItem(storageKey, id)
      }
      setReservationId(id)

      setShowActivateModal(false)
      setShowSpotSecuredModal(true)
    } catch (err) {
      console.error('[V3] Failed to secure spot:', err)

      // Clear intent state on error so user can retry
      setRefuelDetails(null)

      if (err instanceof ApiError) {
        if (err.status === 400) {
          alert('Invalid request. Please check your selections and try again.')
        } else if (err.status === 401) {
          alert('Authentication required. Please sign in again.')
          setIsAuthenticated(false)
          setShowActivateModal(true)
        } else if (err.status >= 500) {
          alert('Server error. Please try again in a moment.')
        } else {
          alert('Failed to secure spot. Please try again.')
        }
      } else {
        alert('Network error. Please check your connection and try again.')
      }
    }
  }

  const handleSpotSecuredContinue = () => {
    // Close modal and transition to walking state
    setShowSpotSecuredModal(false)
    setFlowState('walking')
    // V4 TODO: Open wallet modal or navigate to wallet route
  }

  // V3: Cleanup reservation ID from localStorage when session expires or completes
  useEffect(() => {
    if (remainingSeconds !== null && remainingSeconds <= 0) {
      if (exclusiveSessionId) {
        const storageKey = `reservation_id_${exclusiveSessionId}`
        localStorage.removeItem(storageKey)
      }
    }
  }, [remainingSeconds, exclusiveSessionId])

  // Cleanup when transitioning out of session state
  useEffect(() => {
    if (flowState === 'idle' && exclusiveSessionId) {
      const storageKey = `reservation_id_${exclusiveSessionId}`
      localStorage.removeItem(storageKey)
    }
  }, [flowState, exclusiveSessionId])
```

---

#### Step 5: Update Button Text and Handler (Feature Flag)

**FIND (around line 306-314):**
```typescript
        {flowState === 'idle' && merchantData.wallet.can_add && (
          <Button
            variant="primary"
            className="w-full"
            onClick={handleAddToWallet}
            disabled={activateExclusive.isPending}
          >
            {activateExclusive.isPending ? 'Activating...' : 'Activate Exclusive'}
          </Button>
        )}
```

**REPLACE WITH:**
```typescript
        {flowState === 'idle' && merchantData.wallet.can_add && (
          <Button
            variant="primary"
            className="w-full"
            onClick={FEATURE_FLAGS.SECURE_A_SPOT_V3 ? handleSecureSpot : handleAddToWallet}
            disabled={activateExclusive.isPending}
          >
            {activateExclusive.isPending
              ? (FEATURE_FLAGS.SECURE_A_SPOT_V3 ? 'Securing...' : 'Activating...')
              : (FEATURE_FLAGS.SECURE_A_SPOT_V3 ? 'Secure a Spot' : 'Activate Exclusive')
            }
          </Button>
        )}
```

---

#### Step 6: Add Modal Renders

**FIND (after existing modals, around line 360):**

**ADD:**
```typescript
      {/* V3: Refuel Intent Modal (only when feature flag enabled) */}
      {FEATURE_FLAGS.SECURE_A_SPOT_V3 && (
        <RefuelIntentModal
          merchantName={merchantData?.merchant.name || ''}
          isOpen={showRefuelIntentModal}
          onClose={() => setShowRefuelIntentModal(false)}
          onConfirm={handleIntentConfirm}
        />
      )}

      {/* V3: Spot Secured Modal (only when feature flag enabled) */}
      {FEATURE_FLAGS.SECURE_A_SPOT_V3 && refuelDetails && reservationId && merchantData && (
        <SpotSecuredModal
          merchantName={merchantData.merchant.name}
          merchantBadge={merchantData.perk.badge}
          refuelDetails={refuelDetails}
          remainingMinutes={remainingMinutes}
          reservationId={reservationId}
          isOpen={showSpotSecuredModal}
          onContinue={handleSpotSecuredContinue}
        />
      )}
```

**ALSO UPDATE existing ActivateExclusiveModal onSuccess:**

**FIND:**
```typescript
        onSuccess={async () => {
          setIsAuthenticated(true)
          setShowActivateModal(false)
          await handleActivateExclusive()
        }}
```

**REPLACE WITH:**
```typescript
        onSuccess={async () => {
          setIsAuthenticated(true)
          setShowActivateModal(false)
          // V3: Use intent flow if flag enabled and intent was captured
          if (FEATURE_FLAGS.SECURE_A_SPOT_V3 && refuelDetails) {
            await handleActivateWithIntent(refuelDetails)
          } else {
            await handleActivateExclusive()
          }
        }}
```

---

## F0-F: Update Backend Pydantic Schema (CRITICAL BLOCKER)

**File:** `backend/app/routers/exclusive.py`

### Step 1: Detect Pydantic Version (MANDATORY GATE)

**STOP.** Run this command and note the output. It determines which syntax to use.

```bash
cd /Users/jameskirk/Desktop/Nerava/backend
python -c "import pydantic; v=pydantic.VERSION; print(f'Pydantic v{v} → Use ' + ('@field_validator' if v.startswith('2') else '@validator'))"
```

**Expected output:**
- `Pydantic v2.x.x → Use @field_validator`
- `Pydantic v1.x.x → Use @validator`

**IF OUTPUT IS UNCLEAR:** Do not proceed. Resolve Pydantic version first.

### Step 2: Update Schema (version-specific)

**Choose the CORRECT version below based on Step 1 output.**

**FIND existing ActivateExclusiveRequest class (line 34-42):**
```python
class ActivateExclusiveRequest(BaseModel):
    merchant_id: Optional[str] = None
    merchant_place_id: Optional[str] = None
    charger_id: str
    charger_place_id: Optional[str] = None
    intent_session_id: Optional[str] = None
    lat: float
    lng: float
    accuracy_m: Optional[float] = None
```

**REPLACE WITH (Pydantic v1):**
```python
from pydantic import BaseModel, validator
from typing import Optional

class ActivateExclusiveRequest(BaseModel):
    merchant_id: Optional[str] = None
    merchant_place_id: Optional[str] = None
    charger_id: str
    charger_place_id: Optional[str] = None
    intent_session_id: Optional[str] = None
    lat: Optional[float] = None  # V3: Optional, null when location unavailable
    lng: Optional[float] = None  # V3: Optional, null when location unavailable
    accuracy_m: Optional[float] = None
    # V3: Intent capture fields
    intent: Optional[str] = None  # "eat" | "work" | "quick-stop"
    party_size: Optional[int] = None
    needs_power_outlet: Optional[bool] = None
    is_to_go: Optional[bool] = None

    @validator('intent')
    def validate_intent(cls, v):
        if v is not None and v not in ('eat', 'work', 'quick-stop'):
            raise ValueError('intent must be one of: eat, work, quick-stop')
        return v
```

**REPLACE WITH (Pydantic v2):**
```python
from pydantic import BaseModel, field_validator
from typing import Optional

class ActivateExclusiveRequest(BaseModel):
    merchant_id: Optional[str] = None
    merchant_place_id: Optional[str] = None
    charger_id: str
    charger_place_id: Optional[str] = None
    intent_session_id: Optional[str] = None
    lat: Optional[float] = None  # V3: Optional, null when location unavailable
    lng: Optional[float] = None  # V3: Optional, null when location unavailable
    accuracy_m: Optional[float] = None
    # V3: Intent capture fields
    intent: Optional[str] = None  # "eat" | "work" | "quick-stop"
    party_size: Optional[int] = None
    needs_power_outlet: Optional[bool] = None
    is_to_go: Optional[bool] = None

    @field_validator('intent')
    @classmethod
    def validate_intent(cls, v):
        if v is not None and v not in ('eat', 'work', 'quick-stop'):
            raise ValueError('intent must be one of: eat, work, quick-stop')
        return v
```

### Response Schema Contract (V3 Decision)

**Decision:** Intent fields are **NOT returned** in the activation response for V3.

**Rationale:**
- Frontend doesn't need them back (it already has them from user input)
- Avoids response schema changes that could break existing clients
- Simpler rollout

**V4 TODO:** If intent fields need to be returned (e.g., for session restore), update `ActivateExclusiveResponse` schema.

**Current response shape (unchanged for V3):**
```python
class ActivateExclusiveResponse(BaseModel):
    exclusive_session: ExclusiveSessionResponse  # Does NOT include intent fields
    # ... other existing fields ...
```

**If you need intent in response later:**
```python
# V4: Add to ExclusiveSessionResponse
class ExclusiveSessionResponse(BaseModel):
    # ... existing fields ...
    intent: Optional[str] = None  # V4+
    intent_metadata: Optional[dict] = None  # V4+
```

---

## F0-G: Update Backend SQLAlchemy Model (CRITICAL BLOCKER)

**File:** `backend/app/models/exclusive_session.py`

> **⚠️ WARNING:** Migration without model update = silent data loss. The migration adds columns to the database, but SQLAlchemy won't write to them unless the model is updated.

### Step 1: Verify model file exists

```bash
ls -la /Users/jameskirk/Desktop/Nerava/backend/app/models/exclusive_session.py
```

### Step 2: Add columns to ExclusiveSession class

**FIND the ExclusiveSession class definition and ADD these columns:**

```python
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB

class ExclusiveSession(Base):
    __tablename__ = 'exclusive_sessions'

    # ... existing columns (id, user_id, merchant_id, etc.) ...

    # V3: Intent capture fields - ADD THESE LINES
    intent = Column(String(50), nullable=True)  # "eat" | "work" | "quick-stop"
    intent_metadata = Column(JSONB, nullable=True)  # {party_size, needs_power_outlet, is_to_go}
```

### Step 3: Verify columns are in model

```bash
cd /Users/jameskirk/Desktop/Nerava/backend
python -c "
from app.models.exclusive_session import ExclusiveSession
cols = [c.name for c in ExclusiveSession.__table__.columns]
assert 'intent' in cols, 'ERROR: intent column missing from model'
assert 'intent_metadata' in cols, 'ERROR: intent_metadata column missing from model'
print('✓ Model updated correctly')
"
```

**IF ASSERTION FAILS:** Model was not updated. Fix before proceeding.

### Step 4: Update endpoint handler to save intent data

**CRITICAL:** Activation ALWAYS creates a new `ExclusiveSession` row. The endpoint checks for existing active sessions (see `backend/app/routers/exclusive.py` lines 161-164) and returns an error if one exists, preventing reuse. Therefore, intent fields are always set during initial creation, never updated on existing records.

**If session reuse were ever implemented:** The handler would need to update `intent` and `intent_metadata` on the existing `ExclusiveSession` record, not just set them during creation.

**In `backend/app/routers/exclusive.py`, find the activate endpoint and update session creation:**

```python
# When creating the session:
session = ExclusiveSession(
    # ... existing fields ...
    intent=request.intent,
    intent_metadata={
        'party_size': request.party_size,
        'needs_power_outlet': request.needs_power_outlet,
        'is_to_go': request.is_to_go,
    } if request.intent else None,
)
```

---

## F0-H: Create Migration 054

**BEFORE creating migration file, verify latest migration number:**

```bash
cd /Users/jameskirk/Desktop/Nerava/backend
ls alembic/versions/*.py | tail -1
# Expected: 053_add_verified_visits.py
# If different, update down_revision in migration file below
```

**New File:** `backend/alembic/versions/054_add_intent_to_exclusive_sessions.py`

```python
"""Add intent fields to exclusive_sessions table

Revision ID: 054
Revises: 053
Create Date: 2026-01-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '054'
down_revision = '053'
branch_labels = None
depends_on = None


def upgrade():
    # Add intent columns to exclusive_sessions
    op.add_column('exclusive_sessions', sa.Column('intent', sa.String(50), nullable=True))
    op.add_column('exclusive_sessions', sa.Column('intent_metadata', JSONB, nullable=True))


def downgrade():
    op.drop_column('exclusive_sessions', 'intent_metadata')
    op.drop_column('exclusive_sessions', 'intent')
```

**VERIFICATION after creating migration:**
```bash
cd /Users/jameskirk/Desktop/Nerava/backend
alembic check
# Should show no errors

alembic upgrade head
# Should apply migration successfully

# Verify columns exist:
python -c "
from app.models.exclusive_session import ExclusiveSession
print('intent' in [c.name for c in ExclusiveSession.__table__.columns])
print('intent_metadata' in [c.name for c in ExclusiveSession.__table__.columns])
"
# Should print: True, True
```

---

## iOS Native Changes (SKIP FOR V3)

The web app handles intent capture entirely client-side. Native bridge extension is NOT needed for V3.

**V4 TODO:** If intent data needs to be:
- Persisted in native storage
- Included in native session events
- Used for background location context

Then extend NativeBridge.swift accordingly.

---

## Implementation Order

### Phase 1: Backend (MUST complete before frontend)

1. **🛑 GATE: Detect Pydantic version** - Run version check, note output
2. **Update SQLAlchemy model (F0-G)** - Add intent columns to ExclusiveSession class
3. **🛑 GATE: Verify model columns** - Run verification script, must pass
4. **Create migration 054 (F0-H)** - Add columns to database
5. **Run migration** - `alembic upgrade head`
6. **Update Pydantic schema (F0-F)** - Use correct decorator based on version
7. **Test backend** - Verify existing endpoints still work (null intent)

### Phase 2: Frontend

1. **Update TypeScript interface (F0-E)** - Add intent fields with `number | null`
2. **🛑 GATE: Run typecheck** - Must pass, do not proceed if fails
3. **Create feature flag config (F0-I)** - featureFlags.ts
4. **Create reservationId utility (F0-C)** - reservationId.ts
5. **Create RefuelIntentModal (F0-A)** - Component + barrel export
6. **Create SpotSecuredModal (F0-B)** - Component + barrel export
7. **Update MerchantDetailsScreen (F0-D)** - All integration steps
8. **🛑 GATE: Test with flag=false** - Old flow must work identically
9. **🛑 GATE: Test with flag=true** - New flow must complete end-to-end

**Backward Compatibility Verification (flag=false):**
- Button says "Activate Exclusive"
- No RefuelIntentModal appears
- ExclusiveActivatedModal appears on success
- handleAddToWallet() is called, not handleSecureSpot()

**New Flow Verification (flag=true):**
- Button says "Secure a Spot"
- RefuelIntentModal appears first
- SpotSecuredModal appears with Reservation ID
- handleSecureSpot() → handleActivateWithIntent() flow works

### Phase 3: Deployment

1. **Deploy backend** - Migration runs automatically
2. **Deploy frontend (flag=false)** - No visible change
3. **Enable flag in staging** - Test new flow
4. **Enable flag in production** - Gradual rollout

---

## Validation Commands

### Backend
```bash
cd /Users/jameskirk/Desktop/Nerava/backend

# Compile check
python -m compileall app

# Check migration is valid
alembic check

# Run migration
alembic upgrade head

# Test existing endpoint still works (no intent)
pytest tests/api/test_exclusive.py -v

# Test new fields accepted
curl -X POST http://localhost:8000/v1/exclusive/activate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"charger_id":"test","lat":null,"lng":null,"intent":"eat","party_size":2}'
```

### Web
```bash
cd /Users/jameskirk/Desktop/Nerava/apps/driver

# MANDATORY: Type check must pass
npm run typecheck

# Build check
npm run build

# Start dev server with flag disabled
VITE_SECURE_A_SPOT_V3=false npm run dev

# Start dev server with flag enabled
VITE_SECURE_A_SPOT_V3=true npm run dev
```

### iOS (no changes, verify no regressions)
```bash
cd /Users/jameskirk/Desktop/Nerava/Nerava
xcodebuild -scheme Nerava -configuration Debug build
```

---

## Testing Checklist

### Feature Flag = false (Old Flow)

1. [ ] "Activate Exclusive" button appears
2. [ ] Tapping button opens OTP modal (if not authenticated)
3. [ ] Activation succeeds and shows ExclusiveActivatedModal
4. [ ] No RefuelIntentModal or SpotSecuredModal appears

### Feature Flag = true (New Flow)

1. [ ] "Secure a Spot" button appears
2. [ ] Tapping button opens RefuelIntentModal
3. [ ] User can select intent (Eat/Work/Quick Stop)
4. [ ] Sub-options appear based on intent:
   - Eat: Party size buttons (1-5+)
   - Work: "Need Power Outlet" toggle
   - Quick Stop: "To-Go Order" toggle
5. [ ] OTP modal appears after intent selection (if not authenticated)
6. [ ] Activation succeeds with intent data sent to backend
7. [ ] SpotSecuredModal shows with:
   - "Spot Secured" title
   - Remaining time
   - Reservation ID in format ATX-{MERCHANT}-{DAY}
   - "Continue" button
8. [ ] "Continue" button closes modal and transitions to walking state
9. [ ] Reservation ID does NOT change during active session

### Error Handling

10. [ ] Network failure shows appropriate message
11. [ ] 400 error shows "Invalid request"
12. [ ] 401 error re-opens OTP modal
13. [ ] 500 error shows "Server error"
14. [ ] Location unavailable: activation proceeds with null lat/lng (NOT 0/0)

### Data Integrity (CRITICAL - See Rules Section)

15. [ ] **Rule 1:** `merchant_place_id` in request is Google Place ID (starts with `ChIJ`) or null, NOT our UUID
16. [ ] **Rule 2:** `lat`/`lng` are `null` when unavailable, NEVER `0`
17. [ ] **Rule 2:** Database shows `NULL` for lat/lng when location unavailable (query: `SELECT lat, lng FROM exclusive_sessions WHERE lat = 0`)
18. [ ] **Rule 5:** Database shows `NULL` for intent when old flow used (flag=false)
19. [ ] **Rule 5:** Database shows intent + intent_metadata populated when new flow used (flag=true)

### Backend

20. [ ] Migration 054 applies successfully
21. [ ] **Rule 5:** SQLAlchemy model has `intent` and `intent_metadata` columns
22. [ ] **Rule 5:** Handler writes intent to session (not just schema accepts it)
23. [ ] Existing activations (no intent) still work
24. [ ] New activations with intent are stored in database
25. [ ] Intent validation rejects invalid values (not eat/work/quick-stop)
26. [ ] Pydantic decorator matches version (@validator v1, @field_validator v2)
27. [ ] **Rule 2:** Schema accepts `null` for lat/lng (not just Optional[float])

---

## Rollout Plan

### Stage 1: Local Development
```bash
# .env.local
VITE_SECURE_A_SPOT_V3=true
```
- Full testing of new flow
- Verify old flow still works when flag=false

### Stage 2: Staging Deployment
```bash
# .env.staging
VITE_SECURE_A_SPOT_V3=true
```
- Deploy backend with migration
- Deploy frontend with flag enabled
- QA team testing
- Fix any issues found

### Stage 3: Production (Flag Disabled)
```bash
# .env.production
VITE_SECURE_A_SPOT_V3=false
```
- Deploy backend with migration (safe, new columns are nullable)
- Deploy frontend with flag disabled
- Verify production is stable
- No visible change to users

### Stage 4: Production (Flag Enabled)
```bash
# .env.production
VITE_SECURE_A_SPOT_V3=true
```
- Enable flag
- Monitor for errors
- Rollback: set flag to false and redeploy frontend

### Rollback Plan

If issues found after enabling flag in production:
1. Set `VITE_SECURE_A_SPOT_V3=false` in environment
2. Redeploy frontend (or if using runtime config, just update config)
3. Old flow immediately active
4. Investigate and fix issues
5. Re-enable flag when ready

---

## 🛑 Data Integrity Smoke Test (MANDATORY BEFORE MERGE)

**DO NOT merge or deploy until this test passes.** This catches the silent data corruption bugs.

### Test Script

```bash
cd /Users/jameskirk/Desktop/Nerava/backend

# 1. Start backend locally
uvicorn app.main:app --reload &
sleep 3

# 2. Get a test token (use your auth flow)
TOKEN="your_test_token_here"

# 3. Send activation request with V3 fields
curl -X POST http://localhost:8000/v1/exclusive/activate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "merchant_id": "test-merchant-uuid",
    "merchant_place_id": "ChIJxxxxxxxx",
    "charger_id": "test-charger-uuid",
    "lat": null,
    "lng": null,
    "intent": "eat",
    "party_size": 2
  }'

# 4. Query database and verify
python -c "
from app.db import get_db
from app.models.exclusive_session import ExclusiveSession
from sqlalchemy import desc

db = next(get_db())
session = db.query(ExclusiveSession).order_by(desc(ExclusiveSession.created_at)).first()

# ASSERTIONS - any failure = DO NOT SHIP
assert session is not None, 'No session created'

# Location integrity (Rule 2: Never use zero)
assert session.lat is None, f'ERROR: lat should be NULL, got {session.lat}'
assert session.lng is None, f'ERROR: lng should be NULL, got {session.lng}'
assert session.lat != 0, 'CRITICAL: lat is 0 (null island bug)'
assert session.lng != 0, 'CRITICAL: lng is 0 (null island bug)'

# Intent persistence (Rule 5: Migration + Model + Handler)
assert session.intent == 'eat', f'ERROR: intent not saved, got {session.intent}'
assert session.intent_metadata is not None, 'ERROR: intent_metadata not saved'
assert session.intent_metadata.get('party_size') == 2, 'ERROR: party_size not in metadata'

# Place ID integrity (Rule 1: Never fabricate Place IDs)
if session.merchant_place_id is not None:
    # Detect UUIDs (authoritative check)
    is_uuid = len(session.merchant_place_id) == 36 and session.merchant_place_id.count('-') == 4
    assert not is_uuid, f'CRITICAL: merchant_place_id looks like a UUID: {session.merchant_place_id}'
    # Heuristic check: Many (but not all) Google Place IDs start with 'ChIJ'
    # This is informational only, not authoritative validation
    if not session.merchant_place_id.startswith('ChIJ'):
        print(f'   ⚠️  NOTE: merchant_place_id does not start with ChIJ (heuristic check): {session.merchant_place_id}')

print('✅ All data integrity checks passed')
print(f'   lat: {session.lat} (NULL = correct)')
print(f'   lng: {session.lng} (NULL = correct)')
print(f'   intent: {session.intent}')
print(f'   intent_metadata: {session.intent_metadata}')
print(f'   merchant_place_id: {session.merchant_place_id}')
"
```

### What This Catches

| Bug | Symptom | This Test Catches It |
|-----|---------|---------------------|
| lat/lng = 0 fallback | Sessions at null island | ✅ Asserts lat/lng are NULL, not 0 |
| merchant_place_id = merchantId | Wrong Google Place IDs | ✅ Detects UUID format in place_id field |
| Intent not saved | Empty intent column | ✅ Asserts intent == 'eat' |
| Migration ran but model not updated | Columns exist but NULL | ✅ Asserts intent_metadata populated |
| Pydantic rejects null lat/lng | 422 error on request | ✅ Request would fail |
| Non-Google Place ID | Invalid enrichment data | ⚠️ Warns if place_id doesn't start with 'ChIJ' |

**IF ANY ASSERTION FAILS:** Fix the bug. Do not proceed with deployment.

---

## Success Criteria

### Functional (must work)
1. [ ] Feature flag controls which flow is active
2. [ ] Old flow works identically when flag=false (dual-path verified)
3. [ ] New flow completes: Intent → OTP → Activate → SpotSecured → Walking
4. [ ] Reservation ID format is ATX-{MERCHANT}-{DAY}
5. [ ] TypeScript compiles with no errors
6. [ ] iOS app still builds (no changes made)

### Data Integrity (must not corrupt - see Rules section)
7. [ ] **Rule 1 (Place IDs):** `merchant_place_id` is Google Place ID or null, NEVER our UUID
8. [ ] **Rule 2 (Location):** `lat`/`lng` are null when unavailable, NEVER 0
9. [ ] **Rule 3 (Labels):** Button says "Continue", NOT "View Wallet"
10. [ ] **Rule 4 (Flag):** Both flows exist, flag controls which runs
11. [ ] **Rule 5 (Persistence):** Intent data saved to database (all three: migration + model + handler)
12. [ ] **Smoke test passes:** All assertions in data integrity smoke test are green

### Verification Queries (run after testing)
```sql
-- Rule 1: No UUIDs in place_id (should return 0)
-- Detects UUIDs using regex pattern (not ChIJ assumption)
SELECT COUNT(*) FROM exclusive_sessions
WHERE merchant_place_id IS NOT NULL
  AND merchant_place_id ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$';

-- Rule 2: No null island sessions (should return 0)
SELECT COUNT(*) FROM exclusive_sessions WHERE lat = 0 AND lng = 0;

-- Rule 5: Intent persistence working (should return rows with intent)
SELECT id, intent, intent_metadata FROM exclusive_sessions
WHERE intent IS NOT NULL ORDER BY created_at DESC LIMIT 5;
```

---

## Files Summary

### New Files (Web)
- `apps/driver/src/config/featureFlags.ts`
- `apps/driver/src/utils/reservationId.ts`
- `apps/driver/src/components/RefuelIntentModal/RefuelIntentModal.tsx`
- `apps/driver/src/components/RefuelIntentModal/index.ts`
- `apps/driver/src/components/SpotSecuredModal/SpotSecuredModal.tsx`
- `apps/driver/src/components/SpotSecuredModal/index.ts`

### Modified Files (Web)
- `apps/driver/src/services/api.ts` (ActivateExclusiveRequest interface)
- `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`

### New Files (Backend)
- `backend/alembic/versions/054_add_intent_to_exclusive_sessions.py`

### Modified Files (Backend)
- `backend/app/routers/exclusive.py` (ActivateExclusiveRequest schema)
- `backend/app/models/exclusive_session.py` (intent columns)

### NOT Modified (V3)
- iOS native code
- P1/P2 components (deferred to V4)
- Wallet component/route (deferred to V4)
