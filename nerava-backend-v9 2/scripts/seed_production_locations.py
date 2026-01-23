#!/usr/bin/env python3
"""
Seed script for three production charger-merchant locations.

Locations:
1. Market Heights, Harker Heights, TX - The Heights Pizzeria (with exclusive)
2. Canyon Ridge, Austin, TX - Asadas Grill (with exclusive)
3. Century Oaks, Austin, TX - Starbucks (NO exclusive)

Usage:
    python scripts/seed_production_locations.py

Environment:
    DATABASE_URL - PostgreSQL connection string (required)
"""
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Production database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"
)

# ============================================================================
# LOCATION 1: Market Heights, Harker Heights, TX
# ============================================================================
LOCATION_1 = {
    "charger": {
        "id": "tesla_market_heights",
        "external_id": "tesla_sc_market_heights_tx",
        "name": "Tesla Supercharger - Market Heights",
        "network_name": "Tesla",
        "lat": 31.0571,
        "lng": -97.6650,
        "address": "201 E Central Texas Expy",
        "city": "Harker Heights",
        "state": "TX",
        "zip_code": "76548",
        "connector_types": ["Tesla", "NACS"],
        "power_kw": 250.0,
    },
    "merchant": {
        "id": "m_heights_pizzeria",
        "external_id": "ChIJ_heights_pizzeria_harker",
        "name": "The Heights Pizzeria & Drafthouse",
        "category": "restaurant",
        "lat": 31.0568,
        "lng": -97.6645,
        "address": "215 E Central Texas Expy",
        "city": "Harker Heights",
        "state": "TX",
        "zip_code": "76548",
        "photo_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800",
        "rating": 4.5,
        "price_level": 2,
        "place_types": ["restaurant", "food", "point_of_interest"],
        "primary_category": "food",
    },
    "link": {
        "distance_m": 50.0,
        "walk_duration_s": 60,
        "walk_distance_m": 65.0,
    },
    "perk": {
        "title": "Earn 15 Nova",
        "description": "Enjoy craft pizza while your Tesla charges. Show your Nerava app for 15 Nova reward!",
        "nova_reward": 1500,
    },
}

# ============================================================================
# LOCATION 2: Canyon Ridge, Austin, TX
# ============================================================================
LOCATION_2 = {
    "charger": {
        "id": "tesla_canyon_ridge",
        "external_id": "tesla_sc_canyon_ridge_austin",
        "name": "Tesla Supercharger - Canyon Ridge",
        "network_name": "Tesla",
        "lat": 30.3979,
        "lng": -97.7044,
        "address": "500 W Canyon Ridge Dr",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78753",
        "connector_types": ["Tesla", "NACS"],
        "power_kw": 250.0,
    },
    "merchant": {
        "id": "m_asadas_grill",
        "external_id": "ChIJKV41JMnORIYRu2cBs5CKtBc",
        "name": "Asadas Grill",
        "category": "restaurant",
        "lat": 30.4028,
        "lng": -97.6719,
        "address": "500 Canyon Ridge Dr",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78753",
        "photo_url": "/static/merchant_photos_asadas_grill/asadas_grill_01.jpg",
        "rating": 4.6,
        "price_level": 2,
        "place_types": ["restaurant", "mexican_restaurant", "food"],
        "primary_category": "food",
    },
    "link": {
        "distance_m": 150.0,
        "walk_duration_s": 120,
        "walk_distance_m": 200.0,
    },
    "perk": {
        "title": "Free Beverage Exclusive",
        "description": "Get a free beverage with any meal during charging hours. Show your pass to redeem.",
        "nova_reward": 500,
    },
}

# ============================================================================
# LOCATION 3: Century Oaks, Austin, TX (NO EXCLUSIVE)
# ============================================================================
LOCATION_3 = {
    "charger": {
        "id": "tesla_century_oaks",
        "external_id": "tesla_sc_century_oaks_austin",
        "name": "Tesla Supercharger - Century Oaks",
        "network_name": "Tesla",
        "lat": 30.4021,
        "lng": -97.7266,
        "address": "11410 Century Oaks Terrace",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78758",
        "connector_types": ["Tesla", "NACS"],
        "power_kw": 250.0,
    },
    "merchant": {
        "id": "m_starbucks_century_oaks",
        "external_id": "ChIJ_starbucks_century_oaks",
        "name": "Starbucks",
        "category": "coffee",
        "lat": 30.4025,
        "lng": -97.7262,
        "address": "11410 Century Oaks Terrace",
        "city": "Austin",
        "state": "TX",
        "zip_code": "78758",
        "photo_url": "https://images.unsplash.com/photo-1453614512568-c4024d13c247?w=800",
        "rating": 4.2,
        "price_level": 2,
        "place_types": ["cafe", "coffee_shop", "food"],
        "primary_category": "coffee",
    },
    "link": {
        "distance_m": 80.0,
        "walk_duration_s": 90,
        "walk_distance_m": 100.0,
    },
    "perk": None,  # NO EXCLUSIVE for Starbucks
}

ALL_LOCATIONS = [LOCATION_1, LOCATION_2, LOCATION_3]


