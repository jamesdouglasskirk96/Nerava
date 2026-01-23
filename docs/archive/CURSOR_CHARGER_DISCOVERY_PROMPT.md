# Cursor Implementation Prompt: Charger Discovery + 5 Seeded Austin Chargers

## Objective

Implement a real Pre-Charge → Charging state split based on geolocation:
- **Outside 400m of any charger** → Show Charger Discovery screen with real seeded charger data
- **Within 400m of a charger** → Show existing Charging experience for that charger

Seed the database with 5 chargers (1 existing Asadas + 4 new Tesla Superchargers) and their nearby merchants from Google Places.

---

## Seeded Charger Data (DETERMINISTIC)

| ID | Name | Place ID | Address | Lat | Lng |
|----|------|----------|---------|-----|-----|
| `charger_canyon_ridge` | Canyon Ridge Supercharger | `ChIJK-gKfYnLRIYRQKQmx_DvQko` | 501 W Canyon Ridge Dr, Austin, TX 78753 | 30.4027 | -97.6719 |
| `charger_mopac` | Tesla Supercharger - Mopac | `ChIJ51fvhIfLRIYRf3XcWjepmrA` | 10515 N Mopac Expy, Austin, TX 78759 | 30.390456 | -97.733056 |
| `charger_westlake` | Tesla Supercharger - Westlake | `ChIJJ6_0bN1LW4YRg8l9RLePwz8` | 701 S Capital of Texas Hwy, West Lake Hills, TX 78746 | 30.2898 | -97.827474 |
| `charger_ben_white` | Tesla Supercharger - Ben White | `ChIJcz30IE9LW4YRYVS3g5VSz9Y` | 2300 W Ben White Blvd, Austin, TX 78704 | 30.2334001 | -97.7914251 |
| `charger_sunset_valley` | Tesla Supercharger - Sunset Valley | `ChIJ2Um53XdLW4YRFBnBkfJKFJA` | 5601 Brodie Ln, Austin, TX 78745 | 30.2261013 | -97.8219238 |

---

## Files to Modify/Create

### Backend

| File | Action | Purpose |
|------|--------|---------|
| `backend/scripts/seed_austin_chargers.py` | CREATE | New comprehensive seed script for all 5 chargers |
| `backend/app/routers/chargers.py` | MODIFY | Add `/v1/chargers/discover` and `/v1/chargers/nearest` endpoints |
| `backend/app/schemas/charger_schemas.py` | CREATE | Pydantic schemas for new endpoints |
| `backend/static/seed_photos/` | CREATE | Directory for seeded photos |

### Frontend

| File | Action | Purpose |
|------|--------|---------|
| `nerava-ui 2/src/components/PreCharging/PreChargingScreen.tsx` | MODIFY | Replace mock data with API calls |
| `nerava-ui 2/src/components/PreCharging/ChargerCard.tsx` | MODIFY | Update to use real charger data |
| `nerava-ui 2/src/hooks/useChargerDiscovery.ts` | CREATE | Hook for charger discovery API |
| `nerava-ui 2/src/hooks/useNearestCharger.ts` | CREATE | Hook for nearest charger detection |
| `nerava-ui 2/src/api/chargers.ts` | CREATE | API client for charger endpoints |

---

## Backend Implementation

### 1. Create Pydantic Schemas

**File:** `backend/app/schemas/charger_schemas.py`

```python
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class NearbyExperiencePreview(BaseModel):
    """Mini merchant preview for charger card"""
    place_id: str
    name: str
    photo_url: Optional[str] = None
    has_exclusive: bool = False

class ChargerDiscoveryItem(BaseModel):
    """Charger card for discovery screen"""
    id: str
    name: str
    address: str
    lat: float
    lng: float
    network_name: str = "Tesla"
    photo_url: Optional[str] = None
    distance_m: float
    drive_time_min: Optional[int] = None  # Calculated: distance_m / 500 (avg driving m/min)
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    stalls: Optional[int] = None
    kw: Optional[int] = None
    open_24_hours: bool = True
    nearby_experiences: List[NearbyExperiencePreview] = []

class ChargerDiscoverResponse(BaseModel):
    """Response for /v1/chargers/discover"""
    chargers: List[ChargerDiscoveryItem]
    user_lat: float
    user_lng: float

class NearestChargerResponse(BaseModel):
    """Response for /v1/chargers/nearest"""
    charger: Optional[ChargerDiscoveryItem] = None
    distance_m: Optional[float] = None
    within_radius: bool = False
    radius_m: int = 400
```

