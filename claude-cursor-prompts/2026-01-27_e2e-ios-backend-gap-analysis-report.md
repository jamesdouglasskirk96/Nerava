# iOS <-> Backend E2E Validation + Production Gap Report

**Date**: 2026-01-27
**Scope**: iOS native shell + driver web app + backend API
**Focus**: Real production flows, not UI polish

---

## 1) End-to-End Flow Map

### Flow 1: OTP Auth

```
User enters phone -> SMS OTP -> Verify -> JWT stored -> Token synced to native
```

| Step | Frontend/Native | Backend Endpoint | Backend Service |
|------|----------------|-----------------|-----------------|
| Enter phone | `ActivateExclusiveModal.tsx` L62-80 | | |
| Send OTP | `services/auth.ts` L36-82 `otpStart()` | `POST /v1/auth/otp/start` | `otp_service_v2.py` -> `otp_provider.py` (Twilio) |
| Verify OTP | `services/auth.ts` L87-135 `otpVerify()` | `POST /v1/auth/otp/verify` | `otp_service_v2.py` -> JWT generation |
| Store token | `auth.ts` stores in localStorage | | |
| Sync to native | `useNativeBridge.ts` L137-156 | | |
| Native stores | `NativeBridge.swift` L293 -> `SessionEngine.swift` L395 -> `KeychainService.swift` | | |

### Flow 2: Discovery

```
Location -> Intent capture -> Chargers + merchants -> Set charger target on native
```

| Step | Frontend/Native | Backend Endpoint | Backend Service |
|------|----------------|-----------------|-----------------|
| Get location | `useNativeBridge.ts` L217-231 / `LocationService.swift` | | |
| Capture intent | `services/api.ts` L186-228 `useIntentCapture()` | `POST /v1/intent/capture` | `intent_service.py` |
| Zod validation | `services/schemas.ts` L10-44 `CaptureIntentResponseSchema` | | |
| Set charger target | `useNativeBridge.ts` L172-176 | | |
| Native geofence | `NativeBridge.swift` L287-291 -> `SessionEngine.swift` L360-392 -> `GeofenceManager.swift` | | |

### Flow 3: Merchant Details + Amenity Voting

```
Tap merchant -> Fetch details -> Show amenities -> Vote
```

| Step | Frontend/Native | Backend Endpoint | Backend Service |
|------|----------------|-----------------|-----------------|
| Fetch details | `services/api.ts` L231-249 `useMerchantDetails()` | `GET /v1/merchants/{id}` | `merchant_details.py` |
| Zod validation | `schemas.ts` L84-128 `MerchantDetailsResponseSchema` | | |
| Show amenities | `MerchantDetailsScreen.tsx` L521-536, `AmenityVotes.tsx` | | |
| Vote | `services/api.ts` L500-519 `voteAmenity()` | `POST /v1/merchants/{id}/amenities/{amenity}/vote` | `routers/merchants.py` L104-205 |

### Flow 4: Exclusive Activation

```
Auth check -> Activate exclusive -> Create session -> Notify native -> Start timer
```

| Step | Frontend/Native | Backend Endpoint | Backend Service |
|------|----------------|-----------------|-----------------|
| Activate | `services/api.ts` L316-322 `activateExclusive()` | `POST /v1/exclusive/activate` | `routers/exclusive.py` L140-401 |
| Notify native | `useNativeBridge.ts` L188-197 `confirmExclusiveActivated()` | | |
| Native transition | `SessionEngine.swift` L413-457: ANCHORED -> SESSION_ACTIVE | | |
| Native geofence | Merchant geofence set, hard timeout started | | |
| Web timer | `useExclusiveSessionState.ts` L84-160 | | |

### Flow 5: In-Transit

```
Native detects departure -> Grace period -> Web notified -> Event emitted
```

| Step | Frontend/Native | Backend Endpoint | Backend Service |
|------|----------------|-----------------|-----------------|
| Detect departure | `SessionEngine.swift` L539-549: distance > anchor radius | | |
| State transition | SESSION_ACTIVE -> IN_TRANSIT + `departed_charger` event | | |
| Notify web | `NativeBridge.swift` L222-241 `sendToWeb(.sessionStateChanged)` | | |
| Web receives | `useNativeBridge.ts` L99-104 | | |
| Emit event | `APIClient.swift` L29-67 `emitSessionEvent()` | `POST /v1/native/session-events` | `routers/native_events.py` L134-182 |
| Grace period | `SessionEngine.swift` L701-708: deadline at now + gracePeriodSeconds | | |

