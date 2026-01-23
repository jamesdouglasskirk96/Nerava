# Cursor Implementation: Charger Discovery (Demo-Grade)

---

## ⚠️ SCOPE CONSTRAINTS (READ FIRST)

This is a **DEMO-ONLY** implementation for merchant door-to-door walkthroughs.

### DO NOT:
- Introduce new abstractions or generic frameworks
- Generalize beyond the 5 seeded chargers
- Build future-proof photo routing systems
- Add pagination, caching layers, or background jobs
- Refactor unrelated code
- Create new database migrations (use existing schema)
- Add TypeScript strict mode fixes to unrelated files
- "Improve" existing code that works

### ONLY:
- Seed the exact 5 chargers specified below
- Fetch merchants from Google Places for THIS dataset only
- Store photos locally under `/static/demo_chargers/`
- Make the UI look real and correct for merchant walkthroughs
- Modify only the files explicitly listed

### STOP WHEN:
- All 5 chargers are seeded with photos
- Each charger has 12 merchants with photos
- `/v1/chargers/discovery` returns correct data
- UI shows discovery screen outside 400m
- UI shows charging screen inside 400m

---

## Objective

Implement real Pre-Charge → Charging state split:

| User Location | UI State |
|---------------|----------|
| **>400m from all chargers** | Charger Discovery screen |
| **≤400m from any charger** | Charging Experience for that charger |

---

## Seeded Chargers (EXACT DATA - DO NOT MODIFY)

```python
CHARGERS = [
    {
        "id": "charger_canyon_ridge",
        "name": "Canyon Ridge Supercharger",
        "place_id": "ChIJK-gKfYnLRIYRQKQmx_DvQko",
        "address": "501 W Canyon Ridge Dr, Austin, TX 78753",
        "lat": 30.4027,
        "lng": -97.6719,
        "network": "Tesla",
        "stalls": 8,
        "kw": 150,
        "primary_merchant_place_id": "ChIJA4UGPT_LRIYRjQC0TnNUWRg"  # Asadas Grill
    },
    {
        "id": "charger_mopac",
        "name": "Tesla Supercharger - Mopac",
        "place_id": "ChIJ51fvhIfLRIYRf3XcWjepmrA",
        "address": "10515 N Mopac Expy, Austin, TX 78759",
        "lat": 30.390456,
        "lng": -97.733056,
        "network": "Tesla",
        "stalls": 12,
        "kw": 250,
        "primary_merchant_place_id": None  # Pick closest restaurant
    },
    {
        "id": "charger_westlake",
        "name": "Tesla Supercharger - Westlake",
        "place_id": "ChIJJ6_0bN1LW4YRg8l9RLePwz8",
        "address": "701 S Capital of Texas Hwy, West Lake Hills, TX 78746",
        "lat": 30.2898,
        "lng": -97.827474,
        "network": "Tesla",
        "stalls": 16,
        "kw": 250,
        "primary_merchant_place_id": None
    },
    {
        "id": "charger_ben_white",
        "name": "Tesla Supercharger - Ben White",
        "place_id": "ChIJcz30IE9LW4YRYVS3g5VSz9Y",
        "address": "2300 W Ben White Blvd, Austin, TX 78704",
        "lat": 30.2334001,
        "lng": -97.7914251,
        "network": "Tesla",
        "stalls": 10,
        "kw": 150,
        "primary_merchant_place_id": None
    },
    {
        "id": "charger_sunset_valley",
        "name": "Tesla Supercharger - Sunset Valley",
        "place_id": "ChIJ2Um53XdLW4YRFBnBkfJKFJA",
        "address": "5601 Brodie Ln, Austin, TX 78745",
        "lat": 30.2261013,
        "lng": -97.8219238,
        "network": "Tesla",
        "stalls": 8,
        "kw": 150,
        "primary_merchant_place_id": None
    }
]
```

---

## Files to Modify (ONLY THESE)

### Backend

| File | Action |
|------|--------|
| `backend/scripts/seed_demo_chargers.py` | CREATE - Seed script |
| `backend/app/routers/chargers.py` | MODIFY - Add discovery endpoint |
| `backend/app/main_simple.py` | MODIFY - Mount static files (1 line) |
| `backend/static/demo_chargers/` | CREATE - Photo directory |

### Frontend

