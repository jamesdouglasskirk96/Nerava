#!/usr/bin/env python3
"""
Seed merchants for specific cities using chargers already in the DB.

Instead of seeding the entire US (slow, times out), this targets specific cities
by querying chargers within known bounding boxes and running the Overpass-based
merchant seeder only for those chargers.

Usage:
    cd backend
    python -m scripts.seed_merchants_city --city houston
    python -m scripts.seed_merchants_city --city houston --city austin --city dallas
    python -m scripts.seed_merchants_city  # runs all target cities
"""
import argparse
import asyncio
import logging
import sys

sys.path.insert(0, ".")

logger = logging.getLogger(__name__)

# City bounding boxes: (south_lat, north_lat, west_lng, east_lng)
CITY_BBOXES = {
    # Texas
    "houston": (29.52, 30.11, -95.79, -95.01),
    "austin": (30.10, 30.52, -97.94, -97.56),
    "dallas": (32.62, 33.02, -97.00, -96.46),
    "san_antonio": (29.28, 29.62, -98.70, -98.35),
    # Arizona
    "phoenix": (33.29, 33.70, -112.33, -111.79),
    # Florida
    "miami": (25.65, 25.90, -80.35, -80.12),
    "fort_lauderdale": (26.05, 26.25, -80.25, -80.08),
    "west_palm_beach": (26.60, 26.78, -80.15, -80.02),
    "orlando": (28.35, 28.65, -81.50, -81.20),
    "tampa": (27.85, 28.10, -82.55, -82.35),
    "jacksonville": (30.20, 30.45, -81.80, -81.50),
    "st_petersburg": (27.70, 27.82, -82.72, -82.60),
    "naples": (26.10, 26.25, -81.82, -81.70),
    "sarasota": (27.28, 27.40, -82.58, -82.48),
    "tallahassee": (30.38, 30.52, -84.35, -84.18),
    # California
    "los_angeles": (33.70, 34.34, -118.67, -117.76),
    "san_francisco": (37.63, 37.83, -122.52, -122.35),
    "san_jose": (37.20, 37.45, -122.05, -121.73),
    "san_diego": (32.62, 33.02, -117.28, -116.90),
    "sacramento": (38.44, 38.70, -121.56, -121.30),
    "oakland": (37.73, 37.88, -122.35, -122.11),
    "fresno": (36.65, 36.85, -119.88, -119.68),
    "bakersfield": (35.30, 35.45, -119.12, -118.90),
    "riverside": (33.85, 34.05, -117.50, -117.30),
    "irvine": (33.60, 33.75, -117.85, -117.68),
}

ALL_CITIES = list(CITY_BBOXES.keys())


def get_chargers_in_bbox(db, south, north, west, east):
    """Query chargers within a bounding box."""
    from app.models.while_you_charge import Charger

    return (
        db.query(Charger)
        .filter(
            Charger.lat.between(south, north),
            Charger.lng.between(west, east),
        )
        .all()
    )


async def seed_city(db, city_name: str) -> dict:
    """Seed merchants for a single city."""
    from scripts.seed_merchants_free import seed_merchants

    bbox = CITY_BBOXES.get(city_name)
    if not bbox:
        logger.error(f"Unknown city: {city_name}. Available: {list(CITY_BBOXES.keys())}")
        return {"city": city_name, "error": "unknown_city"}

    south, north, west, east = bbox
    chargers = get_chargers_in_bbox(db, south, north, west, east)
    logger.info(f"[CitySeed] {city_name}: found {len(chargers)} chargers in bbox")

    if not chargers:
        logger.warning(f"[CitySeed] {city_name}: no chargers found — skip")
        return {"city": city_name, "chargers": 0, "skipped": True}

    def on_progress(done, total):
        logger.info(f"[CitySeed] {city_name}: {done}/{total} cells processed")

    result = await seed_merchants(
        db,
        chargers_override=chargers,
        progress_callback=on_progress,
    )
    result["city"] = city_name
    result["chargers_in_bbox"] = len(chargers)
    return result


async def main(cities: list[str]):
    from app.db import SessionLocal

    db = SessionLocal()
    try:
        results = []
        for city in cities:
            logger.info(f"\n{'='*50}\n[CitySeed] Starting: {city}\n{'='*50}")
            result = await seed_city(db, city)
            results.append(result)
            logger.info(f"[CitySeed] {city} result: {result}")

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        total_merchants = 0
        total_junctions = 0
        for r in results:
            city = r.get("city", "?")
            if r.get("skipped"):
                print(f"  {city}: SKIPPED (no chargers)")
            elif r.get("error"):
                print(f"  {city}: ERROR — {r['error']}")
            else:
                mc = r.get("merchants_created", 0)
                jc = r.get("junctions_created", 0)
                ch = r.get("chargers_in_bbox", 0)
                total_merchants += mc
                total_junctions += jc
                print(f"  {city}: {ch} chargers, {mc} merchants created, {jc} junctions")
        print(f"\n  TOTAL: {total_merchants} merchants, {total_junctions} junctions")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed merchants for specific cities")
    parser.add_argument(
        "--city",
        action="append",
        choices=list(CITY_BBOXES.keys()),
        help="City to seed (can specify multiple). Defaults to all target cities.",
    )
    args = parser.parse_args()

    cities = args.city if args.city else ALL_CITIES

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    print(f"Seeding merchants for: {', '.join(cities)}")
    asyncio.run(main(cities))
