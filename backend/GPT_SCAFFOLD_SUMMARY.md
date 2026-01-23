# GPT Endpoints Scaffold - Summary

## ✅ Files Created

### 1. Routers
- **`app/routers/gpt.py`** - GPT endpoints:
  - `GET /v1/gpt/find_charger` (stub)
  - `GET /v1/gpt/find_merchants` (stub)
  - `POST /v1/gpt/create_session_link` (stub)
  - `GET /v1/gpt/me` (stub)
  - `POST /v1/gpt/follow` (stub)
  - `POST /v1/gpt/unfollow` (stub)
  - `POST /v1/gpt/redeem` (logs intent)

- **`app/routers/meta.py`** - Meta endpoints:
  - `GET /health` - Returns `{ok: true}`
  - `GET /version` - Returns `{git_sha, build_time}`
  - `GET /debug` - Returns safe environment snapshot

### 2. Database Migration
- **`alembic/versions/005_gpt_tables.py`** - Creates tables:
  - `users.handle` column (if not exists)
  - `follows` - User following relationships
  - `merchants` - Main merchants table (separate from merchants_local)
  - `offers` - Merchant offers with time windows
  - `sessions` - GPT session links
  - `payments` - Payment transactions
  - `reward_events` - Reward tracking
  - `wallet_ledger` - Wallet transaction ledger
  - `community_pool` - Community reward pools
  - `community_allocations` - Pool allocations

### 3. Seed Script
- **`app/scripts/seed_minimal.py`** - Seeds:
  - 1 user (id=1, handle="james", email="james@example.com")
  - 10 coffee shops in Austin
  - 10 gyms in Austin
  - 6 offers (tied to first 6 coffee shops, window: 14:00-16:00)

## 📝 Registration

Routers registered in `app/main_simple.py`:
- `app.include_router(meta.router)`
- `app.include_router(gpt.router)`

## 🚀 Usage

### Run Migration
```bash
cd nerava-backend-v9
source .venv/bin/activate
python -m alembic upgrade head
```

### Run Seed Script
```bash
cd nerava-backend-v9
source .venv/bin/activate
python -m app.scripts.seed_minimal
```

### Test Endpoints
```bash
# Health check
curl -s http://localhost:8001/health

# Find merchants (stub)
curl -s "http://localhost:8001/v1/gpt/find_merchants?lat=30.2672&lng=-97.7431&category=coffee&radius_m=1200"

# Version
curl -s http://localhost:8001/version

# Debug
curl -s http://localhost:8001/debug
```

## ⚠️ Notes

- Migration `005` depends on revision `004`. Ensure earlier migrations are applied.
- Tables use Postgres types with SQLite fallbacks.
- Seed script handles both SQLite and Postgres.
- All GPT endpoints are stubs (return empty arrays or mock data).
- CORS is permissive for localhost (as requested).

## ✅ Success Criteria

- ✅ App boots with `uvicorn app.main_simple:app --reload`
- ✅ `/health` returns `{ok:true}`
- ✅ Seed script runs without error
- ✅ `find_merchants` returns empty list (stub implementation)
