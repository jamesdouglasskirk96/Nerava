"""
Seed script for Canyon Ridge Supercharger with Asadas Grill primary merchant.

Creates:
- Canyon Ridge charger (501 W Canyon Ridge Dr, Austin, TX 78753)
- Asadas Grill merchant (from place_details.json)
- Primary merchant override link with exclusive offer
- 6-10 real nearby merchants from Google Places API
"""
import sys
import json
import os
import asyncio
import httpx
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant, ChargerCluster
from app.services.google_places_new import (
    _haversine_distance,
    search_nearby,
    place_details
)
from app.core.config import settings as core_settings
import uuid
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8001")

# Photo base URL: Use CloudFront in production, local static in dev
def get_photo_base_url() -> str:
    """Get the base URL for merchant photos based on environment."""
    env = os.getenv("ENV", "dev")
    photos_domain = os.getenv("PHOTOS_BASE_URL", "https://photos.nerava.network")
    
    if env == "prod" or env == "production":
        return photos_domain
    else:
        # Use local API static serving for dev
        return BASE_URL


PHOTO_BASE_URL = get_photo_base_url()


def map_types_to_category(types: List[str]) -> Tuple[str, str]:
    """
    Map Google Places types to human-readable category and primary_category.
    
    Returns:
        (category, primary_category) tuple
    """
    type_set = set(t.lower() for t in types)
    
    # Map to human-readable category
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
        # Use first type, capitalized
        category = types[0].replace("_", " ").title() if types else "Business"
        primary_category = "other"
    
    return category, primary_category


async def fetch_nearby_merchants(
    lat: float,
    lng: float,
    radius_m: int,
    excluded_place_id: Optional[str],
    max_results: int = 15
) -> List[Dict]:
    """
    Fetch nearby merchants from Google Places API.
    
    Args:
        lat: Latitude
        lng: Longitude
        radius_m: Search radius in meters
        excluded_place_id: Place ID to exclude (e.g., Asadas Grill)
        max_results: Maximum number of results to fetch
    
    Returns:
        List of place dictionaries with place_id, name, lat, lng, types, distance_m
    """
    included_types = ["restaurant", "cafe", "convenience_store", "gym", "pharmacy"]
    
    try:
        places = await search_nearby(
            lat=lat,
            lng=lng,
            radius_m=radius_m,
            included_types=included_types,
            max_results=max_results
        )
        
        # Filter out excluded place
        if excluded_place_id:
            places = [p for p in places if p.get("place_id") != excluded_place_id]
        
        return places
    except Exception as e:
        logger.error(f"Error fetching nearby merchants: {e}", exc_info=True)
        return []


async def fetch_place_details(place_id: str) -> Optional[Dict]:
    """
    Fetch full place details from Google Places API.
    
    Args:
        place_id: Google Place ID
    
    Returns:
        Place details dictionary or None if error
    """
    try:
        details = await place_details(place_id)
        if not details:
            return None
        
        # Extract and normalize fields
        place_id_normalized = details.get("id", "").replace("places/", "")
        display_name = details.get("displayName", {})
        name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)
        
        location = details.get("location", {})
        lat = location.get("latitude", 0)
        lng = location.get("longitude", 0)
        
        editorial_summary = details.get("editorialSummary", {})
        description = editorial_summary.get("text", "") if isinstance(editorial_summary, dict) else None
        
        return {
            "place_id": place_id_normalized,
            "name": name,
            "formatted_address": details.get("formattedAddress"),
            "lat": lat,
            "lng": lng,
            "opening_hours": details.get("regularOpeningHours"),
            "photos": details.get("photos", []),
            "types": details.get("types", []),
            "editorial_summary": description,
            "rating": details.get("rating"),
            "user_rating_count": details.get("userRatingCount"),
            "price_level": details.get("priceLevel"),
        }
    except Exception as e:
        logger.error(f"Error fetching place details for {place_id}: {e}", exc_info=True)
        return None