def create_engine_connection():
    """Create database engine."""
    print(f"[DB] Connecting to database...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return engine


def upsert_charger(session, charger_data):
    """Create or update a charger."""
    charger_id = charger_data["id"]
    print(f"\n[Charger] Processing: {charger_data['name']}")

    result = session.execute(
        text("SELECT id FROM chargers WHERE id = :id"),
        {"id": charger_id}
    )
    existing = result.fetchone()

    params = {
        "id": charger_id,
        "external_id": charger_data["external_id"],
        "name": charger_data["name"],
        "network_name": charger_data["network_name"],
        "lat": charger_data["lat"],
        "lng": charger_data["lng"],
        "address": charger_data["address"],
        "city": charger_data["city"],
        "state": charger_data["state"],
        "zip_code": charger_data["zip_code"],
        "connector_types": json.dumps(charger_data["connector_types"]),
        "power_kw": charger_data["power_kw"],
        "is_public": True,
        "status": "available",
        "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Tesla_logo.png/800px-Tesla_logo.png",
    }

    if existing:
        print(f"  -> Updating existing charger")
        session.execute(
            text("""
                UPDATE chargers SET
                    external_id = :external_id, name = :name, network_name = :network_name,
                    lat = :lat, lng = :lng, address = :address, city = :city, state = :state,
                    zip_code = :zip_code, connector_types = CAST(:connector_types AS JSON),
                    power_kw = :power_kw, is_public = :is_public, status = :status,
                    logo_url = :logo_url, updated_at = NOW()
                WHERE id = :id
            """),
            params
        )
    else:
        print(f"  -> Creating new charger")
        session.execute(
            text("""
                INSERT INTO chargers (
                    id, external_id, name, network_name, lat, lng, address, city, state,
                    zip_code, connector_types, power_kw, is_public, status, logo_url,
                    created_at, updated_at
                ) VALUES (
                    :id, :external_id, :name, :network_name, :lat, :lng, :address, :city, :state,
                    :zip_code, CAST(:connector_types AS JSON), :power_kw, :is_public, :status, :logo_url,
                    NOW(), NOW()
                )
            """),
            params
        )

    print(f"  -> Done: {charger_id}")


def upsert_merchant(session, merchant_data, charger_id, link_data):
    """Create or update a merchant."""
    merchant_id = merchant_data["id"]
    print(f"\n[Merchant] Processing: {merchant_data['name']}")

    result = session.execute(
        text("SELECT id FROM merchants WHERE id = :id"),
        {"id": merchant_id}
    )
    existing = result.fetchone()

    params = {
        "id": merchant_id,
        "external_id": merchant_data["external_id"],
        "name": merchant_data["name"],
        "category": merchant_data["category"],
        "lat": merchant_data["lat"],
        "lng": merchant_data["lng"],
        "address": merchant_data["address"],
        "city": merchant_data["city"],
        "state": merchant_data["state"],
        "zip_code": merchant_data["zip_code"],
        "photo_url": merchant_data["photo_url"],
        "rating": merchant_data["rating"],
        "price_level": merchant_data["price_level"],
        "place_types": json.dumps(merchant_data["place_types"]),
        "primary_category": merchant_data["primary_category"],
        "nearest_charger_id": charger_id,
        "nearest_charger_distance_m": int(link_data["distance_m"]),
    }

    if existing:
        print(f"  -> Updating existing merchant")
        session.execute(
            text("""
                UPDATE merchants SET
                    external_id = :external_id, name = :name, category = :category,
                    lat = :lat, lng = :lng, address = :address, city = :city, state = :state,
                    zip_code = :zip_code, photo_url = :photo_url, rating = :rating,
                    price_level = :price_level, place_types = CAST(:place_types AS JSON),
                    primary_category = :primary_category, nearest_charger_id = :nearest_charger_id,
                    nearest_charger_distance_m = :nearest_charger_distance_m, updated_at = NOW()
                WHERE id = :id
            """),
            params
        )
    else:
        print(f"  -> Creating new merchant")
        session.execute(
            text("""
                INSERT INTO merchants (
                    id, external_id, name, category, lat, lng, address, city, state, zip_code,
                    photo_url, rating, price_level, place_types, primary_category,
                    nearest_charger_id, nearest_charger_distance_m, created_at, updated_at
                ) VALUES (
                    :id, :external_id, :name, :category, :lat, :lng, :address, :city, :state, :zip_code,
                    :photo_url, :rating, :price_level, CAST(:place_types AS JSON), :primary_category,
                    :nearest_charger_id, :nearest_charger_distance_m, NOW(), NOW()
                )
            """),
            params
        )

    print(f"  -> Done: {merchant_id}")


def upsert_charger_merchant(session, charger_id, merchant_id, link_data):
    """Create or update the charger-merchant association."""
    print(f"\n[Link] Processing: {charger_id} <-> {merchant_id}")

    result = session.execute(
        text("""
            SELECT id FROM charger_merchants
            WHERE charger_id = :charger_id AND merchant_id = :merchant_id
        """),
        {"charger_id": charger_id, "merchant_id": merchant_id}
    )
    existing = result.fetchone()

    params = {
        "charger_id": charger_id,
        "merchant_id": merchant_id,
        "distance_m": link_data["distance_m"],
        "walk_duration_s": link_data["walk_duration_s"],
        "walk_distance_m": link_data["walk_distance_m"],
    }

    if existing:
        print(f"  -> Updating existing link")
        session.execute(
            text("""
                UPDATE charger_merchants SET
                    distance_m = :distance_m, walk_duration_s = :walk_duration_s,
                    walk_distance_m = :walk_distance_m, updated_at = NOW()
                WHERE charger_id = :charger_id AND merchant_id = :merchant_id
            """),
            params
        )
    else:
        print(f"  -> Creating new link")
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
            params
        )

    print(f"  -> Done")