### 2. Add API Endpoints

**File:** `backend/app/routers/chargers.py` (ADD to existing file)

```python
from app.schemas.charger_schemas import (
    ChargerDiscoverResponse,
    ChargerDiscoveryItem,
    NearestChargerResponse,
    NearbyExperiencePreview
)
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant
from sqlalchemy import func
import math

CHARGER_ACTIVATION_RADIUS_M = 400

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in meters between two lat/lng points"""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c

@router.get("/discover", response_model=ChargerDiscoverResponse)
async def discover_chargers(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    max_results: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Get chargers for discovery screen, sorted by distance.
    Each charger includes 2 nearby merchant previews.
    """
    # Get all seeded chargers
    chargers = db.query(Charger).filter(
        Charger.id.like("charger_%")  # Only seeded chargers
    ).all()

    results = []
    for charger in chargers:
        distance_m = haversine_distance(lat, lng, charger.lat, charger.lng)

        # Get 2 closest merchants for preview
        merchant_links = db.query(ChargerMerchant, Merchant).join(
            Merchant, ChargerMerchant.merchant_id == Merchant.id
        ).filter(
            ChargerMerchant.charger_id == charger.id
        ).order_by(
            ChargerMerchant.distance_m
        ).limit(2).all()

        nearby_experiences = []
        for link, merchant in merchant_links:
            nearby_experiences.append(NearbyExperiencePreview(
                place_id=merchant.place_id,
                name=merchant.name,
                photo_url=merchant.primary_photo_url or merchant.photo_url,
                has_exclusive=link.exclusive_title is not None
            ))

        results.append(ChargerDiscoveryItem(
            id=charger.id,
            name=charger.name,
            address=charger.address or f"{charger.city}, TX",
            lat=charger.lat,
            lng=charger.lng,
            network_name=charger.network_name or "Tesla",
            photo_url=charger.photo_url,
            distance_m=distance_m,
            drive_time_min=max(1, int(distance_m / 500)),  # ~30 km/h average
            rating=charger.rating,
            rating_count=charger.rating_count,
            stalls=charger.stalls,
            kw=charger.power_kw,
            open_24_hours=True,
            nearby_experiences=nearby_experiences
        ))

    # Sort by distance
    results.sort(key=lambda x: x.distance_m)

    return ChargerDiscoverResponse(
        chargers=results[:max_results],
        user_lat=lat,
        user_lng=lng
    )

@router.get("/nearest", response_model=NearestChargerResponse)
async def get_nearest_charger(
    lat: float = Query(..., description="User latitude"),
    lng: float = Query(..., description="User longitude"),
    db: Session = Depends(get_db)
):
    """
    Get the nearest charger and whether user is within activation radius.
    Used to determine Pre-Charge vs Charging state.
    """
    chargers = db.query(Charger).filter(
        Charger.id.like("charger_%")
    ).all()

    if not chargers:
        return NearestChargerResponse(
            charger=None,
            distance_m=None,
            within_radius=False,
            radius_m=CHARGER_ACTIVATION_RADIUS_M
        )

    # Find nearest
    nearest = None
    nearest_distance = float('inf')

    for charger in chargers:
        distance = haversine_distance(lat, lng, charger.lat, charger.lng)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest = charger

    # Get merchant previews for nearest
    merchant_links = db.query(ChargerMerchant, Merchant).join(
        Merchant, ChargerMerchant.merchant_id == Merchant.id
    ).filter(
        ChargerMerchant.charger_id == nearest.id
    ).order_by(
        ChargerMerchant.distance_m
    ).limit(2).all()

    nearby_experiences = []
    for link, merchant in merchant_links:
        nearby_experiences.append(NearbyExperiencePreview(
            place_id=merchant.place_id,
            name=merchant.name,
            photo_url=merchant.primary_photo_url or merchant.photo_url,
            has_exclusive=link.exclusive_title is not None
        ))

    charger_item = ChargerDiscoveryItem(
        id=nearest.id,
        name=nearest.name,
        address=nearest.address or f"{nearest.city}, TX",
        lat=nearest.lat,
        lng=nearest.lng,
        network_name=nearest.network_name or "Tesla",
        photo_url=nearest.photo_url,
        distance_m=nearest_distance,
        drive_time_min=max(1, int(nearest_distance / 500)),
        rating=nearest.rating,
        rating_count=nearest.rating_count,
        stalls=nearest.stalls,
        kw=nearest.power_kw,
        open_24_hours=True,
        nearby_experiences=nearby_experiences
    )

    return NearestChargerResponse(
        charger=charger_item,
        distance_m=nearest_distance,
        within_radius=nearest_distance <= CHARGER_ACTIVATION_RADIUS_M,
        radius_m=CHARGER_ACTIVATION_RADIUS_M
    )
```

