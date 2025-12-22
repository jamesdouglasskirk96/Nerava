#!/usr/bin/env python3
"""
Seed script for "Eggman Coffee" demo merchant.

Idempotent seed that populates:
- merchants table (While You Charge)
- merchant_perks table (Nova redemption)
- chargers table (Domain charger)
- charger_merchants table (charger-merchant links)
- domain_merchants table (legacy compatibility)

Safe to re-run multiple times.
"""

import os
import sys
import json
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import SessionLocal, Base, engine
from app.models.while_you_charge import Merchant, MerchantPerk, Charger, ChargerMerchant
from app.models.domain import DomainMerchant
from app.services.merchant_categories import to_primary_category
from app.services.merchant_charger_map import compute_nearest_charger

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# Canonical demo merchant constants
EGGMAN_ID = "eggman_coffee_001"
EGGMAN_NAME = "Eggman ATX"
EGGMAN_LAT = 30.2634382  # Coordinates for 1720 Barton Springs Rd, Austin, TX 78704
EGGMAN_LNG = -97.7628908  # Coordinates for 1720 Barton Springs Rd, Austin, TX 78704
EGGMAN_ADDRESS = "1720 Barton Springs Rd, Austin, TX 78704"

DAME_CAFE_ID = "dame_cafe_001"
DAME_CAFE_NAME = "Dame Cafe"
DAME_CAFE_LAT = 30.4019  # Domain area, Austin, TX
DAME_CAFE_LNG = -97.7251
DAME_CAFE_ADDRESS = "11821 Rock Rose Ave, Austin, TX 78758"

BULLSEYE_BAGEL_ID = "bullseye_bagel_001"
BULLSEYE_BAGEL_NAME = "Bullseye Bagel"
BULLSEYE_BAGEL_LAT = 30.2676  # Downtown Austin area
BULLSEYE_BAGEL_LNG = -97.7429
BULLSEYE_BAGEL_ADDRESS = "500 Lavaca St, Austin, TX 78701"

ZONE_SLUG = "domain_austin"
NOVA_REWARD = 350  # 350 Nova = $35.00 at 10¢/Nova


