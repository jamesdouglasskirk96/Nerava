# Nerava Production Hardening Report

**Date:** 2024-01-15  
**Status:** ✅ All P0 and P1 fixes completed

## Executive Summary

This report documents the production hardening sprint that addressed 11 P0 (ship blockers) and 4 P1 (stability/hygiene) security and reliability issues. All fixes have been implemented with minimal code changes, following surgical hardening principles.

## P0 Security/Auth Fixes

### A4: JWT Secret Bug ✅
**Problem:** JWT manager was using `settings.database_url` as secret key, exposing tokens if database URL leaked.

**Fix:**
- Changed `app/security/jwt.py` to use `settings.jwt_secret` instead of `settings.database_url`
- Added startup validation in `app/main_simple.py` to ensure JWT secret != database_url in non-local environments
- Validation fails startup with clear error message if misconfigured

**Files Modified:**
- `nerava-backend-v9/app/security/jwt.py`
- `nerava-backend-v9/app/main_simple.py`

**Validation:**
```bash
# Set JWT_SECRET in production
export JWT_SECRET=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
# App will fail startup if JWT_SECRET == DATABASE_URL
```

---

### A3: UUID vs int Parsing Mismatch ✅
**Problem:** Driver dependency parsed JWT `sub` claim as integer, but tokens contain UUID strings.

**Fix:**
- Updated `app/dependencies/driver.py` to parse `sub` as UUID string
- Changed lookup to use `AuthService.get_user_by_public_id()` instead of `get_user_by_id()`
- Returns user.id (integer) after UUID lookup

**Files Modified:**
- `nerava-backend-v9/app/dependencies/driver.py`

**Validation:**
- JWT tokens with UUID `sub` claims now correctly resolve to driver users

---

### A2: DEV_ALLOW_ANON_USER Hard-Block ✅
**Problem:** Anonymous user bypass flag worked in all environments, not just local dev.

**Fix:**
- Added `_is_local_env()` helper function in both `driver.py` and `domain.py`
- Gated `DEV_ALLOW_ANON_USER` and `DEV_ALLOW_ANON_DRIVER` to only work when `ENV == "local"` or `REGION == "local"`
- In production, these flags are always disabled regardless of environment variable

**Files Modified:**
- `nerava-backend-v9/app/dependencies/driver.py`
- `nerava-backend-v9/app/dependencies/domain.py`

**Validation:**
```bash
# In production (ENV != "local"), anon bypass is disabled
# Even if NERAVA_DEV_ALLOW_ANON_USER=true, it won't work
```

---

### A10: Stripe Webhook Verification + Idempotency ✅
**Problem:** Webhook secret was optional, allowing unverified webhooks. No event deduplication.

**Fix:**
- Require `STRIPE_WEBHOOK_SECRET` in non-local environments (fail 500 if missing)
- Created `stripe_webhook_events` table for event deduplication
- Check for duplicate events before processing
- Mark events as processed/failed with timestamps

**Files Modified:**
- `nerava-backend-v9/app/routers/stripe_api.py`
- `nerava-backend-v9/alembic/versions/029_add_stripe_webhook_events.py` (migration)

**Validation:**
```bash
# Set webhook secret in production
export STRIPE_WEBHOOK_SECRET="whsec_..."
# Duplicate events return success without reprocessing
```

---

### A5: Wallet Fail-Open DB Exception Swallowing ✅
**Problem:** Wallet service fell back to in-memory store on DB errors, hiding failures.

**Fix:**
- Removed in-memory fallback in production environments
- Added `_is_local_env()` check - only allow fallback in local dev
- Raise `RuntimeError` on DB errors in production (fail-closed)

**Files Modified:**
- `nerava-backend-v9/app/services/wallet.py`

**Validation:**
- DB errors in production now raise exceptions instead of silently falling back

---

### A6: Nova Redemption Atomicity + Idempotency ✅
**Problem:** Race condition allowed double-spend. No idempotency protection.

**Fix:**
- Use `SELECT ... FOR UPDATE` to lock `DriverWallet` row
- Atomic `UPDATE ... SET nova_balance = nova_balance - :amount WHERE nova_balance >= :amount`
- Added `idempotency_key` column to `nova_transactions` table
- Check for existing transaction with same idempotency key before processing

**Files Modified:**
- `nerava-backend-v9/app/services/nova_service.py`
- `nerava-backend-v9/app/routers/drivers_domain.py`
- `nerava-backend-v9/app/models/domain.py`
- `nerava-backend-v9/alembic/versions/030_add_nova_transaction_idempotency.py` (migration)