### Flow 6: At-Merchant

```
Geofence entry -> Cancel grace period -> Show arrival UI
```

| Step | Frontend/Native | Backend Endpoint | Backend Service |
|------|----------------|-----------------|-----------------|
| Detect arrival | `SessionEngine.swift` L551-563: within merchant radius | | |
| State transition | IN_TRANSIT -> AT_MERCHANT + `entered_merchant_zone` | | |
| Cancel grace | `SessionEngine.swift` L559 | | |
| Notify web | `SESSION_STATE_CHANGED` with `AT_MERCHANT` | | |
| Show modal | `ArrivalConfirmationModal.tsx` L25-164 | | |

### Flow 7: Verify/Complete

```
Auto-verify on arrival -> Show code -> User taps Done -> Notify native -> Session ended
```

| Step | Frontend/Native | Backend Endpoint | Backend Service |
|------|----------------|-----------------|-----------------|
| Verify visit | `ArrivalConfirmationModal.tsx` L40-76 | `POST /v1/exclusive/verify` | `routers/exclusive.py` L580-761 |
| Show code | `ArrivalConfirmationModal.tsx` L117-131 | | |
| User taps Done | Calls `confirmVisitVerified()` | | |
| Notify native | `NativeBridge.swift` L309-312 -> `SessionEngine.swift` L460-467 | | |
| Complete session | `services/api.ts` L324-330 | `POST /v1/exclusive/complete` | `routers/exclusive.py` L404-527 |
| Cleanup | `SessionEngine.swift` L647-649 `cleanup()` | | |

---

## 2) Review of Cursor's Amenity Votes Implementation

### What Cursor Built (10 items)

| # | Item | File | Status |
|---|------|------|--------|
| 1 | DB migration | `backend/alembic/versions/055_add_amenity_votes_table.py` | GOOD |
| 2 | ORM model | `backend/app/models/while_you_charge.py` L284-303 | GOOD |
| 3 | Schemas | `backend/app/schemas/merchants.py` L58-68 | GOOD |
| 4 | Vote endpoint | `backend/app/routers/merchants.py` L104-205 | GOOD |
| 5 | Aggregation | `backend/app/services/merchant_details.py` L277-310 | GOOD |
| 6 | Tests | `backend/tests/api/test_amenity_votes.py` | GOOD |
| 7 | Model exports | `backend/app/models/__init__.py` L35 | GOOD |
| 8 | Frontend API | `apps/driver/src/services/api.ts` L489-519 | GOOD |
| 9 | Zod schema | `apps/driver/src/services/schemas.ts` L98-107 | GOOD |
| 10 | UI integration | `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx` | **HAS BUGS** |

### Cursor Implementation Bugs Found

#### BUG-1: CRITICAL -- `useVoteAmenity` not imported

**File**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`
**Line 3**: Import does NOT include `useVoteAmenity`:
```typescript
import { useMerchantDetails, useActivateExclusive, useVerifyVisit, useCompleteExclusive, ApiError } from '../../services/api'
```
**Line 45**: Uses it:
```typescript
const voteAmenityMutation = useVoteAmenity()
```
**Impact**: **Compile-time error.** The app will not build. TypeScript will report `Cannot find name 'useVoteAmenity'`.

**Fix**: Add `useVoteAmenity` to the import on line 3.

#### BUG-2: Rollback logic contradicts fallback

**File**: `MerchantDetailsScreen.tsx` L497-502
```typescript
// catch block:
setUserAmenityVotes(userAmenityVotes)    // rollback
setLocalAmenityCounts(localAmenityCounts)  // rollback
// then FALLS THROUGH to:
setLocalAmenityCounts(newCounts)  // re-applies optimistic update
localStorage.setItem(...)         // persists the failed vote
```
**Impact**: On API failure, the rollback is immediately undone by the fallback block that re-applies the optimistic counts. The user sees the vote "succeed" even though the API call failed.

**Fix**: The fallback block (localStorage persistence) should only run when the API is disabled, not after an API error. Add `return` after the catch block.

---

## 3) Gaps/Blockers (P0/P1)

### P0 -- Ship Blockers

#### GAP-1: `useVoteAmenity` import missing (COMPILE ERROR)

See BUG-1 above. **The driver app will not build.**

**File**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx:3`
**Fix**: Add `useVoteAmenity` to import.

#### GAP-2: Zod schema `perk` is required but backend sends `null`

