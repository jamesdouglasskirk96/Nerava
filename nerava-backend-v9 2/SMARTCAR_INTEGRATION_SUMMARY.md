# Smartcar Integration - Implementation Summary

## Overview
Production-ready Smartcar integration for connecting Tesla vehicles and polling telemetry data (SOC, location, charging state).

## Files Added/Modified

### New Files
1. **`app/models_vehicle.py`** - Vehicle data models:
   - `VehicleAccount` - Links user to vehicle provider (Smartcar)
   - `VehicleToken` - OAuth tokens for API access
   - `VehicleTelemetry` - SOC, location, charging state records

2. **`app/services/smartcar_client.py`** - Smartcar API client:
   - `exchange_code_for_tokens()` - OAuth token exchange
   - `refresh_tokens()` - Token refresh with auto-retry
   - `list_vehicles()` - Get user's vehicles
   - `get_vehicle_location()` - Get vehicle GPS coordinates
   - `get_vehicle_charge()` - Get battery state and charging status

3. **`app/services/ev_telemetry.py`** - Telemetry polling service:
   - `poll_vehicle_telemetry_for_account()` - Poll and store telemetry
   - `poll_all_active_vehicles()` - Batch polling (for future scheduler)

4. **`app/routers/ev_smartcar.py`** - API endpoints:
   - `GET /v1/ev/connect` - Generate Smartcar Connect URL
   - `GET /oauth/smartcar/callback` - OAuth callback handler
   - `GET /v1/ev/me/telemetry/latest` - Production test endpoint

5. **`alembic/versions/020_add_vehicle_tables.py`** - Database migration

### Modified Files
1. **`app/core/config.py`** - Added Smartcar configuration:
   - `SMARTCAR_CLIENT_ID`
   - `SMARTCAR_CLIENT_SECRET`
   - `SMARTCAR_REDIRECT_URI`
   - `SMARTCAR_MODE` (live/sandbox)
   - `SMARTCAR_BASE_URL`, `SMARTCAR_AUTH_URL`, `SMARTCAR_CONNECT_URL`

2. **`app/models_all.py`** - Added vehicle models import

3. **`app/main.py`** - Registered `ev_smartcar` router

4. **`app/main_simple.py`** - Registered `ev_smartcar` router

5. **`app/middleware/auth.py`** - Excluded `/oauth/smartcar/callback` from auth

## Environment Variables Required

```bash
# Smartcar OAuth credentials (from Smartcar dashboard)
SMARTCAR_CLIENT_ID=your_client_id
SMARTCAR_CLIENT_SECRET=your_client_secret

# OAuth callback URL (must match Smartcar dashboard config)
# Example for current Railway deployment:
# https://web-production-526f6.up.railway.app/oauth/smartcar/callback
SMARTCAR_REDIRECT_URI=https://web-production-526f6.up.railway.app/oauth/smartcar/callback

# Smartcar mode: "live" for production, "sandbox" for testing
SMARTCAR_MODE=live

# Optional: Override Smartcar API URLs (defaults are fine)
# SMARTCAR_BASE_URL=https://api.smartcar.com
# SMARTCAR_AUTH_URL=https://auth.smartcar.com
# SMARTCAR_CONNECT_URL=https://connect.smartcar.com

# Frontend URL for redirects after OAuth
FRONTEND_URL=https://app.nerava.app
```

## Database Migration

Run the migration to create vehicle tables:

```bash
cd nerava-backend-v9
alembic upgrade head
```

This creates:
- `vehicle_accounts` table
- `vehicle_tokens` table
- `vehicle_telemetry` table
- Indexes on `user_id`, `vehicle_account_id`, `recorded_at`

## API Endpoints

### 1. Connect Vehicle
**GET** `/v1/ev/connect`

**Auth:** Required (Bearer token)

**Response:**
```json
{
  "url": "https://connect.smartcar.com/oauth/authorize?..."
}
```

**Usage:** Frontend redirects user to this URL. After Tesla login, Smartcar redirects to callback.

---

### 2. OAuth Callback
**GET** `/oauth/smartcar/callback?code=...&state=...`

