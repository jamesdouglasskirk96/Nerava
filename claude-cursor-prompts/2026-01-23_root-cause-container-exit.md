# Root Cause: Container Exit Code 1

**Date:** 2026-01-23
**Status:** All deployments since v19 roll back
**Evidence:** Service logs show "Container exit code: 1"

## Problem

All deployments since v19-photo-fix fail with:
```
[AppRunner] Your application stopped or failed to start. Container exit code: 1
[AppRunner] Health check failed on protocol `HTTP`[Path: '/healthz'], [Port: '8000']
```

## Key Findings

1. **v19 works** - Deployed successfully on Jan 22, 19:37 UTC
2. **v20-v23 all fail** - Container exits with code 1 before health checks
3. **No application logs** - Container crashes before logging starts
4. **Works locally** - All images work perfectly in local Docker
5. **SKIP_STARTUP_VALIDATION=true** - Set correctly in all deployments

## Root Cause Hypothesis

The container is calling `sys.exit(1)` during startup. Possible causes:

### 1. Import Error (Most Likely)
- Something in the import chain fails in App Runner environment
- Error occurs before logging is configured
- Python exits silently

### 2. Validation Failure Despite SKIP_STARTUP_VALIDATION
- Code path that bypasses SKIP_STARTUP_VALIDATION check
- Validation runs anyway and calls sys.exit(1)

### 3. Missing Dependency
- Package missing in production image
- Import fails silently

## Code Locations That Call sys.exit(1)

1. `main_simple.py:191` - If strict_validation and validation fails
2. `main_simple.py:212` - If strict_validation and unexpected error

Both are guarded by:
- `if strict_validation:` 
- `strict_validation = False` when `SKIP_STARTUP_VALIDATION=true`

## Next Steps

1. **Test with exact production env vars** - See if specific env var causes crash
2. **Check for import errors** - Test all imports that happen during startup
3. **Compare v19 vs v23 code** - Find what changed that could cause exit
4. **Add more startup logging** - Log before every potential exit point

## Current Status

- **Service:** RUNNING (v19-photo-fix)
- **Latest attempt:** v23-fixed-cmd (rolled back)
- **Deployment:** IN_PROGRESS (started 10:25:52 AM)

---

**Critical:** Need to find what causes sys.exit(1) in App Runner but not locally.