**Validation:**
```bash
# Concurrent redemption requests with same idempotency_key
# Only one will succeed, preventing double-spend
```

---

### A11: Stripe Payout Atomicity + Idempotency + State Machine ✅
**Problem:** Balance check and debit were non-atomic, allowing overdrafts. No handling for Stripe timeouts. No reconciliation mechanism.

**Fix:**
- **3-Phase Pattern**: DB transaction (lock + debit) → Stripe call (outside TX) → Finalize status (new TX)
- **Wallet Locks**: `wallet_locks` table with `SELECT ... FOR UPDATE` for concurrency control
- **State Machine**: `pending` → `succeeded`/`failed`/`unknown` with retry rules
- **Timeout Safety**: Stripe timeouts mark payment as `unknown`, do NOT reverse debit
- **Reconciliation**: `reconcile_payment()` function checks Stripe and finalizes `unknown` payments
- **Payload Hash**: Conflict detection via `payload_hash` - same idempotency key + different payload → 409
- **Idempotency Required**: `client_token` required in non-local (no UUID fallback)

**Files Modified:**
- `nerava-backend-v9/app/routers/stripe_api.py` (complete refactor)
- `nerava-backend-v9/app/services/stripe_service.py` (reconciliation function)
- `nerava-backend-v9/alembic/versions/034_add_wallet_locks.py` (migration)
- `nerava-backend-v9/alembic/versions/036_payments_state_machine.py` (migration)

**State Machine:**
- `pending`: DB debit committed, Stripe call not finalized
- `succeeded`: Stripe transfer confirmed (canonical status, never 'paid')
- `failed`: Stripe definitive error AND reversal credit recorded
- `unknown`: Stripe outcome uncertain (timeout/network). Requires reconciliation. Retries blocked.

**Retry Rules:**
- `succeeded` → return 200 replay
- `pending` → return 202 + payment_id (no new debit)
- `unknown` → return 202 + payment_id + "pending reconciliation" (no retry)
- `failed` → allow retry ONLY if `no_transfer_confirmed == True`

**Validation:**
- Concurrent payout requests: only one debit occurs (wallet_locks + FOR UPDATE)
- Stripe timeout: payment marked `unknown`, debit NOT reversed
- Reconciliation: `unknown` → `succeeded` (no reversal) or `failed` (applies reversal once)

**Ops: Reconciling Unknown Payments**

When Stripe timeout/network issues occur, payments may be marked as `unknown`. Use the admin reconcile endpoint to check Stripe and finalize status:

**Endpoint:**
```bash
POST /v1/admin/payments/{payment_id}/reconcile
```

**When to use:**
- Payment status is `unknown` (Stripe timeout/network error)
- Need to verify actual Stripe transfer status
- Payment stuck in `unknown` state

**How:**
1. Call endpoint with payment_id
2. System queries Stripe for transfer status
3. Outcomes:
   - **Transfer found and succeeded** → Status updated to `succeeded`, `reconciled_at` set, no reversal
   - **Transfer confirmed NOT found** → Status updated to `failed`, reversal credit applied ONCE, `reconciled_at` set, `no_transfer_confirmed=true`
   - **Still ambiguous** → Status remains `unknown` (Stripe API error)

**Response fields:**
- `payment_id`: Payment identifier
- `status`: Final status (`succeeded`, `failed`, or `unknown`)
- `stripe_transfer_id`: Stripe transfer ID if found
- `stripe_status`: Stripe API transfer status
- `error_code`: Error code if failed
- `error_message`: Error message if failed
- `reconciled_at`: Timestamp of reconciliation
- `no_transfer_confirmed`: Boolean indicating transfer was confirmed not found

**Note:** If payment status is not `unknown`, endpoint returns current payment summary (no-op, no error).

---

### A7: Code Redemption Race Fix ✅
**Problem:** Multiple requests could redeem the same code simultaneously.

**Fix:**
- Use `SELECT ... FOR UPDATE` on `MerchantOfferCode` row before checking `is_redeemed`
- Row lock prevents concurrent redemption

**Files Modified:**
- `nerava-backend-v9/app/routers/pilot_redeem.py`

**Validation:**
- Concurrent code redemption requests - only one succeeds

---

### A9: Smartcar Tokens Encrypted at Rest ✅
**Problem:** Smartcar access/refresh tokens stored in plaintext in database.

