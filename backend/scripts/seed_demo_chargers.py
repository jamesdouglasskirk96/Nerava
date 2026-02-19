"""
Seed 5 Austin chargers with real merchant data for demo.

Usage:
  cd backend
  GOOGLE_PLACES_API_KEY=... python -m scripts.seed_demo_chargers

Idempotent: Safe to run multiple times.
"""
import sys
import os
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import math

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant
from app.services.google_places_new import (
    _haversine_distance,
    search_nearby,
    place_details
)
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Exact charger data from spec - DO NOT MODIFY
CHARGERS = [
    {
        "id": "charger_canyon_ridge",
        "name": "Canyon Ridge Supercharger",
        "place_id": "ChIJK-gKfYnLRIYRQKQmx_DvQko",
        "address": "501 W Canyon Ridge Dr, Austin, TX 78753",
        "lat": 30.4027,
        "lng": -97.6719,
        "network": "Tesla",
        "stalls": 8,
        "kw": 150,
        "primary_merchant_place_id": "ChIJA4UGPT_LRIYRjQC0TnNUWRg"  # Asadas Grill
    },
    {
        "id": "charger_mopac",
        "name": "Tesla Supercharger - Mopac",
        "place_id": "ChIJ51fvhIfLRIYRf3XcWjepmrA",
        "address": "10515 N Mopac Expy, Austin, TX 78759",
        "lat": 30.390456,
        "lng": -97.733056,
        "network": "Tesla",
        "stalls": 12,
        "kw": 250,
        "primary_merchant_place_id": None  # Pick closest restaurant
    },
    {
        "id": "charger_westlake",
        "name": "Tesla Supercharger - Westlake",
        "place_id": "ChIJJ6_0bN1LW4YRg8l9RLePwz8",
        "address": "701 S Capital of Texas Hwy, West Lake Hills, TX 78746",
        "lat": 30.2898,
        "lng": -97.827474,
        "network": "Tesla",
        "stalls": 16,
        "kw": 250,
        "primary_merchant_place_id": None
    },
    {
        "id": "charger_ben_white",
        "name": "Tesla Supercharger - Ben White",
        "place_id": "ChIJcz30IE9LW4YRYVS3g5VSz9Y",
        "address": "2300 W Ben White Blvd, Austin, TX 78704",
        "lat": 30.2334001,
        "lng": -97.7914251,
        "network": "Tesla",
        "stalls": 10,
        "kw": 150,
        "primary_merchant_place_id": None
    },
    {
        "id": "charger_sunset_valley",
        "name": "Tesla Supercharger - Sunset Valley",
        "place_id": "ChIJ2Um53XdLW4YRFBnBkfJKFJA",
        "address": "5601 Brodie Ln, Austin, TX 78745",
        "lat": 30.2261013,
        "lng": -97.8219238,
        "network": "Tesla",
        "stalls": 8,
        "kw": 150,
        "primary_merchant_place_id": None
    }
]


def map_types_to_category(types: List[str]) -> Tuple[str, str]:
    """Map Google Places types to category and primary_category."""
    type_set = set(t.lower() for t in types)
    
    if any(t in type_set for t in ["restaurant", "meal_takeaway"]):
        category = "Restaurant"
        primary_category = "food"
    elif any(t in type_set for t in ["cafe", "coffee_shop"]):
        category = "Coffee Shop"
        primary_category = "food"
    elif "convenience_store" in type_set:
        category = "Convenience Store"
        primary_category = "other"
    elif any(t in type_set for t in ["gym", "fitness_center"]):
        category = "Gym"
        primary_category = "other"
    elif any(t in type_set for t in ["pharmacy", "drugstore"]):
        category = "Pharmacy"
        primary_category = "other"
    else:
        category = types[0].replace("_", " ").title() if types else "Business"
        primary_category = "other"
    
    return category, primary_category


