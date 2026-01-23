# Local Deployment Instructions

## ✅ Status

- **Migration**: ✅ Applied (049_add_primary_merchant_override)
- **Database Seeded**: ✅ Canyon Ridge charger and Asadas Grill merchant created
- **Code Implementation**: ✅ Complete

## 🚀 Manual Deployment Steps

Due to sandbox restrictions, you'll need to run these commands in your terminal:

### 1. Stop Any Running Instances

```bash
cd /Users/jameskirk/Desktop/Nerava
./stop-local-dev.sh
```

Or manually:
```bash
lsof -ti:8001 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null
pkill -f "uvicorn app.main"
pkill -f "vite"
```

### 2. Start Backend Server

**Terminal 1:**
```bash
cd /Users/jameskirk/Desktop/Nerava/backend
python3 -m uvicorn app.main:app --reload --port 8001
```

Wait for: `Application startup complete`

### 3. Start Driver App

**Terminal 2:**
```bash
cd /Users/jameskirk/Desktop/Nerava/apps/driver
npm run dev
```

Wait for: `Local: http://localhost:5173/`

### 4. Test API Endpoint

**Terminal 3:**
```bash
# Test health endpoint
curl http://localhost:8001/health

# Test primary merchant endpoint (may require auth)
curl "http://localhost:8001/v1/drivers/merchants/open?charger_id=canyon_ridge_tesla&state=pre-charge" \
  -H "Content-Type: application/json"
```

**Expected Response** (pre-charge):
```json
[
  {
    "id": "asadas_grill_canyon_ridge",
    "name": "Asadas Grill",
    "is_primary": true,
    "exclusive_title": "Free Margarita",
    "exclusive_description": "Free Margarita (Charging Exclusive)",
    ...
  }
]
```

### 5. Open Driver App in Browser

Navigate to: **http://localhost:5173/pre-charging**

**What to Verify:**
- ✅ Only ONE merchant card (Asadas Grill) is visible
- ✅ Exclusive badge shows "⭐ Exclusive"
- ✅ Exclusive description: "Free Margarita (Charging Exclusive)"
- ✅ Open/Closed status badge (if Google Places data available)

### 6. Test Charging State

1. Click the "Charging" toggle button in the header
2. Navigate to `/wyc` (While You Charge screen)
3. **Verify:**
   - ✅ Asadas Grill appears first as FeaturedMerchantCard
   - ✅ Exclusive badge visible on primary merchant
   - ✅ Up to 2 secondary merchants appear
   - ✅ Total of 3 merchants maximum

## 🔍 Troubleshooting

### Backend Won't Start
- Check if port 8001 is in use: `lsof -i:8001`
- Check backend logs for errors
- Verify database exists: `ls backend/nerava.db`

### Driver App Won't Start
- Check if port 5173 is in use: `lsof -i:5173`
- Verify node_modules installed: `cd apps/driver && npm install`
- Check driver app logs

### API Returns Empty/Error
- Verify charger exists: Check database for `canyon_ridge_tesla`
- Verify primary override exists: Check `charger_merchants` table
- Check authentication: Endpoint may require driver user login

### No Merchants Showing
- Verify seed script ran: Check database for Asadas Grill merchant
- Check API response in browser DevTools Network tab
- Verify charger_id matches: `canyon_ridge_tesla`

## 📊 Quick Verification Commands

```bash
# Check if servers are running
lsof -i:8001 && echo "Backend running" || echo "Backend not running"
lsof -i:5173 && echo "Driver app running" || echo "Driver app not running"

# Check database
cd backend
python3 -c "
from app.db import SessionLocal
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant
db = SessionLocal()
charger = db.query(Charger).filter(Charger.id == 'canyon_ridge_tesla').first()
merchant = db.query(Merchant).filter(Merchant.id.like('asadas%')).first()
override = db.query(ChargerMerchant).filter(ChargerMerchant.charger_id == 'canyon_ridge_tesla', ChargerMerchant.is_primary == True).first()
print(f'Charger: {charger.name if charger else \"NOT FOUND\"}')
print(f'Merchant: {merchant.name if merchant else \"NOT FOUND\"}')
print(f'Override: {override.exclusive_title if override else \"NOT FOUND\"}')
db.close()
"
```

## 🎯 Success Criteria

- [x] Migration applied
- [x] Database seeded
- [ ] Backend server running on port 8001
- [ ] Driver app running on port 5173
- [ ] Pre-charge shows only Asadas Grill
- [ ] Charging shows Asadas Grill + 2 secondary
- [ ] Exclusive badge visible
- [ ] Google Places photos load (if API key configured)