**File**: `apps/driver/src/services/schemas.ts:114-118`
```typescript
perk: z.object({
  title: z.string(),
  badge: z.string().optional().nullable(),
  description: z.string(),
}),  // <-- NOT .nullable().optional()
```

**Backend**: `backend/app/schemas/merchants.py:53`
```python
perk: Optional[PerkInfo] = None  # Only merchants with exclusive offers have perks
```

**Impact**: Any merchant without an exclusive perk returns `perk: null`. Zod validation throws `"Expected object, received null"` at `schemas.ts:143-158`. The merchant details page crashes for ALL non-exclusive merchants.

**Fix**: Change to `perk: z.object({...}).nullable().optional()` in `schemas.ts`.

#### GAP-3: `moment.label` is required but backend sends `null`

**File**: `apps/driver/src/services/schemas.ts:110`
```typescript
label: z.string(),  // <-- NOT .nullable()
```

**Backend**: `backend/app/schemas/merchants.py:28`
```python
label: Optional[str] = None
```

**Impact**: Merchants without a `ChargerMerchant` link (no walk time data) return `label: null`. Zod validation fails. Merchant details page crashes for these merchants.

**Fix**: Change to `label: z.string().nullable()` in `schemas.ts`.

#### GAP-4: `merchantData.perk.*` accessed without null check

