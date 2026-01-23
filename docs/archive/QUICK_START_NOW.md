# Quick Start - Primary Merchant Override

## 🚨 Current Issue
The driver app shows 404 because the Vite dev server isn't running properly. The sandbox environment blocks network access, so you need to start servers manually.

## ✅ Immediate Steps

### 1. Kill Existing Processes
```bash
# Kill any existing node/vite processes
kill 8412 2>/dev/null  # The node process on port 5173
lsof -ti:5173 | xargs kill -9 2>/dev/null
lsof -ti:8001 | xargs kill -9 2>/dev/null
pkill -f vite
pkill -f uvicorn
```

### 2. Start Backend (Terminal 1)
```bash
cd /Users/jameskirk/Desktop/Nerava/backend
python3 -m uvicorn app.main:app --reload --port 8001
```

**Wait for:** `Application startup complete`

### 3. Start Driver App (Terminal 2)
```bash
cd /Users/jameskirk/Desktop/Nerava/apps/driver
npm run dev
```

**Wait for:** `Local: http://localhost:5173/`

### 4. Open in Browser
Once both servers are running, navigate to:
- **http://localhost:5173/pre-charging**

## 🎯 What You Should See

### Pre-Charge State (`/pre-charging`):
- ✅ Canyon Ridge Tesla Supercharger card
- ✅ **Only ONE merchant**: Asadas Grill
- ✅ Exclusive badge: "⭐ Exclusive"
- ✅ Exclusive description: "Free Margarita (Charging Exclusive)"

### Charging State (`/wyc`):
- ✅ Asadas Grill as primary/featured merchant (first card)
- ✅ Up to 2 secondary merchants
- ✅ Total of 3 merchants maximum

## 🔍 Verify Backend is Working

```bash
# Test health endpoint
curl http://localhost:8001/health

# Test primary merchant endpoint
curl "http://localhost:8001/v1/drivers/merchants/open?charger_id=canyon_ridge_tesla&state=pre-charge" \
  -H "Content-Type: application/json"
```

## 🐛 If Driver App Still Shows 404

1. **Check if Vite is actually running:**
   ```bash
   lsof -i:5173
   ```

2. **Check Vite logs for errors:**
   ```bash
   # Look for errors in the terminal where you ran `npm run dev`
   ```

3. **Try accessing the root:**
   - http://localhost:5173/ (should show the app)
   - Then navigate to /pre-charging

4. **Check Vite config:**
   ```bash
   cd apps/driver
   cat vite.config.ts
   ```

5. **Restart with clean cache:**
   ```bash
   cd apps/driver
   rm -rf node_modules/.vite
   npm run dev
   ```

## 📊 Database Verification

The data is already seeded:
- ✅ Charger: `canyon_ridge_tesla`
- ✅ Merchant: `asadas_grill_canyon_ridge`
- ✅ Primary Override: `Free Margarita` exclusive

You can verify with:
```bash
cd backend
python3 -c "
from app.db import SessionLocal
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant
db = SessionLocal()
charger = db.query(Charger).filter(Charger.id == 'canyon_ridge_tesla').first()
merchant = db.query(Merchant).filter(Merchant.id.like('asadas%')).first()
override = db.query(ChargerMerchant).filter(ChargerMerchant.charger_id == 'canyon_ridge_tesla', ChargerMerchant.is_primary == True).first()
print(f'✅ Charger: {charger.name if charger else \"NOT FOUND\"}')
print(f'✅ Merchant: {merchant.name if merchant else \"NOT FOUND\"}')
print(f'✅ Override: {override.exclusive_title if override else \"NOT FOUND\"}')
db.close()
"
```



