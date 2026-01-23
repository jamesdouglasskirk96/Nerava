# Root Cause Analysis: `/v1/chargers/discovery` Endpoint Not Responding in Production

## Summary
The `/v1/chargers/discovery` endpoint returns `404 Not Found` in production (`https://api.nerava.network/v1/chargers/discovery`) even though:
- ✅ The code exists locally in `nerava-backend-v9 2/app/routers/chargers.py`
- ✅ The router imports successfully
- ✅ The endpoint is registered in the router (verified locally)
- ✅ The router is included in `main_simple.py` (line 857)

## Root Cause
**The code changes have not been deployed to production yet.**

The discovery endpoint was added to the codebase but the Docker image hasn't been rebuilt and redeployed to AWS App Runner.

## Evidence

### 1. Code Exists Locally
```bash
$ python3 -c "from app.routers.chargers import router; print(len(router.routes))"
✅ Router imported successfully
✅ Router has 2 routes
  - {'GET'} /nearby
  - {'GET'} /discovery
```

### 2. Production Returns 404
```bash
$ curl "https://api.nerava.network/v1/chargers/discovery?lat=30.3839&lng=-97.6900"
{"detail":"Not Found"}
```

### 3. Other Endpoint Works
```bash
$ curl "https://api.nerava.network/v1/chargers/nearby?lat=30.3839&lng=-97.6900"
{"detail":"chargers_fetch_failed: ..."}  # Error, but endpoint exists (not 404)
```

### 4. Router Registration Verified
- `main_simple.py` line 857: `app.include_router(chargers.router, prefix="/v1/chargers", tags=["chargers"])`
- Production uses `main_simple.py` (Dockerfile line 49)

## Code Changes Made

### File: `nerava-backend-v9 2/app/routers/chargers.py`

**Added:**
1. `/discovery` endpoint (lines 60-175)
2. Response models: `NearbyMerchantResponse`, `DiscoveryChargerResponse`, `DiscoveryResponse`
3. Asadas Grill photo URL logic (lines 117-121)
4. Imports: `SessionLocal`, `Charger`, `Merchant`, `ChargerMerchant`, `_haversine_distance`

**Key Features:**
- Returns chargers sorted by distance
- Each charger includes 2 nearest merchants
- Sets `within_radius=True` if user is within 400m of nearest charger
- Prioritizes Asadas Grill static photos: `/static/merchant_photos_asadas_grill/asadas_grill_01.jpg`

## Deployment Status

### Current State
- ✅ Code written and tested locally
- ✅ Router imports successfully
- ❌ **Not deployed to production**

### Required Actions
1. **Build new Docker image** with updated `chargers.py`
2. **Push to ECR** (Elastic Container Registry)
3. **Deploy to App Runner** (will auto-deploy if configured, or manual deployment needed)
4. **Verify deployment** by calling the endpoint

## Verification Steps After Deployment

```bash
# 1. Check endpoint exists
curl "https://api.nerava.network/v1/chargers/discovery?lat=30.3839&lng=-97.6900"

# Expected: JSON response with chargers array, not 404

# 2. Verify Asadas Grill photo URL
curl "https://api.nerava.network/v1/chargers/discovery?lat=30.3839&lng=-97.6900" | jq '.chargers[0].nearby_merchants[] | select(.name | contains("Asadas")) | .photo_url'

# Expected: "/static/merchant_photos_asadas_grill/asadas_grill_01.jpg"
```

## Dependencies

The endpoint requires:
- ✅ `app.db.SessionLocal` - Database session factory
- ✅ `app.models.while_you_charge.Charger` - Charger model
- ✅ `app.models.while_you_charge.Merchant` - Merchant model  
- ✅ `app.models.while_you_charge.ChargerMerchant` - Junction table model
- ✅ `app.services.google_places_new._haversine_distance` - Distance calculation

All dependencies exist and are available in the codebase.

## Impact

**Without this endpoint:**
- Frontend cannot fetch charger discovery data
- PreChargingScreen shows "No chargers available" or falls back to mock data
- Asadas Grill photos cannot be loaded (even if endpoint existed, photos need this endpoint to return correct URLs)

**After deployment:**
- Frontend can fetch real charger data
- Merchants display with correct photo URLs
- Asadas Grill photos load correctly

## Next Steps

1. **Deploy backend changes:**
   ```bash
   cd nerava-backend-v9\ 2
   # Build and push Docker image
   # Deploy to App Runner
   ```

2. **Verify deployment:**
   - Check App Runner service status
   - Test endpoint: `curl https://api.nerava.network/v1/chargers/discovery?lat=30.3839&lng=-97.6900`
   - Verify response includes chargers with merchants

3. **Test frontend:**
   - Refresh `http://app.nerava.network/`
   - Allow location permissions
   - Verify chargers display with Asadas Grill photos

## Related Files

- `nerava-backend-v9 2/app/routers/chargers.py` - Discovery endpoint implementation
- `nerava-backend-v9 2/app/main_simple.py` - Router registration (line 857)
- `nerava-backend-v9 2/Dockerfile` - Production build configuration
- `nerava-app-driver/src/api/chargers.ts` - Frontend API client
- `nerava-app-driver/src/hooks/useChargerState.ts` - Frontend hook using discovery endpoint


