# Deleted Code Log

This document tracks code deletions made during the P0-P2 cleanup effort.

**Date Started:** 2025-01-XX

## Rules for Deletions

1. Only LOW risk deletions are made
2. Proof required: Not imported, not in router registry, not referenced by migrations/scripts/docs
3. All deletions documented here with evidence

## Deletions Made

### None Yet

No code has been deleted yet. This log will be updated as dead code is identified and removed with proof.

## Consolidations Made

### Environment Detection Standardization

**Date:** 2025-01-XX

**Changes:**
- Consolidated all environment detection to use `app/core/env.py` centralized functions
- Replaced direct `os.getenv("ENV")` and `os.getenv("REGION")` calls
- Removed REGION-based environment checks (security risk)

**Files Modified:**
- `app/services/token_encryption.py` - Replaced REGION check with `get_env_name()`
- `app/routers/admin_domain.py` - Replaced `app.utils.env` with `app.core.env`
- `app/routers/checkout.py` - Replaced `app.utils.env` with `app.core.env`
- `app/routers/auth_domain.py` - Replaced `app.utils.env` with `app.core.env`
- `app/routers/stripe_api.py` - Replaced `app.utils.env` with `app.core.env`
- `app/routers/drivers_domain.py` - Replaced `app.utils.env` with `app.core.env`
- `app/main_simple.py` - Replaced direct env checks with centralized functions, removed REGION-based CORS check

**Rationale:**
- Single source of truth for environment detection
- Security: REGION can be spoofed, only ENV should be trusted
- Consistency: All code uses same env detection logic

**Status:** ✅ Complete










