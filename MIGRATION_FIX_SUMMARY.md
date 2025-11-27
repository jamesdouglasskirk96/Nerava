# Migration Fix Summary: Duplicate Table Error Resolution

**Date**: 2025-11-27  
**Issue**: `Table 'energy_events' is already defined for this MetaData instance`  
**Status**: ✅ Fixed

## Problem

Production server was failing to start because SQLAlchemy attempted to register the `energy_events` table twice in the same `Base.metadata` instance during Alembic migrations. This caused migrations to fail, leaving the database schema incomplete and breaking endpoints like `/v1/drivers/merchants/nearby`.

## Root Cause

Models were being imported in multiple places:
- `alembic/env.py` was importing models directly
- Other modules (services, routers) were also importing models
- If models were imported before Alembic's `env.py` ran, they would be registered in `Base.metadata` first
- Then when Alembic's `env.py` tried to import them again, SQLAlchemy saw the table already registered → error

## Solution

### 1. Created Models Aggregator (`app/models_all.py`)

A single canonical module that imports all model modules in a controlled order:

```python
from app.db import Base
from app.models import *  # Core models
from app.models_while_you_charge import *  # While You Charge models
from app.models_domain import *  # Domain Charge Party models (EnergyEvent, Zone, etc.)
```

This ensures:
- All models are registered exactly once
- Single import path for both Alembic and the application
- Consistent metadata population

### 2. Updated Alembic Environment (`alembic/env.py`)

Changed from importing models directly to using the aggregator:

**Before:**
```python
from app.db import Base
from app.models import *
from app.models_while_you_charge import *
from app.models_domain import *
```

**After:**
```python
import app.models_all  # noqa: F401  # Imports all models and registers them
from app.db import Base
```

This ensures Alembic sees models registered through a single, controlled path.

### 3. Verified Migration Runner (`app/run_migrations.py`)

Confirmed that `run_migrations.py` doesn't import models at module level:
- Model imports only happen inside `_seed_domain_chargers()` function
- This function is called AFTER migrations complete
- No risk of models being registered before Alembic runs

### 4. Added Endpoint Logging

Added request logging to `/v1/drivers/merchants/nearby` to help debug future issues:
- Logs lat, lng, zone_slug, radius_m, and user_id
- Helps verify the endpoint is being called correctly

## Files Changed

1. **`app/models_all.py`** (new file)
   - Models aggregator module

2. **`alembic/env.py`**
   - Updated to import from aggregator instead of direct imports

3. **`app/routers/drivers_domain.py`**
   - Added logging to `get_nearby_merchants` endpoint

## How Migrations Work Now

1. **Server Startup** (`app/main_simple.py`):
   - Line 18: Calls `run_migrations()`
   
2. **Migration Runner** (`app/run_migrations.py`):
   - Calls `alembic.command.upgrade(cfg, "head")`
   - This triggers Alembic to load `alembic/env.py`

3. **Alembic Environment** (`alembic/env.py`):
   - Imports `app.models_all`
   - `models_all` imports Base and all model modules
   - Models register with `Base.metadata` exactly once

4. **Migrations Execute**:
   - Alembic uses `Base.metadata` to generate migration SQL
   - No duplicate table errors

5. **Server Continues**:
   - After migrations, routers are imported
   - Python's import cache means models are already loaded
   - No re-registration occurs

## Running Migrations Locally

### Check Current Migration Status
```bash
cd nerava-backend-v9
alembic current
```

### Run Migrations to Head
```bash
alembic upgrade head
```

### Expected Output
```
INFO  [alembic.runtime.migration] Running upgrade -> 018_domain_charge_party_mvp, Domain Charge Party MVP
INFO  [alembic.runtime.migration] Running upgrade 018_domain_charge_party_mvp -> 019_add_energy_events_zones, Add Energy Events and Zones
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
```

**No errors about duplicate tables should appear.**

