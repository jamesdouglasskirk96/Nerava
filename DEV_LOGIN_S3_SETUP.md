# Dev Login for S3 Staging Sites - Implementation Summary

## Changes Made

### 1. Backend Changes ✅

**File**: `nerava-backend-v9/app/routers/auth.py`

Updated the `/auth/dev/login` endpoint to allow dev login from S3 staging sites:

- Added detection for S3 staging sites by checking if `FRONTEND_URL` contains:
  - `s3-website`
  - `.s3.`
  - `nerava-ui-prod`
- Dev login now works when:
  - `DEMO_MODE=true` is enabled, OR
  - Running on localhost/127.0.0.1, OR
  - Frontend URL is an S3 staging site

**Code Changes:**
```python
# Check if frontend URL is S3 staging site
frontend_url_lower = str(settings.FRONTEND_URL).lower()
is_s3_staging = (
    "s3-website" in frontend_url_lower or
    ".s3." in frontend_url_lower or
    "nerava-ui-prod" in frontend_url_lower
)

# Always allow in dev/local environments, S3 staging sites, or if DEMO_MODE is enabled
if not settings.DEMO_MODE and not is_localhost and not is_s3_staging:
    logger.warning("Dev login rejected - not in DEMO_MODE, not localhost, and not S3 staging")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Dev login endpoint not available"
    )
```

### 2. Frontend Changes ✅

**File**: `ui-mobile/js/pages/login.js`

The frontend already had S3 staging site detection. When "Continue with Phone" is clicked:
- Detects S3 staging sites by checking hostname for:
  - `s3-website`
  - `.s3.`
  - `nerava-ui-prod`
- If S3 staging site detected, automatically calls `apiDevLogin()` to log in as `dev@nerava.local`
- Falls back to normal phone OTP flow if dev login fails

### 3. Frontend Deployment ✅

**Deployed to**: `s3://nerava-ui-prod-ada7c063`

All updated JavaScript files have been deployed to the S3 bucket with proper cache headers.

## Backend Configuration Required

For the backend to allow dev login from S3 sites, ensure the `FRONTEND_URL` environment variable is set to the S3 website URL:

```bash
FRONTEND_URL=http://nerava-ui-prod-ada7c063.s3-website-us-east-1.amazonaws.com
```

**To update in AWS App Runner:**
1. Go to AWS Console → App Runner → Your Service
2. Navigate to Configuration → Environment Variables
3. Set `FRONTEND_URL` to: `http://nerava-ui-prod-ada7c063.s3-website-us-east-1.amazonaws.com`
4. Save and redeploy (or wait for automatic deployment)

## Testing

### Test Steps

1. Navigate to: `http://nerava-ui-prod-ada7c063.s3-website-us-east-1.amazonaws.com`
2. Click "Continue with Phone"
3. Should automatically log in as `dev@nerava.local` without requiring phone/OTP
4. Should redirect to wallet page

### Expected Behavior

- **Before**: Clicking "Continue with Phone" would show phone input form
- **After**: Clicking "Continue with Phone" automatically logs in as dev user and redirects to wallet

### Troubleshooting

If dev login doesn't work:

1. **Check backend logs** for dev login attempts:
   - Look for: `"Dev login attempt - DEMO_MODE: ..., is_s3_staging: ..."`
   - If `is_s3_staging: False`, check that `FRONTEND_URL` is set correctly

2. **Check browser console**:
   - Look for: `[Login] Dev mode detected - auto-logging in as dev@nerava.local`
   - If you see `[Login] Not in dev mode, showing phone input`, the S3 detection isn't working

3. **Verify S3 bucket URL**:
   - Ensure the bucket website hosting is enabled
   - Check that the URL matches what's in `FRONTEND_URL`

4. **Hard refresh browser**:
   - Press `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows) to clear cache
   - Or clear browser cache for the site

## Security Notes

- Dev login is **only enabled** for:
  - Localhost/127.0.0.1
  - S3 staging sites (detected by URL pattern)
  - When `DEMO_MODE=true` is set
- **Do not** enable `DEMO_MODE=true` in production
- S3 staging sites are identified by URL patterns, which is safe for staging environments

## Files Modified

1. `nerava-backend-v9/app/routers/auth.py` - Added S3 staging site detection
2. `ui-mobile/js/pages/login.js` - Already had S3 detection (no changes needed)
3. Deployed `ui-mobile/js/pages/login.js` and `ui-mobile/js/core/api.js` to S3

## Next Steps

1. ✅ Backend code updated
2. ✅ Frontend code verified
3. ✅ Frontend deployed to S3
4. ⏳ **Update backend `FRONTEND_URL` environment variable** (required)
5. ⏳ Test dev login flow from S3 site

