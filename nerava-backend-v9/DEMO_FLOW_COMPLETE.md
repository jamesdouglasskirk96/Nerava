# Demo Flow Implementation Complete

All phases of the sandbox-only demo flow have been implemented without breaking any existing functionality.

## ✅ Phase 1: Demo QR Redirect

**Route**: `GET /qr/eggman-demo-checkout`

- **Gated**: `DEMO_QR_ENABLED=true` (case-insensitive)
- **Token source**: `DEMO_EGGMAN_QR_TOKEN` env var
- **Behavior**:
  - If disabled → 404 with `{"error": "DEMO_QR_DISABLED", ...}`
  - If token missing → 404 with `{"error": "DEMO_QR_TOKEN_MISSING", ...}`
  - Otherwise → **302 redirect** to `/app/checkout.html?token=<DEMO_EGGMAN_QR_TOKEN>`

**Files**:
- `app/routers/demo_qr.py` - New router
- `app/main_simple.py` - Router mounted
- `tests/integration/test_demo_qr_redirect.py` - Tests

## ✅ Phase 2: Charging Demo Model + Endpoints

**Data Model**:
- Added to `DriverWallet`:
  - `charging_detected` (bool, default False)
  - `charging_detected_at` (datetime, nullable)
- Migration: `025_add_charging_demo_fields.py`

**Endpoints**:
- `POST /v1/demo/charging/start` - Mark charging detected, bumps `wallet_activity_updated_at`
- `POST /v1/demo/charging/stop` - Mark charging stopped
- `GET /v1/wallet/status` - Returns charging state + message

**Gated**: `DEMO_MODE=true` OR `DEMO_QR_ENABLED=true`

**Files**:
- `app/routers/demo_charging.py` - Charging demo endpoints
- `app/routers/wallet_pass.py` - Added `/v1/wallet/status` endpoint
- `app/models/domain.py` - Charging fields in DriverWallet
- `alembic/versions/025_add_charging_demo_fields.py` - Migration
- `tests/integration/test_demo_charging_flow.py` - Tests

## ✅ Phase 3: Wallet UI Banner + Buttons

**Wallet Page** (`ui-mobile/wallet/index.html`):
- **Charging banner**: Shows "Charging detected. Nova is accruing." when `charging_detected=true`
- **Demo buttons** (visible when demo enabled):
  - "Simulate Charging Start" → `POST /v1/demo/charging/start`
  - "Simulate Charging Stop" → `POST /v1/demo/charging/stop`
- **Auto-refresh**: Polls `/v1/wallet/status` every 3 seconds

**Files**:
- `ui-mobile/wallet/index.html` - Updated with banner and buttons

## ✅ Phase 4: Apple Pass Charging Status

**Apple Wallet Pass** (`app/services/apple_wallet_pass.py`):
- **Auxiliary field**: Shows "Status: Charging detected" as first field when `charging_detected=true`
- **Back field**: Always shows charging status:
  - "Status: Charging detected" when `charging_detected=true`
  - "Status: Not charging" when `charging_detected=false`

**Files**:
- `app/services/apple_wallet_pass.py` - Charging status in pass.json
- `tests/unit/test_apple_pass_charging_status.py` - Tests

## 🧪 Tests

All tests written and passing:
- ✅ Demo QR redirect (enabled/disabled/missing token)
- ✅ Charging start bumps `wallet_activity_updated_at`
- ✅ Wallet status returns charging state
- ✅ Apple pass includes charging status field

## 🚀 Manual Test Steps

### 1. Set Environment Variables

```bash
export DEMO_QR_ENABLED=true
export DEMO_EGGMAN_QR_TOKEN=<your-sandbox-merchant-qr-token>
export DEMO_MODE=true  # Optional, enables charging demo endpoints
```

### 2. Start Backend

```bash
cd /Users/jameskirk/Desktop/Nerava/nerava-backend-v9
source .venv/bin/activate  # if using venv
uvicorn app.main_simple:app --reload --port 8001
```

### 3. Test URLs

1. **Demo QR Redirect**:
   ```
   http://127.0.0.1:8001/qr/eggman-demo-checkout
   ```
   Should redirect to: `/app/checkout.html?token=<DEMO_EGGMAN_QR_TOKEN>`

2. **Wallet Page**:
   ```
   http://127.0.0.1:8001/app/wallet/
   ```
   - Should show wallet balance
   - Should show demo buttons (if `DEMO_MODE=true`)
   - Banner appears when charging detected

3. **Start Charging Demo** (if authenticated):
   ```bash
   curl -X POST http://127.0.0.1:8001/v1/demo/charging/start \
     -H "Authorization: Bearer <your-token>"
   ```
   Response:
   ```json
   {
     "status": "OK",
     "charging_detected": true,
     "charging_detected_at": "2025-02-01T12:00:00Z"
   }
   ```

4. **Check Wallet Status**:
   ```bash
   curl http://127.0.0.1:8001/v1/wallet/status \
     -H "Authorization: Bearer <your-token>"
   ```
   Response (when charging):
   ```json
   {
     "charging_detected": true,
     "charging_detected_at": "2025-02-01T12:00:00Z",
     "message": "Charging detected. Nova is accruing."
   }
   ```

5. **Merchant Dashboard** (after redemption):
   ```
   http://127.0.0.1:8001/app/merchant/dashboard.html
   ```
   Should show incremented redemption count.

## 🔒 Safety Guarantees

- ✅ **No breaking changes**: All existing endpoints, payloads, and flows unchanged
- ✅ **Sandbox-only**: All demo features gated behind env vars
- ✅ **Backward compatible**: Migration adds nullable fields
- ✅ **Structured errors**: All errors return `{error, message}` JSON
- ✅ **Existing tests pass**: No regressions in existing test suite

## 📝 Notes

- Demo QR redirect uses existing checkout flow (no changes to checkout logic)
- Charging demo endpoints use existing `mark_wallet_activity()` service (no hacks)
- Apple pass charging status is visible but doesn't affect signing/installability
- Wallet UI banner/buttons are demo-only and don't break normal wallet UI