| File | Action |
|------|--------|
| `nerava-ui 2/src/api/chargers.ts` | CREATE - API client |
| `nerava-ui 2/src/hooks/useChargerState.ts` | CREATE - State hook |
| `nerava-ui 2/src/components/PreCharging/PreChargingScreen.tsx` | MODIFY - Use real data |
| `nerava-ui 2/src/components/PreCharging/ChargerCard.tsx` | MODIFY - Real props |

**DO NOT TOUCH ANY OTHER FILES.**

---

## API Contract (EXACT)

### GET /v1/chargers/discovery

**Query Params:**
- `lat` (float, required)
- `lng` (float, required)

**Response:**
```json
{
  "within_radius": false,
  "nearest_charger_id": "charger_mopac",
  "nearest_distance_m": 1523,
  "radius_m": 400,
  "chargers": [
    {
      "id": "charger_mopac",
      "name": "Tesla Supercharger - Mopac",
      "address": "10515 N Mopac Expy, Austin, TX 78759",
      "lat": 30.390456,
      "lng": -97.733056,
      "distance_m": 1523,
      "drive_time_min": 3,
      "network": "Tesla",
      "stalls": 12,
      "kw": 250,
      "photo_url": "/static/demo_chargers/charger_mopac/hero.jpg",
      "nearby_merchants": [
        {
          "place_id": "ChIJ...",
          "name": "Starbucks",
          "photo_url": "/static/demo_chargers/charger_mopac/merchants/starbucks_0.jpg",
          "distance_m": 45,
          "walk_time_min": 1,
          "has_exclusive": false
        },
        {
          "place_id": "ChIJ...",
          "name": "Chipotle",
          "photo_url": "/static/demo_chargers/charger_mopac/merchants/chipotle_0.jpg",
          "distance_m": 120,
          "walk_time_min": 2,
          "has_exclusive": true
        }
      ]
    }
  ]
}
```

**Key Rules:**
- `chargers` sorted by `distance_m` ascending
- Each charger includes exactly 2 `nearby_merchants` (closest two)
- `within_radius` = true if `nearest_distance_m` <= 400
- `drive_time_min` = `distance_m / 500` (round up, min 1)
- `walk_time_min` = `distance_m / 80` (round up, min 1)

---

## Seed Script Behavior

**File:** `backend/scripts/seed_demo_chargers.py`

```python
"""
Seed 5 Austin chargers with real merchant data for demo.

Usage:
  cd backend
  GOOGLE_PLACES_API_KEY=... python -m scripts.seed_demo_chargers

Idempotent: Safe to run multiple times.
"""
```

### For Each Charger:

1. **Upsert charger record** (use existing `Charger` model)
2. **Fetch charger photo** from Google Places → save to `/static/demo_chargers/{charger_id}/hero.jpg`
3. **Fetch 12 nearest merchants** using Google Places Nearby Search:
   - Types: `restaurant`, `cafe`, `coffee_shop`, `convenience_store`
   - Radius: 500m
   - Exclude the charger itself
4. **For each merchant:**
   - Get place details (name, address, lat/lng, rating, hours, photos)
   - Download first photo → `/static/demo_chargers/{charger_id}/merchants/{place_id}_0.jpg`
   - Upsert `Merchant` record
   - Upsert `ChargerMerchant` link with `distance_m`, `walk_duration_s`
5. **Mark primary merchant:**
   - If `primary_merchant_place_id` specified, use it
   - Else, pick closest restaurant/cafe as primary

### Photo Download (Handle Google's Redirect):

```python
async def download_photo(client: httpx.AsyncClient, photo_name: str, save_path: Path):
    """Download photo from Google Places API v1 (handles redirect)."""
    url = f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=800&key={API_KEY}"
    response = await client.get(url, follow_redirects=True)
    if response.status_code == 200:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        save_path.write_bytes(response.content)
```

---

## Frontend State Machine

**File:** `nerava-ui 2/src/hooks/useChargerState.ts`

```typescript
export function useChargerState() {
  const geo = useGeolocation()
  const [data, setData] = useState<DiscoveryResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (geo.latitude && geo.longitude && !geo.loading) {
      fetch(`/v1/chargers/discovery?lat=${geo.latitude}&lng=${geo.longitude}`)
        .then(r => r.json())
        .then(setData)
        .finally(() => setLoading(false))
    }
  }, [geo.latitude, geo.longitude, geo.loading])

  return {
    loading: loading || geo.loading,
    // THE CRITICAL STATE DECISION:
    showCharging: data?.within_radius ?? false,
    nearestChargerId: data?.nearest_charger_id ?? null,
    chargers: data?.chargers ?? []
  }
}
```

