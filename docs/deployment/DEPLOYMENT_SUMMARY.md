# Backend Deployment Summary - v14-merchants-open

## Deployment Status

✅ **Docker Image Built**: `nerava-backend:latest`
✅ **Image Tagged**: `566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v14-merchants-open`
✅ **Pushed to ECR**: Successfully uploaded
✅ **App Runner Updated**: Deployment in progress (`OPERATION_IN_PROGRESS`)

## Changes Deployed

### 1. Auth Middleware Fix
- **File**: `app/middleware/auth.py`
- **Change**: Added optional auth path prefixes
- **Paths**: 
  - `/v1/drivers/merchants/open` - Optional authentication
  - `/v1/chargers/discovery` - Optional authentication

### 2. New Endpoint: `/v1/drivers/merchants/open`
- **File**: `app/routers/drivers_domain.py`
- **Purpose**: Get merchants linked to a specific charger
- **Auth**: Optional (works without authentication)
- **Features**:
  - Returns merchants sorted by distance
  - Sets `is_primary: true` for Asadas Grill
  - Returns correct photo URLs (`/static/merchant_photos_asadas_grill/asadas_grill_01.jpg`)
  - Returns `exclusive_title: "Free Beverage Exclusive"` for Asadas Grill

### 3. New Endpoint: `/v1/chargers/discovery`
- **File**: `app/routers/chargers.py`
- **Purpose**: Get charger discovery data with nearby merchants
- **Auth**: Optional (works without authentication)
- **Features**:
  - Returns chargers sorted by distance
  - Each charger includes 2 nearest merchants
  - Sets `within_radius=True` if user is within 400m of nearest charger
  - Asadas Grill photos prioritized

### 4. Merchant Details Service Update
- **File**: `app/services/merchant_details.py`
- **Changes**:
  - Asadas Grill shows "Free Beverage Exclusive" instead of "Happy Hour"
  - Category shows as "Restaurant" (not "Restaurant • Food")
  - Badge shows as "Exclusive" (not "Happy Hour ⭐️")

## Next Steps

### 1. Wait for Deployment to Complete

Check deployment status:
```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --region us-east-1 | jq -r '.Service.Status'
```

Wait for status to be `RUNNING` (currently `OPERATION_IN_PROGRESS`)

### 2. Seed Production Database

After deployment completes, seed Asadas Grill data in production:

**Option A: Use seed script (if database access available)**
```bash
cd "nerava-backend-v9 2"
# Set production DATABASE_URL
export DATABASE_URL="postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"
python scripts/seed_asadas_grill.py
```

**Option B: Manual SQL (see cursor-prompt-deploy-and-fix-auth.txt Part 4)**

### 3. Verify Production Endpoints

```bash
# Test health endpoint
curl "https://api.nerava.network/healthz"

# Test merchants/open endpoint (no auth required)
curl "https://api.nerava.network/v1/drivers/merchants/open?charger_id=ch_domain_tesla_001"

# Expected: Returns merchants including Asadas Grill with:
#   - is_primary: true
#   - exclusive_title: "Free Beverage Exclusive"
#   - photo_url: "/static/merchant_photos_asadas_grill/asadas_grill_01.jpg"

# Test discovery endpoint (no auth required)
curl "https://api.nerava.network/v1/chargers/discovery?lat=30.3839&lng=-97.6900"

# Expected: Returns chargers with nearby merchants

# Test merchant details
curl "https://api.nerava.network/v1/merchants/m_asadas_grill"

# Expected: Returns merchant with:
#   - category: "Restaurant"
#   - perk.title: "Free Beverage Exclusive"
#   - perk.badge: "Exclusive"
```

## Files Modified

1. ✅ `app/middleware/auth.py` - Added optional auth path prefixes
2. ✅ `app/routers/drivers_domain.py` - Added `/merchants/open` endpoint
3. ✅ `app/routers/chargers.py` - Added `/discovery` endpoint
4. ✅ `app/services/merchant_details.py` - Updated perk/category logic
5. ✅ `scripts/seed_asadas_grill.py` - Created seed script (run in production)

## Docker Image

- **Image**: `566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v14-merchants-open`
- **Digest**: `sha256:5f1234c7fa2aba6742825254777aa3c175c90ea388fff30c70131a875f2e3557`
- **Size**: 856 bytes (manifest)

## Service Info

- **Service ARN**: `arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3`
- **Service URL**: `tvuywdkems.us-east-1.awsapprunner.com`
- **Status**: `OPERATION_IN_PROGRESS` (deploying)