**File**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`
**Lines**: 530, 585, 586, 601, 697, 740

```typescript
const isExclusive = merchantData.perk.badge === 'Exclusive'  // line 530
title={merchantData.perk.title}  // line 585
```

**Impact**: If `perk` is null (which it will be once GAP-2 Zod fix allows null through), every access throws `TypeError: Cannot read properties of null`.

**Fix**: Guard with optional chaining: `merchantData.perk?.badge`, `merchantData.perk?.title`, etc. Or default `perk` to a fallback object.

### P1 -- High Priority

#### GAP-5: Exclusive session schema mismatch (optional vs required)

**Frontend Zod** (`schemas.ts:49-56`):
```typescript
merchant_id: z.string(),   // REQUIRED
charger_id: z.string(),    // REQUIRED
```

**Backend** (`routers/exclusive.py:58-65`):
```python
merchant_id: Optional[str]  # OPTIONAL
charger_id: Optional[str]   # OPTIONAL
```

**Impact**: If backend returns `null` for these fields (edge case: session created before merchant/charger assigned), Zod validation fails on exclusive session responses.

**Fix**: Change to `.nullable().optional()` in `schemas.ts`.

#### GAP-6: Demo-mode auth bypass on `/v1/exclusive/complete`

**File**: `backend/app/routers/exclusive.py:405-410`
```python
driver: Optional[User] = Depends(get_current_driver_optional)
```
If no auth token, the endpoint creates a demo user (`demo@nerava.local`) and lets them complete ANY exclusive session.

**Impact**: In production, anyone can complete anyone else's exclusive session without auth.

**Fix**: Change to `get_current_driver` (required auth) for production. Gate demo behavior behind `DEMO_MODE` env var.

#### GAP-7: Merchant visits endpoint exposes driver_ids without auth

**File**: `backend/app/routers/exclusive.py:781-835`
```python
# GET /v1/exclusive/visits/{merchant_id} -- NO AUTH
# GET /v1/exclusive/visits/lookup/{code} -- NO AUTH
# POST /v1/exclusive/visits/redeem/{code} -- NO AUTH
```

**Impact**: Anyone can enumerate all visits, look up verification codes, and mark visits as redeemed without authentication.

**Fix**: Add `get_current_driver` dependency to all three endpoints.

#### GAP-8: Token refresh not aliased on `/v1/auth`

**File**: `apps/driver/src/services/api.ts:79`
```typescript
const refreshRes = await fetch(`${API_BASE_URL}/auth/refresh`, ...)
```

The refresh endpoint lives on the legacy router (`/auth/refresh`). The v1 domain router (`backend/app/routers/auth_domain.py`) does NOT alias it.

**Impact**: If the legacy `/auth` router is removed, token refresh breaks. All sessions expire without recovery.

**Fix**: Add `/v1/auth/refresh` alias in `auth_domain.py`, or update the frontend to call `/auth/refresh`.

#### GAP-9: In-memory idempotency cache for native events

**File**: `backend/app/routers/native_events.py:51-82`
```python
# NOTE: Replace with Redis in production
class TTLIdempotencyCache:
```

**Impact**: In multi-instance deployment, idempotency is not guaranteed. Events may be processed twice. On restart, cache is lost.

**Fix**: Replace with Redis-backed cache. The backend already has Redis configured (`backend/app/core/config.py`).

---

## 4) Data Contract Mismatches

| # | Field | Frontend (Zod/TS) | Backend (Pydantic) | Mismatch |
|---|-------|-------------------|-------------------|----------|
| 1 | `perk` | Required `z.object({...})` | `Optional[PerkInfo] = None` | **Frontend rejects null** |
| 2 | `moment.label` | `z.string()` (required) | `Optional[str] = None` | **Frontend rejects null** |
| 3 | `exclusive_session.merchant_id` | `z.string()` (required) | `Optional[str]` | Frontend rejects null |
| 4 | `exclusive_session.charger_id` | `z.string()` (required) | `Optional[str]` | Frontend rejects null |
| 5 | `merchant.place_id` | Accessed at `MerchantDetailsScreen.tsx:49,353` | **Not in MerchantInfo schema** | Always undefined |
| 6 | `activate_response.status` | TS interface has `status: string`, Zod schema omits it | Backend returns `status: "ACTIVE"` | Zod strips it (no crash, but unvalidated) |
| 7 | `otp_verify.user` | Zod schema omits `user` field | Backend returns `user: {...}` | Zod strips it; `auth.ts` reads `data.user` but bypasses Zod |
| 8 | `amenities` (new) | `z.object({...}).optional()` | `Optional[Dict] = None` | **OK** -- correctly aligned by Cursor |

---

## 5) Security/Auth Gaps

| # | Endpoint | Current Auth | Required Auth | Risk |
|---|----------|-------------|---------------|------|
| 1 | `POST /v1/exclusive/complete` | Optional (demo fallback) | Required | Anyone can complete any session |
| 2 | `GET /v1/exclusive/visits/{id}` | None | Required | Exposes driver_ids |
| 3 | `GET /v1/exclusive/visits/lookup/{code}` | None | Required (or merchant auth) | Anyone can look up codes |
| 4 | `POST /v1/exclusive/visits/redeem/{code}` | None | Required (merchant auth) | Anyone can mark visits redeemed |
| 5 | `GET /v1/merchants/{id}` | None | None (intentional) | OK for discovery |
| 6 | Token refresh path | Legacy `/auth/refresh` only | Should also be on `/v1/auth/refresh` | Fragile |
| 7 | `AUTH_REQUIRED` native event | Silently clears tokens | Should show re-auth UI | User stuck |

---

## 6) Observability/Testing Gaps

### Missing Tests

| # | What | Where | Priority |
|---|------|-------|----------|
| 1 | Zod validation for `perk: null` | `apps/driver/e2e/` or `vitest` | P0 (will crash in prod) |
| 2 | Zod validation for `moment.label: null` | Same | P0 |
| 3 | Exclusive activation E2E (web + native) | `apps/driver/e2e/tests/` | P1 |
| 4 | Token refresh flow | Integration test | P1 |
| 5 | Native event idempotency under multi-instance | Backend integration test | P1 |
| 6 | Amenity vote toggle/switch E2E | `apps/driver/e2e/` | P2 |

### Missing Logs/Observability

| # | What | Where | Priority |
|---|------|-------|----------|
| 1 | Amenity vote analytics event | `routers/merchants.py` vote endpoint | P1 (no PostHog event on vote) |
| 2 | Auth failure on native event | `native_events.py` -- logs but no alert | P2 |
| 3 | Zod validation failure tracking | `schemas.ts:153` logs to console but not to PostHog | P1 |

---

## 7) Cursor-Ready Implementation Checklist

### Phase 1: Fix Compile Error + Schema Crashes (P0 -- MUST FIX)

#### Task 1: Fix `useVoteAmenity` import
**File**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`
**Line 3**: Add `useVoteAmenity` to import:
```typescript
import { useMerchantDetails, useActivateExclusive, useVerifyVisit, useCompleteExclusive, useVoteAmenity, ApiError } from '../../services/api'
```

#### Task 2: Fix Zod `perk` field to allow null
**File**: `apps/driver/src/services/schemas.ts`
**Line 114-118**: Change to:
```typescript
perk: z.object({
  title: z.string(),
  badge: z.string().optional().nullable(),
  description: z.string(),
}).nullable().optional(),
```

#### Task 3: Fix Zod `moment.label` to allow null
**File**: `apps/driver/src/services/schemas.ts`
**Line 110**: Change to:
```typescript
label: z.string().nullable(),
```