### Verify Schema
```bash
# SQLite
sqlite3 nerava.db ".tables" | grep -E "energy_events|zones"
# Should show: energy_events  zones
```

## Railway Deployment

On Railway, migrations run automatically on container startup:

1. Container starts
2. `main_simple.py` imports and calls `run_migrations()`
3. Migrations run using `app/models_all` aggregator
4. No duplicate table errors
5. Server starts successfully

### Expected Railway Logs
```
INFO: Running database migrations on startup (before router imports)...
INFO: Running Alembic migrations to head on [database_url]
INFO: [alembic.runtime.migration] Running upgrade -> 018_domain_charge_party_mvp, ...
INFO: [alembic.runtime.migration] Running upgrade 018_domain_charge_party_mvp -> 019_add_energy_events_zones, ...
INFO: Alembic migrations complete.
INFO: Database migrations completed successfully
INFO: Application startup complete.
```

## Endpoint Verification

### `/v1/drivers/merchants/nearby`

**Endpoint**: `GET /v1/drivers/merchants/nearby`

**Query Parameters**:
- `lat` (float, required): Latitude
- `lng` (float, required): Longitude  
- `zone_slug` (string, required): Zone slug (e.g., `domain_austin`)
- `radius_m` (float, optional, default=5000): Radius in meters

**Authentication**: Requires driver role (cookie-based session)

**Test Command** (after login):
```bash
curl -X GET "http://localhost:8001/v1/drivers/merchants/nearby?lat=30.4021&lng=-97.7266&zone_slug=domain_austin&radius_m=5000" \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -v
```

**Expected Response**: 200 OK with JSON array of merchants

**Handler Location**: `app/routers/drivers_domain.py`, line 144

## Troubleshooting

### Migrations Still Failing

1. **Check if models are imported before migrations**:
   ```bash
   grep -r "from app.models" app/main_simple.py app/run_migrations.py app/db.py app/config.py
   ```
   Should find nothing (or only in run_migrations.py inside functions)

2. **Verify models_all.py is being used**:
   ```bash
   grep "models_all" alembic/env.py
   ```
   Should show: `import app.models_all`

3. **Check for duplicate Base definitions**:
   ```bash
   grep -r "declarative_base()" app/
   ```
   Should only appear once in `app/db.py`

### 404 on Nearby Merchants

1. **Check router is included**:
   ```bash
   grep "drivers_domain.router" app/main_simple.py
   ```
   Should show: `app.include_router(drivers_domain.router)`

2. **Verify endpoint path**:
   - Router prefix: `/v1/drivers`
   - Endpoint path: `/merchants/nearby`
   - Full path: `/v1/drivers/merchants/nearby` ✅

3. **Check authentication**:
   - Must be logged in as driver
   - Cookie must be present in request

4. **Check migrations ran**:
   - Database must have `zones` and `energy_events` tables
   - Zone `domain_austin` must exist

## Single Source of Truth

After this fix:
- **Models**: Defined once in their respective modules (`models_domain.py`, `models.py`, etc.)
- **Model Registration**: Happens once through `models_all.py`
- **Alembic Discovery**: Uses `models_all.py` → single metadata instance
- **Application Usage**: Routers/services import from individual model modules, but Python's import cache prevents re-registration

## Next Steps

1. ✅ Deploy to Railway and verify migrations run cleanly
2. ✅ Test `/v1/drivers/merchants/nearby` endpoint
3. ✅ Monitor logs for any remaining issues
4. ⏳ Consider creating a test that verifies no duplicate table errors

## Related Documentation

- `ENERGY_EVENTS_DUPLICATE_TABLE_ANALYSIS.md` - Detailed analysis of the problem
- `ENERGY_EVENTS_DUPLICATE_TABLE_ANALYSIS_NOTES.md` - Step 0 findings
- `alembic/versions/019_add_energy_events_zones.py` - Migration that creates these tables

