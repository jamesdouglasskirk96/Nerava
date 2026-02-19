# Cursor Validation Report — Merchant Portal 10/10 Implementation

**Date:** 2026-01-27
**Validator:** Claude Code (Opus 4.5)
**Prompt:** `claude-cursor-prompts/2026-01-27_merchant-portal-to-10-10-cursor-prompt.md`
**Source review:** `claude-cursor-prompts/2026-01-27_merchant-portal-onboarding-review.md`

---

## Executive Summary

**Cursor solved the wrong problem.** The prompt asked to fix the merchant portal (6.5 → 10/10) by removing mock data, adding auth/logout, gating DemoNav, and fixing non-functional pages. Instead, Cursor addressed items from the *E2E iOS-backend gap analysis report* — auth hardening on exclusive endpoints, Redis idempotency cache, and Zod schema alignment. These are valid backend improvements, but **zero merchant portal frontend fixes were made**.

**Score: 0/8 prompt requirements addressed.**

---

## Requirement-by-Requirement Validation

### 1. Remove hardcoded mock data in Overview — FAIL

**File:** `apps/merchant/app/components/Overview.tsx`

Lines 47-58 are **identical to before Cursor ran**:
```typescript
const activeExclusive = {
  name: 'Free Pastry with Coffee',
  timeWindow: '7:00 AM - 11:00 AM',
  status: 'on',
  activationsToday: 43,
  dailyCap: 100,
};

const primaryExperience = {
  status: 'available',
  explanation: 'Only one business per charging location...',
};
```
Hardcoded mock data remains. A merchant will see "Free Pastry with Coffee" as their active exclusive.

### 2. Add real session management (token expiry + logout) — FAIL

**File:** `apps/merchant/app/components/DashboardLayout.tsx`

No logout button added. File is **identical to before Cursor ran** (55 lines, no changes).

**File:** `apps/merchant/app/services/api.ts`

No 401 interceptor added. No token expiry check. File is **identical to before Cursor ran** (192 lines, no changes).

**File:** `apps/merchant/app/App.tsx`

Auth still uses `localStorage.getItem('businessClaimed') === 'true'` (line 36). No changes.

### 3. Gate DemoNav behind env flag — FAIL

**File:** `apps/merchant/app/App.tsx`

Line 44 still renders `<DemoNav />` unconditionally:
```tsx
<DemoNav />
```
No `VITE_DEMO_MODE` check. The purple demo banner will appear in production.

### 4. Fix non-functional pages (Settings/Billing/PrimaryExperience/SelectLocation) — FAIL

| Page | Status | Evidence |
|---|---|---|
| Settings | Unchanged | `Settings.tsx:4-8` still has hardcoded `businessInfo` with "Downtown Coffee Shop" |
| Billing | Unchanged | `Billing.tsx:5-28` still has hardcoded `billingItems` with $99 and $45.30 charges |
| PrimaryExperience | Unchanged | `PrimaryExperience.tsx:9` still has `useState('available')` with no API call |
| SelectLocation | Unchanged | `SelectLocation.tsx:6-21` still has hardcoded `mockLocations` |

### 5. Replace alert() with inline error UI — FAIL

**File:** `apps/merchant/app/components/Exclusives.tsx`

Line 56 still uses `alert()`:
```typescript
alert(err instanceof ApiError ? err.message : 'Failed to update exclusive');
```

### 6. Wire CustomerExclusiveView to real API — FAIL

**File:** `apps/merchant/app/components/CustomerExclusiveView.tsx`

Lines 6-13 still use hardcoded mock data:
```typescript
const mockExclusiveData = {
  '1': {
    merchantName: 'Downtown Coffee Shop',
    exclusiveName: 'Free Pastry with Coffee',
    ...
  },
};
```

### 7. Fix Exclusives progress bar or remove it until data exists — FAIL

**File:** `apps/merchant/app/components/Exclusives.tsx`

Line 176 still hardcodes `width: '0%'`:
```tsx
style={{ width: '0%' }}
```

### 8. Send all fields in CreateExclusive payload — FAIL

**File:** `apps/merchant/app/components/CreateExclusive.tsx`

Lines 36-41 still only send 4 of 8 fields:
```typescript
const result = await createExclusive(merchantId, {
  title: formData.name,
  description: formData.description,
  daily_cap: parseInt(formData.dailyCap) || undefined,
  eligibility: 'charging_only',
});
```
`type`, `startTime`, `endTime`, and `staffInstructions` are still collected but discarded.

---

## What Cursor Actually Did (E2E Gap Fixes — Not Requested)

These changes are legitimate backend improvements, but they weren't what the prompt asked for:

| Change | File | Verdict |
|---|---|---|
| Auth hardening on `/complete` | `backend/app/routers/exclusive.py:409-434` | Valid — `get_current_driver_optional` with `is_local_env()` gating |
| Auth on `/visits/*` endpoints | `exclusive.py:796,862,902` | Valid — all 3 visit endpoints now require `get_current_driver` |
| Redis idempotency cache | `backend/app/routers/native_events.py:82-122` | Valid — `RedisIdempotencyCache` with in-memory fallback |
| Redis config | `backend/app/core/config.py:102-103` | Valid — `REDIS_URL` + `REDIS_ENABLED` settings |
| `place_id` in merchant schema | `backend/app/schemas/merchants.py:22` | Valid — `place_id: Optional[str] = None` |
| `place_id` in frontend Zod | `apps/driver/src/services/schemas.ts:99` | Valid — already present |
| `status` in activate response | `exclusive.py:69`, `schemas.ts:62` | Valid — aligned |
| `user` in OTP verify response | `schemas.ts:147-152` | Valid — aligned |
| `merchant_id`/`charger_id` nullable | `schemas.ts:51-52` | Valid — already present |
| `perk` nullable | `schemas.ts:116-120` | Valid — already present |
| `moment.label` nullable | `schemas.ts:112` | Valid — already present |

---

## Verdict

**Cursor addressed 0/8 merchant portal requirements.** It instead executed the E2E iOS-backend gap analysis fixes, which were from a different prompt (`2026-01-27_e2e-ios-backend-gap-analysis-report.md`). The backend work is sound, but the merchant portal remains at 6.5/10.

**The merchant portal prompt needs to be re-run**, with explicit instructions to modify files in `apps/merchant/`.

---

## Remaining Work (All 8 Items Still Open)

1. Gate `<DemoNav />` behind `VITE_DEMO_MODE` env flag in `apps/merchant/app/App.tsx:44`
2. Remove hardcoded `activeExclusive` and `primaryExperience` in `apps/merchant/app/components/Overview.tsx:47-58` — replace with real API data or "Coming Soon" cards
3. Add logout button to `apps/merchant/app/components/DashboardLayout.tsx` sidebar
4. Add 401 interceptor + token expiry check in `apps/merchant/app/services/api.ts`
5. Replace mock data in `Settings.tsx`, `Billing.tsx`, `PrimaryExperience.tsx`, `SelectLocation.tsx` with "Coming Soon" or real data
6. Replace `alert()` with inline error banner in `apps/merchant/app/components/Exclusives.tsx:56`
7. Wire `CustomerExclusiveView.tsx` to real API, remove `mockExclusiveData`
8. Fix `CreateExclusive.tsx:36-41` to send `type`, `start_time`, `end_time`, `staff_instructions`
9. Remove hardcoded `width: '0%'` in `Exclusives.tsx:176` — either remove progress bar or fetch real count
