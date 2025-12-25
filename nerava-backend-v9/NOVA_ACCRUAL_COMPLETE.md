# Nova Accrual System - Complete

## Overview
Implemented automatic Nova accrual while charging is detected. The system accrues **1 Nova every 5 seconds** while `charging_detected = true`.

**Exchange Rate:** 1 Nova = 0.01 USD equivalent

## Implementation Details

### Service: `app/services/nova_accrual.py`
- **NovaAccrualService**: Background service that runs every 5 seconds
- Checks all wallets with `charging_detected = true`
- Accrues 1 Nova per wallet per interval
- Creates `NovaTransaction` records for audit trail
- Updates `wallet_activity_updated_at` to trigger pass refresh
- Only runs when `DEMO_MODE=true` or `DEMO_QR_ENABLED=true`

### Integration: `app/main_simple.py`
- Added startup event to start Nova accrual service
- Added shutdown event to gracefully stop the service
- Service starts automatically when server starts (if demo mode enabled)

### Transaction Records
Each accrual creates a `NovaTransaction` with:
- `type`: "driver_earn"
- `amount`: 1 (Nova)
- `transaction_meta`: 
  ```json
  {
    "source": "demo_charging_accrual",
    "rate": "1_nova_per_5_seconds",
    "usd_equivalent": 0.01
  }
  ```

## Testing

### Verify Accrual is Working
1. Start charging demo: `POST /v1/demo/charging/start`
2. Wait 5-10 seconds
3. Check wallet balance: `GET /v1/wallet/status` or wallet page
4. Balance should increase by 1 Nova every 5 seconds

### Current Status
- ✅ Service starts automatically on server startup (if demo mode enabled)
- ✅ Accrues 1 Nova every 5 seconds
- ✅ Creates transaction records
- ✅ Updates wallet activity for pass refresh
- ✅ Only runs in demo mode

## Configuration

### Environment Variables
- `DEMO_MODE=true` - Enables demo mode and Nova accrual
- `DEMO_QR_ENABLED=true` - Alternative flag to enable demo mode

### Service Settings
- **Accrual Interval**: 5 seconds (configurable in `NovaAccrualService.__init__`)
- **Exchange Rate**: 1 Nova = 0.01 USD (hardcoded in transaction metadata)

## Notes
- The service runs continuously in the background
- It automatically stops if demo mode is disabled
- Multiple wallets can accrue simultaneously
- Each accrual triggers wallet pass refresh (Apple Wallet + Google Wallet)



