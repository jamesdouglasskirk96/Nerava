#!/usr/bin/env python3
"""
Production seeding script for Nerava demo data.
Seeds 5 chargers with 12 merchants each using place_ids from local photos.

Usage:
    python scripts/seed_production.py

Requires:
    - GOOGLE_PLACES_API_KEY (optional - for fetching merchant details)
    - Production database connection
"""
import os
import sys
import json
import math
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from app.services.google_places_new import _haversine_distance

# Production database
DATABASE_URL = "postgresql://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"

# Demo chargers (from seed_demo_chargers.py)
DEMO_CHARGERS = [
    {
        "id": "charger_canyon_ridge",
        "name": "Canyon Ridge Supercharger",
        "address": "501 W Canyon Ridge Dr, Austin, TX 78753",
        "lat": 30.4027,
        "lng": -97.6719,
        "network": "Tesla",
        "stalls": 8,
        "kw": 150.0,
    },
    {
        "id": "charger_mopac",
        "name": "Tesla Supercharger - Mopac",
        "address": "10515 N Mopac Expy, Austin, TX 78759",
        "lat": 30.390456,
        "lng": -97.733056,
        "network": "Tesla",
        "stalls": 12,
        "kw": 250.0,
    },
    {
        "id": "charger_westlake",
        "name": "Tesla Supercharger - Westlake",
        "address": "701 S Capital of Texas Hwy, West Lake Hills, TX 78746",
        "lat": 30.2898,
        "lng": -97.827474,
        "network": "Tesla",
        "stalls": 16,
        "kw": 250.0,
    },
    {
        "id": "charger_ben_white",
        "name": "Tesla Supercharger - Ben White",
        "address": "2300 W Ben White Blvd, Austin, TX 78704",
        "lat": 30.2334001,
        "lng": -97.7914251,
        "network": "Tesla",
        "stalls": 10,
        "kw": 150.0,
    },
    {
        "id": "charger_sunset_valley",
        "name": "Tesla Supercharger - Sunset Valley",
        "address": "5601 Brodie Ln, Austin, TX 78745",
        "lat": 30.2261013,
        "lng": -97.8219238,
        "network": "Tesla",
        "stalls": 8,
        "kw": 150.0,
    },
]


def extract_merchant_place_ids() -> Dict[str, List[str]]:
    """Extract merchant place_ids from local photo filenames."""
    import re
    from collections import defaultdict
    
    chargers_dir = Path(__file__).parent.parent / "static" / "demo_chargers"
    merchants_by_charger = defaultdict(list)
    
    if not chargers_dir.exists():
        print(f"⚠️  Warning: {chargers_dir} not found")
        return {}
    
    for charger_dir in sorted(chargers_dir.iterdir()):
        if charger_dir.is_dir():
            charger_id = charger_dir.name
            merchants_dir = charger_dir / "merchants"
            
            if merchants_dir.exists():
                seen_place_ids = set()
                for photo in sorted(merchants_dir.glob("*.jpg")):
                    # Filename format: {place_id}_0.jpg
                    match = re.match(r"(.+?)_\d+\.jpg", photo.name)
                    if match:
                        place_id = match.group(1)
                        if place_id not in seen_place_ids:
                            merchants_by_charger[charger_id].append(place_id)
                            seen_place_ids.add(place_id)
    
    return dict(merchants_by_charger)


async def fetch_merchant_details(place_id: str, api_key: Optional[str]) -> Optional[Dict]:
    """Fetch merchant details from Google Places API."""
    if not api_key:
        return None
    
    try:
        from app.services.google_places_new import place_details
        details = await place_details(place_id)
        if details:
            return {
                "name": details.get("displayName", {}).get("text", "") if isinstance(details.get("displayName"), dict) else str(details.get("displayName", "")),
                "location": details.get("location", {}),
                "address": details.get("formattedAddress"),
                "rating": details.get("rating"),
                "user_rating_count": details.get("userRatingCount"),
                "types": details.get("types", []),
            }
    except Exception as e:
        print(f"  ⚠️  Error fetching details for {place_id}: {e}")
    return None


def seed_chargers(conn):
    """Insert or update chargers."""
    cur = conn.cursor()
    for charger in DEMO_CHARGERS:
        cur.execute("""
            INSERT INTO chargers (id, name, address, lat, lng, network_name, 
                                  connector_types, power_kw, is_public, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true, 'available', NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                address = EXCLUDED.address,
                lat = EXCLUDED.lat,
                lng = EXCLUDED.lng,
                network_name = EXCLUDED.network_name,
                power_kw = EXCLUDED.power_kw,
                updated_at = NOW()
        """, (
            charger["id"],
            charger["name"],
            charger["address"],
            charger["lat"],
            charger["lng"],
            charger["network"],
            '["Tesla"]',
            charger["kw"],
        ))
    conn.commit()
    print(f"✅ Seeded {len(DEMO_CHARGERS)} chargers")


