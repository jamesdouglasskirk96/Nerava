# Root Cause: CMD Difference Between v19 and Newer Versions

**Date:** 2026-01-23
**Root Cause:** Dockerfile CMD uses `python3` instead of `python`

## Problem

All deployments since v19 have rolled back with health check failures. The only difference found:

| Version | CMD | Status in App Runner |
|---------|-----|---------------------|
| v19-photo-fix | `["python", "-m", "uvicorn", ...]` | ✅ Works |
| v20-v22 | `["python3", "-m", "uvicorn", ...]` | ❌ Health check fails |

## Evidence

1. **9 consecutive rollbacks** - All UPDATE_SERVICE operations failed
2. **Last success:** 05:41:28 AM (START_DEPLOYMENT of v19)
3. **Both work locally** - No difference in local Docker
4. **App Runner-specific** - Only fails in App Runner environment

## Root Cause

The Dockerfile CMD was changed from `python` to `python3` at some point. While both should work in Python 3.9-slim images, App Runner appears to have different behavior or timing expectations with `python3` vs `python`.

## Fix Applied

Changed Dockerfile CMD back to `python` to match v19:

```dockerfile
# CRITICAL: Use 'python' not 'python3' to match working v19 deployment
CMD ["python", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Deployment

- **Image:** `v23-fixed-cmd` (with `python` CMD)
- **Configuration:** Full (28 env vars preserved)
- **Egress:** VPC (NAT Gateway configured)

## Expected Result

With the CMD matching v19, the deployment should succeed and OTP should work via NAT Gateway.

---

**Status:** Deploying v23-fixed-cmd with corrected CMD




