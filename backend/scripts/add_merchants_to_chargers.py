#!/usr/bin/env python3
"""
Add merchants to existing charger results with better rate limiting
"""
import sys
import os
import json
import httpx
import asyncio
import math

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

WALKING_TIME_MINUTES = 7
WALKING_SPEED_M_PER_MIN = 83
WALKING_RADIUS_M = WALKING_TIME_MINUTES * WALKING_SPEED_M_PER_MIN

PLACES_API_BASE = "https://places.googleapis.com/v1"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


async def search_nearby_merchants(lat: float, lng: float, radius_m: int, api_key: str) -> list:
    """Search for nearby merchants with retry logic"""
    url = f"{PLACES_API_BASE}/places:searchNearby"
    
    payload = {
        "includedTypes": [
            "restaurant",
            "cafe",
            "meal_takeaway",
            "fast_food_restaurant",
            "bar",
            "bakery",
        ],
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,places.rating,places.formattedAddress"
    }
    
    # Retry logic
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    places = data.get("places", [])
                    merchants = []
                    for place in places:
                        place_id = place.get("id", "").replace("places/", "")
                        display_name = place.get("displayName", {})
                        name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)
                        location = place.get("location", {})
                        place_lat = location.get("latitude", 0)
                        place_lng = location.get("longitude", 0)
                        types = place.get("types", [])
                        rating = place.get("rating")
                        address = place.get("formattedAddress", "")
                        distance_m = haversine_distance(lat, lng, place_lat, place_lng)
                        merchants.append({
                            "name": name,
                            "place_id": place_id,
                            "lat": place_lat,
                            "lng": place_lng,
                            "distance_m": round(distance_m),
                            "walking_time_minutes": round(distance_m / WALKING_SPEED_M_PER_MIN, 1),
                            "types": types,
                            "rating": rating,
                            "address": address,
                        })
                    merchants.sort(key=lambda x: x["distance_m"])
                    return merchants
                elif response.status_code == 429:
                    # Rate limited - wait longer
                    wait_time = (attempt + 1) * 2
                    print(f"    Rate limited, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    error_text = response.text[:200]
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    print(f"    API error {response.status_code}: {error_text}")
                    return []
        except Exception as e:
            if attempt < 2:
                await asyncio.sleep(1)
                continue
            print(f"    Error: {e}")
            return []
    
    return []


async def main():
    api_key = API_KEY
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    if not api_key:
        print("ERROR: Google Places API key required")
        return 1
    
    # Load existing results
    input_file = "chargers_with_merchants.json"
    if not os.path.exists(input_file):
        print(f"ERROR: {input_file} not found")
        return 1
    
    with open(input_file, "r") as f:
        data = json.load(f)
    
    chargers = data.get("chargers", [])
    
    print("=" * 80)
    print("ADDING MERCHANTS TO CHARGING STATIONS")
    print("=" * 80)
    print(f"Total chargers: {len(chargers)}")
    print(f"Walking radius: {WALKING_RADIUS_M}m ({WALKING_TIME_MINUTES} minutes)")
    print()
    
    # Process each charger
    updated_count = 0
    for i, charger in enumerate(chargers, 1):
        # Skip if already has merchants
        if charger.get("merchants") and len(charger["merchants"]) > 0:
            print(f"  [{i}/{len(chargers)}] {charger['name']} - Already has {len(charger['merchants'])} merchants")
            continue
        
        print(f"  [{i}/{len(chargers)}] {charger['name']}")
        print(f"    Searching for merchants...")
        
        merchants = await search_nearby_merchants(
            charger["lat"], charger["lng"], WALKING_RADIUS_M, api_key
        )
        
        charger["merchants"] = merchants
        charger["merchant_count"] = len(merchants)
        
        if merchants:
            print(f"    ✓ Found {len(merchants)} merchants")
            updated_count += 1
        else:
            print(f"    ✗ No merchants found")
        
        # Rate limiting - wait between requests
        await asyncio.sleep(1.0)  # 1 second between requests
    
    # Update totals
    data["total_merchants"] = sum(len(c.get("merchants", [])) for c in chargers)
    
    # Save updated results
    output_file = "chargers_with_merchants.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Updated {updated_count} chargers with merchants")
    print(f"Total merchants found: {data['total_merchants']}")
    print(f"Results saved to: {output_file}")
    
    # Print sample results
    print()
    print("Sample results (first 10 chargers with merchants):")
    for charger in chargers[:10]:
        if charger.get("merchants"):
            print(f"\n{charger['name']}")
            print(f"  {charger['merchant_count']} merchants within {WALKING_TIME_MINUTES} min walk")
            for j, merchant in enumerate(charger['merchants'][:3], 1):
                print(f"    {j}. {merchant['name']} ({merchant['distance_m']}m)")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

