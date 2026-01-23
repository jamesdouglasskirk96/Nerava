#!/usr/bin/env python3
"""
Download one photo for each merchant from Google Places API

This script reads merchants_near_charger.json and downloads one photo
for each merchant that has photos available.
"""
import sys
import os
import json
import httpx
import asyncio
from pathlib import Path
from urllib.parse import quote

# Default API key (can be overridden via environment variable)
API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

# Google Places API endpoints
PLACES_API_NEW_BASE = "https://places.googleapis.com/v1"
PLACES_API_OLD_BASE = "https://maps.googleapis.com/maps/api/place"


async def fetch_place_photos(place_id: str, api_key: str) -> list:
    """
    Fetch photo references for a place using Google Places API (New).
    
    Args:
        place_id: Google Places place ID
        api_key: Google Places API key
    
    Returns:
        List of photo references
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
            data = response.json()
            photos = data.get("photos", [])
            
            # Extract photo references
            photo_refs = []
            for photo in photos:
                photo_name = photo.get("name", "")
                if "/photos/" in photo_name:
                    # Format: places/{place_id}/photos/{photo_reference}
                    photo_ref = photo_name.split("/photos/")[-1]
                    photo_refs.append({
                        "photo_reference": photo_ref,
                        "photo_name": photo_name,
                    })
            
            return photo_refs
    except Exception as e:
        print(f"  Error fetching photos: {e}")
        return []


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
        print(f"  Warning: New API failed, trying legacy API: {e}")
    
    # Fallback to old API format
    return f"{PLACES_API_OLD_BASE}/photo?maxwidth={max_width}&photoreference={photo_reference}&key={api_key}"


async def download_photo(url: str, filepath: Path) -> bool:
    """
    Download a photo from a URL and save it to a file.
    
    Args:
        url: Photo URL
        filepath: Path to save the photo
    
    Returns:
        True if successful, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Save the image
            with open(filepath, "wb") as f:
                f.write(response.content)
            
            return True
    except Exception as e:
        print(f"  Error downloading photo: {e}")
        return False


def sanitize_filename(name: str) -> str:
    """Sanitize a merchant name for use as a filename"""
    # Remove or replace invalid filename characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    # Remove leading/trailing spaces and dots
    name = name.strip('. ')
    # Limit length
    if len(name) > 100:
        name = name[:100]
    return name


async def download_merchant_photo(merchant: dict, output_dir: Path, api_key: str) -> bool:
    """
    Download one photo for a merchant.
    
    Args:
        merchant: Merchant dictionary
        output_dir: Directory to save photos
        api_key: Google Places API key
    
    Returns:
        True if photo was downloaded, False otherwise
    """
    name = merchant.get("name", "Unknown")
    place_id = merchant.get("place_id", "")
    
    if not place_id:
        print(f"  ✗ {name}: No place ID")
        return False
    
    # Fetch photo references
    photo_refs = await fetch_place_photos(place_id, api_key)
    
    if not photo_refs:
        print(f"  ✗ {name}: No photos found")
        return False
    
    # Get the first photo
    first_photo = photo_refs[0]
    photo_ref = first_photo["photo_reference"]
    
    # Get photo URL (try 800px for better quality)
    print(f"  → Getting photo URL...")
    photo_url = await get_photo_url_new_api(place_id, photo_ref, api_key, max_width=800)
    
    # Determine file extension from URL or default to jpg
    file_ext = "jpg"
    if ".jpg" in photo_url.lower() or "jpeg" in photo_url.lower():
        file_ext = "jpg"
    elif ".png" in photo_url.lower():
        file_ext = "png"
    
    # Create filename
    safe_name = sanitize_filename(name)
    filename = f"{safe_name}_{place_id[:10]}.{file_ext}"
    filepath = output_dir / filename
    
    # Download the photo
    print(f"  → Downloading photo...")
    success = await download_photo(photo_url, filepath)
    
    if success:
        file_size = filepath.stat().st_size
        print(f"  ✓ {name}: Saved to {filename} ({file_size:,} bytes)")
        return True
    else:
        print(f"  ✗ {name}: Failed to download")
        return False


async def main():
    # Get API key from environment or command line
    api_key = API_KEY
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("ERROR: Google Places API key required")
        print("Set GOOGLE_PLACES_API_KEY environment variable or provide as argument")
        print("Usage: python download_merchant_photos.py [API_KEY]")
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
    merchants_with_photos = [m for m in merchants if m.get("has_photos")]
    
    print("=" * 80)
    print("DOWNLOADING MERCHANT PHOTOS")
    print("=" * 80)
    print(f"Total merchants: {len(merchants)}")
    print(f"Merchants with photos: {len(merchants_with_photos)}")
    print()
    
    # Create output directory (use location name if available)
    output_dir_name = "merchant_photos"
    if len(sys.argv) > 2:
        # If second argument provided, use it as folder name
        output_dir_name = sys.argv[2]
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("AIza"):
        # If first arg is not an API key, use it as folder name
        output_dir_name = sys.argv[1]
    
    output_dir = Path(output_dir_name)
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir.absolute()}")
    print()
    
    # Download photos
    success_count = 0
    failed_count = 0
    
    for i, merchant in enumerate(merchants_with_photos, 1):
        name = merchant.get("name", "Unknown")
        print(f"[{i}/{len(merchants_with_photos)}] {name}")
        
        success = await download_merchant_photo(merchant, output_dir, api_key)
        if success:
            success_count += 1
        else:
            failed_count += 1
        
        print()
        
        # Rate limiting - small delay between requests
        await asyncio.sleep(0.5)
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Successfully downloaded: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Photos saved to: {output_dir.absolute()}")
    print()
    
    # List downloaded files
    if success_count > 0:
        print("Downloaded photos:")
        for photo_file in sorted(output_dir.glob("*.*")):
            size = photo_file.stat().st_size
            print(f"  - {photo_file.name} ({size:,} bytes)")
    
    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

