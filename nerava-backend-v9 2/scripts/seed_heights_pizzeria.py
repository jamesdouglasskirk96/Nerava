#!/usr/bin/env python3
"""
Seed script for The Heights Pizzeria & Drafthouse as primary merchant
for Market Heights Tesla Supercharger in Harker Heights, TX.

Usage:
    python scripts/seed_heights_pizzeria.py

Environment:
    DATABASE_URL - PostgreSQL connection string (required)
"""
import os
import sys
import json
import uuid
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Production database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"
)

# Market Heights Tesla Supercharger data (Harker Heights, TX)
CHARGER_DATA = {
    "id": "tesla_market_heights",
    "external_id": "tesla_sc_market_heights_tx",
    "name": "Tesla Supercharger - Market Heights",
    "network_name": "Tesla",
    "lat": 31.0571,  # Harker Heights, TX coordinates
    "lng": -97.6650,
    "address": "201 E Central Texas Expy",
    "city": "Harker Heights",
    "state": "TX",
    "zip_code": "76548",
    "connector_types": ["Tesla", "NACS"],
    "power_kw": 250.0,
    "is_public": True,
    "status": "available",
    "logo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e8/Tesla_logo.png/800px-Tesla_logo.png"
}

# The Heights Pizzeria & Drafthouse data
MERCHANT_DATA = {
    "id": "m_heights_pizzeria",
    "external_id": "ChIJExample_HeightsPizzeria",  # Would be real Google Places ID
    "name": "The Heights Pizzeria & Drafthouse",
    "category": "restaurant",
    "lat": 31.0568,  # Very close to the charger
    "lng": -97.6645,
    "address": "215 E Central Texas Expy",
    "city": "Harker Heights",
    "state": "TX",
    "zip_code": "76548",
    "logo_url": None,
    "photo_url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800",  # Pizza photo
    "rating": 4.5,
    "price_level": 2,  # $$
    "phone": "(254) 953-7000",
    "website": "https://theheightspizzeria.com",
    "place_types": ["restaurant", "food", "point_of_interest", "establishment"],
    "primary_category": "food",
}

# Charger-Merchant association
CHARGER_MERCHANT_DATA = {
    "charger_id": CHARGER_DATA["id"],
    "merchant_id": MERCHANT_DATA["id"],
    "distance_m": 50.0,  # 50 meters (very close)
    "walk_duration_s": 60,  # 1 minute walk
    "walk_distance_m": 65.0,
}

# Perk data for the merchant
PERK_DATA = {
    "merchant_id": MERCHANT_DATA["id"],
    "title": "Earn 15 Nova",
    "description": "Enjoy craft pizza while your Tesla charges. Show your Nerava app for 15 Nova reward!",
    "nova_reward": 1500,  # 15 Nova in cents
    "is_active": True,
}


def create_engine_connection():
    """Create database engine."""
    print(f"[DB] Connecting to: {DATABASE_URL[:50]}...")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return engine


def seed_charger(session):
    """Create or update the charger."""
    print("\n[Charger] Checking for existing charger...")

    result = session.execute(
        text("SELECT id FROM chargers WHERE id = :id"),
        {"id": CHARGER_DATA["id"]}
    )
    existing = result.fetchone()

    # Prepare parameters with proper JSON
    params = {
        "id": CHARGER_DATA["id"],
        "external_id": CHARGER_DATA["external_id"],
        "name": CHARGER_DATA["name"],
        "network_name": CHARGER_DATA["network_name"],
        "lat": CHARGER_DATA["lat"],
        "lng": CHARGER_DATA["lng"],
        "address": CHARGER_DATA["address"],
        "city": CHARGER_DATA["city"],
        "state": CHARGER_DATA["state"],
        "zip_code": CHARGER_DATA["zip_code"],
        "connector_types": json.dumps(CHARGER_DATA["connector_types"]),
        "power_kw": CHARGER_DATA["power_kw"],
        "is_public": CHARGER_DATA["is_public"],
        "status": CHARGER_DATA["status"],
        "logo_url": CHARGER_DATA["logo_url"],
    }

    if existing:
        print(f"[Charger] Updating existing charger: {CHARGER_DATA['name']}")
        session.execute(
            text("""
                UPDATE chargers SET
                    external_id = :external_id,
                    name = :name,
                    network_name = :network_name,
                    lat = :lat,
                    lng = :lng,
                    address = :address,
                    city = :city,
                    state = :state,
                    zip_code = :zip_code,
                    connector_types = CAST(:connector_types AS JSON),
                    power_kw = :power_kw,
                    is_public = :is_public,
                    status = :status,
                    logo_url = :logo_url,
                    updated_at = NOW()
                WHERE id = :id
            """),
            params
        )
    else:
        print(f"[Charger] Creating new charger: {CHARGER_DATA['name']}")
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

    print(f"[Charger] Done: {CHARGER_DATA['id']}")


