# Asadas Grill Primary Merchant Fix - URGENT

## ✅ Fixes Applied

### 1. Backend API Response (`drivers_domain.py`)
- ✅ Added `place_id` field (frontend requires this)
- ✅ Added `photo_url` field for compatibility
- ✅ Added `types` array (frontend expects this)
- ✅ Set default `open_now=True` if None (prevents filtering out)
- ✅ Improved walk time calculation

### 2. Database Updates
- ✅ Set default `walk_duration_s=180` (3 minutes)
- ✅ Set default `distance_m=150` (150 meters)

### 3. Frontend Mapping (`PreChargingScreen.tsx`)
- ✅ Fixed to use `place_id` from API response
- ✅ Fixed to use `types` array
- ✅ Added error logging for debugging
- ✅ Fixed photo_url mapping

### 4. Type Definitions (`api.ts`)
- ✅ Added `place_id` to `MerchantForCharger` interface
- ✅ Added `photo_url` and `types` fields

## 🚨 REQUIRED ACTION - RESTART BACKEND

**You must restart the backend server for changes to take effect:**

```bash
# Kill existing backend
lsof -ti:8001 | xargs kill -9 2>/dev/null

# Restart backend
cd /Users/jameskirk/Desktop/Nerava/backend
python3 -m uvicorn app.main:app --reload --port 8001
```

## 🧪 Verification

After restarting, the endpoint should return:

```json
[
  {
    "id": "asadas_grill_canyon_ridge",
    "place_id": "asadas_grill_canyon_ridge",
    "name": "Asadas Grill",
    "is_primary": true,
    "exclusive_title": "Free Margarita",
    "exclusive_description": "Free Margarita (Charging Exclusive)",
    "open_now": true,
    "walk_time_s": 180,
    "distance_m": 150,
    "types": ["restaurant"],
    ...
  }
]
```

## 📱 What Should Appear

After restarting backend and refreshing browser:
- ✅ Asadas Grill card visible
- ✅ "⭐ Exclusive" badge
- ✅ "Free Margarita (Charging Exclusive)" description
- ✅ Walk time: "3 min walk"
- ✅ No other merchants (only one card)

## 🔍 Debugging

If still not showing, check browser console for:
- API errors
- Network tab: `/v1/drivers/merchants/open?charger_id=canyon_ridge_tesla&state=pre-charge`
- Verify response contains Asadas Grill



