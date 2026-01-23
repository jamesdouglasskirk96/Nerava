# Public Verify Flow & Geo Search Implementation

## ✅ Task B: Public Verify Flow

### Files Created/Modified

1. **`app/security/tokens.py`** (new)
   - `create_verify_token()` - Creates short-lived JWT (5-10 min, one-time use)
   - `decode_verify_token()` - Validates and decodes verify tokens
   - Claims: `sub` (user_id), `sid` (session_id), `iat`, `exp`, `jti`, `type: "verify"`

2. **`app/routers/sessions.py`** (new)
   - `GET /verify/{token}` - Public verify page with GPS request
   - `POST /v1/sessions/locate` - Verify session location (one-time use)
   - Features:
     - Requests GPS via navigator.geolocation
     - POSTs location with Bearer token
     - Shows nearby perks after verification
     - One-time use enforcement (409 on reuse)
     - Accuracy validation (rejects > 100m)

3. **`app/routers/gpt.py`** (updated)
   - `POST /v1/gpt/create_session_link` - Now creates actual session and JWT
   - Creates session row with status='started', expires_at=+30m
   - Returns signed verify URL

4. **`alembic/versions/006_add_session_verify_fields.py`** (new)
   - Adds columns to sessions table:
     - `status` (started/verified)
     - `lat`, `lng`, `accuracy_m`
     - `verified_at`, `charger_id`, `started_at`

5. **`app/config.py`** (updated)
   - Added `jwt_secret` and `jwt_alg` settings

6. **`app/main_simple.py`** (updated)
   - Registered `sessions.router` for public verify endpoints

### Testing

```bash
# 1) Create session link
curl -X POST http://localhost:8001/v1/gpt/create_session_link \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"charger_hint":"tesla-123"}'

# 2) Verify location (extract token from URL)
TOKEN="<token from step 1>"
curl -X POST http://localhost:8001/v1/sessions/locate \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"lat":30.2672,"lng":-97.7431,"accuracy":18,"ts":"2025-10-29T15:00:00Z","ua":"curl"}'

# 3) Reuse should fail
curl -X POST http://localhost:8001/v1/sessions/locate \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"lat":30.2672,"lng":-97.7431,"accuracy":18,"ts":"2025-10-29T15:01:00Z","ua":"curl"}'
# => {"verified":false,"reason":"used"}
```

## ✅ Task C: Geo Search

### Files Created/Modified

1. **`app/services/geo.py`** (new)
   - `haversine_m()` - Calculate distance between two lat/lng points in meters

2. **`app/routers/gpt.py`** (updated)
   - `GET /v1/gpt/find_merchants` - Real geo search implementation
     - Filters by category (case-insensitive)
     - Calculates distance via Haversine
     - Attaches offers when available
     - Sorts by distance
   - `GET /v1/gpt/find_charger` - Real charger search
     - Integrates with `chargers_openmap.fetch_chargers()`
     - Computes green window (14:00-16:00)
     - Attaches nearby merchants (within 600m, top 5)

3. **`README_DEV.md`** (updated)
   - Added env vars: `JWT_SECRET`, `JWT_ALG`
   - Added endpoint documentation
   - Added Austin demo coordinates (30.2672, -97.7431)

### Testing

```bash
# Find merchants
curl "http://localhost:8001/v1/gpt/find_merchants?lat=30.2672&lng=-97.7431&category=coffee&radius_m=1200"

# Find chargers
curl "http://localhost:8001/v1/gpt/find_charger?lat=30.2672&lng=-97.7431&radius_m=2000"
```

## ✅ Success Criteria Met

- [x] `/verify/{token}` renders, requests GPS, and POSTs to `/v1/sessions/locate`
- [x] Valid token → 200 `{verified:true}`, subsequent call → `{verified:false, reason:"used"}`
- [x] accuracy > 100 → 400 with clear message
- [x] No PII beyond session row; logs omit exact lat/lng payload
- [x] `find_merchants` returns ≥5 Austin results from seed, sorted by distance
- [x] Each merchant includes `has_offer` and `offer` when applicable
- [x] `find_charger` returns ≥1 charger with `green_window` and `nearby_merchants` (≤600m)
- [x] No 5xx errors

## Environment Variables

Add to `.env` or `ENV.example`:
```
JWT_SECRET=<your-secret-key>
JWT_ALG=HS256
PUBLIC_BASE_URL=http://127.0.0.1:8001
```
