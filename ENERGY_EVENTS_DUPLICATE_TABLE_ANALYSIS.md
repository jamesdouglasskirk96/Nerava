# Analysis: `Table 'energy_events' is already defined` Error

## Executive Summary

The production server is failing to start because SQLAlchemy is attempting to register the `energy_events` table twice in the same `Base.metadata` instance. This happens during Alembic migrations when `alembic/env.py` imports `app.models_domain`, even though there's only ONE definition of `EnergyEvent` in the codebase.

## Root Cause

### Problem Chain:

1. **Server Startup** (`app/main_simple.py` line 18):
   - Calls `run_migrations()` at startup
   
2. **Migrations Run** (`app/run_migrations.py` line 45):
   - Executes `command.upgrade(cfg, "head")`
   - This triggers Alembic to load `alembic/env.py`

3. **Alembic Env Imports Models** (`alembic/env.py` lines 12-15):
   ```python
   from app.db import Base
   from app.models import *  # Import all models
   from app.models_while_you_charge import *  # Import While You Charge models
   from app.models_domain import *  # Import Domain Charge Party MVP models (now canonical v1)
   ```

4. **Model Definition Executes** (`app/models_domain.py` line 36):
   ```python
   class EnergyEvent(Base):
       __tablename__ = "energy_events"
   ```

5. **SQLAlchemy Error**:
   - SQLAlchemy tries to register `EnergyEvent` with `Base.metadata`
   - But `energy_events` table is **already** registered in that metadata instance
   - Error: `Table 'energy_events' is already defined for this MetaData instance`

### Why Is It Already Defined?

**Hypothesis**: Something in the import chain (between `app.db.Base` and `app.models_domain`) is already importing and registering `EnergyEvent`, OR models are being imported/registered before Alembic's env.py runs.

**Possible Causes**:

1. **Circular Import Chain**: 
   - `app.db` → `app.config` → (some service/router) → `app.models_domain` 
   - Models get registered when `Base` is first instantiated
   - Then Alembic tries to import them again

2. **Double Import via `app.models`**:
   - `alembic/env.py` imports `from app.models import *`
   - If `app/models.py` or any module it imports also imports `models_domain`, that would cause double registration

3. **Module Import Order**:
   - If `app/main_simple.py` or any module imported before migrations run imports routers/services that import `models_domain`, models get registered first
   - Then Alembic's `env.py` tries to import them again

4. **Multiple Base Instances** (unlikely but possible):
   - If `app.db.Base` is not a singleton, multiple metadata instances could exist

## Evidence from Logs

### Error Location:
```
File "/app/alembic/env.py", line 12, in <module>
  from app.models_domain import *  # Import Domain Charge Party MVP models
File "/app/app/models_domain.py", line 36, in <module>
  class EnergyEvent(Base):
```

### Timing:
- Error occurs **during** migration startup
- Server **still starts** despite migration failure (line 20-23 in `main_simple.py` catches and continues)
- But migrations never complete, so database schema may be out of sync

### Additional Issues from Logs:

1. **404 on `/v1/drivers/merchants/nearby`**:
   - After migrations fail, the app starts but the endpoint returns 404
   - This suggests the route might not be registered, OR the endpoint handler has issues

2. **CORS OPTIONS Request Returns 400**:
   - `"OPTIONS /v1/drivers/merchants/nearby" 400 Bad Request`
   - This suggests the route exists but rejects preflight requests

## Current State

### What's Working:
- Server health endpoint (`/health`) works
- Server starts despite migration failure
- Uvicorn runs on port 8080

### What's Broken:
- ✅ **Migrations fail** → Database schema may be incomplete/outdated
- ✅ **404 on `/v1/drivers/merchants/nearby`** → Frontend can't load merchants
- ⚠️ **Auth endpoints return 500** (separate issue, but related to missing/incomplete schema)

## Code Locations to Check

### 1. Import Chain Analysis Needed:
```bash
# Check if any module imported before migrations also imports models_domain
grep -r "from.*models_domain\|import.*models_domain" nerava-backend-v9/app/
```

### 2. Check `app/models.py`:
- Does it import `models_domain`?
- If so, that would cause double registration in `alembic/env.py`

### 3. Check `app/db.py`:
- Is `Base` a true singleton?
- Are there any imports in `db.py` that could trigger model registration?