### 3. Add missing columns to Charger model (if needed)

**File:** `backend/app/models/while_you_charge.py`

Ensure `Charger` model has these fields (add if missing):

```python
class Charger(Base):
    __tablename__ = "chargers"

    id = Column(String, primary_key=True)
    external_id = Column(String, nullable=True)
    name = Column(String, nullable=False)
    network_name = Column(String, default="Tesla")
    address = Column(String, nullable=True)  # ADD if missing
    city = Column(String, nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    photo_url = Column(String, nullable=True)  # ADD if missing
    rating = Column(Float, nullable=True)  # ADD if missing
    rating_count = Column(Integer, nullable=True)  # ADD if missing
    stalls = Column(Integer, nullable=True)  # ADD if missing
    power_kw = Column(Integer, nullable=True)
    connector_types = Column(JSON, nullable=True)
    status = Column(String, default="available")
    is_public = Column(Boolean, default=True)
    access_code = Column(String, nullable=True)
```

### 4. Create Seed Script

**File:** `backend/scripts/seed_austin_chargers.py`

```python
"""
Seed script for 5 Austin chargers with real Google Places merchant data.

Chargers:
1. Canyon Ridge (Asadas Grill primary)
2. Mopac
3. Westlake
4. Ben White
5. Sunset Valley

Run: python -m scripts.seed_austin_chargers
"""
import sys
import os
import asyncio
import httpx
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import uuid
import logging
import math

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg")
PHOTOS_DIR = Path(__file__).parent.parent / "static" / "seed_photos"
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# DETERMINISTIC CHARGER DATA
CHARGERS = [
    {
        "id": "charger_canyon_ridge",
        "name": "Canyon Ridge Supercharger",
        "place_id": "ChIJK-gKfYnLRIYRQKQmx_DvQko",
        "address": "501 W Canyon Ridge Dr, Austin, TX 78753",
        "lat": 30.4027,
        "lng": -97.6719,
        "network_name": "Tesla",
        "stalls": 8,
        "power_kw": 150,
        "primary_merchant_place_id": "ChIJA4UGPT_LRIYRjQC0TnNUWRg"  # Asadas Grill
    },
    {
        "id": "charger_mopac",
        "name": "Tesla Supercharger - Mopac",
        "place_id": "ChIJ51fvhIfLRIYRf3XcWjepmrA",
        "address": "10515 N Mopac Expy, Austin, TX 78759",
        "lat": 30.390456,
        "lng": -97.733056,
        "network_name": "Tesla",
        "stalls": 12,
        "power_kw": 250,
        "primary_merchant_place_id": None
    },
    {
        "id": "charger_westlake",
        "name": "Tesla Supercharger - Westlake",
        "place_id": "ChIJJ6_0bN1LW4YRg8l9RLePwz8",
        "address": "701 S Capital of Texas Hwy, West Lake Hills, TX 78746",
        "lat": 30.2898,
        "lng": -97.827474,
        "network_name": "Tesla",
        "stalls": 16,
        "power_kw": 250,
        "primary_merchant_place_id": None
    },
    {
        "id": "charger_ben_white",
        "name": "Tesla Supercharger - Ben White",
        "place_id": "ChIJcz30IE9LW4YRYVS3g5VSz9Y",
        "address": "2300 W Ben White Blvd, Austin, TX 78704",
        "lat": 30.2334001,
        "lng": -97.7914251,
        "network_name": "Tesla",
        "stalls": 10,
        "power_kw": 150,
        "primary_merchant_place_id": None
    },
    {
        "id": "charger_sunset_valley",
        "name": "Tesla Supercharger - Sunset Valley",
        "place_id": "ChIJ2Um53XdLW4YRFBnBkfJKFJA",
        "address": "5601 Brodie Ln, Austin, TX 78745",
        "lat": 30.2261013,
        "lng": -97.8219238,
        "network_name": "Tesla",
        "stalls": 8,
        "power_kw": 150,
        "primary_merchant_place_id": None
    }
]

def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in meters"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def map_types_to_category(types: List[str]) -> Tuple[str, str]:
    """Map Google Places types to category"""
    type_set = set(t.lower() for t in types)

    if any(t in type_set for t in ["restaurant", "meal_takeaway"]):
        return "Restaurant", "food"
    elif any(t in type_set for t in ["cafe", "coffee_shop"]):
        return "Coffee Shop", "food"
    elif "convenience_store" in type_set:
        return "Convenience Store", "other"
    elif any(t in type_set for t in ["gym", "fitness_center"]):
        return "Gym", "other"
    elif any(t in type_set for t in ["pharmacy", "drugstore"]):
        return "Pharmacy", "other"
    else:
        return types[0].replace("_", " ").title() if types else "Business", "other"

async def fetch_place_photo(client: httpx.AsyncClient, photo_name: str, place_id: str, index: int) -> Optional[str]:
    """Download photo and save to static folder"""
    try:
        # Create photo directory
        photo_dir = PHOTOS_DIR / place_id
        photo_dir.mkdir(parents=True, exist_ok=True)

        photo_path = photo_dir / f"photo_{index}.jpg"

        # Check if already downloaded
        if photo_path.exists():
            logger.info(f"Photo already exists: {photo_path}")
            return f"{BASE_URL}/static/seed_photos/{place_id}/photo_{index}.jpg"

        # Fetch via Places API v1
        url = f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=800&key={GOOGLE_API_KEY}"
        response = await client.get(url, follow_redirects=True)

        if response.status_code == 200:
            with open(photo_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Downloaded photo: {photo_path}")
            return f"{BASE_URL}/static/seed_photos/{place_id}/photo_{index}.jpg"
        else:
            logger.warning(f"Failed to download photo: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading photo: {e}")
        return None

async def fetch_nearby_merchants(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    radius_m: int = 500,
    max_results: int = 12
) -> List[Dict]:
    """Fetch nearby merchants from Google Places API"""
    url = "https://places.googleapis.com/v1/places:searchNearby"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.types,places.priceLevel,places.photos,places.regularOpeningHours,places.editorialSummary"
    }

    body = {
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m
            }
        },
        "includedTypes": ["restaurant", "cafe", "coffee_shop", "convenience_store", "gym", "pharmacy"],
        "maxResultCount": max_results
    }

    try:
        response = await client.post(url, headers=headers, json=body)
        if response.status_code == 200:
            data = response.json()
            return data.get("places", [])
        else:
            logger.error(f"Places API error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error fetching nearby places: {e}")
        return []

async def create_or_update_merchant(
    db: Session,
    client: httpx.AsyncClient,
    place_data: Dict,
    charger_lat: float,
    charger_lng: float
) -> Optional[Merchant]:
    """Create or update merchant from Google Places data"""
    place_id = place_data.get("id")
    if not place_id:
        return None

    # Check if exists
    existing = db.query(Merchant).filter(Merchant.place_id == place_id).first()

    name = place_data.get("displayName", {}).get("text", "Unknown")
    address = place_data.get("formattedAddress", "")
    location = place_data.get("location", {})
    lat = location.get("latitude", 0)
    lng = location.get("longitude", 0)
    rating = place_data.get("rating")
    rating_count = place_data.get("userRatingCount")
    types = place_data.get("types", [])
    category, primary_category = map_types_to_category(types)
    price_level = place_data.get("priceLevel")
    hours_json = place_data.get("regularOpeningHours")
    description = place_data.get("editorialSummary", {}).get("text")

    # Download photos
    photos = place_data.get("photos", [])[:3]
    photo_urls = []
    for i, photo in enumerate(photos):
        photo_name = photo.get("name")
        if photo_name:
            url = await fetch_place_photo(client, photo_name, place_id, i)
            if url:
                photo_urls.append(url)

    primary_photo_url = photo_urls[0] if photo_urls else None

    distance_m = haversine_distance(charger_lat, charger_lng, lat, lng)
    walk_duration_s = int(distance_m / 1.4)  # ~1.4 m/s walking speed

    if existing:
        # Update
        existing.name = name
        existing.address = address
        existing.lat = lat
        existing.lng = lng
        existing.rating = rating
        existing.rating_count = rating_count
        existing.category = category
        existing.primary_category = primary_category
        existing.price_level = price_level
        existing.hours_json = json.dumps(hours_json) if hours_json else None
        existing.description = description
        existing.primary_photo_url = primary_photo_url
        existing.photo_urls = json.dumps(photo_urls) if photo_urls else None
        existing.nearest_charger_distance_m = distance_m
        db.commit()
        logger.info(f"Updated merchant: {name}")
        return existing
    else:
        # Create
        merchant = Merchant(
            id=str(uuid.uuid4()),
            place_id=place_id,
            name=name,
            address=address,
            lat=lat,
            lng=lng,
            rating=rating,
            rating_count=rating_count,
            category=category,
            primary_category=primary_category,
            price_level=price_level,
            hours_json=json.dumps(hours_json) if hours_json else None,
            description=description,
            primary_photo_url=primary_photo_url,
            photo_urls=json.dumps(photo_urls) if photo_urls else None,
            nearest_charger_distance_m=distance_m
        )
        db.add(merchant)
        db.commit()
        logger.info(f"Created merchant: {name}")
        return merchant

async def seed_charger(
    db: Session,
    client: httpx.AsyncClient,
    charger_data: Dict
) -> None:
    """Seed a single charger with its merchants"""
    charger_id = charger_data["id"]

    # Upsert charger
    existing = db.query(Charger).filter(Charger.id == charger_id).first()

    if existing:
        existing.name = charger_data["name"]
        existing.address = charger_data["address"]
        existing.lat = charger_data["lat"]
        existing.lng = charger_data["lng"]
        existing.network_name = charger_data["network_name"]
        existing.stalls = charger_data.get("stalls")
        existing.power_kw = charger_data.get("power_kw")
        existing.external_id = charger_data["place_id"]
        charger = existing
        logger.info(f"Updated charger: {charger_data['name']}")
    else:
        charger = Charger(
            id=charger_id,
            external_id=charger_data["place_id"],
            name=charger_data["name"],
            address=charger_data["address"],
            lat=charger_data["lat"],
            lng=charger_data["lng"],
            city="Austin",
            network_name=charger_data["network_name"],
            stalls=charger_data.get("stalls"),
            power_kw=charger_data.get("power_kw"),
            is_public=True,
            status="available"
        )
        db.add(charger)
        logger.info(f"Created charger: {charger_data['name']}")

    db.commit()

    # Fetch nearby merchants
    logger.info(f"Fetching merchants near {charger_data['name']}...")
    places = await fetch_nearby_merchants(
        client,
        charger_data["lat"],
        charger_data["lng"],
        radius_m=500,
        max_results=12
    )

    # Filter out the charger itself
    places = [p for p in places if p.get("id") != charger_data["place_id"]]

    # Create merchants and links
    primary_place_id = charger_data.get("primary_merchant_place_id")

    for place_data in places:
        merchant = await create_or_update_merchant(
            db, client, place_data, charger_data["lat"], charger_data["lng"]
        )

        if merchant:
            # Check if link exists
            existing_link = db.query(ChargerMerchant).filter(
                ChargerMerchant.charger_id == charger_id,
                ChargerMerchant.merchant_id == merchant.id
            ).first()

            distance_m = haversine_distance(
                charger_data["lat"], charger_data["lng"],
                merchant.lat, merchant.lng
            )
            walk_duration_s = int(distance_m / 1.4)
            is_primary = merchant.place_id == primary_place_id

            if existing_link:
                existing_link.distance_m = distance_m
                existing_link.walk_duration_s = walk_duration_s
                existing_link.is_primary = is_primary
            else:
                link = ChargerMerchant(
                    charger_id=charger_id,
                    merchant_id=merchant.id,
                    distance_m=distance_m,
                    walk_duration_s=walk_duration_s,
                    is_primary=is_primary,
                    override_mode="ALWAYS" if is_primary else None,
                    suppress_others=False,
                    exclusive_title="Free Chips & Salsa" if is_primary else None,
                    exclusive_description="Get free chips & salsa with your meal while charging!" if is_primary else None
                )
                db.add(link)

            db.commit()

    logger.info(f"Seeded {len(places)} merchants for {charger_data['name']}")

async def main():
    """Main seed function"""
    logger.info("Starting Austin chargers seed...")

    # Ensure photos directory exists
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()

    async with httpx.AsyncClient(timeout=30.0) as client:
        for charger_data in CHARGERS:
            await seed_charger(db, client, charger_data)

    db.close()
    logger.info("Seed complete!")

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. Serve Static Photos

**File:** `backend/app/main_simple.py` (ADD to existing file after app creation)

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Mount static files for seeded photos
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
```