def main():
    """Main seed function - idempotent."""
    db = SessionLocal()
    
    try:
        # Step 1: Ensure merchants table schema supports string IDs
        from sqlalchemy import text, inspect
        inspector = inspect(engine)
        
        # Check if merchants table exists and if id column is INTEGER
        if 'merchants' in inspector.get_table_names():
            cols = inspector.get_columns('merchants')
            id_col = next((c for c in cols if c['name'] == 'id'), None)
            if id_col and 'INTEGER' in str(id_col['type']).upper() and 'AUTO' not in str(id_col.get('autoincrement', '')).upper():
                # Table has INTEGER ID but we need String - alter it
                # SQLite doesn't support ALTER COLUMN, so we need to recreate
                print("⚠️  merchants table has INTEGER id, but model expects String. Table will be recreated.")
                # Drop indexes first
                db.execute(text("DROP INDEX IF EXISTS idx_merchants_location"))
                db.execute(text("DROP INDEX IF EXISTS idx_merchants_category"))
                db.execute(text("DROP INDEX IF EXISTS ix_merchants_external_id"))
                db.execute(text("DROP TABLE IF EXISTS merchants_backup"))
                db.execute(text("ALTER TABLE merchants RENAME TO merchants_backup"))
                db.commit()
                # Recreate table with correct schema
                Base.metadata.create_all(bind=engine, tables=[Merchant.__table__])
                # Copy data back if any (skip id column since types don't match)
                db.execute(text("""
                    INSERT INTO merchants (name, category, lat, lng, address, logo_url, created_at, updated_at)
                    SELECT name, category, lat, lng, address, logo_url, created_at, updated_at
                    FROM merchants_backup
                """))
                db.execute(text("DROP TABLE merchants_backup"))
                db.commit()
        
        # Helper function to seed a merchant
        def seed_merchant(merchant_id, name, lat, lng, address, category="coffee", place_types=None):
            # Set default place_types based on category
            if place_types is None:
                if category == "coffee":
                    place_types = ["cafe", "coffee_shop"]
                elif category == "food":
                    place_types = ["restaurant", "meal_takeaway"]
                else:
                    place_types = []
            
            # Compute primary_category from place_types
            primary_category = to_primary_category(place_types)
            
            # Seed Merchant
            merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
            
            if not merchant:
                merchant = Merchant(
                    id=merchant_id,
                    name=name,
                    lat=lat,
                    lng=lng,
                    category=category,
                    address=address,
                    logo_url="/assets/merchants/eggman-logo.svg",
                    photo_url="/assets/merchants/eggman-hero.svg",
                    place_types=place_types,
                    primary_category=primary_category
                )
                db.add(merchant)
                db.commit()
                db.refresh(merchant)
            else:
                # Update all fields including coordinates and address
                merchant.name = name
                merchant.lat = lat
                merchant.lng = lng
                merchant.address = address
                merchant.category = category
                merchant.logo_url = "/assets/merchants/eggman-logo.svg"
                merchant.photo_url = "/assets/merchants/eggman-hero.svg"
                merchant.place_types = place_types
                merchant.primary_category = primary_category
                db.commit()
            
            # Compute nearest charger
            if merchant.lat and merchant.lng:
                charger_id, distance_m = compute_nearest_charger(db, merchant.lat, merchant.lng)
                merchant.nearest_charger_id = charger_id
                merchant.nearest_charger_distance_m = distance_m
                db.commit()
                db.refresh(merchant)
            
            # Seed MerchantPerk
            perk = db.query(MerchantPerk).filter(MerchantPerk.merchant_id == merchant_id).first()
            if perk:
                perk.nova_reward = NOVA_REWARD
                perk.is_active = True
                db.commit()
            else:
                perk = MerchantPerk(
                    merchant_id=merchant_id,
                    title="Redeem Nova",
                    description="350 Nova = $35.00",
                    nova_reward=NOVA_REWARD,
                    is_active=True
                )
                db.add(perk)
                db.commit()
            
            return merchant
        
        # Step 2: Remove old Eggman #2 and #3 merchants if they exist
        old_merchants = db.query(Merchant).filter(Merchant.id.in_(["eggman_coffee_002", "eggman_coffee_003"])).all()
        for old_merchant in old_merchants:
            # Delete related records first
            db.query(ChargerMerchant).filter(ChargerMerchant.merchant_id == old_merchant.id).delete()
            db.query(MerchantPerk).filter(MerchantPerk.merchant_id == old_merchant.id).delete()
            db.query(DomainMerchant).filter(DomainMerchant.id == old_merchant.id).delete()
            db.delete(old_merchant)
        db.commit()
        if old_merchants:
            print(f"✅ Removed {len(old_merchants)} old Eggman merchants")
        
        # Step 3: Seed the three merchants
        merchant1 = seed_merchant(EGGMAN_ID, EGGMAN_NAME, EGGMAN_LAT, EGGMAN_LNG, EGGMAN_ADDRESS, category="coffee", place_types=["cafe", "coffee_shop"])
        print("✅ merchants: Eggman ATX present")
        
        merchant2 = seed_merchant(DAME_CAFE_ID, DAME_CAFE_NAME, DAME_CAFE_LAT, DAME_CAFE_LNG, DAME_CAFE_ADDRESS, category="coffee", place_types=["cafe", "coffee_shop"])
        print("✅ merchants: Dame Cafe present")
        
        merchant3 = seed_merchant(BULLSEYE_BAGEL_ID, BULLSEYE_BAGEL_NAME, BULLSEYE_BAGEL_LAT, BULLSEYE_BAGEL_LNG, BULLSEYE_BAGEL_ADDRESS, category="food", place_types=["restaurant", "meal_takeaway"])
        print("✅ merchants: Bullseye Bagel present")
        
        print("✅ merchant_perks: All merchant rewards set to 350 Nova")
        
        # Step 4: Ensure Domain Charger Exists
        domain_chargers = db.query(Charger).filter(Charger.id.like('ch_domain%')).all()
        if not domain_chargers:
            charger = Charger(
                id="ch_domain_tesla_001",
                name="Tesla Supercharger – Domain",
                network_name="Tesla",
                lat=EGGMAN_LAT,
                lng=EGGMAN_LNG,
                address=EGGMAN_ADDRESS,
                # connector_types will use default=list from model
                is_public=True,
                status="available"
            )
            db.add(charger)
            db.commit()
            db.refresh(charger)
            domain_chargers = [charger]
        print("✅ chargers: Domain charger present")
        
        # Step 5: Link Charger ↔ Merchants (all three merchants)
        merchant_ids = [EGGMAN_ID, DAME_CAFE_ID, BULLSEYE_BAGEL_ID]
        for charger in domain_chargers:
            for merchant_id in merchant_ids:
                link = db.query(ChargerMerchant).filter(
                    ChargerMerchant.charger_id == charger.id,
                    ChargerMerchant.merchant_id == merchant_id
                ).first()
                
                if not link:
                    # Calculate approximate distance (use 250m for all, or calculate from charger location)
                    # For simplicity, use 250m for Eggman, 300m for Dame Cafe, 350m for Bullseye Bagel
                    distances = {
                        EGGMAN_ID: 250.0,
                        DAME_CAFE_ID: 300.0,
                        BULLSEYE_BAGEL_ID: 350.0
                    }
                    distance = distances.get(merchant_id, 250.0)
                    walk_duration = int(distance / 1.4)  # Approximate: 1.4 m/s walking speed
                    
                    link = ChargerMerchant(
                        charger_id=charger.id,
                        merchant_id=merchant_id,
                        distance_m=distance,
                        walk_duration_s=walk_duration,
                        walk_distance_m=distance
                    )
                    db.add(link)
                    db.commit()
        print("✅ charger_merchants: All merchants linked to Domain chargers")
        
        # Step 6: Seed DomainMerchants (all three)
        def seed_domain_merchant(merchant_id, name, lat, lng):
            domain_merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
            if not domain_merchant:
                domain_merchant = DomainMerchant(
                    id=merchant_id,
                    name=name,
                    lat=lat,
                    lng=lng,
                    zone_slug=ZONE_SLUG,
                    status="active",
                    nova_balance=0
                )
                db.add(domain_merchant)
                db.commit()
            else:
                domain_merchant.name = name
                domain_merchant.lat = lat
                domain_merchant.lng = lng
                db.commit()
        
        seed_domain_merchant(EGGMAN_ID, EGGMAN_NAME, EGGMAN_LAT, EGGMAN_LNG)
        seed_domain_merchant(DAME_CAFE_ID, DAME_CAFE_NAME, DAME_CAFE_LAT, DAME_CAFE_LNG)
        seed_domain_merchant(BULLSEYE_BAGEL_ID, BULLSEYE_BAGEL_NAME, BULLSEYE_BAGEL_LAT, BULLSEYE_BAGEL_LNG)
        print("✅ domain_merchants: All merchants present")
        
        # Step 7: Final Success Output
        print("\n🎉 Merchants seeded successfully")
        print(f"\nMerchant IDs:")
        print(f"  - {EGGMAN_ID}: {EGGMAN_NAME} at {EGGMAN_LAT}, {EGGMAN_LNG}")
        print(f"  - {DAME_CAFE_ID}: {DAME_CAFE_NAME} at {DAME_CAFE_LAT}, {DAME_CAFE_LNG}")
        print(f"  - {BULLSEYE_BAGEL_ID}: {BULLSEYE_BAGEL_NAME} at {BULLSEYE_BAGEL_LAT}, {BULLSEYE_BAGEL_LNG}")
        print(f"\nZone: {ZONE_SLUG}")
        print(f"Nova Reward: {NOVA_REWARD} (${NOVA_REWARD / 10:.2f})")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding Eggman Coffee: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

