#!/usr/bin/env python3
"""
Seed merchants from OpenStreetMap Overpass API (100% free, no API key).

Strategy:
  1. Load all chargers from DB, group into 0.01 degree grid cells (~1.1km)
  2. For each cell, query Overpass for POIs in bbox + 800m buffer
  3. Classify each POI (corporate vs local)
  4. Create Merchant + ChargerMerchant junction entries
  5. Set fallback category photos when no real photo available

Usage:
    python -m scripts.seed_merchants_free                 # All cells
    python -m scripts.seed_merchants_free --max-cells 10  # Limit for testing
"""
import logging
import asyncio
import math
from collections import defaultdict
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Walk speed: 80m/min (industry standard pedestrian speed)
WALK_SPEED_M_PER_MIN = 80.0
MAX_WALK_DISTANCE_M = 800  # ~10 min walk
GRID_SIZE_DEG = 0.01  # ~1.1 km

# Category-based fallback photos (free Unsplash images, no API key needed)
# These are stable Unsplash photo URLs that serve as placeholders
CATEGORY_FALLBACK_PHOTOS = {
    "restaurant": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop",
    "cafe": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400&h=300&fit=crop",
    "coffee": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400&h=300&fit=crop",
    "bar": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=400&h=300&fit=crop",
    "fast_food": "https://images.unsplash.com/photo-1561758033-d89a9ad46330?w=400&h=300&fit=crop",
    "pub": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=400&h=300&fit=crop",
    "ice_cream": "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=400&h=300&fit=crop",
    "bakery": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=300&fit=crop",
    "food_court": "https://images.unsplash.com/photo-1567521464027-f127ff144326?w=400&h=300&fit=crop",
    "supermarket": "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=400&h=300&fit=crop",
    "grocery": "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=400&h=300&fit=crop",
    "convenience": "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=400&h=300&fit=crop",
    "mall": "https://images.unsplash.com/photo-1519567241046-7f570c474897?w=400&h=300&fit=crop",
    "shopping": "https://images.unsplash.com/photo-1519567241046-7f570c474897?w=400&h=300&fit=crop",
    "department_store": "https://images.unsplash.com/photo-1519567241046-7f570c474897?w=400&h=300&fit=crop",
    "clothes": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=300&fit=crop",
    "electronics": "https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=400&h=300&fit=crop",
    "bookshop": "https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=400&h=300&fit=crop",
    "gift": "https://images.unsplash.com/photo-1513885535751-8b9238bd345a?w=400&h=300&fit=crop",
}
DEFAULT_FALLBACK_PHOTO = "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=400&h=300&fit=crop"

# OSM type -> our category mapping
TYPE_TO_CATEGORY = {
    "restaurant": "restaurant",
    "cafe": "coffee",
    "bar": "bar",
    "fast_food": "fast_food",
    "pub": "bar",
    "ice_cream": "dessert",
    "food_court": "restaurant",
    "bakery": "bakery",
    "supermarket": "grocery",
    "convenience": "convenience",
    "mall": "shopping",
    "department_store": "shopping",
    "clothes": "shopping",
    "electronics": "shopping",
    "bookshop": "shopping",
    "gift": "shopping",
}


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance between two points in meters."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _get_fallback_photo(poi_type: str) -> str:
    """Get a category-based fallback photo URL."""
    return CATEGORY_FALLBACK_PHOTOS.get(poi_type, DEFAULT_FALLBACK_PHOTO)


def _grid_key(lat: float, lng: float) -> tuple[int, int]:
    """Convert lat/lng to grid cell key."""
    return (int(lat / GRID_SIZE_DEG), int(lng / GRID_SIZE_DEG))


