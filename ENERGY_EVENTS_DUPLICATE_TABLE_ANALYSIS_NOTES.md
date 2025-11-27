# Step 0: Reconfirmation of Problem - Findings

**Date**: 2025-11-27
**Purpose**: Document current state before implementing fix

## Model Definitions Found

### EnergyEvent
- **Single definition**: `app/models_domain.py` line 36
- **Table name**: `energy_events`
- **No duplicates found** - the legacy definition in `models_extra.py` has been commented out (line 259-263)

### Zone  
- **Single definition**: `app/models_domain.py` line 20
- **Table name**: `zones`
- **No duplicates found**

## Import Chain Analysis

### Current Alembic Setup (`alembic/env.py`)
- Line 12: `from app.db import Base`
- Line 13: `from app.models import *`
- Line 14: `from app.models_while_you_charge import *`
- Line 15: `from app.models_domain import *` ← **This is where the error occurs**

### Models Imported By Other Modules
These modules import `models_domain`:
- `app/services/nova_service.py`
- `app/services/session_service.py`
- `app/services/auth_service.py`
- `app/services/stripe_service.py`
- `app/routers/drivers_domain.py`
- `app/routers/merchants_domain.py`
- `app/routers/admin_domain.py`
- `app/routers/nova_domain.py`

**Key Finding**: If any of these services/routers are imported BEFORE migrations run, they will register models in `Base.metadata` first. Then when Alembic's `env.py` imports `models_domain`, SQLAlchemy sees the table already registered.

### Startup Sequence (`app/main_simple.py`)
1. Line 5: `from .db import Base, engine` ← Creates Base
2. Line 6: `from .config import settings`
3. Line 7: `from .run_migrations import run_migrations`
4. Lines 11-24: **Migrations run** (calls Alembic)
5. Lines 25+: Router imports (which import models)

**Hypothesis**: The issue is that `run_migrations.py` or something it imports might be importing models, OR the import of `Base` itself triggers some registration.

## Root Cause Hypothesis

The problem is **NOT** multiple definitions, but **double registration**:
1. Models get imported/registered somewhere before Alembic runs
2. Alembic's `env.py` tries to import them again
3. SQLAlchemy sees table already in metadata → error

## Solution Approach

1. **Create a models aggregator module** that both Alembic and the app use
2. **Ensure Alembic's env.py is the ONLY place that imports models** during migrations
3. **Ensure nothing imports models before migrations run**
4. **Use the aggregator pattern** so all model imports go through one canonical path

