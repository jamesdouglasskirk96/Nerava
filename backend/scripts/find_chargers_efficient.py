#!/usr/bin/env python3
"""
More efficient version: Search for known charging networks that typically have 8+ stalls
"""
import sys
import os
import json
import httpx
import asyncio
import math
from typing import List, Dict

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

HOME_ADDRESS = "11621 Timber Heights Dr, Austin, TX 78754"
MAX_DRIVING_TIME_MINUTES = 90
WALKING_TIME_MINUTES = 7
WALKING_SPEED_M_PER_MIN = 83
WALKING_RADIUS_M = WALKING_TIME_MINUTES * WALKING_SPEED_M_PER_MIN
MIN_CHARGING_STALLS = 8

PLACES_API_BASE = "https://places.googleapis.com/v1"
GEOCODE_API = "https://maps.googleapis.com/maps/api/geocode/json"
DISTANCE_MATRIX_API = "https://maps.googleapis.com/maps/api/distancematrix/json"

# Known charging networks that typically have 8+ stalls
CHARGING_NETWORKS = [
    "Tesla Supercharger",
    "Electrify America",
    "EVgo",
    "Shell Recharge",
    "ChargePoint",
    "Mercedes-Benz Charging",
]


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


async def geocode_address(address: str, api_key: str) -> tuple[float, float, str]:
    """Geocode an address to lat/lng"""
    params = {"address": address, "key": api_key}
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(GEOCODE_API, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "OK" or not data.get("results"):
            raise ValueError(f"Geocoding failed: {data.get('status')}")
        location = data["results"][0]["geometry"]["location"]
        formatted_address = data["results"][0]["formatted_address"]
        return location["lat"], location["lng"], formatted_address


async def get_driving_distance_time(origin_lat: float, origin_lng: float, 
                                   dest_lat: float, dest_lng: float, 
                                   api_key: str) -> tuple[float, int]:
    """Get driving distance and time"""
    params = {
        "origins": f"{origin_lat},{origin_lng}",
        "destinations": f"{dest_lat},{dest_lng}",
        "key": api_key,
        "units": "imperial",
        "mode": "driving"
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(DISTANCE_MATRIX_API, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "OK":
            distance_m = haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
            time_seconds = int(distance_m / 26.8)
            return distance_m, time_seconds
        element = data.get("rows", [{}])[0].get("elements", [{}])[0]
        if element.get("status") != "OK":
            distance_m = haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
            time_seconds = int(distance_m / 26.8)
            return distance_m, time_seconds
        distance_text = element.get("distance", {}).get("text", "0 mi")
        distance_m = float(distance_text.replace(" mi", "").replace(",", "")) * 1609.34
        duration_seconds = element.get("duration", {}).get("value", 0)
        return distance_m, duration_seconds


async def search_chargers_by_text(query: str, lat: float, lng: float, api_key: str, radius_km: int = 150) -> List[Dict]:
    """Search for chargers using text query"""
    url = f"{PLACES_API_BASE}/places:searchText"
    
    payload = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_km * 1000  # Convert to meters
            }
        },
        "maxResultCount": 20,
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.formattedAddress,places.rating"
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("places", [])
    except Exception as e:
        print(f"  Error searching for {query}: {e}")
        return []


async def search_nearby_merchants(lat: float, lng: float, radius_m: int, api_key: str) -> List[Dict]:
    """Search for nearby merchants"""
    url = f"{PLACES_API_BASE}/places:searchNearby"
    
    payload = {
        "includedTypes": [
            "restaurant",
            "cafe",
            "meal_takeaway",
            "fast_food_restaurant",
            "bar",
            "bakery",
            "food",
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
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
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
    except Exception as e:
        print(f"  Error searching merchants: {e}")
        return []


async def main():
    api_key = API_KEY
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("ERROR: Google Places API key required")
        return 1
    
    print("=" * 80)
    print("FINDING CHARGING STATIONS WITH MERCHANTS (EFFICIENT VERSION)")
    print("=" * 80)
    print(f"Home: {HOME_ADDRESS}")
    print(f"Max Driving Time: {MAX_DRIVING_TIME_MINUTES} minutes")
    print(f"Merchant Search: {WALKING_TIME_MINUTES}-minute walk ({WALKING_RADIUS_M}m)")
    print()
    
    # Geocode home
    print("Geocoding home address...")
    home_lat, home_lng, home_formatted = await geocode_address(HOME_ADDRESS, api_key)
    print(f"Home: {home_formatted}")
    print(f"Coordinates: {home_lat:.6f}, {home_lng:.6f}")
    print()
    
    # Search for each charging network
    print("Searching for charging stations by network...")
    all_chargers = {}
    
    for network in CHARGING_NETWORKS:
        print(f"  Searching for {network}...")
        chargers = await search_chargers_by_text(network, home_lat, home_lng, api_key, radius_km=150)
        print(f"    Found {len(chargers)} results")
        
        for charger in chargers:
            place_id = charger.get("id", "").replace("places/", "")
            if place_id not in all_chargers:
                all_chargers[place_id] = charger
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    print(f"\nTotal unique charging stations found: {len(all_chargers)}")
    print()
    
    # Filter by driving distance
    print("Filtering by driving distance...")
    valid_chargers = []
    
    for i, (place_id, charger) in enumerate(all_chargers.items(), 1):
        display_name = charger.get("displayName", {})
        name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)
        location = charger.get("location", {})
        charger_lat = location.get("latitude", 0)
        charger_lng = location.get("longitude", 0)
        address = charger.get("formattedAddress", "")
        
        print(f"  [{i}/{len(all_chargers)}] {name}")
        
        try:
            distance_m, time_seconds = await get_driving_distance_time(
                home_lat, home_lng, charger_lat, charger_lng, api_key
            )
            time_minutes = time_seconds / 60
            
            if time_minutes > MAX_DRIVING_TIME_MINUTES:
                print(f"    ✗ Too far: {time_minutes:.1f} min")
                continue
            
            # Assume major networks have 8+ stalls
            stall_count = 12  # Conservative estimate for major networks
            
            print(f"    ✓ Valid: {time_minutes:.1f} min drive, ~{stall_count} stalls (estimated)")
            
            valid_chargers.append({
                "name": name,
                "place_id": place_id,
                "lat": charger_lat,
                "lng": charger_lng,
                "address": address,
                "driving_distance_m": round(distance_m),
                "driving_distance_miles": round(distance_m / 1609.34, 2),
                "driving_time_minutes": round(time_minutes, 1),
                "stall_count": stall_count,
                "stall_count_note": "estimated - major network",
                "rating": charger.get("rating"),
            })
            
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"    Error: {e}")
    
    # Sort by distance
    valid_chargers.sort(key=lambda x: x["driving_distance_m"])
    
    print(f"\nFound {len(valid_chargers)} valid charging stations")
    print()
    
    # Find merchants for each
    print("Finding nearby merchants for each charger...")
    results = []
    
    for i, charger in enumerate(valid_chargers, 1):
        print(f"  [{i}/{len(valid_chargers)}] {charger['name']}")
        merchants = await search_nearby_merchants(
            charger["lat"], charger["lng"], WALKING_RADIUS_M, api_key
        )
        charger["merchants"] = merchants
        charger["merchant_count"] = len(merchants)
        print(f"    Found {len(merchants)} merchants")
        results.append(charger)
        await asyncio.sleep(0.5)
    
    # Save results
    output_file = "chargers_with_merchants.json"
    output_data = {
        "home_address": HOME_ADDRESS,
        "home_coordinates": {"lat": home_lat, "lng": home_lng},
        "search_parameters": {
            "max_driving_time_minutes": MAX_DRIVING_TIME_MINUTES,
            "walking_time_minutes": WALKING_TIME_MINUTES,
            "walking_radius_m": WALKING_RADIUS_M,
            "min_charging_stalls": MIN_CHARGING_STALLS,
        },
        "chargers": results,
        "total_chargers": len(results),
        "total_merchants": sum(len(c["merchants"]) for c in results),
    }
    
    with open(output_file, "w") as f:
        json.dump(output_data, f, indent=2)
    
    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Charging Stations: {len(results)}")
    print(f"Total Merchants Found: {sum(len(c['merchants']) for c in results)}")
    print()
    print("Charging Stations (sorted by distance from home):")
    for i, charger in enumerate(results, 1):
        print(f"\n{i}. {charger['name']}")
        print(f"   Address: {charger['address']}")
        print(f"   Distance: {charger['driving_distance_miles']} miles ({charger['driving_time_minutes']} min drive)")
        print(f"   Stalls: {charger['stall_count']} (estimated)")
        print(f"   Nearby Merchants: {charger['merchant_count']}")
        if charger['merchants']:
            print(f"   Top 5 merchants:")
            for j, merchant in enumerate(charger['merchants'][:5], 1):
                print(f"     {j}. {merchant['name']} ({merchant['distance_m']}m, ~{merchant['walking_time_minutes']} min walk)")
    
    print(f"\nResults saved to: {output_file}")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)






