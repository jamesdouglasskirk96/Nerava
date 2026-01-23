# While You Charge Setup Guide

## Prerequisites

1. **Run database migrations:**
   ```bash
   cd nerava-backend-v9
   alembic upgrade head
   ```
   This creates the required tables: `chargers`, `merchants`, `charger_merchants`, `merchant_perks`

2. **Set environment variables:**
   ```bash
   # NREL API (free key at https://developer.nrel.gov/signup/)
   export NREL_API_KEY=your_nrel_key_here
   
   # Google Places API (same key works for Places and Distance Matrix)
   export GOOGLE_PLACES_API_KEY=your_google_key_here
   # OR use existing key name:
   export GOOGLE_MAPS_API_KEY=your_google_key_here
   # OR:
   export GOOGLE_API_KEY=your_google_key_here
   ```

## Seed Data for Austin

To populate the database with chargers and merchants for Austin:

```bash
python -m app.jobs.seed_city --city="Austin" --bbox="30.0,-98.0,30.5,-97.5"
```

This will:
- Fetch chargers from NREL API
- Find nearby merchants via Google Places (coffee, food, groceries, gym)
- Compute walk times using Google Distance Matrix
- Save everything to the database

## Test the Endpoint

```bash
curl -X POST http://localhost:8001/v1/while_you_charge/search \
  -H "Content-Type: application/json" \
  -d '{"user_lat": 30.2672, "user_lng": -97.7431, "query": "coffee"}'
```

Expected response:
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

## Frontend

The Explore tab automatically calls this endpoint when:
- Page loads (with user's geolocation)
- User clicks category chips (Coffee, Food, Groceries, Gym)
- User selects a charger on the map

If the API fails or returns empty results, the UI falls back to dummy data and logs a warning to the console.

## Troubleshooting

- **No chargers returned**: Check NREL_API_KEY is set and valid
- **No merchants returned**: Check GOOGLE_PLACES_API_KEY is set and valid
- **Empty results after seeding**: Check logs for API errors, verify bbox covers your test location
- **Migration errors**: Ensure all previous migrations have run (`alembic upgrade head`)

