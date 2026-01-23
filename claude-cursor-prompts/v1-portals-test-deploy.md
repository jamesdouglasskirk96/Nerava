# V1 Portals: Test & Deploy

## Phase 1: Run Database Migrations

```bash
cd "/Users/jameskirk/Desktop/Nerava/nerava-backend-v9 2"

# Set production database URL
export DATABASE_URL="postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"

# Run migrations
alembic upgrade head

# Verify migrations applied
alembic current
```

Expected output should show migrations 050, 051, 052 applied.

---

## Phase 2: Test Backend Locally

```bash
cd "/Users/jameskirk/Desktop/Nerava/nerava-backend-v9 2"

# Start local server
python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8001 --reload &

sleep 5

# Test admin login (use existing admin credentials)
curl -X POST http://localhost:8001/v1/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@nerava.network", "password": "YOUR_ADMIN_PASSWORD"}'

# Test admin exclusives list
TOKEN="YOUR_JWT_TOKEN_FROM_LOGIN"
curl -X GET "http://localhost:8001/v1/admin/exclusives?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Test admin logs
curl -X GET "http://localhost:8001/v1/admin/logs?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# Test merchant visits (replace MERCHANT_ID)
curl -X GET "http://localhost:8001/v1/merchants/MERCHANT_ID/visits?period=week" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Phase 3: Build & Deploy Backend

```bash
cd "/Users/jameskirk/Desktop/Nerava/nerava-backend-v9 2"

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 566287346479.dkr.ecr.us-east-1.amazonaws.com

# Build with v1 portal changes
docker build --platform linux/arm64 --no-cache -t 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v26-portals-v1 .

# Push
docker push 566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v26-portals-v1

# Update App Runner (preserve env vars!)
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v26-portals-v1",
      "ImageRepositoryType": "ECR"
    }
  }'
```

---

## Phase 4: Monitor Backend Deployment

```bash
while true; do
  STATUS=$(aws apprunner describe-service \
    --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
    --query 'Service.Status' --output text)

  IMAGE=$(aws apprunner describe-service \
    --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
    --query 'Service.SourceConfiguration.ImageRepository.ImageIdentifier' --output text | sed 's/.*://')

  echo "[$(date +%H:%M:%S)] Status: $STATUS | Image: $IMAGE"

  if [ "$STATUS" = "RUNNING" ]; then
    echo "Deployment complete!"
    break
  fi

  sleep 30
done
```

---

## Phase 5: Test Production Backend

```bash
# Health check
curl -s https://api.nerava.network/healthz | jq .

# Test admin login
curl -X POST https://api.nerava.network/v1/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@nerava.network", "password": "YOUR_PASSWORD"}'

# With token, test:
TOKEN="YOUR_TOKEN"

# Admin exclusives
curl -s "https://api.nerava.network/v1/admin/exclusives?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Admin logs
curl -s "https://api.nerava.network/v1/admin/logs?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Magic link (verify still works)
curl -s -X POST https://api.nerava.network/v1/magic/generate \
  -H "Content-Type: application/json" \
  -d '{"phone":"+17133056318","exclusive_session_id":"test","merchant_id":"test","charger_id":"test"}' | jq .
```

---

## Phase 5.5: Verify Frontend Apps Can Reach Backend

```bash
# Test that frontend apps can reach the API
# Check CORS headers
curl -I https://api.nerava.network/v1/auth/admin/login \
  -H "Origin: https://admin.nerava.network" \
  -H "Access-Control-Request-Method: POST"

# Should see Access-Control-Allow-Origin header
```

---

## Phase 6: Build & Deploy Admin Portal

```bash
cd "/Users/jameskirk/Desktop/Nerava/apps/admin"

# Install dependencies
npm install

# Set API URL for production
echo "VITE_API_BASE_URL=https://api.nerava.network" > .env.production

# Build
npm run build

# Create S3 bucket for admin portal (if not exists)
aws s3 mb s3://admin.nerava.network --region us-east-1 2>/dev/null || true

# Deploy assets with long cache
aws s3 sync dist/assets/ s3://admin.nerava.network/assets/ \
  --delete \
  --cache-control "public,max-age=31536000,immutable" \
  --region us-east-1

# Deploy index.html with no-cache
aws s3 cp dist/index.html s3://admin.nerava.network/index.html \
  --cache-control "no-cache, no-store, must-revalidate" \
  --region us-east-1

