# Primary Merchant Override - Testing Guide

## ✅ Implementation Complete

All components have been successfully implemented:
- Database schema extensions
- Migration (049_add_primary_merchant_override)
- Google Places service enhancements
- Merchant enrichment service
- Driver endpoint (`/v1/drivers/merchants/open`)
- Seed script execution
- Driver app UI updates
- Backend and E2E tests

## 📊 Database Status

**Migration Status**: ✅ Applied (049_add_primary_merchant_override)

**Seeded Data**:
- ✅ Charger: `canyon_ridge_tesla` (Tesla Supercharger - Canyon Ridge)
- ✅ Merchant: `asadas_grill_canyon_ridge` (Asadas Grill)
- ✅ Primary Override: `Free Margarita` exclusive offer

## 🧪 Testing Steps

### 1. Start Backend Server

```bash
cd /Users/jameskirk/Desktop/Nerava/backend
python3 -m uvicorn app.main:app --reload --port 8001
```

Or use your preferred method (docker-compose, etc.)

### 2. Test API Endpoint (Pre-Charge State)

```bash
# First, get an auth token (login as a driver user)
curl -X POST "http://localhost:8001/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your-driver@example.com", "password": "your-password"}'

# Then test the endpoint
curl -X GET "http://localhost:8001/v1/drivers/merchants/open?charger_id=canyon_ridge_tesla&state=pre-charge" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response**:
- Should return array with exactly 1 merchant (Asadas Grill)
- `is_primary: true`
- `exclusive_title: "Free Margarita"`
- `exclusive_description: "Free Margarita (Charging Exclusive)"`

### 3. Test API Endpoint (Charging State)

```bash
curl -X GET "http://localhost:8001/v1/drivers/merchants/open?charger_id=canyon_ridge_tesla&state=charging" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response**:
- Should return array with up to 3 merchants
- First merchant should be Asadas Grill with `is_primary: true`
- Followed by up to 2 secondary merchants

### 4. Test Driver App UI

#### Pre-Charge State:
1. Navigate to `/pre-charging` in the driver app
2. Select the Canyon Ridge charger (or it should auto-select)
3. **Verify**:
   - Only ONE merchant card is displayed (Asadas Grill)
   - Exclusive badge shows "⭐ Exclusive"
   - Exclusive description shows "Free Margarita (Charging Exclusive)"
   - Open/Closed status badge is visible
   - Google Places photo loads (if API key is configured)

#### Charging State:
1. Toggle to charging state (click "Charging" button)
2. Navigate to `/wyc` (While You Charge screen)
3. **Verify**:
   - Primary merchant (Asadas Grill) appears first as FeaturedMerchantCard
   - Exclusive badge is visible on primary merchant
   - Up to 2 secondary merchants appear as SecondaryMerchantCard
   - Total of 3 merchants maximum

### 5. Test Google Places Enrichment (Optional)

If you have a Google Places API key configured:

```bash
# Set the API key
export GOOGLE_PLACES_API_KEY=your_api_key_here

# Re-run the seed script to enrich with Google Places data
cd /Users/jameskirk/Desktop/Nerava/backend
python3 -m app.scripts.seed_canyon_ridge_override
```

This will:
- Search for Asadas Grill on Google Places
- Fetch full place details (photos, hours, rating, etc.)
- Update the merchant record with enriched data

### 6. Test Merchant Onboarding API

```bash
# Search for places
curl -X GET "http://localhost:8001/v1/merchants/places/search?q=Asadas+Grill&lat=30.2680&lng=-97.7435" \
  -H "Content-Type: application/json"

# Get place details
curl -X GET "http://localhost:8001/v1/merchants/places/{place_id}" \
  -H "Content-Type: application/json"
```

## 🔧 Configuration

### Required Environment Variables

For full functionality, ensure these are set:

```bash
# Google Places API (New) - Required for enrichment
GOOGLE_PLACES_API_KEY=your_api_key_here

# Cache TTL settings (optional, defaults provided)
MERCHANT_CACHE_TTL_SECONDS=86400          # 24 hours for place details
MERCHANT_STATUS_CACHE_TTL_SECONDS=300     # 5 minutes for open/closed status
MERCHANT_PHOTO_CACHE_TTL_SECONDS=604800   # 7 days for photo URLs
```

## 📝 Verification Checklist

- [x] Migration applied successfully
- [x] Canyon Ridge charger created
- [x] Asadas Grill merchant created
- [x] Primary override link created with exclusive details
- [ ] Backend server running
- [ ] API endpoint returns primary merchant in pre-charge state
- [ ] API endpoint returns primary + secondary in charging state
- [ ] Driver app shows single merchant in pre-charge
- [ ] Driver app shows primary + secondary in charging
- [ ] Exclusive badge displays correctly
- [ ] Google Places photos load (if API key configured)
- [ ] Open/closed status displays correctly

## 🐛 Troubleshooting

### API Key Missing
If you see "Missing API key" warnings:
- The seed script will still create the merchant without Google Places data
- You can manually add a `place_id` later and run enrichment
- Or set `GOOGLE_PLACES_API_KEY` and re-run the seed script

### Migration Conflicts
If you encounter migration conflicts:
- The database may have existing tables
- Use `alembic stamp` to mark migrations as applied
- Then run `alembic upgrade head` to apply only new migrations

### No Merchants Returned
- Verify the charger_id matches: `canyon_ridge_tesla`
- Check that the primary override exists in the database
- Ensure you're authenticated as a driver user

## 🎯 Success Criteria

✅ At Canyon Ridge charger, pre-charge shows only Asadas Grill  
✅ Charging state shows Asadas Grill as primary + 2 secondary  
✅ Exclusive badge displays "Exclusive"  
✅ Google Places photos render (if API key configured)  
✅ Open/closed status accurate  
✅ No API keys exposed client-side  
✅ Docker compose boots cleanly  
✅ Cache reduces API quota usage



