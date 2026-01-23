#!/usr/bin/env python3
"""
Find merchants within a 10-minute walk of a charger using Google Places API
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Try loading from backend/.env, then root .env
    backend_dir = Path(__file__).parent.parent
    env_file = backend_dir / ".env"
    if not env_file.exists():
        env_file = backend_dir.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.google_places_new import search_nearby
from app.core.config import settings

# Try to use Google Geocoding API to get coordinates
async def geocode_address(address: str) -> tuple[float, float, str]:
    """Geocode an address to lat/lng using Google Geocoding API"""
    import httpx
    
    api_key = settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_PLACES_API_KEY not set in environment")
    
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": api_key}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            raise ValueError(f"Geocoding failed: {data.get('status')}")
        
        location = data["results"][0]["geometry"]["location"]
        formatted_address = data["results"][0]["formatted_address"]
        
        return location["lat"], location["lng"], formatted_address


async def find_merchants_near_charger(address: str, walking_time_minutes: int = 10):
    """
    Find all merchants within walking distance of a charger.
    
    Args:
        address: Charger address
        walking_time_minutes: Walking time in minutes (default 10)
    
    Returns:
        List of merchant dictionaries
    """
    # Calculate radius: average walking speed is ~5 km/h = ~83 m/min
    # For 10 minutes: 10 * 83 = 830 meters, round to 800m
    radius_m = walking_time_minutes * 83
    
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
        lat, lng, formatted_address = await geocode_address(address)
        print(f"Coordinates: {lat:.6f}, {lng:.6f}")
        print(f"Formatted Address: {formatted_address}")
        print()
    except Exception as e:
        print(f"Error geocoding address: {e}")
        return []
    
    # Check API key
    if not settings.GOOGLE_PLACES_API_KEY:
        print("ERROR: GOOGLE_PLACES_API_KEY not configured")
        print("Please set it in your environment or .env file")
        return []
    
    # Search for nearby merchants
    print(f"Searching for merchants within {radius_m}m...")
    try:
        merchants = await search_nearby(
            lat=lat,
            lng=lng,
            radius_m=radius_m,
            max_results=50  # Get more results to show all options
        )
        print(f"Found {len(merchants)} merchants")
        print()
    except Exception as e:
        print(f"Error searching for merchants: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    return merchants


def format_merchant(merchant: dict, index: int) -> str:
    """Format a merchant dictionary for display"""
    name = merchant.get("name", "Unknown")
    distance_m = merchant.get("distance_m", 0)
    distance_miles = distance_m / 1609.34
    types = merchant.get("types", [])
    place_id = merchant.get("place_id", "")
    lat = merchant.get("lat", 0)
    lng = merchant.get("lng", 0)
    
    # Format types (show first 3)
    types_str = ", ".join(types[:3])
    if len(types) > 3:
        types_str += f" (+{len(types) - 3} more)"
    
    # Calculate walking time (assuming 83 m/min)
    walking_time = round(distance_m / 83, 1)
    
    output = f"{index}. {name}\n"
    output += f"   Distance: {distance_m}m ({distance_miles:.2f} miles)\n"
    output += f"   Walking Time: ~{walking_time} minutes\n"
    output += f"   Types: {types_str}\n"
    output += f"   Coordinates: {lat:.6f}, {lng:.6f}\n"
    output += f"   Place ID: {place_id}\n"
    
    if merchant.get("photo_url"):
        photo_url = merchant["photo_url"]
        if not photo_url.startswith("photo_ref:"):
            output += f"   Photo URL: {photo_url}\n"
    
    return output


async def main():
    # Parse command line arguments
    address = "151 Evans Dr Suite 113, Kyle, TX 78640"
    api_key = None
    
    # Check for API key in environment first
    api_key = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
    
    # Parse command line arguments
    args = sys.argv[1:]
    if args:
        # Check if first arg looks like an API key (long alphanumeric string)
        if args[0].startswith("AIza") and len(args[0]) > 30:
            api_key = args[0]
            address = " ".join(args[1:]) if len(args) > 1 else address
        else:
            address = " ".join(args)
    
    # Set API key if provided
    if api_key:
        os.environ["GOOGLE_PLACES_API_KEY"] = api_key
        settings.GOOGLE_PLACES_API_KEY = api_key
    
    # Find merchants
    merchants = await find_merchants_near_charger(address, walking_time_minutes=10)
    
    if not merchants:
        print("No merchants found.")
        return 1
    
    # Sort by distance
    merchants.sort(key=lambda x: x.get("distance_m", float("inf")))
    
    # Display results
    print("=" * 80)
    print("MERCHANTS WITHIN 10-MINUTE WALK")
    print("=" * 80)
    print()
    
    for i, merchant in enumerate(merchants, 1):
        print(format_merchant(merchant, i))
        print()
    
    print(f"Total: {len(merchants)} merchants found")
    
    # Also save to JSON file
    output_file = "merchants_near_charger.json"
    with open(output_file, "w") as f:
        json.dump({
            "charger_address": address,
            "walking_time_minutes": 10,
            "radius_m": 830,
            "merchants": merchants
        }, f, indent=2)
    print(f"\nResults saved to: {output_file}")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

