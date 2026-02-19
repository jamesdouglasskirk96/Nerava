# App Runner Deployment Failure Analysis

## Root Cause Identified

**The containers are crashing during Python module import BEFORE uvicorn starts**, which explains:
- No CloudWatch logs (container exits before HTTP server starts)
- Health check timeouts (no HTTP server to respond)
- Works locally (likely has `ENV=local` or `SKIP_STARTUP_VALIDATION=true`)

## Critical Issue: Strict Startup Validation

### The Problem

In `backend/app/main_simple.py` lines 123-125:

```python
skip_validation = os.getenv("SKIP_STARTUP_VALIDATION", "false").lower() == "true"
strict_validation_default = "true" if not is_local_env() else "false"
strict_validation = os.getenv("STRICT_STARTUP_VALIDATION", strict_validation_default).lower() == "true"
```

**Key Facts:**
1. `STRICT_STARTUP_VALIDATION` defaults to `true` in non-local environments
2. `is_local_env()` returns `False` unless `ENV=local` or `ENV=dev`
3. If validation fails with strict mode enabled, it calls `sys.exit(1)` (lines 191, 212)
4. This happens **BEFORE uvicorn starts**, so no HTTP server = no logs = health check fails

### Validation Checks That Could Fail

From `backend/app/core/startup_validation.py`, these checks run in non-local environments:

1. **JWT_SECRET validation** (lines 16-40)
   - Must not equal DATABASE_URL
   - Must not be "dev-secret" or "dev-secret-change-me"
   - **Fails if:** JWT_SECRET is missing or uses default value

2. **DATABASE_URL validation** (lines 42-60)
   - Must not be SQLite
   - **Fails if:** DATABASE_URL starts with `sqlite:`

3. **REDIS_URL validation** (lines 63-80)
   - Must be configured (not localhost default)
   - **Fails if:** REDIS_URL is missing or `redis://localhost:6379/0`

4. **TOKEN_ENCRYPTION_KEY validation** (lines 119-159)
   - Must be set
   - Must be 44 characters (valid Fernet key)
   - **Fails if:** Missing or invalid format

5. **CORS origins validation** (lines 162-182)
   - Must not be wildcard (*) in non-local
   - **Fails if:** ALLOWED_ORIGINS="*"

6. **Public URLs validation** (lines 185-218)
   - Must not contain localhost in prod
   - **Fails if:** PUBLIC_BASE_URL or FRONTEND_URL contain localhost

7. **DEMO_MODE validation** (lines 221-237)
   - Must be disabled in prod
   - **Fails if:** DEMO_MODE=true in prod

8. **MERCHANT_AUTH_MOCK validation** (lines 240-256)
   - Must be disabled in prod
   - **Fails if:** MERCHANT_AUTH_MOCK=true in prod

## Why v24 Works But v27-v32 Fail

### Hypothesis 1: Environment Variables Changed
- v24 might have had `SKIP_STARTUP_VALIDATION=true` or `STRICT_STARTUP_VALIDATION=false`
- v24 might have had `ENV=local` or `ENV=dev` set
- v27-v32 might be missing required env vars (REDIS_URL, TOKEN_ENCRYPTION_KEY, etc.)

### Hypothesis 2: Validation Logic Was Added/Changed
- Check git history to see if validation was added between v24 and v27
- Check if `is_local_env()` logic changed

### Hypothesis 3: Import-Time Failure
- Something imported at module level (before validation) could be hanging/crashing
- Check imports in `main_simple.py` lines 1-42

## Image Size Discrepancy Analysis

**Observation:**
- v24: 118MB local → 112MB ECR ✅
- v27-v32: ~550MB local → 112MB ECR ❌

**Possible Causes:**
1. **Build context includes large files** that are excluded by `.dockerignore` but still copied
2. **Multi-stage build issue** - intermediate layers not being pruned
3. **Docker build cache** - old layers being reused incorrectly

**Investigation Needed:**
```bash
# Compare what's actually in the images
docker history nerava-backend:v24-lazy-import --no-trunc | head -30
docker history nerava-backend:v32-auth-only --no-trunc | head -30

# Check what's being copied
docker build --no-cache -t test-debug . 2>&1 | grep -i "COPY\|ADD"
```