---

## Frontend Implementation

### 1. Create API Client

**File:** `nerava-ui 2/src/api/chargers.ts`

```typescript
import { api } from './client'

export interface NearbyExperiencePreview {
  place_id: string
  name: string
  photo_url: string | null
  has_exclusive: boolean
}

export interface ChargerDiscoveryItem {
  id: string
  name: string
  address: string
  lat: number
  lng: number
  network_name: string
  photo_url: string | null
  distance_m: number
  drive_time_min: number | null
  rating: number | null
  rating_count: number | null
  stalls: number | null
  kw: number | null
  open_24_hours: boolean
  nearby_experiences: NearbyExperiencePreview[]
}

export interface ChargerDiscoverResponse {
  chargers: ChargerDiscoveryItem[]
  user_lat: number
  user_lng: number
}

export interface NearestChargerResponse {
  charger: ChargerDiscoveryItem | null
  distance_m: number | null
  within_radius: boolean
  radius_m: number
}

export async function discoverChargers(lat: number, lng: number): Promise<ChargerDiscoverResponse> {
  const response = await api.get(`/v1/chargers/discover?lat=${lat}&lng=${lng}`)
  return response.data
}

export async function getNearestCharger(lat: number, lng: number): Promise<NearestChargerResponse> {
  const response = await api.get(`/v1/chargers/nearest?lat=${lat}&lng=${lng}`)
  return response.data
}
```