async def download_merchant_photos(
    place_id: str,
    photos: List[Dict],
    max_photos: int = 3,
    max_width: int = 800
) -> Optional[List[str]]:
    """
    Download merchant photos from Google Places API v1.
    
    The Places v1 photo endpoint returns HTTP 302 redirects to lh3.googleusercontent.com.
    This function follows redirects automatically using httpx with follow_redirects=True.
    
    Args:
        place_id: Google Place ID
        photos: List of photo objects from place details
        max_photos: Maximum number of photos to download
        max_width: Maximum photo width in pixels
    
    Returns:
        List of absolute photo URLs or None if no photos available
    """
    if not photos:
        return None
    
    # Get API key
    api_key = os.getenv("GOOGLE_PLACES_API_KEY") or core_settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        logger.error("GOOGLE_PLACES_API_KEY not set, cannot download photos")
        return None
    
    # Create photo directory (inside backend/static/)
    photo_dir = Path(__file__).parent.parent / "static" / "merchant_photos_google" / place_id
    photo_dir.mkdir(parents=True, exist_ok=True)
    
    photo_urls = []
    
    # Download up to max_photos
    for i, photo in enumerate(photos[:max_photos], 1):
        try:
            photo_name = photo.get("name", "")
            if not photo_name:
                continue
            
            # Construct Places v1 photo endpoint URL
            # photo_name format: "places/{place_id}/photos/{photo_ref}"
            photo_endpoint_url = (
                f"https://places.googleapis.com/v1/{photo_name}/media"
                f"?maxWidthPx={max_width}&key={api_key}"
            )
            
            # Download photo with redirect following
            filename = f"{place_id}_{i:02d}.jpg"
            filepath = photo_dir / filename
            
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0
            ) as client:
                response = await client.get(photo_endpoint_url)
                response.raise_for_status()
                
                with open(filepath, "wb") as f:
                    f.write(response.content)
            
            # Build absolute URL
            # Use CloudFront URL in production, local static in dev
            if PHOTO_BASE_URL.startswith("https://"):
                absolute_url = f"{PHOTO_BASE_URL}/google/{place_id}/{filename}"
            else:
                absolute_url = f"{BASE_URL}/static/merchant_photos_google/{place_id}/{filename}"
            photo_urls.append(absolute_url)
            
            logger.info(f"  ✅ Downloaded photo {i}/{min(len(photos), max_photos)}: {filename} ({len(response.content)} bytes)")
            
        except Exception as e:
            logger.warning(f"Error downloading photo {i} for {place_id}: {e}")
            continue
    
    if not photo_urls:
        return None
    
    return photo_urls


def create_or_update_merchant(
    db: Session,
    place_details: Dict,
    photo_urls: List[str]
) -> Optional[Merchant]:
    """
    Create or update merchant record idempotently.
    
    Args:
        db: Database session
        place_details: Place details dictionary
        photo_urls: List of photo URLs
    
    Returns:
        Merchant object or None if error
    """
    place_id = place_details.get("place_id")
    if not place_id:
        return None
    
    # Check if merchant already exists
    merchant = db.query(Merchant).filter(Merchant.place_id == place_id).first()
    
    # Map types to category
    types = place_details.get("types", [])
    category, primary_category = map_types_to_category(types)
    
    # Extract address components (simple parsing)
    address = place_details.get("formatted_address", "")
    city = "Austin"  # Default
    state = "TX"  # Default
    zip_code = "78753"  # Default
    
    # Try to extract from address
    if address:
        parts = address.split(",")
        if len(parts) >= 3:
            city = parts[-2].strip()
            state_zip = parts[-1].strip().split()
            if len(state_zip) >= 2:
                state = state_zip[0]
                zip_code = state_zip[1]
    
    if merchant:
        # Update missing fields
        updated = False
        
        if not merchant.photo_urls or len(merchant.photo_urls) == 0:
            merchant.primary_photo_url = photo_urls[0] if photo_urls else None
            merchant.photo_urls = photo_urls
            updated = True
        
        if not merchant.description and place_details.get("editorial_summary"):
            merchant.description = place_details.get("editorial_summary")
            updated = True
        
        if not merchant.hours_json and place_details.get("opening_hours"):
            merchant.hours_json = place_details.get("opening_hours")
            updated = True
        
        if updated:
            db.commit()
            logger.info(f"✅ Updated merchant: {merchant.name}")
        
        return merchant
    else:
        # Create new merchant
        merchant_id = f"google_{place_id[:20]}"
        
        merchant = Merchant(
            id=merchant_id,
            place_id=place_id,
            name=place_details.get("name"),
            category=category,
            primary_category=primary_category,
            lat=place_details.get("lat", 0),
            lng=place_details.get("lng", 0),
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            description=place_details.get("editorial_summary"),
            rating=place_details.get("rating"),
            user_rating_count=place_details.get("user_rating_count"),
            price_level=place_details.get("price_level"),
            primary_photo_url=photo_urls[0] if photo_urls else None,
            photo_urls=photo_urls,
            hours_json=place_details.get("opening_hours"),
            place_types=types,
        )
        
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        logger.info(f"✅ Created merchant: {merchant.name}")
        
        return merchant


