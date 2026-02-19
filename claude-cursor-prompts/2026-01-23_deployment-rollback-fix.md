# Deployment Rollback Fix

**Date:** 2026-01-23
**Issue:** App Runner deployment kept rolling back due to startup validation bug
**Root Cause:** Attribute name mismatch in startup validation code

---

## Problem Identified

### Symptoms
- Multiple deployment rollbacks (`ROLLBACK_SUCCEEDED`)
- Service stayed on old image `v19-photo-fix`
- OTP endpoint still timing out
- Health checks failing during deployment

### Root Cause
**File:** `backend/app/core/startup_validation.py`

**Bug:** Line 21 and 47 accessed `settings.database_url` (lowercase) but Settings class uses `DATABASE_URL` (uppercase)

```python
# ❌ WRONG (caused AttributeError)
if settings.jwt_secret == settings.database_url:
database_url = os.getenv("DATABASE_URL", settings.database_url)

# ✅ FIXED
if settings.jwt_secret == settings.DATABASE_URL:
database_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
```

**Error:** `AttributeError: 'Settings' object has no attribute 'database_url'`

This caused startup to fail, health checks to fail, and App Runner to rollback.

---

## Fix Applied

### Changes Made
1. **Fixed `validate_jwt_secret()` function**
   - Changed `settings.database_url` → `settings.DATABASE_URL`

2. **Fixed `validate_database_url()` function**
   - Changed `settings.database_url` → `settings.DATABASE_URL`

### New Image
- **Tag:** `v20-otp-fix-fixed`
- **Digest:** `sha256:13f61fc790d6679b8b5faa1c11020d1f78e59098342178910baa808a64870757`
- **Status:** Pushed to ECR, deployment initiated

---

## Deployment Status

### Current State
- **Operation:** `UPDATE_SERVICE`
- **Status:** `OPERATION_IN_PROGRESS`
- **Image:** `v20-otp-fix-fixed`
- **Started:** Just now

### Previous Attempts
- `v20-otp-fix` - Rolled back due to startup validation bug
- Multiple previous rollbacks (03:08, 03:35, 05:46 AM)

---

## Verification Steps

### 1. Wait for Deployment (5-15 minutes)
```bash
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'OperationSummaryList[0]'
```

**Expected:** Status changes from `IN_PROGRESS` → `SUCCEEDED`

### 2. Verify Service Status
```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --query 'Service.[Status,SourceConfiguration.ImageRepository.ImageIdentifier]'
```

**Expected:**
- Status: `RUNNING`
- Image: `v20-otp-fix-fixed`

### 3. Test OTP Endpoint
```bash
curl -X POST "https://api.nerava.network/v1/auth/otp/start" \
  -H "Content-Type: application/json" \
  -d '{"phone": "+17133056318"}' \
  --max-time 35
```

**Expected:** `{"otp_sent": true}` within 30 seconds

---

## Files Changed

### Backend
- `backend/app/core/startup_validation.py` - Fixed attribute name bug
- `backend/Dockerfile` - No changes (same as before)

### Docker Images
- `v20-otp-fix` - Original fix (had startup bug)
- `v20-otp-fix-fixed` - Fixed version (startup validation corrected)

---

## Success Criteria

- [ ] Deployment status: `SUCCEEDED` (not rollback)
- [ ] Service status: `RUNNING`
- [ ] Image: `v20-otp-fix-fixed`
- [ ] Health check: `{"ok":true}`
- [ ] OTP endpoint: `{"otp_sent":true}` (< 30 seconds)
- [ ] SMS received on phone

---

## Lessons Learned

1. **Always test startup validation locally** before deploying
2. **Check attribute names** match Settings class exactly
3. **Monitor deployment operations** to catch rollbacks early
4. **Health check failures** often indicate startup issues

---

**Next Steps:** Monitor deployment and verify OTP endpoint once deployment completes.




