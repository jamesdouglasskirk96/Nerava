# Docker Build Architecture Fix - Summary

## Problem Identified
Docker BuildKit was adding attestation manifests with `unknown/unknown` architecture, causing App Runner deployments to fail and rollback.

## Solution Applied

### ✅ Step 1: Rebuilt Image Without Attestations
```bash
docker build --platform linux/amd64 --provenance=false --sbom=false -t nerava-backend:v15 .
```

**Result:**
- ✅ Architecture: `linux/amd64`
- ✅ Single manifest (not multi-manifest)
- ✅ No attestation manifests

### ✅ Step 2: Verified Image Architecture
- `docker inspect` confirmed: `linux/amd64`
- `docker manifest inspect` confirmed: Single image (not manifest list)

### ✅ Step 3: Pushed to ECR
- Tagged: `v15-fixed-arch`
- Pushed successfully to ECR
- ECR manifest shows single image (no `unknown/unknown` platform)

### ✅ Step 4: Updated App Runner
- Service updated to use `v15-fixed-arch`
- Deployment status: `OPERATION_IN_PROGRESS`

## Image Details

**ECR Image:** `566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v15-fixed-arch`
**Digest:** `sha256:a17842220f04202c9e09190eec7106324b9d6b4f8b18c5d5f7702abea25f2e2f`
**Manifest Type:** Single image (v2 schema)
**Platform:** `linux/amd64`

## Next Steps

1. **Monitor Deployment:**
   ```bash
   aws apprunner list-operations \
     --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
     --region us-east-1 | jq '.OperationSummaryList[0]'
   ```

2. **Wait for Status:** Should be `SUCCEEDED` (not `ROLLBACK_SUCCEEDED`)

3. **Verify Endpoints:**
   ```bash
   # Health check
   curl https://api.nerava.network/healthz
   
   # Discovery endpoint
   curl "https://api.nerava.network/v1/chargers/discovery?lat=30.3839&lng=-97.6900"
   
   # Merchants/open endpoint
   curl "https://api.nerava.network/v1/drivers/merchants/open?charger_id=ch_domain_tesla_001"
   ```

## Expected Results

- ✅ `/healthz` → `{"ok":true,...}`
- ✅ `/v1/chargers/discovery` → JSON response with chargers (NOT 404)
- ✅ `/v1/drivers/merchants/open` → JSON array (empty or with merchants, NOT 404)

## Key Fix

The critical change was adding `--provenance=false --sbom=false` flags to prevent Docker BuildKit from adding attestation manifests that App Runner cannot handle.


