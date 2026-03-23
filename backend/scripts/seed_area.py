#!/usr/bin/env python3
"""
Seed merchants for a specific geographic area directly against the database.

Usage:
    python3 scripts/seed_area.py --lat 33.98 --lng -118.11 --radius 15
"""
import argparse
import json
import math
import urllib.request
import urllib.parse
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Walk speed: 80m/min
WALK_SPEED_M_PER_MIN = 80.0
MAX_WALK_DISTANCE_M = 800

CATEGORY_FALLBACK_PHOTOS = {
    "restaurant": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop",
    "cafe": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400&h=300&fit=crop",
    "bar": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=400&h=300&fit=crop",
    "fast_food": "https://images.unsplash.com/photo-1561758033-d89a9ad46330?w=400&h=300&fit=crop",
    "pub": "https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=400&h=300&fit=crop",
    "ice_cream": "https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=400&h=300&fit=crop",
    "bakery": "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&h=300&fit=crop",
    "supermarket": "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=400&h=300&fit=crop",
    "convenience": "https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=400&h=300&fit=crop",
    "mall": "https://images.unsplash.com/photo-1519567241046-7f570c474897?w=400&h=300&fit=crop",
    "clothes": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=400&h=300&fit=crop",
    "electronics": "https://images.unsplash.com/photo-1550009158-9ebf69173e03?w=400&h=300&fit=crop",
}
DEFAULT_PHOTO = "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=400&h=300&fit=crop"

TYPE_TO_CATEGORY = {
    "restaurant": "restaurant", "cafe": "coffee", "bar": "bar",
    "fast_food": "fast_food", "pub": "bar", "ice_cream": "dessert",
    "bakery": "bakery", "supermarket": "grocery", "convenience": "convenience",
    "mall": "shopping", "department_store": "shopping", "clothes": "shopping",
    "electronics": "shopping",
}


def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def fetch_overpass_pois(south, west, north, east):
    query = f"""[out:json][timeout:60];
(
  node["amenity"~"restaurant|cafe|bar|fast_food|pub|ice_cream|bakery"]{south},{west},{north},{east});
  node["shop"~"supermarket|convenience|mall|department_store|clothes|electronics"]{south},{west},{north},{east});
);
out body;"""
    # Fix: Overpass needs parens around bbox
    query = f"""[out:json][timeout:60];
(
  node["amenity"~"restaurant|cafe|bar|fast_food|pub|ice_cream|bakery"]({south},{west},{north},{east});
  node["shop"~"supermarket|convenience|mall|department_store|clothes|electronics"]({south},{west},{north},{east});
);
out body;"""

    url = 'https://overpass-api.de/api/interpreter'
    data = urllib.parse.urlencode({'data': query}).encode()
    req = urllib.request.Request(url, data=data, headers={'User-Agent': 'Nerava/1.0'})
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    return result.get('elements', [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lat', type=float, required=True)
    parser.add_argument('--lng', type=float, required=True)
    parser.add_argument('--radius', type=float, default=15, help='Radius in km')
    parser.add_argument('--db-url', type=str, default=None, help='Database URL (defaults to DATABASE_URL env)')
    parser.add_argument('--dry-run', action='store_true', help='Print what would be done without writing')
    args = parser.parse_args()

    db_url = args.db_url or os.getenv('DATABASE_URL')
    if not db_url:
        logger.error("Set DATABASE_URL or pass --db-url")
        sys.exit(1)

    # Connect to DB
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    from app.models.while_you_charge import Charger, Merchant, ChargerMerchant

    # Find chargers in radius
    lat_delta = args.radius / 111.0
    lng_delta = args.radius / (111.0 * max(math.cos(math.radians(args.lat)), 0.01))
    chargers = db.query(Charger).filter(
        Charger.lat.between(args.lat - lat_delta, args.lat + lat_delta),
        Charger.lng.between(args.lng - lng_delta, args.lng + lng_delta),
    ).all()

    # Filter to chargers without merchants
    charger_ids_with_merchants = set(
        row[0] for row in db.query(ChargerMerchant.charger_id)
        .filter(ChargerMerchant.charger_id.in_([c.id for c in chargers]))
        .distinct().all()
    )
    unmapped = [c for c in chargers if c.id not in charger_ids_with_merchants]

    logger.info(f"Found {len(chargers)} chargers in radius, {len(unmapped)} without merchants")

    if not unmapped:
        logger.info("All chargers already have merchants!")
        return

    # Build bounding box for Overpass query
    all_lats = [c.lat for c in unmapped]
    all_lngs = [c.lng for c in unmapped]
    south = min(all_lats) - 0.008
    north = max(all_lats) + 0.008
    west = min(all_lngs) - 0.008
    east = max(all_lngs) + 0.008

    logger.info(f"Querying Overpass for POIs in ({south:.4f},{west:.4f}) to ({north:.4f},{east:.4f})...")
    pois = fetch_overpass_pois(south, west, north, east)
    named_pois = [p for p in pois if p.get('tags', {}).get('name')]
    logger.info(f"Found {len(named_pois)} named POIs from Overpass")

    merchants_created = 0
    junctions_created = 0

    for poi in named_pois:
        tags = poi.get('tags', {})
        name = tags.get('name', '')
        poi_type = tags.get('amenity') or tags.get('shop') or 'other'
        osm_id = f"node_{poi['id']}"
        category = TYPE_TO_CATEGORY.get(poi_type, 'other')
        photo = CATEGORY_FALLBACK_PHOTOS.get(poi_type, DEFAULT_PHOTO)

        # Find or create merchant
        merchant = db.query(Merchant).filter(Merchant.place_id == osm_id).first()
        if not merchant:
            merchant_id = f"osm_{str(poi['id'])}"
            merchant = Merchant(
                id=merchant_id,
                external_id=osm_id,
                name=name,
                category=category,
                lat=poi['lat'],
                lng=poi['lon'],
                place_id=osm_id,
                phone=tags.get('phone'),
                website=tags.get('website'),
                photo_url=photo,
                primary_photo_url=photo,
                primary_category=category.split('_')[0].title() if category != 'other' else 'Local Business',
                description=f"{poi_type.replace('_', ' ').title()} near EV charging",
            )
            if not args.dry_run:
                db.add(merchant)
                db.flush()
            merchants_created += 1

        # Link to nearby chargers
        for charger in unmapped:
            dist = haversine(poi['lat'], poi['lon'], charger.lat, charger.lng)
            if dist > MAX_WALK_DISTANCE_M:
                continue

            # Check if junction exists
            existing = db.query(ChargerMerchant).filter(
                ChargerMerchant.charger_id == charger.id,
                ChargerMerchant.merchant_id == merchant.id,
            ).first()
            if existing:
                continue

            walk_seconds = int(dist / WALK_SPEED_M_PER_MIN * 60)
            if not args.dry_run:
                junction = ChargerMerchant(
                    charger_id=charger.id,
                    merchant_id=merchant.id,
                    distance_m=round(dist, 1),
                    walk_duration_s=walk_seconds,
                    walk_distance_m=round(dist * 1.3, 1),
                )
                db.add(junction)
            junctions_created += 1

    if not args.dry_run:
        db.commit()
        logger.info(f"DONE: {merchants_created} merchants created, {junctions_created} charger-merchant links created")
    else:
        logger.info(f"DRY RUN: would create {merchants_created} merchants, {junctions_created} links")

    db.close()


if __name__ == '__main__':
    main()