### 2. Create Hooks

**File:** `nerava-ui 2/src/hooks/useNearestCharger.ts`

```typescript
import { useState, useEffect } from 'react'
import { getNearestCharger, NearestChargerResponse } from '../api/chargers'
import { useGeolocation } from './useGeolocation'

export function useNearestCharger() {
  const geo = useGeolocation()
  const [data, setData] = useState<NearestChargerResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (geo.latitude && geo.longitude && !geo.loading) {
      setLoading(true)
      getNearestCharger(geo.latitude, geo.longitude)
        .then(setData)
        .catch(e => setError(e.message))
        .finally(() => setLoading(false))
    }
  }, [geo.latitude, geo.longitude, geo.loading])

  return {
    data,
    loading: loading || geo.loading,
    error: error || geo.error,
    withinRadius: data?.within_radius ?? false,
    charger: data?.charger ?? null,
    distance: data?.distance_m ?? null
  }
}
```

**File:** `nerava-ui 2/src/hooks/useChargerDiscovery.ts`

```typescript
import { useState, useEffect } from 'react'
import { discoverChargers, ChargerDiscoverResponse } from '../api/chargers'
import { useGeolocation } from './useGeolocation'

export function useChargerDiscovery() {
  const geo = useGeolocation()
  const [data, setData] = useState<ChargerDiscoverResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (geo.latitude && geo.longitude && !geo.loading) {
      setLoading(true)
      discoverChargers(geo.latitude, geo.longitude)
        .then(setData)
        .catch(e => setError(e.message))
        .finally(() => setLoading(false))
    }
  }, [geo.latitude, geo.longitude, geo.loading])

  return {
    chargers: data?.chargers ?? [],
    loading: loading || geo.loading,
    error: error || geo.error
  }
}
```

