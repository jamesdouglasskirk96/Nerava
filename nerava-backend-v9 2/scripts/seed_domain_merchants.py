#!/usr/bin/env python3
"""
Seed script for Domain Hub merchants with photo URLs.

Seeds real merchants near the Domain (Austin, TX) chargers with proper
photo URLs and links them to the Domain chargers.

Usage:
    python scripts/seed_domain_merchants.py
"""
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"
)

# Domain Hub Chargers (from domain_hub.py config)
DOMAIN_CHARGERS = [
    {"id": "ch_domain_tesla_001", "name": "Tesla Supercharger – Domain", "lat": 30.4021, "lng": -97.7265},
    {"id": "ch_domain_chargepoint_001", "name": "ChargePoint – Domain Shopping Center", "lat": 30.4039, "lng": -97.7252},
    {"id": "ch_domain_chargepoint_002", "name": "ChargePoint – Domain Parking Garage", "lat": 30.4012, "lng": -97.7245},
]

# Merchants near Domain with real photo URLs (using Unsplash for high-quality photos)
DOMAIN_MERCHANTS = [
    {
        "id": "m_domain_starbucks",
        "name": "Starbucks Reserve",
        "category": "coffee",
        "lat": 30.4025,
        "lng": -97.7260,
        "address": "11601 Domain Dr #100",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78758",
        "phone": "(512) 339-4040",
        "website": "https://starbucks.com",
        "photo_url": "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=800",
        "logo_url": "https://logo.clearbit.com/starbucks.com",
        "rating": 4.4,
        "price_level": 2,
        "place_types": ["cafe", "coffee_shop", "food", "point_of_interest"],
        "primary_category": "coffee",
    },
    {
        "id": "m_domain_shake_shack",
        "name": "Shake Shack",
        "category": "restaurant",
        "lat": 30.4028,
        "lng": -97.7255,
        "address": "11601 Domain Dr #130",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78758",
        "phone": "(512) 330-4080",
        "website": "https://shakeshack.com",
        "photo_url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800",
        "logo_url": "https://logo.clearbit.com/shakeshack.com",
        "rating": 4.3,
        "price_level": 2,
        "place_types": ["restaurant", "food", "point_of_interest"],
        "primary_category": "food",
    },
    {
        "id": "m_domain_north_italia",
        "name": "North Italia",
        "category": "restaurant",
        "lat": 30.4018,
        "lng": -97.7248,
        "address": "11506 Century Oaks Terrace #128",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78758",
        "phone": "(512) 339-6300",
        "website": "https://northitalia.com",
        "photo_url": "https://images.unsplash.com/photo-1555992336-fb0d29498b13?w=800",
        "logo_url": None,
        "rating": 4.5,
        "price_level": 3,
        "place_types": ["restaurant", "italian_restaurant", "food", "point_of_interest"],
        "primary_category": "food",
    },
    {
        "id": "m_domain_whole_foods",
        "name": "Whole Foods Market",
        "category": "grocery",
        "lat": 30.4015,
        "lng": -97.7270,
        "address": "11920 Domain Dr",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78758",
        "phone": "(512) 452-0222",
        "website": "https://wholefoodsmarket.com",
        "photo_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?w=800",
        "logo_url": "https://logo.clearbit.com/wholefoodsmarket.com",
        "rating": 4.3,
        "price_level": 3,
        "place_types": ["grocery_or_supermarket", "food", "store", "point_of_interest"],
        "primary_category": "other",
    },
    {
        "id": "m_domain_orange_theory",
        "name": "Orangetheory Fitness",
        "category": "gym",
        "lat": 30.4032,
        "lng": -97.7245,
        "address": "3220 Feathergrass Ct #140",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78758",
        "phone": "(512) 337-9800",
        "website": "https://orangetheory.com",
        "photo_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800",
        "logo_url": "https://logo.clearbit.com/orangetheory.com",
        "rating": 4.7,
        "price_level": 3,
        "place_types": ["gym", "fitness_center", "health", "point_of_interest"],
        "primary_category": "other",
    },
    {
        "id": "m_domain_true_food",
        "name": "True Food Kitchen",
        "category": "restaurant",
        "lat": 30.4022,
        "lng": -97.7240,
        "address": "11410 Century Oaks Terrace #104",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78758",
        "phone": "(512) 339-8001",
        "website": "https://truefoodkitchen.com",
        "photo_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=800",
        "logo_url": None,
        "rating": 4.4,
        "price_level": 2,
        "place_types": ["restaurant", "health_food", "food", "point_of_interest"],
        "primary_category": "food",
    },
]

