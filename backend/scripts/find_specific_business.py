#!/usr/bin/env python3
"""
Search for a specific business near a charger location
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


async def search_nearby_with_all_types(lat: float, lng: float, radius_m: int, api_key: str):
    """Search nearby with a broader set of types"""
    url = "https://places.googleapis.com/v1/places:searchNearby"
    
    # Expanded list of types to include more businesses
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
            "food",
            "establishment",  # This is a catch-all
            "point_of_interest",  # This too
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
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,places.formattedAddress"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("places", [])


async def search_by_text_nearby(query: str, lat: float, lng: float, api_key: str):
    """Search for places by text query near a location"""
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
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,places.formattedAddress"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("places", [])


async def main():
    restaurant_address = "151 Creekside Crossing, New Braunfels, TX 78130"
    
    api_key = API_KEY
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("ERROR: Google Places API key required")
        return 1
    
    print("=" * 80)
    print("SEARCHING FOR BUSINESS AT 151 CREEKSIDE CROSSING")
    print("=" * 80)
    print(f"Charger Location: {CHARGER_LAT}, {CHARGER_LNG}")
    print()
    
    # Try searching by address
    print("1. Searching by address '151 Creekside Crossing'...")
    try:
        places = await search_by_text_nearby("151 Creekside Crossing New Braunfels", CHARGER_LAT, CHARGER_LNG, api_key)
        if places:
            for place in places:
                name = place.get("displayName", {}).get("text", "Unknown")
                location = place.get("location", {})
                place_lat = location.get("latitude", 0)
                place_lng = location.get("longitude", 0)
                types = place.get("types", [])
                addr = place.get("formattedAddress", "")
                distance = haversine_distance(CHARGER_LAT, CHARGER_LNG, place_lat, place_lng)
                
                print(f"\nFound: {name}")
                print(f"  Address: {addr}")
                print(f"  Distance: {distance:.0f}m")
                print(f"  Types: {', '.join(types)}")
                print(f"  Place ID: {place.get('id', 'N/A')}")
        else:
            print("  No results found")
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # Try searching nearby with broader types
    print("2. Searching nearby with expanded business types...")
    try:
        places = await search_nearby_with_all_types(CHARGER_LAT, CHARGER_LNG, 830, api_key)
        print(f"Found {len(places)} places")
        
        # Check if any are near 151 Creekside Crossing
        target_lat, target_lng = 29.727574, -98.075825
        for place in places:
            location = place.get("location", {})
            place_lat = location.get("latitude", 0)
            place_lng = location.get("longitude", 0)
            distance_to_target = haversine_distance(target_lat, target_lng, place_lat, place_lng)
            
            if distance_to_target < 50:  # Within 50m of the address
                name = place.get("displayName", {}).get("text", "Unknown")
                types = place.get("types", [])
                print(f"\n  Match found: {name}")
                print(f"    Types: {', '.join(types)}")
                print(f"    Distance from 151 Creekside: {distance_to_target:.0f}m")
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print("The address '151 Creekside Crossing' is within the search radius (280m)")
    print("but it's not appearing because:")
    print("1. Google Places only has it categorized as 'premise, street_address'")
    print("2. Our search filters for specific business types (restaurant, cafe, etc.)")
    print("3. 'premise' and 'street_address' are not in our included types list")
    print()
    print("To include it, we would need to:")
    print("- Add 'premise' to the includedTypes list (but this would return")
    print("  many non-business addresses)")
    print("- Or search by text query instead of by type")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)