### 3. Update PreChargingScreen

**File:** `nerava-ui 2/src/components/PreCharging/PreChargingScreen.tsx`

Replace mock data with API calls:

```typescript
import { useChargerDiscovery } from '../../hooks/useChargerDiscovery'

export function PreChargingScreen() {
  const { chargers, loading, error } = useChargerDiscovery()

  if (loading) {
    return <div className="flex items-center justify-center h-full">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500" />
    </div>
  }

  if (error) {
    return <div className="text-red-500 text-center p-4">{error}</div>
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">Find a charger near experiences</h2>

      {chargers.map(charger => (
        <ChargerCard
          key={charger.id}
          charger={charger}
        />
      ))}
    </div>
  )
}
```

### 4. Update ChargerCard

**File:** `nerava-ui 2/src/components/PreCharging/ChargerCard.tsx`

Update props to use real data:

```typescript
import { ChargerDiscoveryItem } from '../../api/chargers'

interface ChargerCardProps {
  charger: ChargerDiscoveryItem
}

export function ChargerCard({ charger }: ChargerCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden">
      {/* Hero photo */}
      {charger.photo_url && (
        <img
          src={charger.photo_url}
          alt={charger.name}
          className="w-full h-40 object-cover"
        />
      )}

      <div className="p-4">
        {/* Name + Rating */}
        <div className="flex justify-between items-start">
          <h3 className="font-semibold text-lg">{charger.name}</h3>
          {charger.rating && (
            <span className="text-sm text-gray-600">
              ⭐ {charger.rating.toFixed(1)} ({charger.rating_count})
            </span>
          )}
        </div>

        {/* Address */}
        <p className="text-sm text-gray-500 mt-1">{charger.address}</p>

        {/* Metadata */}
        <div className="flex gap-2 mt-2 text-xs text-gray-600">
          {charger.stalls && <span>{charger.stalls} stalls</span>}
          {charger.kw && <span>•</span>}
          {charger.kw && <span>{charger.kw} kW</span>}
          {charger.open_24_hours && <span>• Open 24 hours</span>}
        </div>

        {/* Drive time badge */}
        <div className="mt-2">
          <span className="inline-block bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded-full">
            {charger.drive_time_min} min drive
          </span>
        </div>

        {/* Nearby experiences */}
        {charger.nearby_experiences.length > 0 && (
          <div className="mt-3">
            <p className="text-xs text-gray-500 mb-2">Nearby experiences</p>
            <div className="flex gap-2">
              {charger.nearby_experiences.map(exp => (
                <div key={exp.place_id} className="relative w-20 h-16 rounded-lg overflow-hidden">
                  {exp.photo_url ? (
                    <img src={exp.photo_url} alt={exp.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full bg-gray-200" />
                  )}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 p-1">
                    <p className="text-white text-[10px] truncate">{exp.name}</p>
                  </div>
                  {exp.has_exclusive && (
                    <span className="absolute top-1 right-1 bg-yellow-400 text-[8px] px-1 rounded">⚡</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <button className="w-full mt-4 bg-purple-600 text-white py-2 rounded-lg text-sm font-medium">
          Navigate to Charger
        </button>
      </div>
    </div>
  )
}
```

