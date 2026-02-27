#!/usr/bin/env python3
"""
Download photos for Asadas Grill from Google Places API
"""
import os
import sys
import asyncio
import httpx
from pathlib import Path
from typing import List, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.google_places_new import search_text, place_details, get_photo_url
from app.core.config import settings

# Asadas Grill location from bootstrap
ASADAS_ADDRESS = "501 W Canyon Ridge Dr, Austin, TX 78753"
ASADAS_LAT = 30.3839
ASADAS_LNG = -97.6900
ASADAS_NAME = "Asadas Grill"

# Output directory - create in workspace root
OUTPUT_DIR = Path(__file__).parent.parent.parent / "merchant_photos_asadas_grill"
OUTPUT_DIR.mkdir(exist_ok=True)


async def download_photo(url: str, output_path: Path) -> bool:
    """Download a photo from URL to file"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            print(f"  ✅ Downloaded: {output_path.name} ({len(response.content)} bytes)")
            return True
    except Exception as e:
        print(f"  ❌ Failed to download {output_path.name}: {e}")
        return False


async def main():
    """Main function to find and download Asadas Grill photos"""
    print(f"🔍 Searching for {ASADAS_NAME}...")
    print(f"   Location: {ASADAS_ADDRESS}")
    print(f"   Coordinates: {ASADAS_LAT}, {ASADAS_LNG}")
    print()
    
    # Check for API key in settings, environment, or use hardcoded fallback
    api_key = settings.GOOGLE_PLACES_API_KEY or os.getenv("GOOGLE_PLACES_API_KEY") or ""
    if not api_key:
        print("ERROR: GOOGLE_PLACES_API_KEY environment variable is required")
        sys.exit(1)
    
    # Temporarily set it in settings
    if not settings.GOOGLE_PLACES_API_KEY:
        settings.GOOGLE_PLACES_API_KEY = api_key
        # Also set in environment for the google_places_new module
        os.environ["GOOGLE_PLACES_API_KEY"] = api_key
    
    print(f"   Using API key: {api_key[:20]}...")
    
    # Search for Asadas Grill
    try:
        search_results = await search_text(
            query=f"{ASADAS_NAME} {ASADAS_ADDRESS}",
            location_bias={"lat": ASADAS_LAT, "lng": ASADAS_LNG},
            max_results=5
        )
        
        if not search_results:
            print("❌ No results found for Asadas Grill")
            sys.exit(1)
        
        # Find the best match (should be first result)
        asadas_place = None
        for place in search_results:
            place_name = place.get("name", "").lower()
            if "asadas" in place_name:
                asadas_place = place
                break
        
        if not asadas_place:
            print("⚠️  Asadas Grill not found in results, using first result")
            asadas_place = search_results[0]
        
        place_id = asadas_place.get("place_id")
        place_name = asadas_place.get("name", "Unknown")
        
        print(f"✅ Found: {place_name}")
        print(f"   Place ID: {place_id}")
        print()
        
        # Get full place details
        print("📋 Fetching place details...")
        place_details_data = await place_details(place_id)
        
        if not place_details_data:
            print("❌ Failed to fetch place details")
            sys.exit(1)
        
        # Get photos
        photos = place_details_data.get("photos", [])
        if not photos:
            print("⚠️  No photos found for Asadas Grill")
            sys.exit(0)
        
        print(f"📸 Found {len(photos)} photos")
        print()
        
        # Download photos
        print(f"💾 Downloading photos to: {OUTPUT_DIR}")
        print()
        
        downloaded_count = 0
        photo_maxwidth = int(os.getenv("GOOGLE_PLACES_PHOTO_MAXWIDTH", "1200"))  # Higher res for storage
        
        for i, photo in enumerate(photos, 1):
            photo_name = photo.get("name", "")
            if not photo_name:
                continue
            
            # Extract photo reference
            photo_ref = photo_name.replace("places/", "").split("/photos/")[-1]
            if not photo_ref:
                continue
            
            # Get photo URL
            print(f"[{i}/{len(photos)}] Fetching photo URL...")
            photo_url = await get_photo_url(photo_ref, max_width=photo_maxwidth)
            
            if not photo_url:
                print(f"  ⚠️  Could not get photo URL for photo {i}")
                continue
            
            # Determine file extension from URL
            if ".jpg" in photo_url or "jpeg" in photo_url.lower():
                ext = "jpg"
            elif ".png" in photo_url.lower():
                ext = "png"
            else:
                ext = "jpg"  # Default
            
            # Download photo
            output_path = OUTPUT_DIR / f"asadas_grill_{i:02d}.{ext}"
            success = await download_photo(photo_url, output_path)
            
            if success:
                downloaded_count += 1
        
        print()
        print(f"✅ Complete! Downloaded {downloaded_count}/{len(photos)} photos")
        print(f"   Photos saved to: {OUTPUT_DIR}")
        
        # Also save place details as JSON for reference
        import json
        details_path = OUTPUT_DIR / "place_details.json"
        with open(details_path, 'w') as f:
            json.dump({
                "place_id": place_id,
                "name": place_name,
                "address": place_details_data.get("formattedAddress"),
                "rating": place_details_data.get("rating"),
                "user_rating_count": place_details_data.get("userRatingCount"),
                "price_level": place_details_data.get("priceLevel"),
                "description": place_details_data.get("editorialSummary", {}).get("text") if place_details_data.get("editorialSummary") else None,
                "photos_count": len(photos),
                "location": {
                    "lat": place_details_data.get("location", {}).get("latitude"),
                    "lng": place_details_data.get("location", {}).get("longitude")
                }
            }, f, indent=2)
        
        print(f"   Place details saved to: {details_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