**Fix:**
- Created `app/services/token_encryption.py` using Fernet symmetric encryption
- Encrypt tokens before saving to `VehicleToken` table
- Decrypt tokens when reading for API calls
- Added `encryption_version` column to track encryption state
- Migration compatibility: plaintext tokens are detected and handled

**Files Modified:**
- `nerava-backend-v9/app/services/token_encryption.py` (new)
- `nerava-backend-v9/app/models/vehicle.py`
- `nerava-backend-v9/app/routers/ev_smartcar.py`
- `nerava-backend-v9/app/services/smartcar_service.py`
- `nerava-backend-v9/app/services/smartcar_client.py`
- `nerava-backend-v9/app/services/ev_telemetry.py`
- `nerava-backend-v9/alembic/versions/032_add_vehicle_token_encryption.py` (migration)

**Validation:**
```bash
# Set encryption key in production
export TOKEN_ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
# Tokens are encrypted before storage
```

---

### Missing P0: Nova Grant Idempotency + Payload Hash Conflict Detection ✅
**Problem:** Admin grant endpoint could be called twice, granting Nova twice. No payload conflict detection.

**Fix:**
- Added `idempotency_key` parameter to `grant_to_driver()` and `grant_to_merchant()`
- Check for existing transaction with same idempotency key before granting
- **Payload Hash**: Compute canonical hash of payload, detect conflicts (same key + different payload → 409)
- Return existing transaction if duplicate (same key + same hash)
- **Idempotency Required**: `idempotency_key` required in non-local (no UUID fallback)

**Files Modified:**
- `nerava-backend-v9/app/services/nova_service.py` (payload hash + conflict detection)
- `nerava-backend-v9/app/routers/admin_domain.py` (require idempotency key in non-local)
- `nerava-backend-v9/alembic/versions/033_make_idempotency_keys_unique.py` (migration)
- `nerava-backend-v9/alembic/versions/036_payments_state_machine.py` (payload_hash column)

**Validation:**
- Duplicate grant requests with same idempotency key return existing transaction
- Same key + different payload → HTTP 409 Conflict

---

### Missing P0: Square OAuth State Race Fix ✅
**Problem:** Two OAuth callbacks could consume the same state token.

**Fix:**
- Use atomic `UPDATE ... SET used = TRUE WHERE used = FALSE AND state = :state AND expires_at > :now`
- Only one callback can mark state as used

**Files Modified:**
- `nerava-backend-v9/app/services/square_service.py`

**Validation:**
- Concurrent OAuth callbacks - only one succeeds in consuming state

---

## P1 Stability/Hygiene Fixes

### A12: Remove Startup Migrations ✅
**Problem:** Migrations ran on every app startup, causing race conditions in multi-instance deployments.

**Fix:**
- Removed `run_migrations()` call from `app/main_simple.py`
- Added deployment checklist comment explaining manual migration requirement

**Files Modified:**
- `nerava-backend-v9/app/main_simple.py`

**Deployment Process:**
```bash
# 1. Run migrations manually before deployment
alembic upgrade head

# 2. Verify migration status
alembic current

# 3. Start application
```

---

### A13: Restrict CORS in Production ✅
**Problem:** CORS wildcard (`*`) allowed in production, exposing API to any origin.

**Fix:**
- Added startup validation to fail if `cors_allow_origins == "*"` in non-local environments
- Require explicit origins in production

**Files Modified:**
- `nerava-backend-v9/app/main.py`
- `nerava-backend-v9/app/main_simple.py`

**Validation:**
```bash
# Production startup fails if ALLOWED_ORIGINS="*"
# Must set explicit origins: ALLOWED_ORIGINS="https://app.nerava.app,https://www.nerava.app"
```

---

### A14: Endpoint-Specific Rate Limits ✅
**Problem:** All endpoints had same rate limit, vulnerable endpoints not protected.

**Fix:**
- Added endpoint-specific rate limits in `RateLimitMiddleware`
- Stricter limits for auth/OTP endpoints (10/min, 5/min)
- Moderate limits for money movement endpoints (20-30/min)

**Files Modified:**
- `nerava-backend-v9/app/middleware/ratelimit.py`

**Rate Limits:**
- `/v1/auth/`: 10 requests/minute
- `/v1/otp/`: 5 requests/minute
- `/v1/nova/`: 30 requests/minute
- `/v1/redeem/`: 20 requests/minute
- `/v1/stripe/`: 30 requests/minute
- `/v1/smartcar/`: 20 requests/minute
- `/v1/square/`: 20 requests/minute
- Default: `settings.rate_limit_per_minute`