def seed_asadas_grill_charger():
    """Seed Canyon Ridge charger with Asadas Grill primary merchant and nearby merchants"""
    # Check for Google Places API key
    api_key = os.getenv("GOOGLE_PLACES_API_KEY") or core_settings.GOOGLE_PLACES_API_KEY
    if not api_key:
        logger.error("❌ GOOGLE_PLACES_API_KEY not set. Cannot proceed with seeding.")
        logger.error("   Set the environment variable: export GOOGLE_PLACES_API_KEY=your_key")
        sys.exit(1)
    
    # Set API key in core_settings if not already set
    if not core_settings.GOOGLE_PLACES_API_KEY:
        core_settings.GOOGLE_PLACES_API_KEY = api_key
        os.environ["GOOGLE_PLACES_API_KEY"] = api_key
    
    db = SessionLocal()
    
    try:
        # Load Asadas Grill place details
        place_details_path = Path(__file__).parent.parent.parent / "merchant_photos_asadas_grill" / "place_details.json"
        with open(place_details_path, 'r') as f:
            place_data = json.load(f)
        
        # Charger details
        charger_id = "canyon_ridge_supercharger"
        charger_lat = 30.4027
        charger_lng = -97.6719
        charger_address = "501 W Canyon Ridge Dr, Austin, TX 78753"
        
        # 1. Create or get charger
        charger = db.query(Charger).filter(Charger.id == charger_id).first()
        if not charger:
            charger = Charger(
                id=charger_id,
                name="Canyon Ridge Supercharger",
                network_name="TESLA",
                lat=charger_lat,
                lng=charger_lng,
                address=charger_address,
                city="Austin",
                state="TX",
                zip_code="78753",
                status="available",
                is_public=True,
                connector_types=["Tesla"],
            )
            db.add(charger)
            db.commit()
            db.refresh(charger)
            logger.info(f"✅ Created charger: {charger_id}")
        else:
            logger.info(f"✅ Charger already exists: {charger_id}")
        
        # 2. Create Asadas Grill merchant from place_details.json
        asadas_place_id = place_data.get("place_id")
        merchant_id = f"asadas_grill_{asadas_place_id[:20]}" if asadas_place_id else "asadas_grill_canyon_ridge"
        
        # Check if merchant already exists
        merchant = db.query(Merchant).filter(
            Merchant.place_id == asadas_place_id
        ).first() if asadas_place_id else None
        
        if not merchant:
            location = place_data.get("location", {})
            
            # Build photo URLs (CloudFront in production, local static in dev)
            if PHOTO_BASE_URL.startswith("https://"):
                photo_urls = [
                    f"{PHOTO_BASE_URL}/asadas_grill/asadas_grill_{i:02d}.jpg"
                    for i in range(1, 11)
                ]
            else:
                photo_urls = [
                    f"{BASE_URL}/static/merchant_photos_asadas_grill/asadas_grill_{i:02d}.jpg"
                    for i in range(1, 11)
                ]
            
            merchant = Merchant(
                id=merchant_id,
                place_id=asadas_place_id,
                name=place_data.get("name", "Asadas Grill"),
                lat=location.get("lat", charger_lat),
                lng=location.get("lng", charger_lng),
                address=place_data.get("address"),
                city="Austin",
                state="TX",
                zip_code="78753",
                category="Mexican Restaurant",
                primary_category="food",
                rating=place_data.get("rating"),
                user_rating_count=place_data.get("user_rating_count"),
                price_level=place_data.get("price_level"),
                description=place_data.get("description"),
                hours_json=place_data.get("opening_hours"),
                primary_photo_url=photo_urls[0] if photo_urls else None,
                photo_urls=photo_urls,
                open_now=place_data.get("opening_hours", {}).get("open_now"),
            )
            db.add(merchant)
            db.commit()
            db.refresh(merchant)
            logger.info(f"✅ Created merchant: {merchant_id}")
        else:
            # Update photo URLs if missing
            if not merchant.photo_urls or len(merchant.photo_urls) == 0:
                if PHOTO_BASE_URL.startswith("https://"):
                    photo_urls = [
                        f"{PHOTO_BASE_URL}/asadas_grill/asadas_grill_{i:02d}.jpg"
                        for i in range(1, 11)
                    ]
                else:
                    photo_urls = [
                        f"{BASE_URL}/static/merchant_photos_asadas_grill/asadas_grill_{i:02d}.jpg"
                        for i in range(1, 11)
                    ]
                merchant.primary_photo_url = photo_urls[0]
                merchant.photo_urls = photo_urls
                db.commit()
                logger.info(f"✅ Updated merchant photo URLs: {merchant_id}")
            merchant_id = merchant.id
            logger.info(f"✅ Merchant already exists: {merchant_id}")
        
        # 3. Calculate distance and walk time
        distance_m = _haversine_distance(charger.lat, charger.lng, merchant.lat, merchant.lng)
        walk_duration_s = int((distance_m / 80) * 60)  # 80m/min walking speed
        
        # 4. Create or update primary merchant override link
        override = db.query(ChargerMerchant).filter(
            ChargerMerchant.charger_id == charger_id,
            ChargerMerchant.merchant_id == merchant_id
        ).first()
        
        if override:
            override.is_primary = True
            override.override_mode = "ALWAYS"
            override.suppress_others = False
            override.exclusive_title = "Free Chips & Salsa"
            override.exclusive_description = "Show this screen to your server for complimentary chips and salsa with any entree purchase while you charge!"
            override.distance_m = distance_m
            override.walk_duration_s = walk_duration_s
            logger.info(f"✅ Updated existing ChargerMerchant link to primary")
        else:
            override = ChargerMerchant(
                charger_id=charger_id,
                merchant_id=merchant_id,
                distance_m=distance_m,
                walk_duration_s=walk_duration_s,
                is_primary=True,
                override_mode="ALWAYS",
                suppress_others=False,
                exclusive_title="Free Chips & Salsa",
                exclusive_description="Show this screen to your server for complimentary chips and salsa with any entree purchase while you charge!",
            )
            db.add(override)
            logger.info(f"✅ Created primary merchant override")
        
        db.commit()
        
        # 5. Fetch and create real nearby merchants from Google Places API
        logger.info("🔍 Fetching nearby merchants from Google Places API...")
        
        async def process_nearby_merchants():
            # Fetch nearby merchants
            nearby_places = await fetch_nearby_merchants(
                lat=charger_lat,
                lng=charger_lng,
                radius_m=400,
                excluded_place_id=asadas_place_id,
                max_results=15
            )
            
            if not nearby_places:
                logger.warning("⚠️  No nearby merchants found from Google Places API")
                return []
            
            logger.info(f"📋 Found {len(nearby_places)} nearby places, processing...")
            
            # Select 6-10 merchants (prioritize by distance, ensure variety)
            selected_places = nearby_places[:10]  # Take up to 10
            
            successful_merchants = []
            
            for place in selected_places:
                try:
                    place_id = place.get("place_id")
                    if not place_id:
                        continue
                    
                    logger.info(f"  Processing: {place.get('name', 'Unknown')} ({place_id[:20]}...)")
                    
                    # Fetch full place details
                    place_details_data = await fetch_place_details(place_id)
                    if not place_details_data:
                        logger.warning(f"  ⚠️  Could not fetch details for {place_id}")
                        continue
                    
                    # Download photos
                    photos = place_details_data.get("photos", [])
                    photo_urls = await download_merchant_photos(place_id, photos, max_photos=3, max_width=800)
                    
                    if not photo_urls:
                        logger.warning(f"  ⚠️  No photos available for {place_details_data.get('name')}, skipping")
                        continue
                    
                    # Create or update merchant
                    merchant = create_or_update_merchant(db, place_details_data, photo_urls)
                    if not merchant:
                        logger.warning(f"  ⚠️  Could not create merchant for {place_details_data.get('name')}")
                        continue
                    
                    # Calculate distance and walk time
                    merchant_distance_m = _haversine_distance(
                        charger.lat, charger.lng,
                        merchant.lat, merchant.lng
                    )
                    merchant_walk_duration_s = int((merchant_distance_m / 80) * 60)
                    
                    # Create simple exclusive offer based on category
                    category = merchant.category.lower()
                    if "coffee" in category or "cafe" in category:
                        exclusive_title = "10% Off Any Drink"
                        exclusive_description = "Show this screen for 10% off any drink while you charge!"
                    elif "restaurant" in category or "food" in category:
                        exclusive_title = "10% Off Your Order"
                        exclusive_description = "Show this screen for 10% off your order while you charge!"
                    elif "gym" in category or "fitness" in category:
                        exclusive_title = "Free Day Pass"
                        exclusive_description = "Show this screen for a free day pass while you charge!"
                    elif "pharmacy" in category:
                        exclusive_title = "15% Off Vitamins"
                        exclusive_description = "Show this screen for 15% off all vitamins and supplements!"
                    else:
                        exclusive_title = "10% Off While You Charge"
                        exclusive_description = "Show this screen for 10% off any purchase while you charge!"
                    
                    # Create or update ChargerMerchant link
                    charger_merchant_link = db.query(ChargerMerchant).filter(
                        ChargerMerchant.charger_id == charger_id,
                        ChargerMerchant.merchant_id == merchant.id
                    ).first()
                    
                    if charger_merchant_link:
                        charger_merchant_link.is_primary = False
                        charger_merchant_link.distance_m = merchant_distance_m
                        charger_merchant_link.walk_duration_s = merchant_walk_duration_s
                        charger_merchant_link.exclusive_title = exclusive_title
                        charger_merchant_link.exclusive_description = exclusive_description
                        logger.info(f"  ✅ Updated link for {merchant.name}")
                    else:
                        charger_merchant_link = ChargerMerchant(
                            charger_id=charger_id,
                            merchant_id=merchant.id,
                            distance_m=merchant_distance_m,
                            walk_duration_s=merchant_walk_duration_s,
                            is_primary=False,
                            exclusive_title=exclusive_title,
                            exclusive_description=exclusive_description,
                        )
                        db.add(charger_merchant_link)
                        logger.info(f"  ✅ Created link for {merchant.name}")
                    
                    successful_merchants.append(merchant.name)
                    
                except Exception as e:
                    logger.error(f"  ❌ Error processing merchant {place.get('name', 'Unknown')}: {e}", exc_info=True)
                    continue
            
            db.commit()
            return successful_merchants
        
        # Run async function
        successful_merchants = asyncio.run(process_nearby_merchants())
        
        logger.info(f"✅ Successfully processed {len(successful_merchants)} nearby merchants")
        
        # 6. Create or update ChargerCluster for party endpoint
        cluster = db.query(ChargerCluster).filter(ChargerCluster.name == "asadas_party").first()
        if not cluster:
            cluster = ChargerCluster(
                id=str(uuid.uuid4()),
                name="asadas_party",
                charger_lat=charger_lat,
                charger_lng=charger_lng,
                charger_radius_m=400,
                merchant_radius_m=40,
                charger_id=charger_id,
            )
            db.add(cluster)
            db.commit()
            logger.info(f"✅ Created ChargerCluster: asadas_party")
        else:
            cluster.charger_id = charger_id
            cluster.charger_lat = charger_lat
            cluster.charger_lng = charger_lng
            db.commit()
            logger.info(f"✅ Updated ChargerCluster: asadas_party")
        
        logger.info("\n" + "="*60)
        logger.info("✅ Asadas Grill charger seeded successfully!")
        logger.info(f"   Charger ID: {charger_id}")
        logger.info(f"   Primary Merchant ID: {merchant_id}")
        logger.info(f"   Place ID: {asadas_place_id or 'N/A'}")
        logger.info(f"   Distance: {distance_m:.0f}m")
        logger.info(f"   Walk time: {walk_duration_s // 60} min")
        logger.info(f"   Nearby merchants: {len(successful_merchants)}")
        logger.info("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Error seeding Asadas Grill charger: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_asadas_grill_charger()