async def seed_merchants(conn, merchants_by_charger: Dict[str, List[str]], api_key: Optional[str]):
    """Insert or update merchants and charger-merchant links."""
    import asyncio
    
    cur = conn.cursor()
    total_merchants = 0
    total_links = 0
    
    for charger_id, place_ids in merchants_by_charger.items():
        # Find charger coordinates
        charger = next((c for c in DEMO_CHARGERS if c["id"] == charger_id), None)
        if not charger:
            print(f"⚠️  Skipping {charger_id} - charger not found in DEMO_CHARGERS")
            continue
        
        charger_lat = charger["lat"]
        charger_lng = charger["lng"]
        
        print(f"\n📋 Processing {charger_id}: {len(place_ids)} merchants")
        
        for idx, place_id in enumerate(place_ids):
            merchant_id = f"google_{place_id[:20]}"
            
            # Try to fetch merchant details
            details = await fetch_merchant_details(place_id, api_key)
            
            if details:
                # Use fetched details
                location = details.get("location", {})
                merchant_lat = location.get("latitude", charger_lat)
                merchant_lng = location.get("longitude", charger_lng)
                name = details.get("name", f"Merchant {idx+1}")
                address = details.get("address", charger["address"])
                rating = details.get("rating")
                user_rating_count = details.get("user_rating_count")
                types = details.get("types", [])
                
                # Determine category
                type_set = set(t.lower() for t in types)
                if any(t in type_set for t in ["restaurant", "meal_takeaway"]):
                    category = "Restaurant"
                    primary_category = "food"
                elif any(t in type_set for t in ["cafe", "coffee_shop"]):
                    category = "Coffee Shop"
                    primary_category = "food"
                else:
                    category = types[0].replace("_", " ").title() if types else "Business"
                    primary_category = "other"
            else:
                # Use minimal data
                merchant_lat = charger_lat + (idx * 0.0001)  # Slight offset
                merchant_lng = charger_lng + (idx * 0.0001)
                name = f"Merchant {idx+1} near {charger['name']}"
                address = charger["address"]
                rating = None
                user_rating_count = None
                category = "Business"
                primary_category = "other"
                types = []
            
            # Calculate distance and walk time
            distance_m = _haversine_distance(charger_lat, charger_lng, merchant_lat, merchant_lng)
            walk_duration_s = int(math.ceil(distance_m / 1.33))  # 1.33 m/s walking speed
            
            # Insert or update merchant
            cur.execute("""
                INSERT INTO merchants (id, place_id, name, lat, lng, address, city, state, zip_code,
                                      category, primary_category, rating, user_rating_count, place_types,
                                      created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (id) DO UPDATE SET
                    place_id = EXCLUDED.place_id,
                    name = EXCLUDED.name,
                    lat = EXCLUDED.lat,
                    lng = EXCLUDED.lng,
                    address = EXCLUDED.address,
                    category = EXCLUDED.category,
                    primary_category = EXCLUDED.primary_category,
                    rating = EXCLUDED.rating,
                    user_rating_count = EXCLUDED.user_rating_count,
                    place_types = EXCLUDED.place_types,
                    updated_at = NOW()
            """, (
                merchant_id,
                place_id,
                name,
                merchant_lat,
                merchant_lng,
                address,
                "Austin",
                "TX",
                None,
                category,
                primary_category,
                rating,
                user_rating_count,
                json.dumps(types) if types else None,
            ))
            total_merchants += 1
            
            # Determine if primary merchant (first one for each charger)
            is_primary = (idx == 0)
            exclusive_title = "Free Welcome Offer" if is_primary else None
            exclusive_description = "Show this screen for a special welcome offer!" if is_primary else None
            
            # Insert or update charger-merchant link
            cur.execute("""
                INSERT INTO charger_merchants (charger_id, merchant_id, distance_m, walk_duration_s,
                                               is_primary, override_mode, suppress_others,
                                               exclusive_title, exclusive_description,
                                               created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (charger_id, merchant_id) DO UPDATE SET
                    distance_m = EXCLUDED.distance_m,
                    walk_duration_s = EXCLUDED.walk_duration_s,
                    is_primary = EXCLUDED.is_primary,
                    override_mode = EXCLUDED.override_mode,
                    suppress_others = EXCLUDED.suppress_others,
                    exclusive_title = EXCLUDED.exclusive_title,
                    exclusive_description = EXCLUDED.exclusive_description,
                    updated_at = NOW()
            """, (
                charger_id,
                merchant_id,
                distance_m,
                walk_duration_s,
                is_primary,
                "ALWAYS" if is_primary else None,
                False,
                exclusive_title,
                exclusive_description,
            ))
            total_links += 1
            
            if idx < 3:  # Print first 3
                print(f"  ✅ {name} ({distance_m:.0f}m away)")
        
        conn.commit()
    
    print(f"\n✅ Seeded {total_merchants} merchants and {total_links} charger-merchant links")


async def main():
    """Main seeding function."""
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if api_key:
        print("✅ Google Places API key found - will fetch merchant details")
    else:
        print("⚠️  No GOOGLE_PLACES_API_KEY - using minimal merchant data")
    
    # Extract merchant place_ids from photos
    print("\n📸 Extracting merchant place_ids from local photos...")
    merchants_by_charger = extract_merchant_place_ids()
    
    if not merchants_by_charger:
        print("❌ No merchant photos found. Cannot proceed.")
        sys.exit(1)
    
    total_merchants = sum(len(ids) for ids in merchants_by_charger.values())
    print(f"✅ Found {total_merchants} merchants across {len(merchants_by_charger)} chargers")
    
    # Connect to database
    print(f"\n🔌 Connecting to production database...")
    conn = psycopg2.connect(DATABASE_URL)
    
    try:
        # Seed chargers
        print("\n🔌 Seeding chargers...")
        seed_chargers(conn)
        
        # Seed merchants
        print("\n🔌 Seeding merchants...")
        await seed_merchants(conn, merchants_by_charger, api_key)
        
        print("\n" + "="*60)
        print("✅ Production seeding complete!")
        print("="*60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