def upsert_perk(session, merchant_id, perk_data):
    """Create or update a merchant perk."""
    if perk_data is None:
        print(f"\n[Perk] Skipping (no exclusive for merchant: {merchant_id})")
        return

    print(f"\n[Perk] Processing: {perk_data['title']} for {merchant_id}")

    result = session.execute(
        text("""
            SELECT id FROM merchant_perks
            WHERE merchant_id = :merchant_id AND is_active = true
        """),
        {"merchant_id": merchant_id}
    )
    existing = result.fetchone()

    params = {
        "merchant_id": merchant_id,
        "title": perk_data["title"],
        "description": perk_data["description"],
        "nova_reward": perk_data["nova_reward"],
        "is_active": True,
    }

    if existing:
        print(f"  -> Updating existing perk")
        session.execute(
            text("""
                UPDATE merchant_perks SET
                    title = :title, description = :description, nova_reward = :nova_reward,
                    updated_at = NOW()
                WHERE merchant_id = :merchant_id AND is_active = true
            """),
            params
        )
    else:
        print(f"  -> Creating new perk")
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

    print(f"  -> Done")


def verify_data(session):
    """Verify all seeded data."""
    print("\n" + "=" * 60)
    print("VERIFICATION")
    print("=" * 60)

    for location in ALL_LOCATIONS:
        charger = location["charger"]
        merchant = location["merchant"]
        perk = location.get("perk")

        print(f"\n{charger['name']}:")

        # Check charger
        result = session.execute(
            text("SELECT name, city, state FROM chargers WHERE id = :id"),
            {"id": charger["id"]}
        )
        row = result.fetchone()
        if row:
            print(f"  Charger: {row[0]} ({row[1]}, {row[2]})")
        else:
            print(f"  ERROR: Charger not found!")

        # Check merchant
        result = session.execute(
            text("SELECT name, category FROM merchants WHERE id = :id"),
            {"id": merchant["id"]}
        )
        row = result.fetchone()
        if row:
            print(f"  Merchant: {row[0]} ({row[1]})")
        else:
            print(f"  ERROR: Merchant not found!")

        # Check link
        result = session.execute(
            text("""
                SELECT distance_m, walk_duration_s FROM charger_merchants
                WHERE charger_id = :charger_id AND merchant_id = :merchant_id
            """),
            {"charger_id": charger["id"], "merchant_id": merchant["id"]}
        )
        row = result.fetchone()
        if row:
            print(f"  Link: {row[0]}m, {row[1]}s walk")
        else:
            print(f"  ERROR: Link not found!")

        # Check perk
        if perk:
            result = session.execute(
                text("""
                    SELECT title, nova_reward FROM merchant_perks
                    WHERE merchant_id = :merchant_id AND is_active = true
                """),
                {"merchant_id": merchant["id"]}
            )
            row = result.fetchone()
            if row:
                print(f"  Perk: {row[0]} ({row[1]} Nova)")
            else:
                print(f"  ERROR: Perk not found!")
        else:
            print(f"  Perk: None (intentionally no exclusive)")


def main():
    """Main entry point."""
    print("=" * 60)
    print("SEEDING PRODUCTION LOCATIONS")
    print("=" * 60)
    print("\nLocations to seed:")
    print("  1. Market Heights, Harker Heights - The Heights Pizzeria (exclusive)")
    print("  2. Canyon Ridge, Austin - Asadas Grill (exclusive)")
    print("  3. Century Oaks, Austin - Starbucks (NO exclusive)")

    try:
        engine = create_engine_connection()
        Session = sessionmaker(bind=engine)
        session = Session()

        for location in ALL_LOCATIONS:
            charger = location["charger"]
            merchant = location["merchant"]
            link = location["link"]
            perk = location.get("perk")

            print(f"\n{'=' * 40}")
            print(f"Processing: {charger['name']}")
            print(f"{'=' * 40}")

            upsert_charger(session, charger)
            upsert_merchant(session, merchant, charger["id"], link)
            upsert_charger_merchant(session, charger["id"], merchant["id"], link)
            upsert_perk(session, merchant["id"], perk)

        # Commit all changes
        session.commit()
        print("\n[DB] All changes committed successfully!")

        # Verify
        verify_data(session)

        print("\n" + "=" * 60)
        print("SUCCESS! All locations seeded.")
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


