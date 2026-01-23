#!/usr/bin/env python3
"""
Check if a restaurant is within the search radius of a charger
"""
import sys
import os
import httpx
import asyncio
import math

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

# Charger location from previous search
CHARGER_LAT = 29.726346
CHARGER_LNG = -98.078351
SEARCH_RADIUS_M = 830  # 10-minute walk


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


async def geocode_address(address: str, api_key: str) -> tuple[float, float, str]:
    """Geocode an address to lat/lng"""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            raise ValueError(f"Geocoding failed: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
        
        location = data["results"][0]["geometry"]["location"]
        formatted_address = data["results"][0]["formatted_address"]
        
        return location["lat"], location["lng"], formatted_address


async def search_place_by_address(address: str, api_key: str):
    """Search for a place by address using Places API"""
    url = "https://places.googleapis.com/v1/places:searchText"
    
    payload = {
        "textQuery": address,
        "maxResultCount": 5,
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
    
    # Get API key from command line if provided
    api_key = API_KEY
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("ERROR: Google Places API key required")
        print("Usage: python check_restaurant_location.py [API_KEY]")
        return 1
    
    print("=" * 80)
    print("CHECKING RESTAURANT LOCATION")
    print("=" * 80)
    print(f"Restaurant Address: {restaurant_address}")
    print(f"Charger Location: 2760 I-35, New Braunfels, TX 78130")
    print(f"Charger Coordinates: {CHARGER_LAT}, {CHARGER_LNG}")
    print(f"Search Radius: {SEARCH_RADIUS_M}m (~{SEARCH_RADIUS_M/1609.34:.2f} miles)")
    print()
    
    # Geocode the restaurant address
    print("Geocoding restaurant address...")
    try:
        rest_lat, rest_lng, formatted_address = await geocode_address(restaurant_address, api_key)
        print(f"Restaurant Coordinates: {rest_lat:.6f}, {rest_lng:.6f}")
        print(f"Formatted Address: {formatted_address}")
        print()
    except Exception as e:
        print(f"Error geocoding: {e}")
        return 1
    
    # Calculate distance
    distance_m = haversine_distance(CHARGER_LAT, CHARGER_LNG, rest_lat, rest_lng)
    distance_miles = distance_m / 1609.34
    walking_time = round(distance_m / 83, 1)  # 83 m/min walking speed
    
    print("=" * 80)
    print("DISTANCE ANALYSIS")
    print("=" * 80)
    print(f"Distance from charger: {distance_m:.0f}m ({distance_miles:.2f} miles)")
    print(f"Walking time: ~{walking_time} minutes")
    print(f"Search radius: {SEARCH_RADIUS_M}m")
    print()
    
    if distance_m <= SEARCH_RADIUS_M:
        print(f"✓ Restaurant IS within the search radius!")
        print(f"  It should have appeared in the results.")
        print()
        print("Possible reasons it wasn't included:")
        print("  1. Google Places API may not have it categorized as a merchant type")
        print("     we're searching for (restaurant, cafe, etc.)")
        print("  2. The place might not be in Google's Places database")
        print("  3. The search may have hit the 20 result limit")
    else:
        print(f"✗ Restaurant is OUTSIDE the search radius")
        print(f"  Distance: {distance_m:.0f}m > {SEARCH_RADIUS_M}m")
        print(f"  It's {distance_m - SEARCH_RADIUS_M:.0f}m beyond the 10-minute walk radius")
    
    print()
    
    # Try to find the place in Google Places
    print("Searching Google Places for this address...")
    try:
        places = await search_place_by_address(restaurant_address, api_key)
        if places:
            print(f"Found {len(places)} matching places:")
            for i, place in enumerate(places, 1):
                name = place.get("displayName", {}).get("text", "Unknown")
                location = place.get("location", {})
                place_lat = location.get("latitude", 0)
                place_lng = location.get("longitude", 0)
                types = place.get("types", [])
                formatted_addr = place.get("formattedAddress", "")
                
                # Calculate distance
                place_distance = haversine_distance(CHARGER_LAT, CHARGER_LNG, place_lat, place_lng)
                
                print(f"\n{i}. {name}")
                print(f"   Address: {formatted_addr}")
                print(f"   Coordinates: {place_lat:.6f}, {place_lng:.6f}")
                print(f"   Distance from charger: {place_distance:.0f}m")
                print(f"   Types: {', '.join(types[:5])}")
        else:
            print("No places found in Google Places API")
    except Exception as e:
        print(f"Error searching Places API: {e}")
        import traceback
        traceback.print_exc()
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