def _cell_bbox(grid_key: tuple[int, int], buffer_deg: float = 0.008):
    """Get bounding box for a grid cell with buffer (~800m at mid-latitudes)."""
    lat_base = grid_key[0] * GRID_SIZE_DEG
    lng_base = grid_key[1] * GRID_SIZE_DEG
    return (
        lat_base - buffer_deg,             # south
        lng_base - buffer_deg,             # west
        lat_base + GRID_SIZE_DEG + buffer_deg,  # north
        lng_base + GRID_SIZE_DEG + buffer_deg,  # east
    )


async def seed_merchants(
    db,
    max_cells: Optional[int] = None,
    progress_callback=None,
) -> dict:
    """
    Discover merchants near chargers using OpenStreetMap Overpass API.

    Args:
        db: SQLAlchemy Session
        max_cells: Limit number of grid cells to process (for testing)
        progress_callback: Optional callable(cells_done, total_cells)

    Returns:
        {cells_processed, merchants_created, merchants_updated,
         junctions_created, corporate_flagged}
    """
    from app.models.while_you_charge import Charger, Merchant, ChargerMerchant
    from app.integrations.overpass_client import OverpassClient
    from app.services.corporate_classifier import CorporateClassifier

    overpass = OverpassClient(timeout=45.0)
    classifier = CorporateClassifier()

    result = {
        "cells_processed": 0,
        "merchants_created": 0,
        "merchants_updated": 0,
        "junctions_created": 0,
        "corporate_flagged": 0,
        "errors": [],
    }

    # Step 1: Load all chargers
    chargers = db.query(Charger).all()
    if not chargers:
        logger.warning("[MerchantSeed] No chargers in DB. Run charger seed first.")
        return result

    logger.info(f"[MerchantSeed] Loaded {len(chargers)} chargers")

    # Step 2: Group chargers into grid cells
    grid_cells: dict[tuple, list] = defaultdict(list)
    for c in chargers:
        key = _grid_key(c.lat, c.lng)
        grid_cells[key].append(c)

    total_cells = len(grid_cells)
    if max_cells:
        # Take only first N cells (sorted for deterministic behavior)
        keys = sorted(grid_cells.keys())[:max_cells]
        grid_cells = {k: grid_cells[k] for k in keys}
        total_cells = len(grid_cells)

    logger.info(f"[MerchantSeed] {total_cells} grid cells to process")

    # Track seen OSM IDs to avoid duplicate merchant creation
    seen_osm_ids: set[str] = set()

    # Step 3: Process each grid cell
    for cell_idx, (cell_key, cell_chargers) in enumerate(grid_cells.items()):
        try:
            south, west, north, east = _cell_bbox(cell_key)
            pois = await overpass.find_pois_in_bbox(south, west, north, east)

            for poi in pois:
                osm_id = poi["osm_id"]
                poi_name = poi["name"]
                poi_type = poi["type"]

                # Classify
                classification = classifier.classify(
                    name=poi_name,
                    website=poi.get("website"),
                    place_type=poi_type,
                    brand=poi.get("brand"),
                )
                is_corporate = classification == "corporate"
                if is_corporate:
                    result["corporate_flagged"] += 1

                # Map category
                category = TYPE_TO_CATEGORY.get(poi_type, "other")
                fallback_photo = _get_fallback_photo(poi_type)

                # Find or create Merchant (keyed on place_id = osm_id)
                existing_merchant = (
                    db.query(Merchant)
                    .filter(Merchant.place_id == osm_id)
                    .first()
                )

                if existing_merchant:
                    merchant = existing_merchant
                    # Update fields if needed
                    if poi.get("phone") and not merchant.phone:
                        merchant.phone = poi["phone"]
                    if poi.get("website") and not merchant.website:
                        merchant.website = poi["website"]
                    if not merchant.photo_url:
                        merchant.photo_url = fallback_photo
                    merchant.is_corporate = is_corporate
                    merchant.updated_at = datetime.utcnow()
                    if osm_id not in seen_osm_ids:
                        result["merchants_updated"] += 1
                else:
                    # Generate merchant ID
                    merchant_id = f"osm_{osm_id.replace('_', '')}"
                    merchant = Merchant(
                        id=merchant_id,
                        external_id=osm_id,
                        name=poi_name,
                        category=category,
                        lat=poi["lat"],
                        lng=poi["lng"],
                        place_id=osm_id,
                        phone=poi.get("phone"),
                        website=poi.get("website"),
                        photo_url=fallback_photo,
                        primary_photo_url=fallback_photo,
                        primary_category=_primary_category(category),
                        is_corporate=is_corporate,
                        description=f"{poi_type.replace('_', ' ').title()} near EV charging",
                    )
                    db.add(merchant)
                    db.flush()  # Get the ID
                    result["merchants_created"] += 1

                seen_osm_ids.add(osm_id)

                # Create ChargerMerchant junctions for nearby chargers
                for charger in cell_chargers:
                    dist = haversine_distance(
                        poi["lat"], poi["lng"], charger.lat, charger.lng
                    )
                    if dist > MAX_WALK_DISTANCE_M:
                        continue

                    walk_seconds = int(dist / WALK_SPEED_M_PER_MIN * 60)

                    # Check if junction exists
                    existing_junction = (
                        db.query(ChargerMerchant)
                        .filter(
                            ChargerMerchant.charger_id == charger.id,
                            ChargerMerchant.merchant_id == merchant.id,
                        )
                        .first()
                    )
                    if existing_junction:
                        continue

                    junction = ChargerMerchant(
                        charger_id=charger.id,
                        merchant_id=merchant.id,
                        distance_m=round(dist, 1),
                        walk_duration_s=walk_seconds,
                        walk_distance_m=round(dist * 1.3, 1),  # ~30% walking factor
                    )
                    db.add(junction)
                    result["junctions_created"] += 1

                    # Update merchant's nearest charger cache if this is closer
                    if (
                        merchant.nearest_charger_distance_m is None
                        or dist < merchant.nearest_charger_distance_m
                    ):
                        merchant.nearest_charger_id = charger.id
                        merchant.nearest_charger_distance_m = int(dist)

            # Commit batch
            if (cell_idx + 1) % 10 == 0:
                db.commit()
                logger.info(
                    f"[MerchantSeed] {cell_idx + 1}/{total_cells} cells, "
                    f"{result['merchants_created']} merchants, "
                    f"{result['junctions_created']} junctions"
                )

            result["cells_processed"] += 1

            if progress_callback:
                progress_callback(cell_idx + 1, total_cells)

        except Exception as e:
            error_msg = f"Cell {cell_key}: {str(e)}"
            logger.error(f"[MerchantSeed] {error_msg}")
            result["errors"].append(error_msg)
            db.rollback()

    # Final commit
    try:
        db.commit()
    except Exception as e:
        logger.error(f"[MerchantSeed] Final commit failed: {e}")
        db.rollback()

    logger.info(
        f"[MerchantSeed] Complete: {result['merchants_created']} created, "
        f"{result['junctions_created']} junctions, "
        f"{result['corporate_flagged']} corporate flagged"
    )
    return result


def _primary_category(category: str) -> str:
    """Map detailed category to primary_category (coffee, food, other)."""
    if category in ("coffee", "cafe"):
        return "coffee"
    if category in ("restaurant", "fast_food", "bakery", "bar", "dessert"):
        return "food"
    return "other"


if __name__ == "__main__":
    import argparse
    import sys

    sys.path.insert(0, ".")

    parser = argparse.ArgumentParser(description="Seed merchants from OSM Overpass")
    parser.add_argument("--max-cells", type=int, help="Limit grid cells (for testing)")
    args = parser.parse_args()

    from app.db import SessionLocal

    logging.basicConfig(level=logging.INFO)

    db = SessionLocal()
    try:
        result = asyncio.run(seed_merchants(db, max_cells=args.max_cells))
        print(f"\nResult: {result}")
    finally:
        db.close()
