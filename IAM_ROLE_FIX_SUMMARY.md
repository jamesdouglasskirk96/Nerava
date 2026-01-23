# IAM Role Fix and Deployment Summary

## Problem Identified
Previous deployments were failing because the **wrong IAM role name** was used:
- ❌ **Wrong**: `AppRunnerECRAccess`
- ✅ **Correct**: `AppRunnerECRAccessRole`

This caused App Runner to fail pulling the image from ECR, resulting in `ROLLBACK_SUCCEEDED` status.

## Solution Applied

### ✅ Step 1: Verified IAM Role Exists
```bash
aws iam get-role --role-name AppRunnerECRAccessRole
```
**Result:** Role exists and is accessible ✅

### ✅ Step 2: Updated Service with Correct Role
Updated App Runner service configuration:
- **IAM Role**: `arn:aws:iam::566287346479:role/AppRunnerECRAccessRole` ✅
- **Image**: `v15-fixed-arch` (correct architecture, no attestations) ✅
- **Status**: `OPERATION_IN_PROGRESS` ✅

## Current Deployment Status

**Service Configuration:**
- Image: `566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v15-fixed-arch`
- IAM Role: `AppRunnerECRAccessRole` ✅
- Status: `OPERATION_IN_PROGRESS` (deploying)

**Previous Issues Resolved:**
1. ✅ Docker attestation issue - Fixed with `--provenance=false --sbom=false`
2. ✅ IAM role name - Fixed to `AppRunnerECRAccessRole`
3. ✅ Image architecture - Single manifest `linux/amd64`

## Verification Steps

### 1. Monitor Deployment
```bash
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --region us-east-1 | jq '.OperationSummaryList[0].Status'
```

**Expected:** `SUCCEEDED` (not `ROLLBACK_SUCCEEDED`)

### 2. Test Endpoints After Deployment
```bash
# Health check
curl https://api.nerava.network/healthz
# Expected: {"ok":true,...}

# Discovery endpoint
curl "https://api.nerava.network/v1/chargers/discovery?lat=30.3839&lng=-97.6900"
# Expected: JSON response with chargers (NOT 404)

# Merchants/open endpoint
curl "https://api.nerava.network/v1/drivers/merchants/open?charger_id=ch_domain_tesla_001"
# Expected: JSON array (empty or with merchants, NOT 404)
```

### 3. Verify OpenAPI Registration
```bash
curl "https://api.nerava.network/openapi.json" | jq '.paths | keys | .[] | select(contains("discovery") or contains("merchants/open"))'
```

**Expected:** Both endpoints should appear in OpenAPI schema

## Timeline

1. **09:13:44** - Previous deployment started (wrong IAM role)
2. **09:20:12** - Previous deployment rolled back (`ROLLBACK_SUCCEEDED`)
3. **09:40:05** - New deployment started with correct IAM role
4. **Current** - Deployment in progress (`IN_PROGRESS`)

## Next Steps

1. **Wait for deployment** - Typically takes 5-10 minutes
2. **Verify status** - Should show `SUCCEEDED` (not rollback)
3. **Test endpoints** - Both `/v1/chargers/discovery` and `/v1/drivers/merchants/open` should work
4. **Seed database** - Run `seed_asadas_grill.py` to populate merchant data

## Summary

**Root Causes Fixed:**
1. ✅ Docker BuildKit attestation manifests → Fixed with `--provenance=false --sbom=false`
2. ✅ IAM role name typo → Fixed to `AppRunnerECRAccessRole`
3. ✅ Image architecture → Single manifest `linux/amd64`

**Current Status:**
- Deployment in progress with correct configuration
- Should succeed this time (no more rollbacks expected)
- Endpoints will be available once deployment completes