**Auth:** Not required (called by Smartcar)

**Behavior:**
- Validates state token
- Exchanges code for tokens
- Fetches vehicle list
- Creates/updates `VehicleAccount` and `VehicleToken`
- Redirects to frontend success page

**Redirect URLs:**
- Success: `{FRONTEND_URL}/vehicle/connected?provider=smartcar&vehicle_id=...`
- Error: `{FRONTEND_URL}/vehicle/connect?error=...`

---

### 3. Get Latest Telemetry (Production Test Endpoint)
**GET** `/v1/ev/me/telemetry/latest`

**Auth:** Required (Bearer token)

**Response:**
```json
{
  "recorded_at": "2025-02-03T12:00:00Z",
  "soc_pct": 85.5,
  "charging_state": "CHARGING",
  "latitude": 30.2672,
  "longitude": -97.7431
}
```

**Error Responses:**
- `404`: No connected vehicle
- `502`: Smartcar API error or network failure

**Usage:** This is the endpoint to call in production to verify end-to-end integration.

## Example cURL for Testing

### 1. Get Connect URL
```bash
curl -X GET "https://web-production-526f6.up.railway.app/v1/ev/connect" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 2. Test Telemetry Endpoint (After Connecting Vehicle)
```bash
curl -X GET "https://web-production-526f6.up.railway.app/v1/ev/me/telemetry/latest" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Security Features

1. **State Token Signing**: OAuth state is cryptographically signed with JWT to prevent CSRF
2. **Token Encryption**: Access/refresh tokens stored in DB (should be encrypted in production)
3. **Auto Token Refresh**: Tokens automatically refresh when expired (5-minute buffer)
4. **User Isolation**: All endpoints scoped to authenticated user
5. **No Token Logging**: Tokens are never logged (only truncated versions if needed)

## Error Handling

- **401/403 from Smartcar**: Token expired/revoked → Account marked inactive
- **Network Errors**: Returns 502 with descriptive message
- **Missing Config**: Returns 500 if Smartcar not configured
- **No Vehicles**: Redirects to frontend with error parameter

## Testing Plan

1. **Deploy to staging/production**
2. **Set environment variables** (see above)
3. **Run migration**: `alembic upgrade head`
4. **Log in via magic link** (existing flow)
5. **Call `/v1/ev/connect`** from frontend
6. **Redirect browser** to returned Smartcar URL
7. **Log into Tesla** and approve
8. **Verify redirect** to success page
9. **Call `/v1/ev/me/telemetry/latest`** and confirm:
   - Valid `soc_pct` (0-100)
   - Valid `charging_state` (CHARGING, FULLY_CHARGED, NOT_CHARGING)
   - Valid `latitude`/`longitude` coordinates

## TODOs / Follow-ups

1. **Multi-vehicle support**: Currently uses first vehicle only. Extend to:
   - List all vehicles in `/v1/ev/me/vehicles`
   - Allow user to select primary vehicle
   - Support multiple vehicles per user

2. **Background polling scheduler**: Wire `poll_all_active_vehicles()` to:
   - Celery/Redis queue
   - Cron job
   - Or scheduled FastAPI background task

3. **Token encryption**: Encrypt `access_token` and `refresh_token` in DB using:
   - Fernet (symmetric encryption)
   - Or use a secrets manager (AWS Secrets Manager, etc.)

4. **Vehicle info endpoint**: Fetch display name from Smartcar vehicle info API

5. **Telemetry history**: Add endpoint to fetch historical telemetry:
   - `GET /v1/ev/me/telemetry/history?days=7`

6. **Error recovery**: Handle Smartcar API rate limits and retries

7. **Webhook support**: If Smartcar supports webhooks for real-time updates

## Notes

- Uses `httpx` for async HTTP (already in requirements.txt)
- Uses `jose` JWT library for state token signing (already in requirements.txt)
- Follows existing code patterns (FastAPI, SQLAlchemy, Alembic)
- All endpoints use existing magic-link auth system
- Production-safe: No hardcoded URLs, all env-based config

