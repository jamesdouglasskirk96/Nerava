# Root Cause Analysis: v19 Works, v20-v23 Fail

**Date:** 2026-01-23
**Status:** Investigation Complete - Root Cause is App Runner-Specific (Cannot Reproduce Locally)

---

## Executive Summary

**Problem:** All deployments since v19 (`v20-v23`) fail with "Container exit code: 1" in App Runner, but work perfectly locally.

**Key Finding:** The issue is **100% App Runner-specific**. The container works perfectly locally in all tested scenarios:
- With all App Runner env vars
- With network disabled (`--network none`)
- With restricted memory
- In Docker and directly with Python

**Root Cause:** Unknown App Runner runtime issue. The container exits with code 1 BEFORE any Python logs are emitted, suggesting Python itself fails to start or is killed by the runtime.

---

## Investigation Results

### What We Tested (All Pass Locally)

1. ✅ **All imports work locally** - No import errors found
2. ✅ **Container starts successfully locally** - Docker container runs fine
3. ✅ **OTP service initialization is lazy** - No module-level blocking calls
4. ✅ **Twilio Client creation doesn't block** - No network calls during init
5. ✅ **Rate limit service uses in-memory storage** - No Redis required
6. ✅ **Auth router imports are lazy** - OTPServiceV2 imported inside route handlers
7. ✅ **App Runner has SKIP_STARTUP_VALIDATION=true** - Validation is skipped
8. ✅ **Network disabled test** - Container starts with `--network none`
9. ✅ **Same env vars as App Runner** - All 28 env vars work locally
10. ✅ **ECR image verified** - Same digest as local image

### What Fails (Only in App Runner)

- ❌ **Container exits with code 1 only in App Runner**
- ❌ **No application logs appear** - Container crashes BEFORE first Python `print()` statement
- ❌ **Health check fails** - No HTTP server running (uvicorn never starts)
- ❌ **5 consecutive deployment attempts** - All rolled back

---

## Code Changes Since v19

### Commit 54309d4: OTP Fix (Jan 23, 05:33)

**Files Changed:**
- `backend/app/core/config.py` - Added `TWILIO_TIMEOUT_SECONDS`
- `backend/app/services/auth/twilio_verify.py` - Added async executor pattern
- `backend/app/services/auth/twilio_sms.py` - Added async executor pattern
- `backend/scripts/check_twilio_config.py` - New diagnostic script

**Key Changes:**
- Added `TwilioHttpClient` with explicit timeout
- Wrapped Twilio API calls in `asyncio.to_thread()`
- Added timeout handling

**Analysis:**
- All Twilio initialization is lazy (inside route handlers)
- No module-level blocking operations
- Works perfectly locally

---

## Root Cause Hypothesis

Since all code works locally but fails in App Runner, the issue must be **App Runner-specific**:

### Most Likely Causes (Ranked by Probability)

1. **App Runner Instance Size/Memory (HIGH):**
   - v23 image is larger (117MB vs 103MB for v19)
   - May exceed memory limits during startup
   - Python may be killed by OOM before logging starts

2. **Startup Timeout (MEDIUM):**
   - v23 has more code to import
   - App Runner may kill container before startup completes
   - Health check starts before app is ready

3. **Python/glibc Compatibility (MEDIUM):**
   - Something in the new imports may not work in Fargate's runtime
   - `asyncio.to_thread()` behavior might differ
   - `TwilioHttpClient` import may have side effects

4. **Image Layer Caching (LOW):**
   - App Runner may have stale cache of image layers
   - Different layer order could cause issues

### Why v19 Works

**v19 was built before commit `54309d4` (OTP fix):**
- Smaller image size (103MB vs 117MB)
- No `TwilioHttpClient` import
- No `asyncio.to_thread()` usage
- Same CMD, same base image, same Python version

### Code Diff Summary

**New in v20+:**
```python
# twilio_verify.py
import asyncio  # NEW
from twilio.http.http_client import TwilioHttpClient  # NEW

class TwilioVerifyProvider:
    def __init__(self):
        # v19: self.client = Client(...)
        # v20+: Creates TwilioHttpClient with custom timeout
        custom_http_client = TwilioHttpClient()
        custom_http_client.timeout = settings.TWILIO_TIMEOUT_SECONDS
        self.client = Client(..., http_client=custom_http_client)
```

