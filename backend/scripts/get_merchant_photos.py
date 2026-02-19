#!/usr/bin/env python3
"""
Get photo URLs for merchants from Google Places API

This script reads the merchants_near_charger.json file and fetches actual photo URLs
for merchants that have photos available.
"""
import sys
import os
import json
import httpx
import asyncio
from pathlib import Path

# Default API key (can be overridden via environment variable)
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

# Google Places API endpoints
PLACES_API_NEW_BASE = "https://places.googleapis.com/v1"
PLACES_API_OLD_BASE = "https://maps.googleapis.com/maps/api/place"


async def get_photo_url_new_api(place_id: str, photo_reference: str, api_key: str, max_width: int = 400) -> str:
    """
    Get photo URL using Google Places API (New) GetPhotoMedia endpoint.
    
    Args:
        place_id: Google Places place ID
        photo_reference: Photo reference from place data
        api_key: Google Places API key
        max_width: Maximum width in pixels
    
    Returns:
        Photo URL string
    """
    # Format: places/{place_id}/photos/{photo_reference}
    photo_name = f"places/{place_id}/photos/{photo_reference}"
    url = f"{PLACES_API_NEW_BASE}/{photo_name}/media"
    
    params = {
        "maxWidthPx": max_width,
        "key": api_key,
    }
    
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "photoUri",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            photo_uri = data.get("photoUri")
            if photo_uri:
                return photo_uri
    except Exception as e:
        print(f"  Warning: New API failed for {place_id}: {e}")
    
    # Fallback to old API format
    return f"{PLACES_API_OLD_BASE}/photo?maxwidth={max_width}&photoreference={photo_reference}&key={api_key}"


async def get_photo_url_old_api(photo_reference: str, api_key: str, max_width: int = 400) -> str:
    """
    Get photo URL using Google Places API (Old) format.
    
    Args:
        photo_reference: Photo reference from place data
        api_key: Google Places API key
        max_width: Maximum width in pixels
    
    Returns:
        Photo URL string
    """
    return f"{PLACES_API_OLD_BASE}/photo?maxwidth={max_width}&photoreference={photo_reference}&key={api_key}"


async def fetch_place_details(place_id: str, api_key: str) -> dict:
    """
    Fetch place details including photos using Google Places API (New).
    
    Args:
        place_id: Google Places place ID
        api_key: Google Places API key
    
    Returns:
        Place details dictionary with photos
    """
    url = f"{PLACES_API_NEW_BASE}/places/{place_id}"
    
    params = {
        "key": api_key,
    }
    
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "id,displayName,photos",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"  Error fetching place details for {place_id}: {e}")
        return {}


async def get_photos_for_merchant(merchant: dict, api_key: str) -> list:
    """
    Get photo URLs for a merchant.
    
    Args:
        merchant: Merchant dictionary with place_id
        api_key: Google Places API key
    
    Returns:
        List of photo URL dictionaries with different sizes
    """
    place_id = merchant.get("place_id", "")
    if not place_id:
        return []
    
    # Fetch place details to get photo references
    place_details = await fetch_place_details(place_id, api_key)
    photos_data = place_details.get("photos", [])
    
    if not photos_data:
        return []
    
    photo_urls = []
    for i, photo in enumerate(photos_data[:5]):  # Get up to 5 photos
        # Extract photo reference from the photo name
        # Format: places/{place_id}/photos/{photo_reference}
        photo_name = photo.get("name", "")
        if "/photos/" in photo_name:
            photo_reference = photo_name.split("/photos/")[-1]
        else:
            continue
        
        # Get different sizes
        sizes = [
            ("small", 200),
            ("medium", 400),
            ("large", 800),
        ]
        
        for size_name, max_width in sizes:
            try:
                photo_url = await get_photo_url_new_api(place_id, photo_reference, api_key, max_width)
                photo_urls.append({
                    "index": i + 1,
                    "size": size_name,
                    "width": max_width,
                    "url": photo_url,
                    "photo_reference": photo_reference,
                })
            except Exception as e:
                print(f"  Warning: Failed to get {size_name} photo: {e}")
    
    return photo_urls


async def main():
    if not API_KEY:
        print("ERROR: Google Places API key required")
        print("Set GOOGLE_PLACES_API_KEY environment variable or provide as argument")
        return 1
    
    # Read merchants JSON file
    json_file = Path("backend/merchants_near_charger.json")
    if not json_file.exists():
        json_file = Path("merchants_near_charger.json")
    
    if not json_file.exists():
        print(f"ERROR: Could not find {json_file}")
        return 1
    
    with open(json_file, "r") as f:
        data = json.load(f)
    
    merchants = data.get("merchants", [])
    
    print("=" * 80)
    print("FETCHING PHOTO URLs FOR MERCHANTS")
    print("=" * 80)
    print(f"Found {len(merchants)} merchants")
    print()
    
    # Filter merchants with photos
    merchants_with_photos = [m for m in merchants if m.get("has_photos")]
    print(f"Merchants with photos: {len(merchants_with_photos)}")
    print()
    
    # Fetch photos for each merchant
    results = []
    for i, merchant in enumerate(merchants_with_photos, 1):
        name = merchant.get("name", "Unknown")
        place_id = merchant.get("place_id", "")
        
        print(f"{i}. {name} ({place_id})")
        print("   Fetching photos...")
        
        try:
            photo_urls = await get_photos_for_merchant(merchant, API_KEY)
            if photo_urls:
                merchant["photo_urls"] = photo_urls
                print(f"   ✓ Found {len(set(p['index'] for p in photo_urls))} photo(s)")
                # Show first photo URL
                first_photo = photo_urls[0]
                print(f"   Sample URL ({first_photo['size']}, {first_photo['width']}px): {first_photo['url'][:80]}...")
            else:
                print("   ✗ No photos found")
        except Exception as e:
            print(f"   ✗ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
        results.append(merchant)
        
        # Rate limiting - small delay between requests
        await asyncio.sleep(0.5)
    
    # Save updated results
    output_file = "merchants_near_charger_with_photos.json"
    data["merchants"] = merchants  # Update with photo URLs
    
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"Results saved to: {output_file}")
    
    # Print summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    merchants_with_photo_urls = [m for m in merchants if m.get("photo_urls")]
    print(f"Merchants with photo URLs: {len(merchants_with_photo_urls)}")
    
    for merchant in merchants_with_photo_urls[:5]:  # Show first 5
        name = merchant.get("name")
        photo_urls = merchant.get("photo_urls", [])
        unique_photos = len(set(p["index"] for p in photo_urls))
        print(f"  - {name}: {unique_photos} photo(s) available")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)






