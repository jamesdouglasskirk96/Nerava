#!/usr/bin/env python3
"""
Seed a demo merchant if the database is empty.
Safe to run multiple times - only creates if no merchants exist.
"""
import os
import sys

sys.path.insert(0, '/app')

def main():
    """Seed demo merchant if database is empty."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not set, skipping demo merchant seed")
        return 0

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Check if demo merchant exists
            result = conn.execute(text("SELECT id FROM merchants WHERE id = 'demo-asadas-grill'"))
            row = result.fetchone()

            if row:
                print("Demo merchant already exists, skipping seed")
                return 0

            print("Seeding demo merchant and charger...")

            # Insert demo merchant - Asadas Grill
            # Uses only columns that exist in the merchants table (from while_you_charge.py model)
            conn.execute(text("""
                INSERT INTO merchants (
                    id, name, category, primary_category,
                    lat, lng, address,
                    place_id, place_types,
                    rating, user_rating_count,
                    short_code, region_code,
                    created_at, updated_at
                ) VALUES (
                    'demo-asadas-grill',
                    'Asadas Grill',
                    'restaurant',
                    'food',
                    30.4027, -97.6719,
                    '501 W Canyon Ridge Dr, Austin, TX 78753',
                    'ChIJA4UGPT_LRIYRjQC0TnNUWRg',
                    '["restaurant", "food", "point_of_interest", "establishment"]'::json,
                    4.5, 150,
                    'ASADAS', 'ATX',
                    NOW(), NOW()
                )
                ON CONFLICT (id) DO NOTHING
            """))

            # Insert demo charger
            conn.execute(text("""
                INSERT INTO chargers (
                    id, name, network_name,
                    lat, lng, address,
                    power_kw, connector_types, status,
                    is_public,
                    created_at, updated_at
                ) VALUES (
                    'demo-canyon-ridge',
                    'Canyon Ridge Supercharger',
                    'Tesla',
                    30.4027, -97.6719,
                    '501 W Canyon Ridge Dr, Austin, TX 78753',
                    150, '["Tesla"]'::json,
                    'available',
                    true,
                    NOW(), NOW()
                )
                ON CONFLICT (id) DO NOTHING
            """))

            # Link charger to merchant
            conn.execute(text("""
                INSERT INTO charger_merchants (
                    charger_id, merchant_id,
                    distance_m, walk_duration_s, is_primary,
                    created_at, updated_at
                ) VALUES (
                    'demo-canyon-ridge',
                    'demo-asadas-grill',
                    50, 60, true,
                    NOW(), NOW()
                )
                ON CONFLICT (charger_id, merchant_id) DO NOTHING
            """))

            conn.commit()
            print("Demo merchant and charger seeded successfully!")
            return 0

    except Exception as e:
        print(f"Error seeding demo merchant: {e}")
        import traceback
        traceback.print_exc()
        return 0  # Don't fail startup

if __name__ == "__main__":
    sys.exit(main())
