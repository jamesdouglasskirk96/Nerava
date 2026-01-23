# Auth Disabled for Merchants Endpoint - TEMPORARY

## ✅ Changes Applied

### 1. Auth Middleware (`app/middleware/auth.py`)
- ✅ Added `/v1/drivers/merchants/open` to excluded paths
- ✅ Endpoint now bypasses authentication middleware

### 2. Endpoint Dependency (`app/routers/drivers_domain.py`)
- ✅ Changed from `get_current_driver` (required) to `get_current_driver_optional` (optional)
- ✅ User parameter is now `Optional[User]`
- ✅ Endpoint works with or without authentication

## 🚨 REQUIRED ACTION - RESTART BACKEND

**You must restart the backend server for changes to take effect:**

```bash
# Kill existing backend
lsof -ti:8001 | xargs kill -9 2>/dev/null

# Restart backend
cd /Users/jameskirk/Desktop/Nerava/backend
python3 -m uvicorn app.main:app --reload --port 8001
```

## 🧪 Test the Endpoint

After restarting, test without auth:

```bash
curl "http://localhost:8001/v1/drivers/merchants/open?charger_id=canyon_ridge_tesla&state=pre-charge"
```

**Expected Response:**
```json
[
  {
    "id": "asadas_grill_canyon_ridge",
    "place_id": "asadas_grill_canyon_ridge",
    "name": "Asadas Grill",
    "is_primary": true,
    "exclusive_title": "Free Margarita",
    ...
  }
]
```

## ⚠️ Security Note

This is a **TEMPORARY** change for the Asadas Grill demo. In production:
- Remove `/v1/drivers/merchants/open` from excluded paths
- Change back to `get_current_driver` (required auth)
- Or use proper authentication tokens

## 🔄 To Re-enable Auth Later

1. Remove `/v1/drivers/merchants/open` from `auth.py` excluded_paths
2. Change `get_current_driver_optional` back to `get_current_driver`
3. Restart backend



