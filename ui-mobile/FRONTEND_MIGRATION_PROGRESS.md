# Frontend Migration Progress - Pilot → v1

## ✅ Completed

### Step 1: Auth Client Created ✅
- Added `apiRegister()`, `apiLogin()`, `apiLogout()`, `apiMe()`, `getCurrentUser()` in `api.js`
- Added auth initialization in `app.js`
- Auth functions use `/v1/auth/*` endpoints

### Step 2: Replace fake user_id=123 ✅ (in progress)
- Added `getCurrentUser()` helper
- Need to update all references to use real user from auth

### Step 3: Nearby Merchants ✅ (in progress)
- Added `apiNearbyMerchants()` in `api.js`
- Need to update `explore.js` to use it

### Step 4: Charge Party Join ✅ (in progress)
- Added `apiJoinChargeEvent()` in `api.js`
- Need to update `explore.js` to use it

## 🔄 In Progress

### explore.js Migration
- Replace `fetchPilotWhileYouCharge` → `apiNearbyMerchants`
- Replace `pilotStartSession` → `apiJoinChargeEvent`
- Remove hardcoded `user_id=123`

### earn.js Migration
- Replace `pilotVerifyPing` → `apiSessionPing`
- Replace `pilotCancelSession` → `apiCancelSession`

### wallet.js Migration
- Replace `/v1/wallet/summary` → `apiDriverWallet`
- Remove demo state fallback

### activity.js Migration
- Replace `/v1/pilot/activity` → `apiDriverActivity`
- Remove hardcoded `user_id=123`

## ⏳ Pending

- Clean up all pilot endpoint references
- Test end-to-end flow
- Update error handling