# Deploy other static files
for file in dist/*.{ico,png,svg,txt,xml} 2>/dev/null; do
  if [ -f "$file" ]; then
    aws s3 cp "$file" s3://admin.nerava.network/ \
      --cache-control "public,max-age=3600" \
      --region us-east-1
  fi
done

# Invalidate CloudFront cache (if distribution exists)
# ADMIN_DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[?contains(@, 'admin.nerava.network')]].Id" --output text)
# if [ ! -z "$ADMIN_DIST_ID" ]; then
#   aws cloudfront create-invalidation \
#     --distribution-id "$ADMIN_DIST_ID" \
#     --paths "/index.html" "/assets/*"
# fi
```

---

## Phase 7: Build & Deploy Merchant Portal

```bash
cd "/Users/jameskirk/Desktop/Nerava/apps/merchant"

# Install dependencies
npm install

# Set API URL for production
echo "VITE_API_BASE_URL=https://api.nerava.network" > .env.production

# Build
npm run build

# Create S3 bucket for merchant portal (if not exists)
aws s3 mb s3://merchant.nerava.network --region us-east-1 2>/dev/null || true

# Deploy assets with long cache
aws s3 sync dist/assets/ s3://merchant.nerava.network/assets/ \
  --delete \
  --cache-control "public,max-age=31536000,immutable" \
  --region us-east-1

# Deploy index.html with no-cache
aws s3 cp dist/index.html s3://merchant.nerava.network/index.html \
  --cache-control "no-cache, no-store, must-revalidate" \
  --region us-east-1

# Deploy other static files
for file in dist/*.{ico,png,svg,txt,xml} 2>/dev/null; do
  if [ -f "$file" ]; then
    aws s3 cp "$file" s3://merchant.nerava.network/ \
      --cache-control "public,max-age=3600" \
      --region us-east-1
  fi
done

# Invalidate CloudFront cache (if distribution exists)
# MERCHANT_DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[?contains(@, 'merchant.nerava.network')]].Id" --output text)
# if [ ! -z "$MERCHANT_DIST_ID" ]; then
#   aws cloudfront create-invalidation \
#     --distribution-id "$MERCHANT_DIST_ID" \
#     --paths "/index.html" "/assets/*"
# fi
```

---

## Phase 8: Build & Deploy Driver App

```bash
# NOTE: The primary driver app is at nerava-app-driver, not apps/driver
cd "/Users/jameskirk/Desktop/Nerava/nerava-app-driver"

# Install dependencies
npm install

# Set API URL for production
echo "VITE_API_BASE_URL=https://api.nerava.network" > .env.production
echo "VITE_ENV=prod" >> .env.production
echo "VITE_MOCK_MODE=false" >> .env.production

# Build
npm run build

# Create S3 bucket for driver app (if not exists)
aws s3 mb s3://app.nerava.network --region us-east-1 2>/dev/null || true

# Deploy assets with long cache
aws s3 sync dist/assets/ s3://app.nerava.network/assets/ \
  --delete \
  --cache-control "public,max-age=31536000,immutable" \
  --region us-east-1

# Deploy index.html with no-cache
aws s3 cp dist/index.html s3://app.nerava.network/index.html \
  --cache-control "no-cache, no-store, must-revalidate" \
  --region us-east-1

# Deploy other static files (favicon, etc.)
for file in dist/*.{ico,png,svg,txt,xml} 2>/dev/null; do
  if [ -f "$file" ]; then
    aws s3 cp "$file" s3://app.nerava.network/ \
      --cache-control "public,max-age=3600" \
      --region us-east-1
  fi
done

# Invalidate CloudFront cache (if distribution exists)
# Get distribution ID first:
# DRIVER_DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[?contains(@, 'app.nerava.network')]].Id" --output text)
# if [ ! -z "$DRIVER_DIST_ID" ]; then
#   aws cloudfront create-invalidation \
#     --distribution-id "$DRIVER_DIST_ID" \
#     --paths "/index.html" "/assets/*"
# fi
```

---

## Phase 9: Build & Deploy Landing Page

```bash
cd "/Users/jameskirk/Desktop/Nerava/apps/landing"

# Install dependencies
npm install

# Set environment for static export
export NEXT_STATIC_EXPORT=true
echo "NEXT_STATIC_EXPORT=true" > .env.production

# Build (Next.js will export static files to 'out' directory)
npm run build

# Verify build output exists
if [ ! -d "out" ]; then
  echo "Error: Build output 'out' directory not found"
  echo "Check next.config.mjs - ensure output: 'export' is set"
  exit 1
fi

# Create S3 bucket for landing page (if not exists)
aws s3 mb s3://nerava.network --region us-east-1 2>/dev/null || true

# Deploy static assets with long cache
aws s3 sync out/_next/static/ s3://nerava.network/_next/static/ \
  --delete \
  --cache-control "public,max-age=31536000,immutable" \
  --region us-east-1

# Deploy other assets
aws s3 sync out/ s3://nerava.network/ \
  --delete \
  --cache-control "public,max-age=3600" \
  --exclude "_next/static/*" \
  --exclude "*.html" \
  --region us-east-1

# Deploy HTML files with no-cache
aws s3 sync out/ s3://nerava.network/ \
  --delete \
  --cache-control "no-cache, no-store, must-revalidate" \
  --include "*.html" \
  --region us-east-1

# Invalidate CloudFront cache (if distribution exists)
# Get distribution ID first:
# LANDING_DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[?contains(@, 'nerava.network') && !contains(@, 'app.') && !contains(@, 'merchant.') && !contains(@, 'admin.')]].Id" --output text)
# if [ ! -z "$LANDING_DIST_ID" ]; then
#   aws cloudfront create-invalidation \
#     --distribution-id "$LANDING_DIST_ID" \
#     --paths "/*"
# fi
```

---

## Phase 9.5: Verify Frontend Apps Deployment

```bash
# Check S3 buckets have files
echo "Checking Admin Portal..."
aws s3 ls s3://admin.nerava.network/ --recursive | head -5

echo "Checking Merchant Portal..."
aws s3 ls s3://merchant.nerava.network/ --recursive | head -5

echo "Checking Driver App..."
aws s3 ls s3://app.nerava.network/ --recursive | head -5

echo "Checking Landing Page..."
aws s3 ls s3://nerava.network/ --recursive | head -5

# Test S3 website endpoints (if website hosting enabled)
# curl -I http://admin.nerava.network.s3-website-us-east-1.amazonaws.com
# curl -I http://merchant.nerava.network.s3-website-us-east-1.amazonaws.com
# curl -I http://app.nerava.network.s3-website-us-east-1.amazonaws.com
# curl -I http://nerava.network.s3-website-us-east-1.amazonaws.com
```

---

## Phase 10: Create Admin User (if needed)

If no admin user exists, create one:

```bash
cd "/Users/jameskirk/Desktop/Nerava/nerava-backend-v9 2"

python3 << 'EOF'
import os
os.environ['DATABASE_URL'] = 'postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava'

from app.db import SessionLocal
from app.models import User
from app.core.security import get_password_hash

db = SessionLocal()

# Check if admin exists
admin = db.query(User).filter(User.email == "admin@nerava.network").first()
if admin:
    print(f"Admin exists: {admin.email}, role_flags: {admin.role_flags}")
    if "admin" not in (admin.role_flags or ""):
        admin.role_flags = "admin"
        db.commit()
        print("Added admin role")
else:
    # Create admin
    admin = User(
        email="admin@nerava.network",
        hashed_password=get_password_hash("SECURE_PASSWORD_HERE"),
        role_flags="admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    print(f"Created admin: {admin.email}")

db.close()
EOF
```

---

## Verification Checklist

### Backend
- [ ] Migrations 050, 051, 052 applied
- [ ] `/v1/auth/admin/login` returns token
- [ ] `/v1/admin/exclusives` returns list
- [ ] `/v1/admin/exclusives/{id}/toggle` works with reason
- [ ] `/v1/admin/merchants/{id}/pause` works
- [ ] `/v1/admin/merchants/{id}/resume` works
- [ ] `/v1/admin/sessions/force-close` works
- [ ] `/v1/admin/overrides/emergency-pause` works with confirmation
- [ ] `/v1/admin/logs` returns audit entries
- [ ] `/v1/merchants/{id}/visits` returns billable events
- [ ] Magic link endpoint still works

### Admin Portal
- [ ] Can login with admin credentials
- [ ] Exclusives page loads real data
- [ ] Can toggle exclusive on/off
- [ ] Overrides page force-close works
- [ ] Logs page shows real entries
- [ ] Merchants page pause/resume works

### Merchant Portal
- [ ] Visits page loads real data
- [ ] Period filter works (week/month)
- [ ] Status filter works
- [ ] Verified count displays
- [ ] Billing page shows manual invoicing banner

### Driver App
- [ ] App loads at https://app.nerava.network (or CloudFront URL)
- [ ] Can navigate between screens
- [ ] API calls work (check network tab - should call https://api.nerava.network)
- [ ] Exclusive activation flow works
- [ ] Wallet displays correctly
- [ ] No console errors related to API calls

### Landing Page
- [ ] Landing page loads at https://nerava.network (or CloudFront URL)
- [ ] All images and assets load correctly
- [ ] Navigation works
- [ ] Links to driver app work
- [ ] Mobile responsive
- [ ] No console errors

---

## Rollback Plan

If deployment fails:

```bash
# Rollback backend to previous working version
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v25-import-fixes",
      "ImageRepositoryType": "ECR"
    }
  }'

# Rollback migrations if needed
cd "/Users/jameskirk/Desktop/Nerava/nerava-backend-v9 2"
export DATABASE_URL="..."
alembic downgrade -3  # Go back 3 migrations

# Rollback frontend deployments (revert to previous S3 version if needed)
# Note: S3 versioning must be enabled for this to work
# aws s3api list-object-versions --bucket app.nerava.network --prefix index.html
# aws s3api get-object --bucket app.nerava.network --key index.html --version-id PREVIOUS_VERSION_ID index.html
```