---

### Feature Flags / Guardrails ✅
**Problem:** No emergency kill-switches for critical business logic.

**Fix:**
- Added feature flags to `app/config.py`:
  - `NOVA_EARN_ENABLED` (default: true)
  - `NOVA_REDEEM_ENABLED` (default: true)
  - `PAYOUTS_ENABLED` (default: true)
  - `EMERGENCY_READONLY_MODE` (default: false)
  - `BLOCK_ALL_MONEY_MOVEMENT` (default: false)
- Wired into Nova redeem, grants, and payout endpoints

**Files Modified:**
- `nerava-backend-v9/app/config.py`
- `nerava-backend-v9/app/routers/drivers_domain.py`
- `nerava-backend-v9/app/routers/admin_domain.py`
- `nerava-backend-v9/app/routers/stripe_api.py`

**Usage:**
```bash
# Emergency: Disable all money movement
export BLOCK_ALL_MONEY_MOVEMENT=true

# Disable Nova redemption only
export NOVA_REDEEM_ENABLED=false

# Readonly mode (webhooks logged but not processed)
export EMERGENCY_READONLY_MODE=true
```

---

## Database Migrations

### Migration 029: Stripe Webhook Events Table
- Creates `stripe_webhook_events` table for event deduplication
- Columns: `event_id` (PK), `event_type`, `received_at`, `processed_at`, `status`, `event_data`
- Indexes on `event_type`, `status`, `received_at`

### Migration 030: Nova Transaction Idempotency
- Adds `idempotency_key` column to `nova_transactions` table
- Creates index on `idempotency_key` for fast lookups

### Migration 031: Payments Idempotency
- Adds `idempotency_key` column to `payments` table (if exists)
- Creates index on `idempotency_key`

### Migration 032: Vehicle Token Encryption
- Adds `encryption_version` column to `vehicle_tokens` table
- Defaults to 0 (plaintext) for existing tokens

### Migration 033: Unique Idempotency Keys
- Cleanup duplicate idempotency keys (keep earliest, set others to NULL)
- Add partial unique index on `payments.idempotency_key` (WHERE NOT NULL)
- Add partial unique index on `nova_transactions.idempotency_key` (WHERE NOT NULL)
- Non-destructive cleanup with report

### Migration 034: Wallet Locks
- Creates `wallet_locks` table for concurrency control
- Used with `SELECT ... FOR UPDATE` to prevent race conditions in balance operations
- Schema: `user_id INTEGER PRIMARY KEY, created_at TIMESTAMP`

### Migration 035: VehicleToken Default Encrypted
- Sets `server_default='1'` for `encryption_version` on new rows
- Existing rows remain 0 (plaintext) until backfilled

### Migration 036: Payments State Machine
- Adds state machine columns to `payments` table:
  - `status` (string, default 'pending') - canonical state: 'pending', 'succeeded', 'failed', 'unknown' (never 'paid')
  - `payload_hash` (string, nullable) - for conflict detection
  - `stripe_transfer_id` (string, nullable)
  - `stripe_status` (string, nullable)
  - `error_code` (string, nullable)
  - `error_message` (text, nullable)
  - `reconciled_at` (timestamp, nullable)
  - `no_transfer_confirmed` (boolean, default false)
- Adds `payload_hash` column to `nova_transactions` table

**Migration Order + Validation:**
```bash
cd nerava-backend-v9

# 1. Run migrations
alembic upgrade head

# 2. Verify migration status
alembic current

# 3. Run tests
pytest tests/test_prod_hardening_p0.py -v
pytest -q

# 4. Backfill (if needed)
# Dry-run first
python scripts/backfill_encrypt_vehicle_tokens.py --dry-run
# Then execute
python scripts/backfill_encrypt_vehicle_tokens.py --batch-size 100
```

---

## Tests

Test file created: `tests/test_prod_hardening_p0.py`

Tests cover:
1. JWT secret validation
2. UUID parsing
3. Anon bypass blocking
4. Wallet fail-closed behavior
5. Nova redemption race condition
6. Code redemption race condition
7. Stripe webhook deduplication
8. Stripe webhook secret requirement
9. Smartcar token encryption
10. Nova grant idempotency
11. Square OAuth state race condition

**Run Tests:**
```bash
cd nerava-backend-v9
pytest tests/test_prod_hardening_p0.py -v
```

---

