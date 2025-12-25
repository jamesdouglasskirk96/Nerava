# Database Migration Fix

## Issue
The database was missing columns and tables from recent migrations (022, 023, 024, 025).

## Solution Applied
✅ Added missing columns to `driver_wallets`:
- `apple_authentication_token`
- `wallet_pass_token`
- `wallet_activity_updated_at`
- `wallet_pass_last_generated_at`
- `charging_detected`
- `charging_detected_at`

## Remaining Issue
The database is still missing some tables (e.g., `merchant_redemptions`). 

## Fix Options

### Option 1: Restart Server (Recommended)
The server runs migrations on startup. **Stop the server, then restart it**:

```bash
# Stop the current server (Ctrl+C or kill the process)
# Then restart:
cd /Users/jameskirk/Desktop/Nerava/nerava-backend-v9
uvicorn app.main_simple:app --reload --port 8001
```

The server will automatically run all pending migrations on startup.

### Option 2: Run Migrations Manually (When Server Stopped)
```bash
cd /Users/jameskirk/Desktop/Nerava/nerava-backend-v9
python3 -m app.run_migrations
```

### Option 3: Check Migration Status
```bash
cd /Users/jameskirk/Desktop/Nerava/nerava-backend-v9
alembic current
alembic heads
```

## Current Status
- ✅ `/v1/wallet/status` endpoint is now working
- ⚠️ `/v1/wallet/timeline` needs `merchant_redemptions` table (will be created by migrations)
- ⚠️ Other endpoints may need additional tables

**Next Step**: Restart the server to apply all migrations automatically.



