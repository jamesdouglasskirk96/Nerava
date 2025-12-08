# Remaining TODOs Summary

## Status Overview

### ✅ Completed
- Phase 1: Navigation & Tab Consolidation (all 6 tasks)
- Phase 2.1: Backend Magic-Link Auth (endpoints at `/v1/auth/magic_link/*`)
- Backend Routing Fix: Magic-link endpoints moved to `/v1/auth/*`
- Frontend API Functions: `apiRequestMagicLink()` and `apiVerifyMagicLink()` added

### 🔄 Remaining Work

#### Phase 2.2-2.3: Frontend Magic-Link UI Implementation

**Files to Modify:**
1. `ui-mobile/js/app.js`
   - Replace `renderSSO()` function with magic-link email-only UI
   - Add magic-link callback handler in `handleHashRoute()` for `#/auth/magic?token=...`
   - Import magic-link API functions

**Implementation Steps:**
1. Replace SSO overlay HTML with single email input form
2. On submit, call `apiRequestMagicLink(email)`
3. Show "Check your email" state
4. Handle `#/auth/magic?token=...` route:
   - Extract token from URL
   - Call `apiVerifyMagicLink(token)`
   - On success: set session, navigate to Wallet
   - On failure: show error, allow retry

**Estimated Complexity:** Medium (2-3 hours)

#### Phase 3.1: Behavior Loop Verification

**Tasks:**
1. Verify Wallet → Discovery → Merchant → QR → Wallet loop works
2. Test instant reward visibility after off-peak charging
3. Verify reputation updates are visible
4. Check activity feed updates correctly

**Testing Checklist:**
- [ ] Sign in via magic link
- [ ] Navigate Wallet → Discovery
- [ ] Open merchant detail
- [ ] Scan QR code
- [ ] Verify Nova balance updates
- [ ] Check activity feed shows new transaction
- [ ] Verify reputation progress updates

**Estimated Complexity:** Low (1 hour)

#### Phase 3.2: Logging & Cleanup

**Tasks:**
1. Add comprehensive logging with clear tags:
   - `[Auth][MagicLink]` for auth flows
   - `[Nav][Tabs]` for navigation (already added)
   - `[Wallet]`, `[Discovery]`, `[Profile]` for tab-specific actions
2. Clean up redundant screens:
   - Hide standalone Activity page (already hidden from nav)
   - Ensure all deep links still work
   - Remove noisy debug logs

**Files to Review:**
- `ui-mobile/js/app.js` - Add/clean logs
- `ui-mobile/js/pages/wallet-new.js` - Add logs for balance updates
- `ui-mobile/js/pages/explore.js` - Add logs for merchant interactions
- `ui-mobile/js/pages/me.js` - Add logs for profile actions

**Estimated Complexity:** Low (1 hour)

## Recommended Implementation Order

1. **Frontend Magic-Link UI** (Phase 2.2-2.3) - Highest priority, blocks testing
2. **Behavior Loop Verification** (Phase 3.1) - Can be done manually after UI is complete
3. **Logging & Cleanup** (Phase 3.2) - Polish work, can be done incrementally

## Quick Start: Frontend Magic-Link Implementation

### Step 1: Update imports in `ui-mobile/js/app.js`
```javascript
import { apiRequestMagicLink, apiVerifyMagicLink } from './core/api.js';
```

### Step 2: Replace `renderSSO()` function
Replace with magic-link email-only UI (see implementation notes in NEXT_MOBILE_IMPL_SUMMARY.md)

### Step 3: Add magic-link callback handler
Add to `handleHashRoute()` function:
```javascript
// Handle magic-link callback
if (hash.startsWith('#/auth/magic')) {
  const params = new URLSearchParams(hash.split('?')[1] || '');
  const token = params.get('token');
  
  if (token) {
    // Verify token and create session
    apiVerifyMagicLink(token).then(() => {
      // Navigate to Wallet on success
      location.hash = '#/wallet';
      window.location.reload();
    }).catch(err => {
      // Show error state
      console.error('[Auth][MagicLink] Verification failed:', err);
    });
  }
  return;
}
```

## Notes

- Backend endpoints are ready at `/v1/auth/magic_link/*`
- API functions are already added to `api.js`
- Current SSO overlay can remain as fallback during transition
- Magic-link flow should work alongside existing password auth (backend supports both)