### 4. Check `app/config.py`:
- Does it import any models or services that import models?

### 5. Check Import Order in `app/main_simple.py`:
- Line 11-24: Migrations run
- Line 25+: Router imports
- But if routers are imported elsewhere before migrations, models could be registered twice

## Recommended Fixes (In Order of Likelihood)

### Fix 1: Ensure Models Are Only Imported Once
**Hypothesis**: Models are imported before Alembic's `env.py` runs.

**Solution**: 
- Ensure `alembic/env.py` is the FIRST place models are imported
- Check if `app/main_simple.py` or any module it imports at the top level imports routers/services before migrations
- Move any model imports that happen before migrations to after migrations

### Fix 2: Lazy Model Registration
**Hypothesis**: Models get registered when modules are imported.

**Solution**:
- Use `__all__` to control what gets exported from `models_domain`
- Or delay model registration until explicitly needed

### Fix 3: Check for Circular Imports
**Hypothesis**: Circular import causes models to be registered twice.

**Solution**:
- Trace import chains: `app.db` → `app.config` → ... → `app.models_domain`
- Break any circular dependencies

### Fix 4: Clear Metadata Before Alembic Runs
**Hypothesis**: Models were already registered in a previous import.

**Solution** (not recommended, but could work):
- Clear `Base.metadata` before Alembic runs (risky)

### Fix 5: Separate Base for Alembic
**Hypothesis**: Same `Base.metadata` is used by app and Alembic.

**Solution**:
- Create a separate `Base` instance for Alembic (complex, not recommended)

## Immediate Action Items

1. **Check Import Order**: 
   - Verify nothing imports models before `run_migrations()` is called
   - Check if `app/config.py`, `app/db.py`, or any middleware imports models

2. **Check `app/models.py`**:
   - Ensure it doesn't import `models_domain`
   - If it does, that's the source of double registration

3. **Add Debug Logging**:
   - Log when `EnergyEvent` class is first defined
   - Log when `Base.metadata` first contains `energy_events`
   - This will show the order of events

4. **Verify Single Base Instance**:
   - Ensure `app.db.Base` is imported from a single location
   - Check for multiple `declarative_base()` calls

5. **Fix 404 Endpoint**:
   - Once migrations work, verify `/v1/drivers/merchants/nearby` is registered
   - Check router inclusion in `main_simple.py`

## Expected Outcome After Fix

- Migrations run successfully without duplicate table errors
- Database schema is up-to-date
- `/v1/drivers/merchants/nearby` returns 200 instead of 404
- Server starts cleanly without errors

## Related Files

- `nerava-backend-v9/alembic/env.py` - Where models are imported for migrations
- `nerava-backend-v9/app/models_domain.py` - Where `EnergyEvent` is defined
- `nerava-backend-v9/app/main_simple.py` - Where migrations are called
- `nerava-backend-v9/app/db.py` - Where `Base` is defined
- `nerava-backend-v9/app/run_migrations.py` - Migration runner
- `nerava-backend-v9/app/models.py` - Core models (check if it imports models_domain)

---

## Final Fix Implemented (2025-11-27)

### Root Cause
Models were being imported directly in multiple places, causing SQLAlchemy to attempt to register tables multiple times with the same `Base.metadata` instance.

### Solution Applied
1. **Created `app/models_all.py`**: A single aggregator module that imports all model modules
   - Imports Base first
   - Then imports all model modules in order
   - Ensures models are registered exactly once

2. **Updated `alembic/env.py`**: Now imports only the aggregator module
   - Changed from: `from app.models_domain import *`
   - Changed to: `import app.models_all  # noqa: F401`
   - This ensures Alembic sees the same metadata populated by a single import path

3. **Verified `run_migrations.py`**: Confirmed it doesn't import models at module level
   - Model imports only happen inside `_seed_domain_chargers()` function (after migrations)

4. **Added logging to `/v1/drivers/merchants/nearby`**: Added request logging to help debug 404s

### Changes Made
- ✅ Created `app/models_all.py` (new file)
- ✅ Updated `alembic/env.py` to use aggregator
- ✅ Added logging to `drivers_domain.py` nearby merchants endpoint

### Verification
- Migrations should now run cleanly without duplicate table errors
- `/v1/drivers/merchants/nearby` endpoint is registered and should work after migrations succeed
- Single source of truth for model registration