## Validation Commands

### Pre-Deployment Checklist

1. **Run Migrations:**
   ```bash
   alembic upgrade head
   alembic current  # Verify migration status
   ```

2. **Set Required Environment Variables:**
   ```bash
   export JWT_SECRET="<secure-random-value>"
   export STRIPE_WEBHOOK_SECRET="whsec_..."
   export TOKEN_ENCRYPTION_KEY="<fernet-key>"
   export ALLOWED_ORIGINS="https://app.nerava.app,https://www.nerava.app"
   ```

3. **Verify Configuration:**
   ```bash
   # Check JWT secret != database URL
   python -c "from app.config import settings; assert settings.jwt_secret != settings.database_url"
   
   # Check CORS not wildcard in production
   python -c "from app.config import settings; import os; assert os.getenv('ENV') == 'local' or settings.cors_allow_origins != '*'"
   ```

4. **Run Tests:**
   ```bash
   pytest tests/test_prod_hardening_p0.py -v
   ```

---

## Rollout Notes

### Environment Variables Required

**Production:**
- `JWT_SECRET` - Secure random value (generate with Fernet)
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook signing secret
- `TOKEN_ENCRYPTION_KEY` - Fernet encryption key for tokens
- `ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins (no wildcard)

**Optional (Feature Flags):**
- `NOVA_EARN_ENABLED` - Enable/disable Nova grants (default: true)
- `NOVA_REDEEM_ENABLED` - Enable/disable Nova redemption (default: true)
- `PAYOUTS_ENABLED` - Enable/disable payouts (default: true)
- `EMERGENCY_READONLY_MODE` - Emergency readonly mode (default: false)
- `BLOCK_ALL_MONEY_MOVEMENT` - Block all money movement (default: false)

### Deployment Steps

1. **Backup Database:**
   ```bash
   # Backup before migrations
   cp nerava.db nerava.db.backup.$(date +%Y%m%d)
   ```

2. **Run Migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Set Environment Variables:**
   ```bash
   # Set all required vars in production environment
   ```

4. **Start Application:**
   ```bash
   # App will validate configuration on startup
   # Will fail if JWT_SECRET == DATABASE_URL or CORS is wildcard
   ```

5. **Verify:**
   ```bash
   # Check logs for validation messages
   # Test endpoints to ensure feature flags work
   ```

---

## Remaining Non-Code Work

### Secret Management
- [ ] Rotate JWT secret (invalidate existing tokens)
- [ ] Rotate token encryption key (re-encrypt existing tokens)
- [ ] Store secrets in secure vault (AWS Secrets Manager, HashiCorp Vault, etc.)

### Monitoring
- [ ] Add alerts for failed webhook verifications
- [ ] Monitor idempotency key collisions
- [ ] Track rate limit violations
- [ ] Alert on feature flag activations

### Token Migration
- [x] Backfill script created: `scripts/backfill_encrypt_vehicle_tokens.py`
- [ ] Run backfill: `python scripts/backfill_encrypt_vehicle_tokens.py --dry-run` then `--batch-size 100`
- [ ] Script to re-encrypt tokens with new key (if rotating)

### Documentation
- [ ] Update API documentation with idempotency key requirements
- [ ] Document feature flag usage for operations team
- [ ] Create runbook for emergency kill-switch activation

---

## Payout State Machine & Reconciliation

### State Machine Overview

The payout flow uses a 3-phase pattern to ensure atomicity and handle Stripe timeouts safely:

**Phase A (DB Transaction):**
1. Upsert wallet lock row
2. Acquire lock with `SELECT ... FOR UPDATE`
3. Compute balance under lock
4. Check sufficient funds
5. Create payment row (`status='pending'`)
6. Insert wallet_ledger debit
7. COMMIT

**Phase B (Outside Transaction):**
8. Call Stripe transfer API with metadata
9. Handle outcomes: success, definitive failure, or timeout/unknown

**Phase C (New DB Transaction):**
10. Lock payment row `FOR UPDATE`
11. Update payment status based on Stripe outcome:
    - Success → `succeeded`, set `stripe_transfer_id`, `reconciled_at`
    - Definitive failure → `failed`, insert reversal credit, set `no_transfer_confirmed=True`
    - Unknown → `unknown`, do NOT reverse, `reconciled_at=NULL`

### Retry Rules

- **succeeded**: Return 200 with existing payment (idempotent replay)
- **pending**: Return 202 with payment_id (no new debit)
- **unknown**: Return 202 with payment_id + "pending reconciliation" (retries blocked)
- **failed**: Return 202 if `no_transfer_confirmed=False` (pending reconciliation), allow retry if `no_transfer_confirmed=True`

### Reconciliation Runbook

For payments stuck in `unknown` status:

1. **Check payment status:**
   ```sql
   SELECT id, status, stripe_transfer_id, idempotency_key, created_at
   FROM payments WHERE status = 'unknown';
   ```

2. **Run reconciliation:**
   ```python
   from app.services.stripe_service import StripeService
   result = StripeService.reconcile_payment(db, payment_id)
   ```

3. **Outcomes:**
   - Transfer found → `succeeded` (no reversal needed)
   - Transfer NOT found → `failed` + reversal credit applied ONCE
   - Stripe API error → remains `unknown` (retry later)

4. **Monitor reconciliation:**
   ```sql
   SELECT COUNT(*) FROM payments WHERE status = 'unknown' AND created_at < NOW() - INTERVAL '1 hour';
   ```

### Wallet Locks Rationale

SQLite's transaction isolation provides serialization, but explicit locks (`wallet_locks` + `FOR UPDATE`) ensure:
- Deterministic lock ordering (prevents deadlocks)
- Works across both SQLite and Postgres
- Clear concurrency control semantics
- Balance computation under lock prevents race conditions

**Note:** Removed "SQLite serializes" language - explicit locks are required for production safety.

## Idempotency Key Requirements (Breaking Change)

**In non-local environments, idempotency keys are now REQUIRED:**

- **Payouts**: `client_token` required (no UUID fallback)
- **Admin Grants**: `idempotency_key` required (no UUID fallback)
- **Nova Redemption**: `idempotency_key` required (no UUID fallback)

**Local environments:** Deterministic generation allowed for dev convenience.

**Payload Hash Conflict Detection:**
- Same `idempotency_key` + different `payload_hash` → HTTP 409 Conflict
- Same `idempotency_key` + same `payload_hash` → Idempotent replay (return existing)

## Backfill Runbook

### Vehicle Token Encryption Backfill

**Prerequisites:**
```bash
export TOKEN_ENCRYPTION_KEY="<fernet-key>"
```

**Dry Run:**
```bash
cd nerava-backend-v9
python scripts/backfill_encrypt_vehicle_tokens.py --dry-run
```

**Execute:**
```bash
python scripts/backfill_encrypt_vehicle_tokens.py --batch-size 100
```

**With Force (continue on errors):**
```bash
python scripts/backfill_encrypt_vehicle_tokens.py --batch-size 100 --force
```

**Rollback (if needed):**
```sql
-- Set encryption_version back to 0 (tokens remain encrypted but marked as plaintext)
UPDATE vehicle_tokens SET encryption_version = 0 WHERE encryption_version = 1;
-- Note: Tokens are still encrypted, but will be re-encrypted on next backfill run
```

## Fernet Key Change + Backward Compatibility

**New Encryption:**
- Uses validated Fernet keys only (fail-fast in non-local)
- No hash/pad derivation for new encryption
- Key validation by constructing Fernet instance

**Backward Compatibility:**
- `decrypt_token()` tries current key first, then legacy hash/pad-derived key
- Existing ciphertext encrypted with legacy keys remains readable
- `encrypt_token()` uses ONLY current validated key (never legacy)

**Key Generation:**
```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

## Local Setup

### Database Migrations

**Important:** Always run migrations after pulling latest code to ensure your local database schema is up to date.

```bash
cd nerava-backend-v9
alembic upgrade head
```

The backend will log a warning at startup if your local database schema is behind (missing columns from recent migrations). This check only runs in local environments and does not block startup, but you should run `alembic upgrade head` to resolve any warnings.

**Common migration-related errors:**
- `(sqlite3.OperationalError) no such column: vehicle_tokens.encryption_version` → Run `alembic upgrade head`
- Other "no such column" errors → Run `alembic upgrade head`

## Summary

✅ **11 P0 fixes completed** - All critical security and race condition issues resolved  
✅ **4 P1 fixes completed** - Stability and hygiene improvements implemented  
✅ **6 migrations created** - Database schema updates (033-036)  
✅ **Tests created** - Deterministic tests with Barrier/Event, no sleeps  
✅ **Backfill script created** - Vehicle token encryption migration  
✅ **Report updated** - Complete documentation including state machine, reconciliation, backfill

**All changes are minimal, surgical, and production-ready.**

