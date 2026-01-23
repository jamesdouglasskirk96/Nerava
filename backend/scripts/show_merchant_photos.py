#!/usr/bin/env python3
"""
Show what photos are available for merchants and how to access them.

This script explains the photo URLs that can be generated from Google Places API.
"""
import json
import sys
from pathlib import Path

def show_photo_info():
    """Show information about available photos for merchants"""
    
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
    print("GOOGLE PLACES API PHOTOS - INFORMATION")
    print("=" * 80)
    print()
    print("When a merchant has 'has_photos: true', it means Google Places API")
    print("has photos available for that location. Here's how to access them:")
    print()
    print("METHOD 1: Using Place Details API (Recommended)")
    print("-" * 80)
    print("1. Call: GET https://places.googleapis.com/v1/places/{place_id}")
    print("   Headers: X-Goog-Api-Key: {your_api_key}")
    print("   Field Mask: places.photos")
    print()
    print("2. This returns photo references in format:")
    print("   places/{place_id}/photos/{photo_reference}")
    print()
    print("3. Get photo URL using GetPhotoMedia endpoint:")
    print("   GET https://places.googleapis.com/v1/places/{place_id}/photos/{photo_reference}/media")
    print("   Params: maxWidthPx=400 (or 800, 1200, etc.)")
    print("   Headers: X-Goog-Api-Key: {your_api_key}")
    print()
    print("METHOD 2: Using Legacy Places API Photo endpoint")
    print("-" * 80)
    print("GET https://maps.googleapis.com/maps/api/place/photo")
    print("Params:")
    print("  - maxwidth=400 (or maxheight)")
    print("  - photoreference={photo_reference}")
    print("  - key={your_api_key}")
    print()
    print("=" * 80)
    print(f"MERCHANTS WITH PHOTOS AVAILABLE ({len(merchants_with_photos)}/{len(merchants)})")
    print("=" * 80)
    print()
    
    for i, merchant in enumerate(merchants_with_photos[:10], 1):  # Show first 10
        name = merchant.get("name", "Unknown")
        place_id = merchant.get("place_id", "")
        distance_m = merchant.get("distance_m", 0)
        
        print(f"{i}. {name}")
        print(f"   Place ID: {place_id}")
        print(f"   Distance: {distance_m}m")
        print(f"   To get photos:")
        print(f"   - Use Place Details API: GET places/{place_id} with fieldMask=photos")
        print(f"   - Or use the existing service: app.services.google_places_new.get_photo_url()")
        print()
    
    if len(merchants_with_photos) > 10:
        print(f"... and {len(merchants_with_photos) - 10} more merchants with photos")
        print()
    
    print("=" * 80)
    print("EXAMPLE CODE")
    print("=" * 80)
    print()
    print("To get photos programmatically, you can use the existing service:")
    print()
    print("```python")
    print("from app.services.google_places_new import search_nearby, get_photo_url")
    print("")
    print("# Search for merchants")
    print("merchants = await search_nearby(lat=30.012878, lng=-97.862488, radius_m=830)")
    print("")
    print("# For each merchant with photos, get photo URLs")
    print("for merchant in merchants:")
    print("    if merchant.get('photo_url', '').startswith('photo_ref:'):")
    print("        photo_ref = merchant['photo_url'].replace('photo_ref:', '')")
    print("        photo_url = await get_photo_url(photo_ref, max_width=400)")
    print("        print(f\"{merchant['name']}: {photo_url}\")")
    print("```")
    print()
    print("=" * 80)
    print("PHOTO SIZES AVAILABLE")
    print("=" * 80)
    print()
    print("Google Places API supports these common sizes:")
    print("  - Small: 200px width")
    print("  - Medium: 400px width")
    print("  - Large: 800px width")
    print("  - Extra Large: 1200px width")
    print()
    print("Note: Photos are typically exterior shots of the business, storefronts,")
    print("or interior shots provided by the business owner.")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(show_photo_info())



