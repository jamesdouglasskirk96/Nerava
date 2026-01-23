#!/usr/bin/env python3
"""
Find walkable merchants near a charging station using Google Places API
"""
import sys
import os
import json
import math
import ssl
from urllib.request import urlopen, Request
from urllib.parse import urlencode

# Disable SSL verification for local testing (not recommended for production)
ssl._create_default_https_context = ssl._create_unverified_context

# Use environment variable with hardcoded fallback
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg")

def geocode_address(address):
    """Geocode an address to lat/lng"""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = urlencode({"address": address, "key": API_KEY})
    
    req = Request(f"{url}?{params}")
    with urlopen(req, timeout=10) as response:
        data = json.loads(response.read())
        
        if data.get("status") != "OK" or not data.get("results"):
            raise ValueError(f"Geocoding failed: {data.get('status')}")
        
        location = data["results"][0]["geometry"]["location"]
        formatted_address = data["results"][0]["formatted_address"]
        
        return location["lat"], location["lng"], formatted_address


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def search_nearby_places(lat, lng, radius_m=800):
    """Search for nearby places using Google Places API (New)"""
    import urllib.request
    import json
    
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
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.types,places.iconMaskBaseUri,places.photos,places.rating,places.priceLevel"
    }
    
    req = Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    
    with urlopen(req, timeout=12) as response:
        data = json.loads(response.read())
        return data.get("places", [])


def main():
    if len(sys.argv) > 1:
        address = sys.argv[1]
    else:
        address = "500 W Canyon Ridge Dr, Austin, TX 78753"
    
    print("=" * 80)
    print("FINDING WALKABLE MERCHANTS NEAR CHARGING STATION")
    print("=" * 80)
    print(f"Address: {address}")
    print()
    
    # Geocode address
    print("Geocoding address...")
    try:
        lat, lng, formatted_address = geocode_address(address)
        print(f"Coordinates: {lat}, {lng}")
        print(f"Formatted: {formatted_address}")
        print()
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    # Search for nearby places
    print(f"Searching for walkable merchants (800m radius)...")
    try:
        places = search_nearby_places(lat, lng, radius_m=800)
        print(f"Found {len(places)} places")
        print()
    except Exception as e:
        print(f"Error searching places: {e}")
        return 1
    
    # Process and sort results
    results = []
    for place in places:
        place_id = place.get("id", "").replace("places/", "")
        display_name = place.get("displayName", {})
        name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)
        location = place.get("location", {})
        place_lat = location.get("latitude", 0)
        place_lng = location.get("longitude", 0)
        types = place.get("types", [])
        rating = place.get("rating")
        price_level = place.get("priceLevel")
        icon_uri = place.get("iconMaskBaseUri", "")
        photos = place.get("photos", [])
        
        # Get photo URL if available
        photo_url = None
        if photos and len(photos) > 0:
            # Photos are returned as references that need to be resolved
            photo_ref = photos[0].get("name", "").replace("places/", "")
            if photo_ref:
                # For display, we can construct a photo URL using the old API format
                # or use the icon as fallback
                photo_url = f"Photo available (ref: {photo_ref[:20]}...)"
        
        distance_m = haversine_distance(lat, lng, place_lat, place_lng)
        
        results.append({
            "name": name,
            "place_id": place_id,
            "distance_m": round(distance_m),
            "types": types,
            "rating": rating,
            "price_level": price_level,
            "lat": place_lat,
            "lng": place_lng,
            "icon_uri": icon_uri,
            "photo_url": photo_url,
            "has_photos": len(photos) > 0 if photos else False,
        })
    
    # Sort by distance
    results.sort(key=lambda x: x["distance_m"])
    
    # Print results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    
    for i, merchant in enumerate(results, 1):
        print(f"{i}. {merchant['name']}")
        print(f"   Distance: {merchant['distance_m']}m ({merchant['distance_m']/1609.34:.2f} miles)")
        print(f"   Types: {', '.join(merchant['types'][:3])}")
        if merchant.get("rating"):
            print(f"   Rating: {merchant['rating']}/5.0")
        if merchant.get("price_level"):
            price_level = merchant['price_level']
            if isinstance(price_level, (int, float)):
                print(f"   Price Level: {'$' * int(price_level)}")
            else:
                print(f"   Price Level: {price_level}")
        
        # Show logo/icon information
        if merchant.get("icon_uri"):
            print(f"   Icon/Logo: {merchant['icon_uri']}")
        if merchant.get("has_photos"):
            print(f"   Photos: Available (can be retrieved via Places API)")
        
        print(f"   Place ID: {merchant['place_id']}")
        print()
    
    print(f"Total: {len(results)} walkable merchants found")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

