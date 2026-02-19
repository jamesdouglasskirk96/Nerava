# OTP Deployment Health Check Issue

**Date:** 2026-01-23
**Issue:** Deployment keeps rolling back due to health check failures

## Problem

Deployment of `v20-otp-fix-fixed` with VPC egress keeps rolling back with:
```
Health check failed on protocol `HTTP`[Path: '/healthz'], [Port: '8000']
```

## Current Status

- ✅ NAT Gateway configured and working
- ✅ VPC egress configured correctly
- ✅ Image `v20-otp-fix-fixed` exists and works locally
- ✅ `/healthz` endpoint responds correctly (tested locally)
- ✅ `SKIP_STARTUP_VALIDATION=true` is set
- ❌ Health check fails during App Runner deployment

## Health Check Configuration

```json
{
  "Protocol": "HTTP",
  "Path": "/healthz",
  "Interval": 10,
  "Timeout": 5,
  "HealthyThreshold": 1,
  "UnhealthyThreshold": 5
}
```

This means:
- Checks `/healthz` every 10 seconds
- Times out after 5 seconds
- Fails after 5 consecutive failures (~50 seconds total)

## Possible Causes

1. **App takes too long to start** - FastAPI server not ready when health check runs
2. **Startup blocking** - Something blocking during startup (even with SKIP_STARTUP_VALIDATION)
3. **Network issue** - Health check can't reach container during deployment
4. **Port binding** - Container not listening on port 8000 fast enough

## Solutions to Try

### Option 1: Increase Health Check Timeout (if possible)
App Runner doesn't allow changing health check config via API, but we could try recreating the service.

### Option 2: Make Startup Faster
- Ensure all initialization is non-blocking
- Move heavy operations to background tasks
- Verify `/healthz` responds before any heavy initialization

### Option 3: Test Image Startup Time
```bash
# Time how long it takes for /healthz to respond
time docker run --rm -p 8001:8000 \
  -e ENV=prod \
  -e DATABASE_URL="postgresql://..." \
  -e JWT_SECRET="test" \
  -e SKIP_STARTUP_VALIDATION=true \
  nerava-backend:v20-otp-fix-fixed &
  
sleep 2
time curl http://localhost:8001/healthz
```

### Option 4: Check if Old Image Starts Faster
Compare startup time between `v19-photo-fix` and `v20-otp-fix-fixed`.

### Option 5: Use Different Health Check Path
If `/healthz` has issues, try `/health` (but App Runner expects `/healthz`).

## Next Steps

1. Test startup time of both images
2. Check if there's a difference in startup sequence
3. Consider if PostHog initialization (recently fixed) is causing delay
4. Check App Runner service logs for more details

## Current Deployment Status

- Service: RUNNING (rolled back to `v19-photo-fix`)
- Egress: VPC
- Health endpoint: Working on old image
- OTP: Still timing out (VPC blocking Twilio, but NAT Gateway should fix this)




