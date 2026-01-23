#!/usr/bin/env python3
"""
Find merchants within a 10-minute walk of a charger using Google Places API

Usage:
    python find_merchants_near_charger_standalone.py [API_KEY] [ADDRESS]
    
    Or set GOOGLE_PLACES_API_KEY environment variable:
    export GOOGLE_PLACES_API_KEY=your_key_here
    python find_merchants_near_charger_standalone.py "151 Evans Dr Suite 113, Kyle, TX 78640"
"""
import sys
import os
import json
import math
import httpx
import asyncio

# Default address
DEFAULT_ADDRESS = "151 Evans Dr Suite 113, Kyle, TX 78640"

# Walking speed: ~83 meters per minute (5 km/h)
WALKING_SPEED_M_PER_MIN = 83


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
    """Geocode an address to lat/lng using Google Geocoding API"""
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


async def search_nearby_places(lat: float, lng: float, radius_m: int, api_key: str) -> tuple[list, str]:
    """Search for nearby places using Google Places API (New)"""
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
        "maxResultCount": 20,  # API limit is 20
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m
            }
        }
    }
    
    # Use the same field mask as the existing service
    field_mask = "places.id,places.displayName,places.location,places.types,places.iconMaskBaseUri,places.photos"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            error_text = response.text
            print(f"API Error Response: {error_text}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                pass
        response.raise_for_status()
        data = response.json()
        return (data.get("places", []), api_key)


async def main():
    # Parse arguments
    api_key = None
    address = DEFAULT_ADDRESS
    
    # Check environment variable first
    api_key = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
    
    # Parse command line arguments
    args = sys.argv[1:]
    if args:
        # Check if first arg looks like an API key (starts with AIza and is long)
        if args[0].startswith("AIza") and len(args[0]) > 30:
            api_key = args[0]
            if len(args) > 1:
                address = " ".join(args[1:])
        else:
            address = " ".join(args)
    
    if not api_key:
        print("ERROR: Google Places API key required")
        print("\nUsage:")
        print("  python find_merchants_near_charger_standalone.py [API_KEY] [ADDRESS]")
        print("\nOr set environment variable:")
        print("  export GOOGLE_PLACES_API_KEY=your_key_here")
        print("  python find_merchants_near_charger_standalone.py \"151 Evans Dr Suite 113, Kyle, TX 78640\"")
        print("\nGet your API key from: https://console.cloud.google.com/google/maps-apis")
        return 1
    
    # Calculate radius for 10-minute walk
    walking_time_minutes = 10
    radius_m = walking_time_minutes * WALKING_SPEED_M_PER_MIN
    
    print("=" * 80)
    print("FINDING MERCHANTS NEAR CHARGER")
    print("=" * 80)
    print(f"Charger Address: {address}")
    print(f"Walking Time: {walking_time_minutes} minutes")
    print(f"Search Radius: {radius_m}m (~{radius_m/1609.34:.2f} miles)")
    print()
    
    # Geocode address
    print("Geocoding charger address...")
    try:
        lat, lng, formatted_address = await geocode_address(address, api_key)
        print(f"Coordinates: {lat:.6f}, {lng:.6f}")
        print(f"Formatted Address: {formatted_address}")
        print()
    except Exception as e:
        print(f"Error geocoding address: {e}")
        return 1
    
    # Search for nearby merchants
    print(f"Searching for merchants within {radius_m}m...")
    try:
        places, places_api_key = await search_nearby_places(lat, lng, radius_m, api_key)
        print(f"Found {len(places)} places")
        print()
    except Exception as e:
        print(f"Error searching for merchants: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    if not places:
        print("No merchants found within the search radius.")
        return 0
    
    # Process results
    results = []
    for place in places:
        place_id = place.get("id", "").replace("places/", "")
        display_name = place.get("displayName", {})
        name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)
        
        if not name or not place_id:
            continue
        
        location = place.get("location", {})
        place_lat = location.get("latitude", 0)
        place_lng = location.get("longitude", 0)
        types = place.get("types", [])
        rating = place.get("rating")
        price_level = place.get("priceLevel")
        phone = place.get("nationalPhoneNumber", "")
        
        # Calculate distance
        distance_m = haversine_distance(lat, lng, place_lat, place_lng)
        walking_time = round(distance_m / WALKING_SPEED_M_PER_MIN, 1)
        
        # Get photo info
        photos = place.get("photos", [])
        has_photos = len(photos) > 0 if photos else False
        
        # Extract photo references
        photo_references = []
        if photos:
            for photo in photos[:3]:  # Get up to 3 photo references
                photo_name = photo.get("name", "")
                if "/photos/" in photo_name:
                    # Extract photo reference: places/{place_id}/photos/{photo_reference}
                    photo_ref = photo_name.split("/photos/")[-1]
                    photo_references.append({
                        "photo_reference": photo_ref,
                        "photo_name": photo_name,
                        # Generate photo URL using old API format (works without additional API call)
                        "photo_url_400px": f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo_ref}&key={places_api_key}",
                        "photo_url_800px": f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference={photo_ref}&key={places_api_key}",
                    })
        
        results.append({
            "name": name,
            "place_id": place_id,
            "distance_m": round(distance_m),
            "walking_time_minutes": walking_time,
            "types": types,
            "rating": rating,
            "price_level": price_level,
            "phone": phone,
            "lat": place_lat,
            "lng": place_lng,
            "has_photos": has_photos,
            "photo_references": photo_references if photo_references else None,
        })
    
    # Sort by distance
    results.sort(key=lambda x: x["distance_m"])
    
    # Display results
    print("=" * 80)
    print("MERCHANTS WITHIN 10-MINUTE WALK")
    print("=" * 80)
    print()
    
    for i, merchant in enumerate(results, 1):
        name = merchant["name"]
        distance_m = merchant["distance_m"]
        distance_miles = distance_m / 1609.34
        walking_time = merchant["walking_time_minutes"]
        types = merchant["types"]
        types_str = ", ".join(types[:3])
        if len(types) > 3:
            types_str += f" (+{len(types) - 3} more)"
        
        print(f"{i}. {name}")
        print(f"   Distance: {distance_m}m ({distance_miles:.2f} miles)")
        print(f"   Walking Time: ~{walking_time} minutes")
        print(f"   Types: {types_str}")
        if merchant.get("rating"):
            print(f"   Rating: {merchant['rating']}/5.0")
        if merchant.get("price_level") is not None:
            price_level = merchant["price_level"]
            if isinstance(price_level, (int, float)):
                print(f"   Price Level: {'$' * int(price_level)}")
        if merchant.get("phone"):
            print(f"   Phone: {merchant['phone']}")
        if merchant.get("photo_references"):
            photo_refs = merchant["photo_references"]
            print(f"   Photos: {len(photo_refs)} available")
            for idx, photo in enumerate(photo_refs[:2], 1):  # Show first 2
                print(f"     Photo {idx} (400px): {photo['photo_url_400px'][:80]}...")
        print(f"   Place ID: {merchant['place_id']}")
        print(f"   Coordinates: {merchant['lat']:.6f}, {merchant['lng']:.6f}")
        print()
    
    print(f"Total: {len(results)} merchants found")
    
    # Save to JSON file
    output_file = "merchants_near_charger.json"
    output_data = {
        "charger_address": address,
        "charger_coordinates": {"lat": lat, "lng": lng},
        "walking_time_minutes": walking_time_minutes,
        "radius_m": radius_m,
        "merchants": results
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nResults saved to: {output_file}")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