**Usage in App:**

```typescript
function DriverHome() {
  const { showCharging, nearestChargerId, chargers, loading } = useChargerState()

  if (loading) return <LoadingSpinner />

  if (showCharging && nearestChargerId) {
    return <WhileYouChargeScreen chargerId={nearestChargerId} />
  }

  return <PreChargingScreen chargers={chargers} />
}
```

---

## UI Requirements

### Charger Card (Google Maps Style)

```
┌─────────────────────────────────────┐
│ [Hero Photo - 160px height]         │
├─────────────────────────────────────┤
│ Tesla Supercharger - Mopac          │
│ ⭐ 4.5 (123)  •  12 stalls  •  250kW│
│ 10515 N Mopac Expy                  │
│ Open 24 hours                       │
├─────────────────────────────────────┤
│ 🚗 3 min drive                      │
├─────────────────────────────────────┤
│ Nearby experiences                  │
│ ┌─────────┐ ┌─────────┐             │
│ │[Photo]  │ │[Photo]  │             │
│ │Starbucks│ │Chipotle⚡│             │
│ │1 min    │ │2 min    │             │
│ └─────────┘ └─────────┘             │
├─────────────────────────────────────┤
│ [ Navigate to Charger ]             │
└─────────────────────────────────────┘
```

### Rules:
- No placeholder images (every card must have real photo)
- Exclusive badge (⚡) only if `has_exclusive: true`
- Distance badge uses drive time for chargers, walk time for merchants
- Cards sorted by distance (closest first)

---

## Validation Commands

### 1. Run Seed

```bash
cd /Users/jameskirk/Desktop/Nerava/backend
GOOGLE_PLACES_API_KEY="AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg" \
PYTHONPATH=. python -m scripts.seed_demo_chargers
```

### 2. Verify Photos Exist

```bash
find static/demo_chargers -name "*.jpg" | wc -l
# Expected: ~65 (5 charger heroes + ~60 merchant photos)
```

### 3. Test API - Far Location (Downtown)

```bash
curl -s "http://localhost:8001/v1/chargers/discovery?lat=30.27&lng=-97.74" | jq '.within_radius'
# Expected: false
```

### 4. Test API - Near Canyon Ridge

```bash
curl -s "http://localhost:8001/v1/chargers/discovery?lat=30.4027&lng=-97.6719" | jq '.within_radius'
# Expected: true
```

### 5. UI Test - Mock Far Location

```
http://localhost:5173/?mock=far
```
- Should show Charger Discovery with 5 chargers
- Each charger should have photo + 2 merchants

### 6. UI Test - Mock Near Charger

```
http://localhost:5173/?mock=charger
```
- Should show Charging Experience (existing UI)

---

## Non-Goals (EXPLICIT)

❌ Real-time charger availability
❌ Background sync jobs
❌ Infinite scrolling / pagination
❌ Production CDN photo routing
❌ Generalized charger ingestion pipeline
❌ New database migrations
❌ TypeScript strict mode cleanup
❌ Refactoring existing working code

---

## Acceptance Criteria (Demo Walkthrough)

**Scenario: Merchant door-to-door demo**

1. Open app at downtown Austin (outside all charger radii)
2. See "Find a charger near experiences" screen
3. See 5 chargers with real photos, sorted by distance
4. Each charger shows address, stalls, kW, drive time
5. Each charger shows 2 nearby merchants with photos
6. Tap charger → (future: navigate or show details)
7. Spoof location to Canyon Ridge charger
8. App switches to Charging Experience
9. Asadas Grill is primary merchant
10. Other merchants sorted by distance with real photos

**If any of these fail, implementation is incomplete.**

---

## Execution Checklist

- [ ] Create `backend/static/demo_chargers/` directory
- [ ] Create `backend/scripts/seed_demo_chargers.py`
- [ ] Add static mount to `main_simple.py`
- [ ] Add `/v1/chargers/discovery` endpoint to `chargers.py`
- [ ] Run seed script, verify photos downloaded
- [ ] Create `nerava-ui 2/src/api/chargers.ts`
- [ ] Create `nerava-ui 2/src/hooks/useChargerState.ts`
- [ ] Update `PreChargingScreen.tsx` to use real data
- [ ] Update `ChargerCard.tsx` to use real props
- [ ] Test mock=far shows discovery
- [ ] Test mock=charger shows charging
- [ ] Verify no placeholder images in UI
