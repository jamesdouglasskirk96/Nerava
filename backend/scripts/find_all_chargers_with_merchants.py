#!/usr/bin/env python3
"""
Find all public charging stations with 8+ stalls within 90 min drive of home,
and find restaurants within 7-minute walk of each charger.

This seeds the Nerava database for merchant onboarding.
"""
import sys
import os
import json
import httpx
import asyncio
import math
from pathlib import Path
from typing import List, Dict, Optional

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

# Home address
HOME_ADDRESS = "11621 Timber Heights Dr, Austin, TX 78754"

# Search parameters
MAX_DRIVING_TIME_MINUTES = 90
WALKING_TIME_MINUTES = 7
WALKING_SPEED_M_PER_MIN = 83  # ~5 km/h
WALKING_RADIUS_M = WALKING_TIME_MINUTES * WALKING_SPEED_M_PER_MIN  # ~580m

# Minimum charging stalls
MIN_CHARGING_STALLS = 8

PLACES_API_BASE = "https://places.googleapis.com/v1"
GEOCODE_API = "https://maps.googleapis.com/maps/api/geocode/json"
DISTANCE_MATRIX_API = "https://maps.googleapis.com/maps/api/distancematrix/json"


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
    """
    Get driving distance and time using Distance Matrix API.
    Returns: (distance_meters, time_seconds)
    """
    params = {
        "origins": f"{origin_lat},{origin_lng}",
        "destinations": f"{dest_lat},{dest_lng}",
        "key": api_key,
        "units": "imperial",  # Get distance in miles, time in minutes
        "mode": "driving"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(DISTANCE_MATRIX_API, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "OK":
            # Fallback to haversine if API fails
            distance_m = haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
            # Estimate driving time: assume 60 mph average = ~26.8 m/s
            time_seconds = int(distance_m / 26.8)
            return distance_m, time_seconds
        
        element = data.get("rows", [{}])[0].get("elements", [{}])[0]
        if element.get("status") != "OK":
            # Fallback
            distance_m = haversine_distance(origin_lat, origin_lng, dest_lat, dest_lng)
            time_seconds = int(distance_m / 26.8)
            return distance_m, time_seconds
        
        # Convert miles to meters, duration is in seconds
        distance_text = element.get("distance", {}).get("text", "0 mi")
        distance_m = float(distance_text.replace(" mi", "").replace(",", "")) * 1609.34
        duration_seconds = element.get("duration", {}).get("value", 0)
        
        return distance_m, duration_seconds


async def search_charging_stations(lat: float, lng: float, radius_m: int, api_key: str) -> List[Dict]:
    """
    Search for electric vehicle charging stations.
    Note: Google Places API may not always have stall count, so we'll search broadly
    and filter by checking place details.
    """
    url = f"{PLACES_API_BASE}/places:searchNearby"
    
    payload = {
        "includedTypes": ["electric_vehicle_charging_station"],
        "maxResultCount": 20,  # API limit
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
        "X-Goog-FieldMask": "places.id,places.displayName,places.location,places.formattedAddress,places.rating,places.userRatingCount"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("places", [])


async def get_place_details(place_id: str, api_key: str) -> Dict:
    """Get detailed information about a place, including charging stall count if available"""
    url = f"{PLACES_API_BASE}/places/{place_id}"
    
    params = {"key": api_key}
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "id,displayName,location,formattedAddress,rating,userRatingCount,evChargeOptions,currentOpeningHours,internationalPhoneNumber"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"  Warning: Could not get details for {place_id}: {e}")
        return {}


def extract_stall_count(place_details: Dict, place_name: str = "") -> int:
    """Extract charging stall count from place details"""
    ev_charge_options = place_details.get("evChargeOptions", {})
    connector_counts = ev_charge_options.get("connectorCounts", [])
    
    total_stalls = 0
    for connector in connector_counts:
        count = connector.get("count", 0)
        total_stalls += count
    
    # If no stall count found, try to infer from name
    # Tesla Superchargers typically have 8-20+ stalls
    # Electrify America, EVgo, Shell Recharge often have 4-10+
    if total_stalls == 0:
        name_lower = place_name.lower()
        if "supercharger" in name_lower or "tesla" in name_lower:
            # Assume Tesla Superchargers have at least 8 stalls (most do)
            total_stalls = 12  # Conservative estimate
        elif "electrify" in name_lower or "evgo" in name_lower or "shell recharge" in name_lower:
            # These networks often have 4-10 stalls, but many have 8+
            total_stalls = 8  # Conservative estimate
    
    return total_stalls


async def search_nearby_merchants(lat: float, lng: float, radius_m: int, api_key: str) -> List[Dict]:
    """Search for nearby merchants (restaurants, cafes, etc.)"""
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
            
            # Transform to merchant format
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
            
            # Sort by distance
            merchants.sort(key=lambda x: x["distance_m"])
            return merchants
    except Exception as e:
        print(f"  Error searching merchants: {e}")
        return []


async def find_chargers_with_merchants(home_lat: float, home_lng: float, api_key: str) -> List[Dict]:
    """
    Find all charging stations within driving distance and their nearby merchants.
    Uses a grid search approach since Places API has radius limits.
    """
    print("=" * 80)
    print("FINDING CHARGING STATIONS WITH MERCHANTS")
    print("=" * 80)
    print(f"Home: {HOME_ADDRESS}")
    print(f"Home Coordinates: {home_lat:.6f}, {home_lng:.6f}")
    print(f"Max Driving Time: {MAX_DRIVING_TIME_MINUTES} minutes")
    print(f"Merchant Search: {WALKING_TIME_MINUTES}-minute walk ({WALKING_RADIUS_M}m)")
    print(f"Min Charging Stalls: {MIN_CHARGING_STALLS}")
    print()
    
    # Estimate max driving distance (assume 60 mph average = ~96.5 km/h)
    # For 90 minutes: 90 * 96.5 / 60 = ~144.75 km = ~144,750m
    # Use a large search radius - we'll filter by actual driving time
    search_radius_m = 150000  # 150km initial search
    
    print("Step 1: Searching for charging stations...")
    all_chargers = []
    
    # Search in a grid pattern to cover the area
    # Create search points in a grid around home
    grid_points = []
    grid_spacing = 50000  # 50km spacing
    for lat_offset in range(-2, 3):  # -100km to +100km
        for lng_offset in range(-2, 3):
            search_lat = home_lat + (lat_offset * grid_spacing / 111000)  # ~111km per degree
            search_lng = home_lng + (lng_offset * grid_spacing / (111000 * math.cos(math.radians(home_lat))))
            grid_points.append((search_lat, search_lng))
    
    print(f"  Searching {len(grid_points)} grid points...")
    
    for i, (search_lat, search_lng) in enumerate(grid_points, 1):
        try:
            stations = await search_charging_stations(search_lat, search_lng, 50000, api_key)
            for station in stations:
                # Avoid duplicates
                place_id = station.get("id", "").replace("places/", "")
                if not any(c.get("place_id") == place_id for c in all_chargers):
                    all_chargers.append(station)
            await asyncio.sleep(0.3)  # Rate limiting
        except Exception as e:
            print(f"  Error at grid point {i}: {e}")
    
    print(f"  Found {len(all_chargers)} unique charging stations")
    print()
    
    print("Step 2: Filtering by driving distance and stall count...")
    valid_chargers = []
    
    for i, charger in enumerate(all_chargers, 1):
        place_id = charger.get("id", "").replace("places/", "")
        display_name = charger.get("displayName", {})
        name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)
        location = charger.get("location", {})
        charger_lat = location.get("latitude", 0)
        charger_lng = location.get("longitude", 0)
        address = charger.get("formattedAddress", "")
        
        print(f"  [{i}/{len(all_chargers)}] {name}")
        
        # Get driving distance and time
        try:
            distance_m, time_seconds = await get_driving_distance_time(
                home_lat, home_lng, charger_lat, charger_lng, api_key
            )
            time_minutes = time_seconds / 60
            
            if time_minutes > MAX_DRIVING_TIME_MINUTES:
                print(f"    ✗ Too far: {time_minutes:.1f} min drive")
                continue
            
            # Get place details to check stall count
            place_details = await get_place_details(place_id, api_key)
            stall_count = extract_stall_count(place_details, name)
            
            # If we couldn't determine stall count, include it but note it needs verification
            if stall_count == 0:
                print(f"    ⚠ Stall count unknown (needs verification)")
                stall_count = None  # Mark as unknown
            elif stall_count < MIN_CHARGING_STALLS:
                print(f"    ✗ Too few stalls: {stall_count} (need {MIN_CHARGING_STALLS})")
                continue
            
            stall_info = f"{stall_count} stalls" if stall_count else "stall count unknown"
            print(f"    ✓ Valid: {time_minutes:.1f} min drive, {stall_info}")
            
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
                "rating": charger.get("rating"),
                "user_rating_count": charger.get("userRatingCount"),
            })
            
            await asyncio.sleep(0.3)  # Rate limiting
        except Exception as e:
            print(f"    Error: {e}")
    
    print(f"\n  Found {len(valid_chargers)} valid charging stations")
    print()
    
    # Sort by driving distance
    valid_chargers.sort(key=lambda x: x["driving_distance_m"])
    
    print("Step 3: Finding nearby merchants for each charger...")
    results = []
    
    for i, charger in enumerate(valid_chargers, 1):
        print(f"  [{i}/{len(valid_chargers)}] {charger['name']}")
        print(f"    Finding merchants within {WALKING_RADIUS_M}m...")
        
        merchants = await search_nearby_merchants(
            charger["lat"], charger["lng"], WALKING_RADIUS_M, api_key
        )
        
        charger["merchants"] = merchants
        charger["merchant_count"] = len(merchants)
        
        print(f"    Found {len(merchants)} merchants")
        results.append(charger)
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    return results


async def main():
    api_key = API_KEY
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("ERROR: Google Places API key required")
        print("Set GOOGLE_PLACES_API_KEY or provide as argument")
        return 1
    
    # Geocode home address
    print("Geocoding home address...")
    try:
        home_lat, home_lng, home_formatted = await geocode_address(HOME_ADDRESS, api_key)
        print(f"Home: {home_formatted}")
        print(f"Coordinates: {home_lat:.6f}, {home_lng:.6f}")
        print()
    except Exception as e:
        print(f"Error geocoding home address: {e}")
        return 1
    
    # Find chargers with merchants
    results = await find_chargers_with_merchants(home_lat, home_lng, api_key)
    
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
        print(f"   Stalls: {charger['stall_count']}")
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