### 5. Update App State Machine

**File:** `nerava-ui 2/src/App.tsx` or main component

Add state machine logic:

```typescript
import { useNearestCharger } from './hooks/useNearestCharger'

function DriverApp() {
  const { withinRadius, charger, loading } = useNearestCharger()

  if (loading) {
    return <LoadingScreen />
  }

  // State machine: Pre-Charge vs Charging
  if (withinRadius && charger) {
    // User is within 400m of a charger - show charging experience
    return <WhileYouChargeScreen chargerId={charger.id} />
  } else {
    // User is outside 400m - show charger discovery
    return <PreChargingScreen />
  }
}
```

---

## Validation Commands

### 1. Run Seed Script

```bash
cd /Users/jameskirk/Desktop/Nerava/backend
GOOGLE_PLACES_API_KEY="AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg" \
PYTHONPATH=/Users/jameskirk/Desktop/Nerava/backend \
python3 -m scripts.seed_austin_chargers
```

### 2. Verify Chargers Seeded

```bash
curl -s "http://localhost:8001/v1/chargers/discover?lat=30.27&lng=-97.74" | python3 -m json.tool
```

Expected: 5 chargers sorted by distance, each with 2 nearby_experiences

### 3. Test Nearest Charger (Far)

```bash
# Downtown Austin - should be outside 400m of all chargers
curl -s "http://localhost:8001/v1/chargers/nearest?lat=30.27&lng=-97.74" | python3 -m json.tool
```

