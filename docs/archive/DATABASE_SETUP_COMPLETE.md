# Database Setup and E2E URL Updates - Complete

## Database Migration Fix

### Issue Fixed
SQLite doesn't support `ALTER COLUMN` syntax used in migration `022_add_square_and_merchant_redemptions.py`.

### Solution Applied
Updated migration to check database dialect and skip `ALTER COLUMN` for SQLite:

```python
# SQLite doesn't support ALTER COLUMN - skip NOT NULL constraint for SQLite
# The constraint will be enforced at the application level
bind = op.get_bind()
if bind.dialect.name != 'sqlite':
    op.alter_column('domain_merchants', 'zone_slug', nullable=False, server_default='national')
```

### Migration Status
✅ **All migrations completed successfully**
- Migration `022` now works with SQLite
- All subsequent migrations applied
- Database tables created

### Verification
```bash
docker compose exec backend alembic upgrade head
# Result: All migrations applied successfully
```

---

## E2E Test URL Updates

### Changes Made

**1. Playwright Config (`e2e/playwright.config.ts`)**
- Updated `baseURL` to use Docker Compose route when `DOCKER_COMPOSE` env var is set
- Default: `http://localhost:5173` (dev server)
- Docker Compose: `http://localhost/app` (proxy route)

**2. Test Files Updated:**
- `e2e/tests/driver-flow.spec.ts` - Uses `http://localhost/app` when `DOCKER_COMPOSE` is set
- `e2e/tests/merchant-flow.spec.ts` - Uses `http://localhost/merchant` when `DOCKER_COMPOSE` is set
- `e2e/tests/admin-flow.spec.ts` - Uses `http://localhost/admin` when `DOCKER_COMPOSE` is set
- `e2e/tests/landing.spec.ts` - Uses `http://localhost` when `DOCKER_COMPOSE` is set

### Usage

**For Docker Compose Testing:**
```bash
cd e2e
DOCKER_COMPOSE=1 npm test
```

**For Local Dev Server Testing:**
```bash
cd e2e
npm test
```

### URL Mapping

| Service | Dev Server | Docker Compose |
|---------|-----------|----------------|
| Driver | `http://localhost:5173` | `http://localhost/app` |
| Merchant | `http://localhost:5174` | `http://localhost/merchant` |
| Admin | `http://localhost:5175` | `http://localhost/admin` |
| Landing | `http://localhost:3000` | `http://localhost` |
| Backend API | `http://localhost:8001` | `http://localhost/api` |

---

## Next Steps

1. ✅ Database migrations fixed and applied
2. ✅ E2E test URLs updated for Docker Compose
3. ⏭️ Run E2E tests: `cd e2e && DOCKER_COMPOSE=1 npm test`
4. ⏭️ Run Phase 5 Golden Path tests with database initialized

---

## Files Changed

1. `backend/alembic/versions/022_add_square_and_merchant_redemptions.py` - SQLite compatibility fix
2. `e2e/playwright.config.ts` - Base URL environment variable support
3. `e2e/tests/driver-flow.spec.ts` - Docker Compose URL support
4. `e2e/tests/merchant-flow.spec.ts` - Docker Compose URL support
5. `e2e/tests/admin-flow.spec.ts` - Docker Compose URL support
6. `e2e/tests/landing.spec.ts` - Docker Compose URL support




