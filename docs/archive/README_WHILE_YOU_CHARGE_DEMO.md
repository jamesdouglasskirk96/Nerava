# While You Charge - Demo Guide

This guide walks you through setting up and demonstrating the "While You Charge" feature in the Explore tab.

## Prerequisites

- Python 3.8+
- FastAPI server running on port 8001
- API keys are hardcoded (no environment variables needed)

## Quick Start

### 1. Run Database Migration

Ensure the database schema is up to date:

```bash
cd nerava-backend-v9
alembic upgrade head
```

This creates the required tables:
- `chargers` - EV charging stations
- `merchants` - Places near chargers  
- `charger_merchants` - Junction table with walk times
- `merchant_perks` - Active rewards/offers

### 2. Seed Austin Data

Populate the database with chargers and merchants for Austin:

```bash
python3 -m app.jobs.seed_city --city="Austin" --bbox="30.0,-98.0,30.5,-97.5"
```

This will:
- Fetch ~100 chargers from NREL API
- Find nearby merchants via Google Places (coffee, food, groceries, gym)
- Compute walk times using Google Distance Matrix
- Save everything to the database

**Expected output:**
```
🌱 Seeding Austin with bbox (30.0, -98.0, 30.5, -97.5)...
📡 Fetching chargers from NREL API...
   Found 100 chargers
   Saved 100 chargers to DB
   Processing charger: Hotel San Jose - Tesla Destination
   ...
✅ Seeded X merchants and Y charger-merchant links
```

### 3. Start the Backend Server

```bash
cd nerava-backend-v9
python3 -m uvicorn app.main_simple:app --port 8001 --reload
```

### 4. Test the API Endpoint

Verify the endpoint returns results:

```bash
curl -X POST http://localhost:8001/v1/while_you_charge/search \
  -H "Content-Type: application/json" \
  -d '{"user_lat": 30.2672, "user_lng": -97.7431, "query": "coffee"}'
```

**Expected response:**
```json
{
  "chargers": [
    {
      "id": "ch_...",
      "lat": 30.2672,
      "lng": -97.7431,
      "network_name": "Tesla",
      "logo_url": "...",
      "name": "..."
    }
  ],
  "recommended_merchants": [
    {
      "id": "m_...",
      "name": "Starbucks",
      "logo_url": "...",
      "nova_reward": 12,
      "walk_minutes": 3
    }
  ]
}
```

### 5. Open the Explore Tab

1. Open `ui-mobile/index.html` in a browser
2. Navigate to the **Explore** tab
3. Allow location access when prompted (or use browser dev tools to simulate location near Austin: `30.2672, -97.7431`)

## Demo Flow

### Initial Load
- Map centers on your location (or Austin if simulated)
- Search bar shows placeholder: "What to do, while you charge..."
- Category chips appear: Coffee, Food, Groceries, Gym
- "Recommended Perks" card shows 3 merchants with Nova rewards and walk times

### Category Filter
1. Click a category chip (e.g., "Coffee")
2. Map updates with relevant chargers
3. Perks card updates with top 3 merchants for that category
4. Console shows: `[WhileYouCharge] Category filter: Using X real merchants from API`

### Text Search
1. Type in the search bar (e.g., "starbucks", "gym", "target")
2. After 500ms delay, search executes
3. Map and perks update with results
4. Console shows: `[WhileYouCharge] Search query: "starbucks"`

### Charger Selection
1. Click a charger pin on the map
2. Map centers on that charger
3. Perks update to show merchants near that charger
4. Console shows: `[WhileYouCharge] Charger tapped: ch_...`

## Console Logging

All "While You Charge" operations are logged with the `[WhileYouCharge]` prefix:

- `[WhileYouCharge] Searching: lat=..., lng=..., query="..."`
- `[WhileYouCharge] Results: X chargers, Y merchants`
- `[WhileYouCharge] Rendering X perk cards`
- `[WhileYouCharge] No merchants returned` (if empty)

## Troubleshooting

### Manual SQLite hotfixes
- If you previously added columns via `sqlite3 nerava.db ALTER TABLE merchants ...`, you can either drop and recreate the DB before running `alembic upgrade head`, or leave it alone. The new `014_add_merchant_columns` migration checks for existing columns and is effectively a no-op on SQLite when the columns already exist.

### No Chargers on Map
- Check backend logs for NREL API errors
- Verify chargers exist: `sqlite3 nerava.db "SELECT COUNT(*) FROM chargers;"`
- Re-run seed job if needed

### No Merchants in Perks Card
- Check backend logs for Google Places API errors
- Verify merchants exist: `sqlite3 nerava.db "SELECT COUNT(*) FROM merchants;"`
- Check charger-merchant links: `sqlite3 nerava.db "SELECT COUNT(*) FROM charger_merchants;"`
- Re-run seed job to create links

### Empty State Shows
- Check browser console for API errors
- Verify backend is running on port 8001
- Check network tab for failed requests
- Ensure location is set (real or simulated)

### Search Not Working
- Check browser console for JavaScript errors
- Verify `searchWhileYouCharge()` function is called
- Check that location is available (`_userLocation` is set)

## Backend Logging

Backend logs use the `[WhileYouCharge]` prefix:

```
[WhileYouCharge] Search request: lat=30.2672, lng=-97.7431, query='coffee'
[WhileYouCharge] Finding chargers near (30.2672, -97.7431) within 15000m
[WhileYouCharge] Found 50 chargers in DB
[WhileYouCharge] Finding merchants for 50 chargers, category=coffee, name=None
[WhileYouCharge] Found 15 existing merchants in DB
[WhileYouCharge] Ranking 15 merchants for 50 chargers
[WhileYouCharge] Ranked 10 merchants (skipped 5 without charger links)
[WhileYouCharge] Search complete: 20 chargers, 3 merchants
```

## Success Criteria

✅ **Explore tab shows real perks in Austin**
- Perks card displays 3 merchants with logos, Nova rewards, and walk times
- Merchants are real businesses (Starbucks, Target, etc.)

✅ **Console clearly shows live API responses**
- All `[WhileYouCharge]` logs are visible
- Response data is logged before rendering

✅ **No obvious UX dead-ends**
- Loading state appears during search
- Empty state shows if no results
- Error messages are user-friendly

## Next Steps

- Add voice search functionality
- Implement merchant detail view
- Add "Start session" flow from perk cards
- Create merchant perks dynamically based on time/context

