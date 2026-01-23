# Legacy Code Status

**Date:** 2025-01-XX  
**Status:** Legacy code identified and documented

## Overview

This document identifies legacy code paths in the Nerava codebase and confirms which code is actually deployed in production.

## Deployed Entrypoint

**Current Production Entrypoint:** `app/main_simple.py`

Confirmed via:
- `Procfile`: `web: python -m app.db.run_migrations && python -m uvicorn app.main_simple:app --host 0.0.0.0 --port ${PORT:-8000}`
- `Dockerfile`: `CMD ["python", "-m", "uvicorn", "app.main_simple:app", "--host", "0.0.0.0", "--port", "8000"]`

## Legacy Code Paths

### `server/src/` Directory

**Status:** NOT DEPLOYED - Legacy code

**Location:** `nerava-backend-v9/server/src/`

**Contents:**
- `routes_square.py` - Contains dangerous bypass logic (`DEV_WEBHOOK_BYPASS`, signature placeholder bypasses)
- `routes_earn.py`, `routes_explore.py`, `routes_activity_wallet_me.py` - Legacy route handlers
- `config.py` - Legacy configuration with `DEV_WEBHOOK_BYPASS` flag
- Various other legacy modules

**Security Concerns:**
- `server/src/routes_square.py` line 19: Contains bypass logic:
  ```python
  if config.DEV_WEBHOOK_BYPASS or config.SQUARE_WEBHOOK_SIGNATURE_KEY == 'REPLACE_ME':
      return True  # Bypass in dev mode
  ```
- This bypass logic could be dangerous if accidentally deployed

**Verification:**
- ✅ Not imported in `app/` directory (grep confirmed)
- ✅ Excluded from pytest (`pytest.ini` excludes `server` directory)
- ✅ Not referenced in deployment configs (Procfile, Dockerfile)

### `server/main_simple.py`

**Status:** NOT DEPLOYED - Legacy entrypoint

**Location:** `nerava-backend-v9/server/main_simple.py`

**Details:**
- Legacy FastAPI entrypoint that imports from `server/src/`
- Uses old import pattern: `from src.routes_square import router as square`
- Not referenced in any deployment configuration

**Verification:**
- ✅ Not used in `Procfile`
- ✅ Not used in `Dockerfile`
- ✅ Not referenced in deployment scripts

## Actions Taken

1. **Documentation:** This document created to track legacy code status
2. **Deployment Guard:** Script `scripts/check_deployment_entrypoint.sh` will be created to prevent accidental deployment of legacy code
3. **Legacy Code Guard:** Environment check will be added to `server/src/routes_square.py` to fail if accidentally imported in production

## Recommendations

1. **Do NOT deploy `server/src/`** - It contains bypass logic that is not appropriate for production
2. **Do NOT use `server/main_simple.py`** - Use `app/main_simple.py` instead
3. **Future cleanup:** Consider removing `server/src/` directory entirely after confirming no dependencies exist
4. **CI/CD:** Add checks to prevent accidental deployment of legacy code paths

## Related Files

- `scripts/check_deployment_entrypoint.sh` - Deployment guard script (to be created)
- `tests/test_no_legacy_deployment.py` - Test to verify legacy code not deployed (to be created)










