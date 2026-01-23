#!/usr/bin/env python3
"""
Check why Las Palapas - Town Center wasn't in the results
"""
import sys
import os
import httpx
import asyncio
import math

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

# Charger location
CHARGER_LAT = 29.726346
CHARGER_LNG = -98.078351
SEARCH_RADIUS_M = 830


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters"""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


async def search_by_name(query: str, lat: float, lng: float, api_key: str):
    """Search for places by name near a location"""
    url = "https://places.googleapis.com/v1/places:searchText"
    
    payload = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": 1000  # 1km radius
            }
        },
        "maxResultCount": 10,
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,places.formattedAddress,places.rating"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("places", [])


async def check_in_nearby_search(lat: float, lng: float, radius_m: int, api_key: str, target_place_id: str):
    """Check if a place would be found in a nearby search"""
    url = "https://places.googleapis.com/v1/places:searchNearby"
    
    payload = {
        "includedTypes": [
            "restaurant",
            "cafe",
            "meal_takeaway",
            "shopping_mall",
            "clothing_store",
            "department_store",
            "supermarket",
            "bar",
            "tourist_attraction",
            "movie_theater",
            "book_store",
            "gym",
            "convenience_store",
            "pharmacy",
            "gas_station",
            "bank",
            "atm",
            "store",
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
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        places = data.get("places", [])
        
        # Check if target is in results
        for place in places:
            place_id = place.get("id", "").replace("places/", "")
            if place_id == target_place_id:
                return True, place
        return False, None


async def main():
    business_name = "Las Palapas - Town Center"
    
    api_key = API_KEY
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("ERROR: Google Places API key required")
        return 1
    
    print("=" * 80)
    print("CHECKING LAS PALAPAS - TOWN CENTER")
    print("=" * 80)
    print(f"Business Name: {business_name}")
    print(f"Charger Location: {CHARGER_LAT}, {CHARGER_LNG}")
    print(f"Search Radius: {SEARCH_RADIUS_M}m")
    print()
    
    # Search for the business by name
    print("1. Searching for business by name...")
    try:
        places = await search_by_name(business_name, CHARGER_LAT, CHARGER_LNG, api_key)
        if places:
            for i, place in enumerate(places, 1):
                name = place.get("displayName", {}).get("text", "Unknown")
                location = place.get("location", {})
                place_lat = location.get("latitude", 0)
                place_lng = location.get("longitude", 0)
                types = place.get("types", [])
                addr = place.get("formattedAddress", "")
                place_id = place.get("id", "").replace("places/", "")
                rating = place.get("rating")
                
                distance = haversine_distance(CHARGER_LAT, CHARGER_LNG, place_lat, place_lng)
                
                print(f"\n{i}. {name}")
                print(f"   Address: {addr}")
                print(f"   Coordinates: {place_lat:.6f}, {place_lng:.6f}")
                print(f"   Distance from charger: {distance:.0f}m ({distance/1609.34:.2f} miles)")
                print(f"   Walking time: ~{round(distance/83, 1)} minutes")
                print(f"   Types: {', '.join(types)}")
                if rating:
                    print(f"   Rating: {rating}/5.0")
                print(f"   Place ID: {place_id}")
                
                # Check if it's within radius
                if distance <= SEARCH_RADIUS_M:
                    print(f"   ✓ WITHIN search radius!")
                else:
                    print(f"   ✗ OUTSIDE search radius ({distance - SEARCH_RADIUS_M:.0f}m too far)")
                
                # Check if it would be found in nearby search
                print(f"\n2. Checking if it appears in nearby search...")
                found, place_data = await check_in_nearby_search(CHARGER_LAT, CHARGER_LNG, SEARCH_RADIUS_M, api_key, place_id)
                
                if found:
                    print(f"   ✓ Found in nearby search!")
                    print(f"   Types in search: {', '.join(place_data.get('types', []))}")
                else:
                    print(f"   ✗ NOT found in nearby search")
                    print(f"   Reason: Business types {', '.join(types)} don't match search filters")
                    print(f"   Search looks for: restaurant, cafe, meal_takeaway, store, etc.")
                    
                    # Check if any types match
                    search_types = ["restaurant", "cafe", "meal_takeaway", "store", "bar", "fast_food_restaurant"]
                    matching_types = [t for t in types if t in search_types]
                    if matching_types:
                        print(f"   However, it HAS matching types: {', '.join(matching_types)}")
                        print(f"   This suggests it might have been excluded due to the 20 result limit")
                    else:
                        print(f"   No matching types found - this is why it's excluded")
        else:
            print("  No results found")
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)