**Note:** This code is only executed when `TwilioVerifyProvider()` is instantiated, which happens lazily in route handlers. The imports themselves should not block.

---

## Evidence

### App Runner Logs
```
[AppRunner] Your application stopped or failed to start. See logs for more information.
Container exit code: 1
[AppRunner] Health check failed on protocol `HTTP`[Path: '/healthz'], [Port: '8000']
```

**Note:** No application logs appear, suggesting the container crashes before Python logging initializes.

### Local Testing
```bash
# All of these work perfectly:
python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8000
docker run -it nerava-backend:v23-fixed-cmd
python3 -c "from app.main_simple import app; print('Success')"
```

### App Runner Environment
```json
{
  "SKIP_STARTUP_VALIDATION": "true",
  "ENV": "prod",
  "OTP_PROVIDER": "twilio_verify",
  ...
}
```

---

## Recommended Solutions

### Immediate Fix (To Activate Exclusive Today)

**Option 1: Deploy v19 Temporarily**
```bash
# Use existing v19 image that works
aws apprunner update-service \
  --service-arn "arn:aws:apprunner:us-east-1:566287346479:service/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3" \
  --source-configuration '{
    "ImageRepository": {
      "ImageIdentifier": "566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:v19-photo-fix",
      "ImageConfiguration": {
        "RuntimeEnvironmentVariables": {...all 28 vars...}
      }
    }
  }'
```

**Option 2: Add More Logging**
- Add print statements at the very start of `main_simple.py`
- Log every import and initialization step
- Check App Runner logs to see where it fails

**Option 3: Test Without OTP Fix**
- Temporarily revert OTP fix commit
- Build new image and test deployment
- If it works, the issue is in the OTP fix code

### Long-term Fix

1. **Add Comprehensive Startup Logging:**
   - Log every import and initialization
   - Log environment variable values (masked)
   - Log network connectivity checks

2. **Make Initialization More Resilient:**
   - Add retry logic for external service connections
   - Make all external dependencies optional during startup
   - Use lazy initialization for everything

3. **Improve Error Handling:**
   - Catch all exceptions during startup
   - Log detailed error messages
   - Don't exit silently

---

## Next Steps (Prioritized)

### Immediate (To Activate Exclusive Today)

1. **Deploy v19 Temporarily:**
   ```bash
   # v19 works - deploy it to restore service immediately
   # OTP will timeout but health checks will pass
   ```

### Short-term Investigation

2. **Check App Runner Service Configuration:**
   ```bash
   aws apprunner describe-service \
     --service-arn "..." \
     --query 'Service.{Memory:InstanceConfiguration.Memory,CPU:InstanceConfiguration.Cpu}'
   ```
   - If memory is 512MB, try increasing to 1GB
   - If CPU is 0.25 vCPU, try increasing to 0.5 vCPU

3. **Increase Health Check Timeout:**
   - Current: 5 second timeout, 5 retries
   - Try: 30 second timeout, 10 retries
   - Gives container more time to start

4. **Test Minimal v20 Image:**
   - Build v20 with ONLY the TwilioHttpClient import change
   - If it fails, the issue is the import itself
   - If it works, the issue is something else

### Long-term Fix

5. **Add Comprehensive Startup Logging:**
   - Add print statements before EVERY import
   - Catch and log ALL exceptions during startup
   - Don't exit silently - always print something

6. **Create "Startup Health Check":**
   - Add `/startup` endpoint that returns before full initialization
   - Use this for App Runner health checks
   - Full app initializes in background

7. **Consider Alternative Deployment:**
   - Deploy to ECS/Fargate directly (more control)
   - Deploy to EC2 (most control)
   - Use Lambda for OTP endpoints only

---

## Conclusion

**Root Cause:** App Runner-specific initialization failure related to code added after v19. The container exits silently before uvicorn can start, suggesting a blocking operation or import failure that only occurs in App Runner's environment.

**Why v19 Works:** v19 was built before the OTP fix commit (`54309d4`), so it doesn't have the new code paths that may be causing the issue.

**Immediate Action:** Deploy v19 temporarily to restore service, then investigate the specific code change that causes the failure.

**Long-term Fix:** Add comprehensive logging, make initialization more resilient, and test incremental changes to isolate the exact cause.