async def download_photo(client: httpx.AsyncClient, photo_name: str, save_path: Path, api_key: str):
    """Download photo from Google Places API v1 (handles redirect)."""
    url = f"https://places.googleapis.com/v1/{photo_name}/media?maxWidthPx=800&key={api_key}"
    try:
        response = await client.get(url, follow_redirects=True)
        if response.status_code == 200:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(response.content)
            logger.info(f"  ✅ Downloaded photo: {save_path.name} ({len(response.content)} bytes)")
            return True
        else:
            logger.warning(f"  ⚠️ Failed to download photo: {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"  ⚠️ Error downloading photo: {e}")
        return False


async def seed_charger(db: Session, charger_data: Dict, api_key: str):
    """Seed a single charger with merchants."""
    charger_id = charger_data["id"]
    logger.info(f"\n{'='*60}")
    logger.info(f"Seeding charger: {charger_data['name']}")
    logger.info(f"{'='*60}")
    
    # 1. Upsert charger record
    charger = db.query(Charger).filter(Charger.id == charger_id).first()
    if charger:
        # Update existing charger
        charger.name = charger_data["name"]
        charger.network_name = charger_data["network"]
        charger.lat = charger_data["lat"]
        charger.lng = charger_data["lng"]
        charger.address = charger_data["address"]
        charger.power_kw = charger_data["kw"]
        charger.connector_types = ["Tesla"]  # All are Tesla Superchargers
        logger.info(f"✅ Updated charger: {charger.name}")
    else:
        # Create new charger
        charger = Charger(
            id=charger_id,
            name=charger_data["name"],
            network_name=charger_data["network"],
            lat=charger_data["lat"],
            lng=charger_data["lng"],
            address=charger_data["address"],
            power_kw=charger_data["kw"],
            connector_types=["Tesla"],
            status="available"
        )
        db.add(charger)
        logger.info(f"✅ Created charger: {charger.name}")
    
    db.commit()
    
    # 2. Fetch charger hero photo
    charger_photo_path = Path(__file__).parent.parent / "static" / "demo_chargers" / charger_id / "hero.jpg"
    if not charger_photo_path.exists():
        try:
            # Get charger place details to find photo
            place_details_data = await place_details(charger_data["place_id"])
            if place_details_data and place_details_data.get("photos"):
                photos = place_details_data["photos"]
                if photos:
                    photo_name = photos[0].get("name", "")
                    if photo_name:
                        async with httpx.AsyncClient() as client:
                            await download_photo(client, photo_name, charger_photo_path, api_key)
        except Exception as e:
            logger.warning(f"⚠️ Could not download charger photo: {e}")
    
    # 3. Fetch 12 nearest merchants
    logger.info(f"Fetching nearby merchants...")
    nearby_places = await search_nearby(
        lat=charger_data["lat"],
        lng=charger_data["lng"],
        radius_m=500,
        included_types=["restaurant", "cafe", "coffee_shop", "convenience_store"],
        max_results=15
    )
    
    # Filter out charger itself
    nearby_places = [p for p in nearby_places if p.get("place_id") != charger_data["place_id"]]
    
    # Limit to 12 merchants
    nearby_places = nearby_places[:12]
    logger.info(f"Found {len(nearby_places)} merchants")
    
    # 4. Process each merchant
    merchants_processed = []
    async with httpx.AsyncClient() as client:
        for place in nearby_places:
            place_id = place.get("place_id")
            if not place_id:
                continue
            
            try:
                # Get place details
                details = await place_details(place_id)
                if not details:
                    continue
                
                # Extract merchant data
                name = details.get("displayName", {}).get("text", "") if isinstance(details.get("displayName"), dict) else str(details.get("displayName", ""))
                location = details.get("location", {})
                merchant_lat = location.get("latitude", 0)
                merchant_lng = location.get("longitude", 0)
                types = details.get("types", [])
                rating = details.get("rating")
                user_rating_count = details.get("userRatingCount")
                photos = details.get("photos", [])
                
                # Calculate distance
                distance_m = _haversine_distance(
                    charger_data["lat"], charger_data["lng"],
                    merchant_lat, merchant_lng
                )
                
                # Calculate walk duration (80 m/min = 1.33 m/s)
                walk_duration_s = int(math.ceil(distance_m / 1.33))
                
                # Map types to category
                category, primary_category = map_types_to_category(types)
                
                # Upsert merchant
                merchant = db.query(Merchant).filter(Merchant.place_id == place_id).first()
                merchant_id = f"google_{place_id[:20]}"
                
                if merchant:
                    # Update existing
                    merchant.name = name
                    merchant.lat = merchant_lat
                    merchant.lng = merchant_lng
                    merchant.category = category
                    merchant.primary_category = primary_category
                    merchant.rating = rating
                    merchant.user_rating_count = user_rating_count
                else:
                    # Create new
                    merchant = Merchant(
                        id=merchant_id,
                        place_id=place_id,
                        name=name,
                        category=category,
                        primary_category=primary_category,
                        lat=merchant_lat,
                        lng=merchant_lng,
                        rating=rating,
                        user_rating_count=user_rating_count,
                        place_types=types
                    )
                    db.add(merchant)
                
                db.commit()
                
                # Download merchant photo
                merchant_photo_path = Path(__file__).parent.parent / "static" / "demo_chargers" / charger_id / "merchants" / f"{place_id}_0.jpg"
                if not merchant_photo_path.exists() and photos:
                    photo_name = photos[0].get("name", "")
                    if photo_name:
                        await download_photo(client, photo_name, merchant_photo_path, api_key)
                
                # Upsert ChargerMerchant link
                link = db.query(ChargerMerchant).filter(
                    ChargerMerchant.charger_id == charger_id,
                    ChargerMerchant.merchant_id == merchant.id
                ).first()
                
                if link:
                    link.distance_m = distance_m
                    link.walk_duration_s = walk_duration_s
                else:
                    link = ChargerMerchant(
                        charger_id=charger_id,
                        merchant_id=merchant.id,
                        distance_m=distance_m,
                        walk_duration_s=walk_duration_s,
                        is_primary=False
                    )
                    db.add(link)
                
                db.commit()
                merchants_processed.append({
                    "merchant": merchant,
                    "link": link,
                    "distance_m": distance_m
                })
                
                logger.info(f"  ✅ Processed merchant: {name} ({distance_m:.0f}m)")
                
            except Exception as e:
                logger.warning(f"  ⚠️ Error processing merchant {place_id}: {e}")
                continue
    
    # 5. Mark primary merchant
    if charger_data["primary_merchant_place_id"]:
        # Use specified primary merchant
        primary_merchant = db.query(Merchant).filter(
            Merchant.place_id == charger_data["primary_merchant_place_id"]
        ).first()
        if primary_merchant:
            primary_link = db.query(ChargerMerchant).filter(
                ChargerMerchant.charger_id == charger_id,
                ChargerMerchant.merchant_id == primary_merchant.id
            ).first()
            if primary_link:
                # Unset all other primary flags
                db.query(ChargerMerchant).filter(
                    ChargerMerchant.charger_id == charger_id
                ).update({"is_primary": False})
                # Set this one as primary
                primary_link.is_primary = True
                db.commit()
                logger.info(f"✅ Set primary merchant: {primary_merchant.name}")
    else:
        # Pick closest restaurant/cafe
        restaurant_links = [
            m for m in merchants_processed
            if m["merchant"].primary_category == "food"
        ]
        if restaurant_links:
            restaurant_links.sort(key=lambda x: x["distance_m"])
            closest = restaurant_links[0]
            # Unset all other primary flags
            db.query(ChargerMerchant).filter(
                ChargerMerchant.charger_id == charger_id
            ).update({"is_primary": False})
            # Set closest as primary
            closest["link"].is_primary = True
            db.commit()
            logger.info(f"✅ Set primary merchant: {closest['merchant'].name}")
    
    logger.info(f"✅ Completed seeding charger: {charger_data['name']}")


async def main():
    """Main seeding function."""
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        logger.error("GOOGLE_PLACES_API_KEY environment variable not set")
        sys.exit(1)
    
    # Create static directory
    static_dir = Path(__file__).parent.parent / "static" / "demo_chargers"
    static_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created static directory: {static_dir}")
    
    db = SessionLocal()
    try:
        for charger_data in CHARGERS:
            await seed_charger(db, charger_data, api_key)
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ All chargers seeded successfully!")
        logger.info(f"{'='*60}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())