Expected: `within_radius: false`

### 4. Test Nearest Charger (Near Canyon Ridge)

```bash
# Near Canyon Ridge charger - should be within 400m
curl -s "http://localhost:8001/v1/chargers/nearest?lat=30.4027&lng=-97.6719" | python3 -m json.tool
```

Expected: `within_radius: true`, charger = Canyon Ridge

### 5. Verify Photos Downloaded

```bash
ls -la /Users/jameskirk/Desktop/Nerava/backend/static/seed_photos/
```

### 6. Manual UI Verification

1. Start backend: `uvicorn app.main_simple:app --reload --port 8001`
2. Start frontend: `cd nerava-ui\ 2 && npm run dev`
3. Open browser with mock location far from chargers
4. Verify: Charger Discovery screen shows 5 chargers with photos
5. Set mock location to Canyon Ridge: `?mock=charger`
6. Verify: Charging screen shows with merchants

---

## Acceptance Criteria Checklist

- [ ] 5 chargers seeded (Canyon Ridge + 4 Tesla Superchargers)
- [ ] Each charger has 10-12 nearby merchants with photos
- [ ] `/v1/chargers/discover` returns chargers sorted by distance
- [ ] `/v1/chargers/nearest` returns `within_radius: true/false` based on 400m
- [ ] Photos served from `/static/seed_photos/`
- [ ] Frontend shows Charger Discovery when outside 400m
- [ ] Frontend shows Charging experience when within 400m
- [ ] Charger cards show photo, name, address, drive time, 2 nearby experiences
- [ ] Seed script is idempotent (can run multiple times)

---

## Constraints (DO NOT VIOLATE)

1. **No ELB/ALB** - We're using App Runner, not ECS
2. **No long-term photo pipeline** - Static files only
3. **No background jobs** - Synchronous seed script
4. **No unrelated UI changes** - Scope to charger discovery only
5. **Deterministic seed** - Same data every time, no random generation