# Charger-Merchant associations
# Each merchant is linked to the nearest charger(s) with walk times
CHARGER_MERCHANT_ASSOCIATIONS = [
    # Tesla Supercharger merchants
    {"charger_id": "ch_domain_tesla_001", "merchant_id": "m_domain_starbucks", "distance_m": 80, "walk_duration_s": 90, "walk_distance_m": 95},
    {"charger_id": "ch_domain_tesla_001", "merchant_id": "m_domain_shake_shack", "distance_m": 120, "walk_duration_s": 150, "walk_distance_m": 140},
    {"charger_id": "ch_domain_tesla_001", "merchant_id": "m_domain_north_italia", "distance_m": 180, "walk_duration_s": 200, "walk_distance_m": 210},
    {"charger_id": "ch_domain_tesla_001", "merchant_id": "m_domain_whole_foods", "distance_m": 150, "walk_duration_s": 180, "walk_distance_m": 175},
    {"charger_id": "ch_domain_tesla_001", "merchant_id": "m_domain_true_food", "distance_m": 220, "walk_duration_s": 270, "walk_distance_m": 250},

    # ChargePoint Shopping Center merchants
    {"charger_id": "ch_domain_chargepoint_001", "merchant_id": "m_domain_starbucks", "distance_m": 100, "walk_duration_s": 120, "walk_distance_m": 115},
    {"charger_id": "ch_domain_chargepoint_001", "merchant_id": "m_domain_shake_shack", "distance_m": 60, "walk_duration_s": 70, "walk_distance_m": 70},
    {"charger_id": "ch_domain_chargepoint_001", "merchant_id": "m_domain_orange_theory", "distance_m": 90, "walk_duration_s": 110, "walk_distance_m": 100},

    # ChargePoint Parking Garage merchants
    {"charger_id": "ch_domain_chargepoint_002", "merchant_id": "m_domain_north_italia", "distance_m": 70, "walk_duration_s": 85, "walk_distance_m": 80},
    {"charger_id": "ch_domain_chargepoint_002", "merchant_id": "m_domain_true_food", "distance_m": 50, "walk_duration_s": 60, "walk_distance_m": 55},
    {"charger_id": "ch_domain_chargepoint_002", "merchant_id": "m_domain_whole_foods", "distance_m": 200, "walk_duration_s": 240, "walk_distance_m": 230},
]

# Perks for merchants
MERCHANT_PERKS = [
    {"merchant_id": "m_domain_starbucks", "title": "Earn 12 Nova", "description": "Get Nova rewards when you visit while charging", "nova_reward": 1200},
    {"merchant_id": "m_domain_shake_shack", "title": "Earn 15 Nova", "description": "Enjoy a burger while you charge", "nova_reward": 1500},
    {"merchant_id": "m_domain_north_italia", "title": "Earn 20 Nova", "description": "Fine Italian dining rewards", "nova_reward": 2000},
    {"merchant_id": "m_domain_whole_foods", "title": "Earn 10 Nova", "description": "Groceries while you charge", "nova_reward": 1000},
    {"merchant_id": "m_domain_orange_theory", "title": "Earn 25 Nova", "description": "Workout while your car charges", "nova_reward": 2500},
    {"merchant_id": "m_domain_true_food", "title": "Earn 18 Nova", "description": "Healthy food rewards", "nova_reward": 1800},
]


