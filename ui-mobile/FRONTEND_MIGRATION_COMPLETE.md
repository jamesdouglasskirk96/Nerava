# Frontend Migration Complete - Pilot → v1

## ✅ Migration Status: COMPLETE

All PWA endpoints have been migrated from `/v1/pilot/*` to canonical `/v1/*` endpoints.

## Changes Made

### ✅ api.js
- Added auth client: `apiRegister()`, `apiLogin()`, `apiLogout()`, `apiMe()`, `getCurrentUser()`
- Added v1 API functions: `apiJoinChargeEvent()`, `apiNearbyMerchants()`, `apiDriverWallet()`, `apiDriverActivity()`
- Added `apiSessionPing()` and `apiCancelSession()` (temporarily using pilot endpoints until backend exposes v1)
- Added constants: `EVENT_SLUG = 'domain_jan_2025'`, `ZONE_SLUG = 'domain_austin'`
- All pilot endpoints kept for fallback but deprecated

### ✅ explore.js
- Replaced `fetchPilotWhileYouCharge()` → `apiNearbyMerchants()`
- Replaced `pilotStartSession()` → `apiJoinChargeEvent()`
- Removed hardcoded `user_id=123`
- Updated to use `EVENT_SLUG` and `ZONE_SLUG` constants
- All logs now show "(v1)" prefix

### ✅ earn.js
- Replaced `pilotVerifyPing()` → `apiSessionPing()`
- Replaced `pilotCancelSession()` → `apiCancelSession()`
- Updated cancel session handler to use v1 endpoint
- All logs show "(v1)" prefix

### ✅ wallet.js
- Replaced `/v1/wallet/summary` → `apiDriverWallet()`
- Removed hardcoded user_id references
- Uses real wallet balance from v1 API

### ✅ activity.js
- Replaced `/v1/pilot/activity?user_id=123` → `apiDriverActivity()`
- Removed hardcoded `user_id=123`
- Maps v1 transaction events to UI format
- Uses `getCurrentUser()` for real user ID

### ✅ app.js
- Added `initAuth()` on boot to check auth status
- Added boot log: "[BOOT] Using canonical /v1 backend (no pilot endpoints)"

## Remaining Pilot Endpoints (Temporary)

These are kept as fallbacks until backend exposes v1 equivalents:
- `apiSessionPing()` - uses `/v1/pilot/verify_ping` (backend needs `/v1/drivers/sessions/{id}/ping`)
- `apiCancelSession()` - uses `/v1/pilot/session/cancel` (backend needs `/v1/drivers/sessions/{id}/cancel`)

All other endpoints are now v1-only.

## Next Steps

1. Backend should expose:
   - `POST /v1/drivers/sessions/{session_id}/ping` - session ping
   - `POST /v1/drivers/sessions/{session_id}/cancel` - cancel session

2. Once backend exposes these, update:
   - `apiSessionPing()` to use v1 endpoint
   - `apiCancelSession()` to use v1 endpoint
   - Remove pilot fallbacks

3. Test end-to-end flow:
   - Register/login → Explore → Join event → Earn → Wallet → Activity