def seed_merchant(session):
    """Create or update the merchant."""
    print("\n[Merchant] Checking for existing merchant...")

    result = session.execute(
        text("SELECT id FROM merchants WHERE id = :id"),
        {"id": MERCHANT_DATA["id"]}
    )
    existing = result.fetchone()

    # Prepare parameters with proper JSON
    params = {
        "id": MERCHANT_DATA["id"],
        "external_id": MERCHANT_DATA["external_id"],
        "name": MERCHANT_DATA["name"],
        "category": MERCHANT_DATA["category"],
        "lat": MERCHANT_DATA["lat"],
        "lng": MERCHANT_DATA["lng"],
        "address": MERCHANT_DATA["address"],
        "city": MERCHANT_DATA["city"],
        "state": MERCHANT_DATA["state"],
        "zip_code": MERCHANT_DATA["zip_code"],
        "logo_url": MERCHANT_DATA["logo_url"],
        "photo_url": MERCHANT_DATA["photo_url"],
        "rating": MERCHANT_DATA["rating"],
        "price_level": MERCHANT_DATA["price_level"],
        "phone": MERCHANT_DATA["phone"],
        "website": MERCHANT_DATA["website"],
        "place_types": json.dumps(MERCHANT_DATA["place_types"]),
        "primary_category": MERCHANT_DATA["primary_category"],
        "nearest_charger_id": CHARGER_DATA["id"],
        "nearest_charger_distance_m": int(CHARGER_MERCHANT_DATA["distance_m"]),
    }

    if existing:
        print(f"[Merchant] Updating existing merchant: {MERCHANT_DATA['name']}")
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
                    nearest_charger_id = :nearest_charger_id,
                    nearest_charger_distance_m = :nearest_charger_distance_m,
                    updated_at = NOW()
                WHERE id = :id
            """),
            params
        )
    else:
        print(f"[Merchant] Creating new merchant: {MERCHANT_DATA['name']}")
        session.execute(
            text("""
                INSERT INTO merchants (
                    id, external_id, name, category, lat, lng, address, city, state, zip_code,
                    logo_url, photo_url, rating, price_level, phone, website, place_types,
                    primary_category, nearest_charger_id, nearest_charger_distance_m,
                    created_at, updated_at
                ) VALUES (
                    :id, :external_id, :name, :category, :lat, :lng, :address, :city, :state, :zip_code,
                    :logo_url, :photo_url, :rating, :price_level, :phone, :website, CAST(:place_types AS JSON),
                    :primary_category, :nearest_charger_id, :nearest_charger_distance_m,
                    NOW(), NOW()
                )
            """),
            params
        )

    print(f"[Merchant] Done: {MERCHANT_DATA['id']}")


def seed_charger_merchant(session):
    """Create or update the charger-merchant association."""
    print("\n[ChargerMerchant] Checking for existing association...")

    result = session.execute(
        text("""
            SELECT id FROM charger_merchants
            WHERE charger_id = :charger_id AND merchant_id = :merchant_id
        """),
        {
            "charger_id": CHARGER_MERCHANT_DATA["charger_id"],
            "merchant_id": CHARGER_MERCHANT_DATA["merchant_id"],
        }
    )
    existing = result.fetchone()

    if existing:
        print(f"[ChargerMerchant] Updating existing association")
        session.execute(
            text("""
                UPDATE charger_merchants SET
                    distance_m = :distance_m,
                    walk_duration_s = :walk_duration_s,
                    walk_distance_m = :walk_distance_m,
                    updated_at = NOW()
                WHERE charger_id = :charger_id AND merchant_id = :merchant_id
            """),
            CHARGER_MERCHANT_DATA
        )
    else:
        print(f"[ChargerMerchant] Creating new association")
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
            CHARGER_MERCHANT_DATA
        )

    print(f"[ChargerMerchant] Done: {CHARGER_MERCHANT_DATA['charger_id']} <-> {CHARGER_MERCHANT_DATA['merchant_id']}")


def seed_perk(session):
    """Create or update the merchant perk."""
    print("\n[MerchantPerk] Checking for existing perk...")

    result = session.execute(
        text("""
            SELECT id FROM merchant_perks
            WHERE merchant_id = :merchant_id AND is_active = true
        """),
        {"merchant_id": PERK_DATA["merchant_id"]}
    )
    existing = result.fetchone()

    if existing:
        print(f"[MerchantPerk] Updating existing perk")
        session.execute(
            text("""
                UPDATE merchant_perks SET
                    title = :title,
                    description = :description,
                    nova_reward = :nova_reward,
                    updated_at = NOW()
                WHERE merchant_id = :merchant_id AND is_active = true
            """),
            PERK_DATA
        )
    else:
        print(f"[MerchantPerk] Creating new perk")
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
            PERK_DATA
        )

    print(f"[MerchantPerk] Done: {PERK_DATA['title']}")


def verify_data(session):
    """Verify the seeded data."""
    print("\n[Verify] Checking seeded data...")

    # Check charger
    result = session.execute(
        text("SELECT id, name, city, state FROM chargers WHERE id = :id"),
        {"id": CHARGER_DATA["id"]}
    )
    charger = result.fetchone()
    if charger:
        print(f"  Charger: {charger[1]} ({charger[2]}, {charger[3]})")
    else:
        print("  ERROR: Charger not found!")

    # Check merchant
    result = session.execute(
        text("SELECT id, name, photo_url FROM merchants WHERE id = :id"),
        {"id": MERCHANT_DATA["id"]}
    )
    merchant = result.fetchone()
    if merchant:
        print(f"  Merchant: {merchant[1]}")
        print(f"  Photo URL: {merchant[2][:50]}..." if merchant[2] else "  Photo URL: None")
    else:
        print("  ERROR: Merchant not found!")

    # Check association
    result = session.execute(
        text("""
            SELECT cm.distance_m, cm.walk_duration_s, m.name
            FROM charger_merchants cm
            JOIN merchants m ON m.id = cm.merchant_id
            WHERE cm.charger_id = :charger_id
            ORDER BY cm.distance_m ASC
        """),
        {"charger_id": CHARGER_DATA["id"]}
    )
    associations = result.fetchall()
    print(f"  Merchants near charger: {len(associations)}")
    for assoc in associations:
        print(f"    - {assoc[2]}: {assoc[0]}m, {assoc[1]}s walk")

    # Check perk
    result = session.execute(
        text("""
            SELECT title, nova_reward, is_active
            FROM merchant_perks
            WHERE merchant_id = :merchant_id AND is_active = true
        """),
        {"merchant_id": MERCHANT_DATA["id"]}
    )
    perks = result.fetchall()
    print(f"  Active perks: {len(perks)}")
    for perk in perks:
        print(f"    - {perk[0]}: {perk[1]} Nova")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Seeding The Heights Pizzeria & Drafthouse")
    print("Market Heights Tesla Supercharger, Harker Heights, TX")
    print("=" * 60)

    try:
        engine = create_engine_connection()
        Session = sessionmaker(bind=engine)
        session = Session()

        # Seed data
        seed_charger(session)
        seed_merchant(session)
        seed_charger_merchant(session)
        seed_perk(session)

        # Commit all changes
        session.commit()
        print("\n[DB] All changes committed successfully!")

        # Verify
        verify_data(session)

        print("\n" + "=" * 60)
        print("SUCCESS! Data seeded successfully.")
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
