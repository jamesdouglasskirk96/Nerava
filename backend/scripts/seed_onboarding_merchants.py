#!/usr/bin/env python3
"""
Seed onboarding merchants and their nearby chargers.
Safe to run multiple times - uses ON CONFLICT DO NOTHING.
"""
import os
import sys

sys.path.insert(0, '/app')

# Charger and merchant data for onboarding
CHARGERS_AND_MERCHANTS = [
    {
        "charger": {
            "id": "charger_ben_white_tesla",
            "name": "Tesla Supercharger - Ben White",
            "network_name": "Tesla",
            "lat": 30.2260,
            "lng": -97.7480,
            "address": "2201 E Ben White Blvd, Austin, TX 78744",
            "power_kw": 250,
        },
        "merchants": [
            {
                "id": "m_pinthouse_brewery",
                "name": "Pinthouse Brewery",
                "category": "brewery",
                "primary_category": "food",
                "lat": 30.2265,
                "lng": -97.7475,
                "address": "2201 E Ben White Blvd, Austin, TX 78744",
                "short_code": "PINTHOUSE",
                "distance_m": 50,
                "walk_duration_s": 60,
            }
        ]
    },
    {
        "charger": {
            "id": "charger_south_congress_tesla",
            "name": "Tesla Supercharger - South Congress",
            "network_name": "Tesla",
            "lat": 30.2475,
            "lng": -97.7530,
            "address": "1603 S Congress Ave, Austin, TX 78704",
            "power_kw": 250,
        },
        "merchants": [
            {
                "id": "m_maie_day_steakhouse",
                "name": "Maie Day Steakhouse",
                "category": "steakhouse",
                "primary_category": "food",
                "lat": 30.2478,
                "lng": -97.7528,
                "address": "1603 S Congress Ave, Austin, TX 78704",
                "short_code": "MAIEDAY",
                "distance_m": 40,
                "walk_duration_s": 45,
            }
        ]
    },
    {
        "charger": {
            "id": "charger_mopac_tesla",
            "name": "Tesla Supercharger - Mopac",
            "network_name": "Tesla",
            "lat": 30.3905,
            "lng": -97.7330,
            "address": "10515 N Mopac Expy, Austin, TX 78759",
            "power_kw": 250,
        },
        "merchants": [
            {
                "id": "m_might_fine_burgers",
                "name": "Might Fine Burgers",
                "category": "restaurant",
                "primary_category": "food",
                "lat": 30.3908,
                "lng": -97.7332,
                "address": "10515 N Mopac Expy, Austin, TX 78759",
                "short_code": "MIGHTFINE",
                "distance_m": 35,
                "walk_duration_s": 40,
            },
            {
                "id": "m_bella_vita_ice_cream",
                "name": "Bella Vita Ice Cream",
                "category": "ice_cream",
                "primary_category": "food",
                "lat": 30.3906,
                "lng": -97.7334,
                "address": "10515 N Mopac Expy, Austin, TX 78759",
                "short_code": "BELLAVITA",
                "distance_m": 45,
                "walk_duration_s": 50,
            }
        ]
    },
    {
        "charger": {
            "id": "charger_market_heights_tesla",
            "name": "Tesla Supercharger - Market Heights",
            "network_name": "Tesla",
            "lat": 31.0571,
            "lng": -97.6650,
            "address": "201 E Central Texas Expy, Harker Heights, TX 76548",
            "power_kw": 250,
        },
        "merchants": [
            {
                "id": "m_heights_pizzeria",
                "name": "The Heights Pizzeria",
                "category": "pizzeria",
                "primary_category": "food",
                "lat": 31.0573,
                "lng": -97.6648,
                "address": "201 E Central Texas Expy, Harker Heights, TX 76548",
                "short_code": "HEIGHTS",
                "distance_m": 30,
                "walk_duration_s": 35,
            }
        ]
    },
]


def main():
    """Seed onboarding merchants and chargers."""
    from sqlalchemy import create_engine, text

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not set, skipping onboarding merchant seed")
        return 0

    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            for entry in CHARGERS_AND_MERCHANTS:
                charger = entry["charger"]
                merchants = entry["merchants"]

                print(f"Seeding charger: {charger['name']}")

                # Insert charger
                conn.execute(text("""
                    INSERT INTO chargers (
                        id, name, network_name,
                        lat, lng, address,
                        power_kw, connector_types, status,
                        is_public,
                        created_at, updated_at
                    ) VALUES (
                        :id, :name, :network_name,
                        :lat, :lng, :address,
                        :power_kw, '["Tesla"]'::json, 'available',
                        true,
                        NOW(), NOW()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        lat = EXCLUDED.lat,
                        lng = EXCLUDED.lng,
                        address = EXCLUDED.address,
                        updated_at = NOW()
                """), {
                    "id": charger["id"],
                    "name": charger["name"],
                    "network_name": charger["network_name"],
                    "lat": charger["lat"],
                    "lng": charger["lng"],
                    "address": charger["address"],
                    "power_kw": charger["power_kw"],
                })

                for merchant in merchants:
                    print(f"  Seeding merchant: {merchant['name']}")

                    # Insert merchant
                    conn.execute(text("""
                        INSERT INTO merchants (
                            id, name, category, primary_category,
                            lat, lng, address,
                            short_code, region_code,
                            rating, user_rating_count,
                            created_at, updated_at
                        ) VALUES (
                            :id, :name, :category, :primary_category,
                            :lat, :lng, :address,
                            :short_code, 'ATX',
                            4.5, 100,
                            NOW(), NOW()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            lat = EXCLUDED.lat,
                            lng = EXCLUDED.lng,
                            address = EXCLUDED.address,
                            updated_at = NOW()
                    """), {
                        "id": merchant["id"],
                        "name": merchant["name"],
                        "category": merchant["category"],
                        "primary_category": merchant["primary_category"],
                        "lat": merchant["lat"],
                        "lng": merchant["lng"],
                        "address": merchant["address"],
                        "short_code": merchant["short_code"],
                    })

                    # Link charger to merchant
                    conn.execute(text("""
                        INSERT INTO charger_merchants (
                            charger_id, merchant_id,
                            distance_m, walk_duration_s, is_primary,
                            created_at, updated_at
                        ) VALUES (
                            :charger_id, :merchant_id,
                            :distance_m, :walk_duration_s, true,
                            NOW(), NOW()
                        )
                        ON CONFLICT (charger_id, merchant_id) DO UPDATE SET
                            distance_m = EXCLUDED.distance_m,
                            walk_duration_s = EXCLUDED.walk_duration_s,
                            updated_at = NOW()
                    """), {
                        "charger_id": charger["id"],
                        "merchant_id": merchant["id"],
                        "distance_m": merchant["distance_m"],
                        "walk_duration_s": merchant["walk_duration_s"],
                    })

            conn.commit()
            print("Onboarding merchants and chargers seeded successfully!")
            return 0

    except Exception as e:
        print(f"Error seeding onboarding merchants: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