## Immediate Fixes

### Fix 1: Make Validation Non-Fatal for Health Checks

**Option A: Set environment variable in App Runner**
```
SKIP_STARTUP_VALIDATION=true
```
OR
```
STRICT_STARTUP_VALIDATION=false
```

**Option B: Modify code to always allow /healthz even if validation fails**

The `/healthz` endpoint is already defined early (line 332), but validation happens before uvicorn starts. We need to ensure validation failures don't prevent uvicorn from starting.

**Recommended:** Set `STRICT_STARTUP_VALIDATION=false` in App Runner environment variables as a temporary fix, then investigate which validation is failing.

### Fix 2: Add Better Error Logging

The validation errors are printed with `flush=True`, but if the container exits immediately, logs might not be captured. Consider:

1. **Write to a file** before exiting:
```python
if strict_validation:
    with open("/tmp/startup_validation_error.log", "w") as f:
        f.write(f"Validation failed: {error_msg}\n")
    sys.exit(1)
```

2. **Use stderr** explicitly:
```python
print(f"[STARTUP ERROR] {error_msg}", file=sys.stderr, flush=True)
```

### Fix 3: Ensure Required Environment Variables Are Set

Check App Runner environment variables for:
- `ENV` (should be `prod` or `staging`, not `local` or `dev`)
- `JWT_SECRET` (must be set and not default)
- `DATABASE_URL` (must be PostgreSQL, not SQLite)
- `REDIS_URL` (must be configured)
- `TOKEN_ENCRYPTION_KEY` (must be 44-char Fernet key)
- `ALLOWED_ORIGINS` (must not be `*`)

## Diagnostic Steps

### Step 1: Check App Runner Environment Variables
```bash
# In AWS Console or CLI, check App Runner service environment variables
aws apprunner describe-service --service-arn <arn> | jq '.Service.InstanceConfiguration.EnvironmentVariables'
```

### Step 2: Test Locally with Production-Like Environment
```bash
# Simulate App Runner environment
export ENV=prod
export STRICT_STARTUP_VALIDATION=true
# Unset or set to invalid values to test validation failures
unset REDIS_URL
unset TOKEN_ENCRYPTION_KEY

# Run container
docker run --rm -e ENV=prod -e STRICT_STARTUP_VALIDATION=true \
  -e DATABASE_URL=postgresql://... \
  nerava-backend:v32-auth-only
```

### Step 3: Add Debug Logging
Add this at the very start of `main_simple.py`:
```python
import sys
import os

# Write startup log to file immediately
with open("/tmp/startup.log", "w") as f:
    f.write(f"Python started\n")
    f.write(f"ENV={os.getenv('ENV', 'not set')}\n")
    f.write(f"STRICT_STARTUP_VALIDATION={os.getenv('STRICT_STARTUP_VALIDATION', 'not set')}\n")
    f.flush()
```

### Step 4: Check Dockerfile CMD
The Dockerfile CMD is correct:
```dockerfile
CMD ["python", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
```

But if Python exits during import, uvicorn never runs.

## Recommended Action Plan

1. **Immediate:** Set `STRICT_STARTUP_VALIDATION=false` in App Runner to allow deployment
2. **Short-term:** Add file-based error logging to capture validation failures
3. **Medium-term:** Review and fix missing/invalid environment variables
4. **Long-term:** Make validation failures non-fatal but log them, allow /healthz to work

## Files to Review

1. `backend/app/main_simple.py` - Lines 123-215 (validation logic)
2. `backend/app/core/startup_validation.py` - All validation functions
3. `backend/app/core/env.py` - Environment detection logic
4. `backend/Dockerfile` - Build process
5. App Runner environment variables configuration

## Questions to Answer

1. What is the `ENV` variable set to in App Runner?
2. Are `REDIS_URL` and `TOKEN_ENCRYPTION_KEY` set?
3. What does `ALLOWED_ORIGINS` contain?
4. Is `DATABASE_URL` a PostgreSQL URL (not SQLite)?
5. Is `JWT_SECRET` set and not using default value?



