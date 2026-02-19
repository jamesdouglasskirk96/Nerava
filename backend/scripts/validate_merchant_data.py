#!/usr/bin/env python3
"""
Validate what data is available from Google Places API for merchants
"""
import sys
import os
import json
import httpx
import asyncio

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")

PLACES_API_BASE = "https://places.googleapis.com/v1"


async def get_place_details_comprehensive(place_id: str, api_key: str) -> dict:
    """Get comprehensive place details with all available fields"""
    url = f"{PLACES_API_BASE}/places/{place_id}"
    
    # Comprehensive field mask
    field_mask = (
        "id,displayName,location,formattedAddress,types,rating,userRatingCount,priceLevel,"
        "photos,currentOpeningHours,regularOpeningHours,businessStatus,"
        "editorialSummary,nationalPhoneNumber,internationalPhoneNumber,websiteUri,"
        "googleMapsUri,utcOffsetMinutes"
    )
    
    params = {"key": api_key}
    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": field_mask
    }
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"  Error: {e}")
        if hasattr(e, 'response'):
            print(f"  Response: {e.response.text[:500]}")
        return {}


async def main():
    api_key = API_KEY
    if not api_key and len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    if not api_key:
        print("ERROR: Google Places API key required")
        return 1
    
    # Test with known merchants from our list
    test_merchants = [
        {"name": "Las Palapas - Town Center", "place_id": "ChIJcWepMjOjXIYRtS2oKtuvSE4"},
        {"name": "Chick-fil-A (Kyle)", "place_id": "ChIJMYo-YgZUW4YRBSDAiNJ8kts"},
        {"name": "Target (Kyle)", "place_id": "ChIJKSokiAZUW4YROUVjxD1wsQk"},
        {"name": "Starbucks (Kyle)", "place_id": "ChIJL8vHHn1RW4YR1LYtjVbc9bU"},
    ]
    
    print("=" * 80)
    print("VALIDATING GOOGLE PLACES API DATA AVAILABILITY")
    print("=" * 80)
    print()
    
    results = []
    
    for merchant in test_merchants:
        print(f"Testing: {merchant['name']}")
        print(f"Place ID: {merchant['place_id']}")
        
        details = await get_place_details_comprehensive(merchant['place_id'], api_key)
        
        if not details:
            print("  ✗ Failed to get details")
            print()
            continue
        
        # Extract data
        data_availability = {
            "name": merchant['name'],
            "place_id": merchant['place_id'],
            "has_photos": len(details.get("photos", [])) > 0,
            "photo_count": len(details.get("photos", [])),
            "has_hours": details.get("currentOpeningHours") is not None,
            "has_regular_hours": details.get("regularOpeningHours") is not None,
            "has_status": details.get("businessStatus") is not None,
            "business_status": details.get("businessStatus"),
            "open_now": details.get("currentOpeningHours", {}).get("openNow") if details.get("currentOpeningHours") else None,
            "has_phone_national": details.get("nationalPhoneNumber") is not None,
            "phone_national": details.get("nationalPhoneNumber"),
            "has_phone_international": details.get("internationalPhoneNumber") is not None,
            "phone_international": details.get("internationalPhoneNumber"),
            "has_website": details.get("websiteUri") is not None,
            "website": details.get("websiteUri"),
            "has_description": details.get("editorialSummary") is not None,
            "description": details.get("editorialSummary", {}).get("text") if details.get("editorialSummary") else None,
            "has_rating": details.get("rating") is not None,
            "rating": details.get("rating"),
            "rating_count": details.get("userRatingCount"),
            "price_level": details.get("priceLevel"),
        }
        
        results.append(data_availability)
        
        # Print summary
        print(f"  Photos: {'✓' if data_availability['has_photos'] else '✗'} ({data_availability['photo_count']} photos)")
        print(f"  Hours: {'✓' if data_availability['has_hours'] else '✗'}")
        if data_availability['has_hours']:
            print(f"    Open Now: {data_availability['open_now']}")
        print(f"  Status: {'✓' if data_availability['has_status'] else '✗'} ({data_availability['business_status']})")
        print(f"  Phone: {'✓' if data_availability['has_phone_national'] else '✗'}")
        if data_availability['has_phone_national']:
            print(f"    {data_availability['phone_national']}")
        print(f"  Website: {'✓' if data_availability['has_website'] else '✗'}")
        if data_availability['has_website']:
            print(f"    {data_availability['website']}")
        print(f"  Description: {'✓' if data_availability['has_description'] else '✗'}")
        if data_availability['has_description']:
            desc = data_availability['description'][:100] + "..." if len(data_availability['description'] or "") > 100 else data_availability['description']
            print(f"    {desc}")
        print()
        
        await asyncio.sleep(0.5)  # Rate limiting
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total = len(results)
    if total > 0:
        photos_available = sum(1 for r in results if r['has_photos'])
        hours_available = sum(1 for r in results if r['has_hours'])
        status_available = sum(1 for r in results if r['has_status'])
        phone_available = sum(1 for r in results if r['has_phone_national'])
        website_available = sum(1 for r in results if r['has_website'])
        description_available = sum(1 for r in results if r['has_description'])
        
        print(f"Tested {total} merchants:")
        print(f"  Photos: {photos_available}/{total} ({photos_available/total*100:.0f}%)")
        print(f"  Hours: {hours_available}/{total} ({hours_available/total*100:.0f}%)")
        print(f"  Status: {status_available}/{total} ({status_available/total*100:.0f}%)")
        print(f"  Phone: {phone_available}/{total} ({phone_available/total*100:.0f}%)")
        print(f"  Website: {website_available}/{total} ({website_available/total*100:.0f}%)")
        print(f"  Description: {description_available}/{total} ({description_available/total*100:.0f}%)")
    
    # Save detailed results
    with open("merchant_data_validation.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nDetailed results saved to: merchant_data_validation.json")
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)






