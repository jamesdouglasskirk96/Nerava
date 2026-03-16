#!/usr/bin/env python3
"""
Curate merchant links for top chargers.

Queries top chargers by session count and finds nearby merchants using
Google Places. Creates ChargerMerchant junction rows with walk times.

Usage:
    cd backend && python -m scripts.curate_top_chargers
    cd backend && python -m scripts.curate_top_chargers --limit 20 --radius 800
"""
import argparse
import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant
from app.models.session_event import SessionEvent
from sqlalchemy import func

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


def get_top_chargers(db, limit: int = 20):
    """Get top chargers by session count in last 30 days."""
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    results = db.query(
        SessionEvent.charger_id,
        func.count(SessionEvent.id).label('session_count'),
    ).filter(
        SessionEvent.charger_id.isnot(None),
        SessionEvent.session_start >= thirty_days_ago,
    ).group_by(SessionEvent.charger_id).order_by(
        func.count(SessionEvent.id).desc()
    ).limit(limit).all()

    charger_ids = [r[0] for r in results]
    chargers = db.query(Charger).filter(Charger.id.in_(charger_ids)).all()

    logger.info(f"Found {len(chargers)} top chargers by session count")
    return chargers


async def find_nearby_merchants_for_charger(charger, radius_m: int = 800):
    """Find nearby merchants for a charger using Google Places."""
    try:
        from app.services.google_places_new import search_nearby, get_place_details

        types = ["restaurant", "cafe", "store", "shopping_mall", "bakery", "bar"]
        results = await search_nearby(charger.lat, charger.lng, radius_m, types)

        merchants = []
        for place in results[:10]:  # Limit to 10 per charger
            place_id = place.get("place_id") or place.get("id")
            name = place.get("displayName", {}).get("text") or place.get("name", "Unknown")
            lat = place.get("location", {}).get("latitude") or place.get("lat")
            lng = place.get("location", {}).get("longitude") or place.get("lng")

            if not place_id or not lat or not lng:
                continue

            merchants.append({
                "place_id": place_id,
                "name": name,
                "lat": lat,
                "lng": lng,
                "types": place.get("types", []),
            })

        return merchants
    except Exception as e:
        logger.warning(f"Google Places search failed for charger {charger.id}: {e}")
        return []


def create_merchant_link(db, charger, merchant_data: dict):
    """Create Merchant + ChargerMerchant rows if not already linked."""
    from app.services.google_places_new import _haversine_distance
    import uuid

    place_id = merchant_data["place_id"]

    # Check if merchant exists
    merchant = db.query(Merchant).filter(Merchant.place_id == place_id).first()
    if not merchant:
        merchant = Merchant(
            id=f"m_{uuid.uuid4().hex[:12]}",
            name=merchant_data["name"],
            place_id=place_id,
            lat=merchant_data["lat"],
            lng=merchant_data["lng"],
            category=merchant_data["types"][0] if merchant_data["types"] else "other",
            place_types=merchant_data["types"],
        )
        db.add(merchant)
        db.flush()

    # Check if link exists
    existing = db.query(ChargerMerchant).filter(
        ChargerMerchant.charger_id == charger.id,
        ChargerMerchant.merchant_id == merchant.id,
    ).first()

    if existing:
        return False

    # Calculate distance
    distance_m = _haversine_distance(charger.lat, charger.lng, merchant.lat, merchant.lng)
    walk_time_s = int(distance_m / 1.33)  # ~80 m/min = 1.33 m/s

    link = ChargerMerchant(
        charger_id=charger.id,
        merchant_id=merchant.id,
        distance_m=distance_m,
        walk_duration_s=walk_time_s,
        walk_distance_m=distance_m,
    )
    db.add(link)
    return True


async def main():
    parser = argparse.ArgumentParser(description="Curate merchant links for top chargers")
    parser.add_argument("--limit", type=int, default=20, help="Number of top chargers to process")
    parser.add_argument("--radius", type=int, default=800, help="Search radius in meters")
    parser.add_argument("--dry-run", action="store_true", help="Don't commit changes")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        chargers = get_top_chargers(db, args.limit)

        if not chargers:
            # Fallback: just get all chargers
            chargers = db.query(Charger).limit(args.limit).all()
            logger.info(f"No session data; using first {len(chargers)} chargers")

        total_links = 0
        for charger in chargers:
            logger.info(f"Processing charger: {charger.name} ({charger.id})")
            merchants = await find_nearby_merchants_for_charger(charger, args.radius)

            for m in merchants:
                created = create_merchant_link(db, charger, m)
                if created:
                    total_links += 1
                    logger.info(f"  + Linked: {m['name']}")

        if args.dry_run:
            logger.info(f"DRY RUN: Would have created {total_links} merchant links")
            db.rollback()
        else:
            db.commit()
            logger.info(f"Created {total_links} new merchant links")

    except Exception as e:
        db.rollback()
        logger.error(f"Script failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
