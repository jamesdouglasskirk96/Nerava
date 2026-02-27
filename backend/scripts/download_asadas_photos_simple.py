#!/usr/bin/env python3
"""
Download photos for Asadas Grill from Google Places API (using old API)
"""
import os
import sys
import requests
from pathlib import Path
from typing import List, Optional

GOOGLE_PLACES_API_KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "")
if not GOOGLE_PLACES_API_KEY:
    print("ERROR: GOOGLE_PLACES_API_KEY environment variable is required")
    sys.exit(1)
GOOGLE_PLACES_BASE_URL = "https://maps.googleapis.com/maps/api/place"

# Asadas Grill location
ASADAS_ADDRESS = "501 W Canyon Ridge Dr, Austin, TX 78753"
ASADAS_LAT = 30.3839
ASADAS_LNG = -97.6900
ASADAS_NAME = "Asadas Grill"

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "merchant_photos_asadas_grill"
OUTPUT_DIR.mkdir(exist_ok=True)


def search_place(query: str, location: tuple) -> Optional[dict]:
    """Search for a place using Google Places Text Search API"""
    url = f"{GOOGLE_PLACES_BASE_URL}/textsearch/json"
    params = {
        "query": query,
        "location": f"{location[0]},{location[1]}",
        "radius": 1000,  # 1km radius
        "key": GOOGLE_PLACES_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK" and data.get("results"):
            return data["results"][0]  # Return first result
        return None
    except Exception as e:
        print(f"❌ Error searching: {e}")
        return None


def get_place_details(place_id: str) -> Optional[dict]:
    """Get detailed information about a place"""
    url = f"{GOOGLE_PLACES_BASE_URL}/details/json"
    params = {
        "place_id": place_id,
        "fields": "place_id,name,formatted_address,geometry,photos,rating,user_ratings_total,price_level,editorial_summary,opening_hours,current_opening_hours",
        "key": GOOGLE_PLACES_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") == "OK":
            return data.get("result")
        return None
    except Exception as e:
        print(f"❌ Error getting details: {e}")
        return None


def download_photo(photo_reference: str, output_path: Path, max_width: int = 1200) -> bool:
    """Download a photo from Google Places"""
    url = f"{GOOGLE_PLACES_BASE_URL}/photo"
    params = {
        "photoreference": photo_reference,
        "maxwidth": max_width,
        "key": GOOGLE_PLACES_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=30, stream=True)
        response.raise_for_status()
        
        # Determine file extension from content type
        content_type = response.headers.get("content-type", "")
        if "jpeg" in content_type or "jpg" in content_type:
            ext = "jpg"
        elif "png" in content_type:
            ext = "png"
        else:
            ext = "jpg"  # Default
        
        # Update output path with correct extension
        output_path = output_path.with_suffix(f".{ext}")
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = output_path.stat().st_size
        print(f"  ✅ Downloaded: {output_path.name} ({file_size:,} bytes)")
        return True
    except Exception as e:
        print(f"  ❌ Failed to download {output_path.name}: {e}")
        return False


def main():
    """Main function"""
    print(f"🔍 Searching for {ASADAS_NAME}...")
    print(f"   Location: {ASADAS_ADDRESS}")
    print(f"   Coordinates: {ASADAS_LAT}, {ASADAS_LNG}")
    print()
    
    # Search for Asadas Grill
    query = f"{ASADAS_NAME} {ASADAS_ADDRESS}"
    place = search_place(query, (ASADAS_LAT, ASADAS_LNG))
    
    if not place:
        print("❌ No results found for Asadas Grill")
        sys.exit(1)
    
    place_id = place.get("place_id")
    place_name = place.get("name", "Unknown")
    
    print(f"✅ Found: {place_name}")
    print(f"   Place ID: {place_id}")
    print()
    
    # Get full place details
    print("📋 Fetching place details...")
    details = get_place_details(place_id)
    
    if not details:
        print("❌ Failed to fetch place details")
        sys.exit(1)
    
    # Get photos
    photos = details.get("photos", [])
    if not photos:
        print("⚠️  No photos found for Asadas Grill")
        sys.exit(0)
    
    print(f"📸 Found {len(photos)} photos")
    print()
    
    # Download photos
    print(f"💾 Downloading photos to: {OUTPUT_DIR}")
    print()
    
    downloaded_count = 0
    max_photos = min(10, len(photos))  # Download up to 10 photos
    
    for i, photo in enumerate(photos[:max_photos], 1):
        photo_ref = photo.get("photo_reference")
        if not photo_ref:
            continue
        
        print(f"[{i}/{max_photos}] Downloading photo {i}...")
        output_path = OUTPUT_DIR / f"asadas_grill_{i:02d}.jpg"
        success = download_photo(photo_ref, output_path, max_width=1200)
        
        if success:
            downloaded_count += 1
    
    print()
    print(f"✅ Complete! Downloaded {downloaded_count}/{max_photos} photos")
    print(f"   Photos saved to: {OUTPUT_DIR}")
    
    # Save place details as JSON
    import json
    
    # Extract opening hours
    opening_hours = details.get("opening_hours", {})
    current_opening_hours = details.get("current_opening_hours", {})
    
    hours_info = {}
    if opening_hours:
        hours_info["open_now"] = opening_hours.get("open_now")
        hours_info["weekday_text"] = opening_hours.get("weekday_text", [])
        hours_info["periods"] = opening_hours.get("periods", [])
    
    if current_opening_hours:
        hours_info["current_open_now"] = current_opening_hours.get("open_now")
        hours_info["current_weekday_text"] = current_opening_hours.get("weekday_text", [])
        hours_info["current_periods"] = current_opening_hours.get("periods", [])
    
    details_path = OUTPUT_DIR / "place_details.json"
    with open(details_path, 'w') as f:
        json.dump({
            "place_id": place_id,
            "name": place_name,
            "address": details.get("formatted_address"),
            "rating": details.get("rating"),
            "user_rating_count": details.get("user_ratings_total"),
            "price_level": details.get("price_level"),
            "description": details.get("editorial_summary", {}).get("overview") if details.get("editorial_summary") else None,
            "photos_count": len(photos),
            "location": {
                "lat": details.get("geometry", {}).get("location", {}).get("lat"),
                "lng": details.get("geometry", {}).get("location", {}).get("lng")
            },
            "opening_hours": hours_info if hours_info else None
        }, f, indent=2)
    
    print(f"   Place details saved to: {details_path}")


if __name__ == "__main__":
    main()

