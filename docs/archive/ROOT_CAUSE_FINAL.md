# Root Cause Analysis - Final Determination

## Root Cause: Strict Startup Validation Failing During Module Import

### The Problem

Containers in App Runner are **crashing silently** during Python module import due to strict startup validation that runs **before** any logging is configured.

### Why This Happens

1. **Container starts** → Docker runs the CMD
2. **Python process begins** → `python3 -m uvicorn app.main_simple:app`
3. **Uvicorn tries to import** → `import app.main_simple`
4. **During import, validation code runs** → Lines 130-215 in `main_simple.py`
5. **Validation fails** → One of these checks fails:
   - `OTP_PROVIDER=stub` not allowed in production
   - `JWT_SECRET` not set or using default value
   - `TOKEN_ENCRYPTION_KEY` invalid or missing
   - `DATABASE_URL` is SQLite in production
   - `REDIS_URL` not configured
   - CORS origins is wildcard `*`
6. **Python exits immediately** → `sys.exit(1)` called (line 190, 211)
7. **No logs written** → Python exits before logging handlers configured
8. **Container exits** → App Runner sees no application logs

### Evidence

**Local Testing:**
- ✅ Container starts successfully with correct env vars
- ✅ Container crashes immediately with missing/incorrect env vars
- ✅ Error message: `OTP_PROVIDER=stub is not allowed in production`
- ✅ Error message: `JWT secret must be set and not use default value`

**App Runner Behavior:**
- ✅ Image pulled successfully
- ✅ Instance provisioning starts
- ❌ **No application logs appear** (Python exits during import)
- ❌ Health check times out (no HTTP server running)
- ❌ Service stuck in `OPERATION_IN_PROGRESS` or `CREATE_FAILED`

**Code Analysis:**
- Validation runs at **module import time** (lines 130-215)
- Validation happens **before** FastAPI app is created
- Validation happens **before** logging is fully configured
- `sys.exit(1)` called immediately on failure
- No try/except around import to catch and log errors

### Why No Logs Appear

The critical issue is **when** validation runs:

```python
# In main_simple.py - runs during import
try:
    validate_jwt_secret()  # Can raise ValueError
    validate_database_url()  # Can raise ValueError
    # ... more validations
except ValueError as e:
    # Log error
    if strict_validation:
        sys.exit(1)  # ← Python exits HERE
```

**Timeline:**
1. `python3 -m uvicorn app.main_simple:app` starts
2. Uvicorn calls `import app.main_simple`
3. Python executes `main_simple.py` top-level code
4. Validation code runs (lines 130-215)
5. Validation fails → `sys.exit(1)` called
6. **Python process terminates** → No logs, no HTTP server
7. Container exits → App Runner sees empty logs

### Validation Checks That Can Fail

1. **OTP_PROVIDER validation** (`validate_config()` in `config.py`):
   - `OTP_PROVIDER=stub` not allowed in production
   - Requires `OTP_PROVIDER=twilio` or `twilio_verify` in prod

2. **JWT_SECRET validation** (`validate_jwt_secret()`):
   - Must be set (not empty)
   - Must not be default values: `dev-secret`, `dev-secret-change-me`
   - Must not equal `DATABASE_URL`

3. **TOKEN_ENCRYPTION_KEY validation** (`validate_token_encryption_key()`):
   - Must be set
   - Must be 44 characters (valid Fernet key)
   - Must be valid Fernet key format

4. **DATABASE_URL validation** (`validate_database_url()`):
   - Must not be SQLite in production
   - Must be PostgreSQL connection string

5. **REDIS_URL validation** (`validate_redis_url()`):
   - Must be configured in production
   - Must not be `redis://localhost:6379/0`

6. **CORS validation** (`validate_cors_origins()`):
   - Must not be wildcard `*` in production
   - Must be explicit origins (comma-separated)

### Fixes Applied

1. **Debug Output Added** (`backend/Dockerfile`):
   - CMD now shows env vars before Python starts
   - Helps verify env vars are passed correctly
   - Shows: `=== CONTAINER STARTING ===`, env var values, `=== LAUNCHING PYTHON ===`

2. **SKIP_STARTUP_VALIDATION Support** (`backend/app/main_simple.py`):
   - Added `SKIP_STARTUP_VALIDATION=true` env var support
   - Bypasses all validation checks when set
   - Allows app to start for debugging/testing

3. **Debug Image Built**:
   - Image: `566287346479.dkr.ecr.us-east-1.amazonaws.com/nerava-backend:debug`
   - Includes debug output and validation bypass

### Verification

**Test locally:**
```bash
# Without SKIP_STARTUP_VALIDATION (fails)
docker run --rm -e ENV=prod nerava-backend:debug
# → Exits with: OTP_PROVIDER=stub is not allowed in production

# With SKIP_STARTUP_VALIDATION (succeeds)
docker run --rm -e ENV=prod -e SKIP_STARTUP_VALIDATION=true nerava-backend:debug
# → Starts successfully, shows debug output
```

### Recommended Solution

**Option 1: Fix Environment Variables** (Preferred)
- Ensure all required env vars are set correctly in App Runner
- Set `OTP_PROVIDER=twilio` (not `stub`)
- Set proper `JWT_SECRET`, `TOKEN_ENCRYPTION_KEY`, etc.
- Remove validation bypass after fixing

**Option 2: Disable Strict Validation** (Temporary)
- Set `SKIP_STARTUP_VALIDATION=true` in App Runner
- Allows app to start for debugging
- Fix validation issues, then re-enable validation

**Option 3: Move Validation Later** (Long-term)
- Move validation to after app initialization
- Run validation in startup event handler
- Allows app to start and log errors before exiting

### Next Steps

1. Deploy debug image with `SKIP_STARTUP_VALIDATION=true`
2. Check logs for debug output (should show env vars)
3. If app starts → Fix validation issues
4. If app still fails → Check for other import errors

### Files Modified

- `backend/Dockerfile` - Added debug CMD
- `backend/app/main_simple.py` - Added SKIP_STARTUP_VALIDATION support
- `scripts/update-service-debug.sh` - Script to deploy debug image


