# Fix for 500 Errors on Demo Charging Endpoints

## Issues Fixed

1. **OPTIONS 405 Error**: Added OPTIONS handlers for `/v1/demo/charging/start` and `/v1/demo/charging/stop` endpoints to handle CORS preflight requests.

2. **POST 500 Error**: Improved error handling in authentication dependencies:
   - Updated `get_current_driver_id` to return structured JSON errors
   - Updated `get_current_driver` to return structured JSON errors
   - Fixed settings import to use `core.config.settings` correctly

3. **UI Error Handling**: Updated wallet HTML to:
   - Handle 401 (authentication required) errors gracefully
   - Show user-friendly error messages
   - Properly check demo mode availability

## Changes Made

### Backend (`app/routers/demo_charging.py`)
- Added `@router.options()` handlers for both charging endpoints
- Added try/catch around demo mode check

### Backend (`app/dependencies/driver.py`)
- Changed HTTPException `detail` from string to structured dict format:
  ```python
  detail={
      "error": "AUTHENTICATION_REQUIRED",
      "message": "Driver authentication required"
  }
  ```

### Frontend (`ui-mobile/wallet/index.html`)
- Updated `startChargingDemo()` and `stopChargingDemo()` to:
  - Handle 401 errors with user-friendly messages
  - Parse error responses properly
  - Show appropriate alerts

## Next Steps

**IMPORTANT**: The server needs to be **restarted** to pick up these changes:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd /Users/jameskirk/Desktop/Nerava/nerava-backend-v9
uvicorn app.main_simple:app --reload --port 8001
```

## Testing

After restarting the server:

1. **Without Authentication** (should return 401):
   ```bash
   curl -X POST http://127.0.0.1:8001/v1/demo/charging/start
   ```
   Expected: `{"detail": {"error": "AUTHENTICATION_REQUIRED", "message": "..."}}`

2. **With Authentication** (if logged in):
   - Visit `/app/wallet/` in browser
   - Click "Simulate Charging Start" button
   - Should work if you're logged in and `DEMO_MODE=true` or `DEMO_QR_ENABLED=true`

3. **OPTIONS Request** (should return 200):
   ```bash
   curl -X OPTIONS http://127.0.0.1:8001/v1/demo/charging/start
   ```
   Expected: `{"status": "OK"}`

## Environment Variables

To enable demo mode, set one of:
- `DEMO_MODE=true`
- `DEMO_QR_ENABLED=true`

To allow anonymous driver access in dev (optional):
- `NERAVA_DEV_ALLOW_ANON_DRIVER=true`

