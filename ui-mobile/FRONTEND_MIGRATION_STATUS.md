# Frontend Migration Status - Pilot → Canonical v1

## Step 0: Reconnaissance ✅

### Pilot Endpoints Currently Used:
- `/v1/pilot/app/bootstrap` - used in explore.js
- `/v1/pilot/while_you_charge` - used in explore.js
- `/v1/pilot/start_session` - used in explore.js (with hardcoded user_id=123)
- `/v1/pilot/verify_ping` - used in earn.js
- `/v1/pilot/session/cancel` - used in earn.js
- `/v1/pilot/activity` - used in activity.js (with hardcoded user_id=123)

### Fake State:
- `user_id=123` hardcoded in multiple places
- `localStorage.NERAVA_USER_ID` used as fallback
- No real authentication flow

### Target v1 Endpoints:
- `/v1/auth/register`, `/v1/auth/login`, `/v1/auth/logout`, `/v1/auth/me`
- `/v1/drivers/charge_events/{event_slug}/join`
- `/v1/drivers/merchants/nearby?zone_slug=...`
- `/v1/drivers/me/wallet`
- `/v1/drivers/activity` (if exists) or use transactions

## Migration Steps:
1. ✅ Create AuthClient in api.js
2. ✅ Replace fake user_id=123 with real auth/me
3. ✅ Migrate while_you_charge → nearby merchants
4. ✅ Wire charge party join
5. ✅ Update earn page ping loop
6. ✅ Update wallet & activity
7. ✅ Clean up pilot usage

