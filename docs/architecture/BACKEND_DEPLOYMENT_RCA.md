# Backend Deployment Root Cause Analysis

## Issue
Backend endpoints `/v1/chargers/discovery` and `/v1/drivers/merchants/open` return 404 Not Found in production.

## Root Cause
**Deployment rolled back** - The service is running the old image (`v12-merchant-photo-fix`) instead of the new image (`v14-merchants-open`).

### Evidence
1. **Service Status**: `RUNNING` ✅
2. **Current Image**: `v12-merchant-photo-fix` ❌ (old version)
3. **Expected Image**: `v14-merchants-open` ❌ (not deployed)
4. **Last Operation**: `UPDATE_SERVICE` → `ROLLBACK_SUCCEEDED` ❌
5. **Endpoints**: Return 404 (not in old version)
6. **OpenAPI**: No discovery or merchants/open paths registered

## Why Deployment Rolled Back

Possible causes:
1. **Health check failure** - New endpoints might have caused startup issues
2. **Import errors** - Missing dependencies or import paths
3. **Database connection issues** - New endpoints query database
4. **Startup timeout** - App Runner health check timed out

## Verification

### ✅ Code is Correct
- All imports work locally
- Routes are registered correctly
- Docker image builds successfully
- Image imports successfully in container

### ❌ Deployment Failed
- App Runner rolled back to previous version
- No error logs available (log group doesn't exist or not accessible)

## Solution

### Step 1: Redeploy with New Image
```bash
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v14-merchants-open",
      ...
    }
  }'
```

### Step 2: Monitor Deployment
```bash
# Check status
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --region us-east-1 | jq '.Service.Status'

# Check operations
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --region us-east-1
```

### Step 3: Verify Endpoints After Deployment
```bash
# Test discovery endpoint
curl "https://api.nerava.network/v1/chargers/discovery?lat=30.3839&lng=-97.6900"

# Test merchants/open endpoint
curl "https://api.nerava.network/v1/drivers/merchants/open?charger_id=ch_domain_tesla_001"

# Check OpenAPI
curl "https://api.nerava.network/openapi.json" | jq '.paths | keys | .[] | select(contains("discovery") or contains("merchants/open"))'
```

## Files Changed in v14-merchants-open

1. ✅ `app/middleware/auth.py` - Added optional auth paths
2. ✅ `app/routers/chargers.py` - Added `/discovery` endpoint
3. ✅ `app/routers/drivers_domain.py` - Added `/merchants/open` endpoint
4. ✅ `app/services/merchant_details.py` - Updated Asadas Grill logic

## Next Steps

1. **Redeploy** - Use the command above to deploy v14-merchants-open
2. **Monitor** - Watch for deployment success (should be RUNNING, not ROLLBACK_SUCCEEDED)
3. **Test** - Verify endpoints work after deployment
4. **Seed Database** - Run seed script for Asadas Grill data