#### Task 4: Guard `merchantData.perk` null access
**File**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`
**Lines 530, 585, 586, 601, 697, 740**: Add optional chaining:
```typescript
// Line 530:
const isExclusive = merchantData.perk?.badge === 'Exclusive'
// Lines 585-586:
title={merchantData.perk?.title ?? ''}
description={merchantData.perk?.description ?? ''}
// Line 601:
{merchantData.perk?.description}
// Line 697:
perkTitle={merchantData.perk?.title ?? ''}
// Line 740:
merchantBadge={merchantData.perk?.badge}
```

#### Task 5: Fix Zod exclusive session fields to allow null
**File**: `apps/driver/src/services/schemas.ts`
**Lines 51-52**: Change to:
```typescript
merchant_id: z.string().nullable(),
charger_id: z.string().nullable(),
```

#### Task 6: Fix amenity vote rollback logic
**File**: `apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx`
In `handleAmenityVote`, after the catch block (around line 498), add `return` to prevent falling through to the localStorage fallback:
```typescript
} catch (error) {
  console.error('Amenity vote API failed, rolling back:', error)
  setUserAmenityVotes(userAmenityVotes)
  setLocalAmenityCounts(localAmenityCounts)
  return  // <-- ADD THIS: Don't fall through to localStorage fallback
}
```

### Phase 2: Security Hardening (P1)

#### Task 7: Require auth on `/v1/exclusive/complete`
**File**: `backend/app/routers/exclusive.py`
**Line ~405**: Change `get_current_driver_optional` to `get_current_driver`. Gate demo behavior:
```python
driver: User = Depends(get_current_driver)
# Remove demo user fallback
```

#### Task 8: Require auth on visits endpoints
**File**: `backend/app/routers/exclusive.py`
**Lines ~781, ~836, ~870**: Add auth dependency:
```python
driver: User = Depends(get_current_driver),
```

#### Task 9: Alias token refresh on v1
**File**: `backend/app/routers/auth_domain.py`
Add:
```python
@router.post("/refresh")
async def refresh_token_v1(request: RefreshRequest, db: Session = Depends(get_db)):
    return await refresh_token(request=request, db=db)
```

### Phase 3: Observability + Testing (P1)

#### Task 10: Add PostHog event for amenity votes
**File**: `backend/app/routers/merchants.py` vote endpoint (~line 190)
```python
analytics_service.capture_event(
    distinct_id=driver.public_id,
    event="amenity_voted",
    properties={"merchant_id": merchant_id, "amenity": amenity, "vote_type": request.vote_type}
)
```

#### Task 11: Replace in-memory idempotency cache with Redis
**File**: `backend/app/routers/native_events.py`
Replace `TTLIdempotencyCache` with Redis-backed implementation using existing Redis connection.

#### Task 12: Track Zod validation failures in PostHog
**File**: `apps/driver/src/services/schemas.ts` `validateResponse()` function
```typescript
import { analytics } from '../analytics'
// In catch block:
analytics.capture('schema_validation_failed', { endpoint, errors: zodError.errors })
```

---

## Summary

### Cursor Implementation Verdict

**7 of 10 items are correct.** The backend (migration, model, schemas, endpoint, aggregation, tests, exports) is solid. The frontend API client and Zod schema are correct. But the UI integration has 2 bugs: a missing import (compile error) and a rollback logic issue.

### Production Readiness

| Category | P0 Blockers | P1 Issues | P2 Nice-to-Have |
|----------|:-----------:|:---------:|:---------------:|
| Cursor bugs | 2 (import, rollback) | 0 | 0 |
| Schema mismatches | 3 (perk null, label null, perk access) | 2 (exclusive fields, place_id) | 1 (status field) |
| Security | 0 | 3 (demo auth, visits auth, refresh alias) | 0 |
| Observability | 0 | 3 (PostHog vote, Redis idem, Zod tracking) | 1 (auth failure alert) |
| **Total** | **5** | **8** | **2** |

### Priority Order

1. **Fix GAP-1** (import) -- app won't compile
2. **Fix GAP-2 + GAP-3** (Zod schema) -- merchant details crashes for most merchants
3. **Fix GAP-4** (null access) -- crashes after Zod fix allows null through
4. **Fix GAP-5** (exclusive schema) -- exclusive flow may crash on edge cases
5. **Fix GAP-6 + GAP-7** (auth hardening) -- security risk in production
6. **Fix GAP-8** (refresh alias) -- token expiry breaks sessions
7. **Fix GAP-9** (Redis cache) -- idempotency gap in multi-instance deploy
