# Frontend Migration Summary - Pilot → Canonical v1

## Status: IN PROGRESS

This migration moves the PWA from fake pilot endpoints (`/v1/pilot/*`, `user_id=123`) to real production endpoints (`/v1/*` with proper auth).

## What's Been Done

### ✅ Step 1: Auth Client Created
- Added authentication functions in `api.js`:
  - `apiRegister()`, `apiLogin()`, `apiLogout()`, `apiMe()`, `getCurrentUser()`
- Auth uses `/v1/auth/*` endpoints
- Added `initAuth()` in `app.js` to check auth status on boot

### ✅ Step 2: New v1 API Functions Added
- `apiJoinChargeEvent()` - join charge party
- `apiNearbyMerchants()` - get nearby merchants
- `apiDriverWallet()` - get wallet balance
- `apiDriverActivity()` - get activity/transactions
- `apiSessionPing()` - session ping (with pilot fallback)
- `apiCancelSession()` - cancel session

### 🔄 Step 3: Files to Update
- `explore.js` - Replace pilot endpoints with v1
- `earn.js` - Replace pilot ping with v1
- `wallet.js` - Use real wallet endpoint
- `activity.js` - Use real activity endpoint

## Constants
- `EVENT_SLUG = 'domain_jan_2025'`
- `ZONE_SLUG = 'domain_austin'`

## Next Steps
1. Complete explore.js migration
2. Complete earn.js migration  
3. Complete wallet.js migration
4. Complete activity.js migration
5. Remove all pilot endpoint references
6. Test end-to-end flow