def create_engine_connection():
    print(f"[DB] Connecting to: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return engine


def upsert_merchant(session, merchant):
    """Insert or update a merchant."""
    result = session.execute(
        text("SELECT id FROM merchants WHERE id = :id"),
        {"id": merchant["id"]}
    )
    existing = result.fetchone()

    params = {
        "id": merchant["id"],
        "external_id": f"seed_{merchant['id']}",
        "name": merchant["name"],
        "category": merchant["category"],
        "lat": merchant["lat"],
        "lng": merchant["lng"],
        "address": merchant["address"],
        "city": merchant["city"],
        "state": merchant["state"],
        "zip_code": merchant["zip_code"],
        "logo_url": merchant.get("logo_url"),
        "photo_url": merchant["photo_url"],
        "rating": merchant.get("rating"),
        "price_level": merchant.get("price_level"),
        "phone": merchant.get("phone"),
        "website": merchant.get("website"),
        "place_types": json.dumps(merchant.get("place_types", [])),
        "primary_category": merchant.get("primary_category", "other"),
    }

    if existing:
        session.execute(
            text("""
                UPDATE merchants SET
                    external_id = :external_id,
                    name = :name,
                    category = :category,
                    lat = :lat,
                    lng = :lng,
                    address = :address,
                    city = :city,
                    state = :state,
                    zip_code = :zip_code,
                    logo_url = :logo_url,
                    photo_url = :photo_url,
                    rating = :rating,
                    price_level = :price_level,
                    phone = :phone,
                    website = :website,
                    place_types = CAST(:place_types AS JSON),
                    primary_category = :primary_category,
                    updated_at = NOW()
                WHERE id = :id
            """),
            params
        )
        return "updated"
    else:
        session.execute(
            text("""
                INSERT INTO merchants (
                    id, external_id, name, category, lat, lng, address, city, state, zip_code,
                    logo_url, photo_url, rating, price_level, phone, website, place_types,
                    primary_category, created_at, updated_at
                ) VALUES (
                    :id, :external_id, :name, :category, :lat, :lng, :address, :city, :state, :zip_code,
                    :logo_url, :photo_url, :rating, :price_level, :phone, :website, CAST(:place_types AS JSON),
                    :primary_category, NOW(), NOW()
                )
            """),
            params
        )
        return "inserted"


def upsert_charger_merchant(session, assoc):
    """Insert or update a charger-merchant association."""
    result = session.execute(
        text("""
            SELECT id FROM charger_merchants
            WHERE charger_id = :charger_id AND merchant_id = :merchant_id
        """),
        {"charger_id": assoc["charger_id"], "merchant_id": assoc["merchant_id"]}
    )
    existing = result.fetchone()

    if existing:
        session.execute(
            text("""
                UPDATE charger_merchants SET
                    distance_m = :distance_m,
                    walk_duration_s = :walk_duration_s,
                    walk_distance_m = :walk_distance_m,
                    updated_at = NOW()
                WHERE charger_id = :charger_id AND merchant_id = :merchant_id
            """),
            assoc
        )
        return "updated"
    else:
        session.execute(
            text("""
                INSERT INTO charger_merchants (
                    charger_id, merchant_id, distance_m, walk_duration_s, walk_distance_m,
                    created_at, updated_at
                ) VALUES (
                    :charger_id, :merchant_id, :distance_m, :walk_duration_s, :walk_distance_m,
                    NOW(), NOW()
                )
            """),
            assoc
        )
        return "inserted"


def upsert_perk(session, perk):
    """Insert or update a merchant perk."""
    result = session.execute(
        text("""
            SELECT id FROM merchant_perks
            WHERE merchant_id = :merchant_id AND is_active = true
        """),
        {"merchant_id": perk["merchant_id"]}
    )
    existing = result.fetchone()

    params = {
        "merchant_id": perk["merchant_id"],
        "title": perk["title"],
        "description": perk["description"],
        "nova_reward": perk["nova_reward"],
        "is_active": True,
    }

    if existing:
        session.execute(
            text("""
                UPDATE merchant_perks SET
                    title = :title,
                    description = :description,
                    nova_reward = :nova_reward,
                    updated_at = NOW()
                WHERE merchant_id = :merchant_id AND is_active = true
            """),
            params
        )
        return "updated"
    else:
        session.execute(
            text("""
                INSERT INTO merchant_perks (
                    merchant_id, title, description, nova_reward, is_active,
                    created_at, updated_at
                ) VALUES (
                    :merchant_id, :title, :description, :nova_reward, :is_active,
                    NOW(), NOW()
                )
            """),
            params
        )
        return "inserted"


def main():
    print("=" * 60)
    print("Seeding Domain Hub Merchants")
    print("Austin, TX - The Domain")
    print("=" * 60)

    try:
        engine = create_engine_connection()
        Session = sessionmaker(bind=engine)
        session = Session()

        # Seed merchants
        print("\n[Merchants] Seeding merchants...")
        for merchant in DOMAIN_MERCHANTS:
            result = upsert_merchant(session, merchant)
            print(f"  {result}: {merchant['name']}")

        # Seed charger-merchant associations
        print("\n[Associations] Seeding charger-merchant links...")
        for assoc in CHARGER_MERCHANT_ASSOCIATIONS:
            result = upsert_charger_merchant(session, assoc)
            print(f"  {result}: {assoc['charger_id']} -> {assoc['merchant_id']}")

        # Seed perks
        print("\n[Perks] Seeding merchant perks...")
        for perk in MERCHANT_PERKS:
            result = upsert_perk(session, perk)
            print(f"  {result}: {perk['merchant_id']} - {perk['title']}")

        # Commit
        session.commit()
        print("\n[DB] All changes committed successfully!")

        # Verify
        print("\n[Verify] Checking seeded data...")

        result = session.execute(text("""
            SELECT c.name, COUNT(cm.merchant_id) as merchant_count
            FROM chargers c
            LEFT JOIN charger_merchants cm ON cm.charger_id = c.id
            WHERE c.id LIKE 'ch_domain%'
            GROUP BY c.id, c.name
        """))
        charger_stats = result.fetchall()

        print("  Domain chargers and merchant counts:")
        for row in charger_stats:
            print(f"    {row[0]}: {row[1]} merchants")

        result = session.execute(text("""
            SELECT COUNT(*) FROM merchants WHERE photo_url IS NOT NULL
        """))
        photo_count = result.fetchone()[0]
        print(f"\n  Merchants with photos: {photo_count}")

        print("\n" + "=" * 60)
        print("SUCCESS! Domain hub merchants seeded successfully.")
        print("=" * 60)

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'session' in locals():
            session.close()


if __name__ == "__main__":
    main()
