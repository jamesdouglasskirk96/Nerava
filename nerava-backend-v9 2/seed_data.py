#!/usr/bin/env python3
"""
Seed data script for Nerava backend.

Supports two modes:
1. Generic/demo mode (default): Seeds user reputation and demo intent
2. Domain hub mode: Seeds only Domain hub chargers and merchants (--hub=domain)

Usage:
    python seed_data.py                    # Generic/demo mode
    python seed_data.py --hub=domain       # Domain hub mode
    PILOT_HUB=domain python seed_data.py   # Domain hub mode via env var
"""
import os
import sys
import uuid
import argparse
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models_while_you_charge import Charger, Merchant


def seed_domain_hub(db: Session):
    """
    Seed Domain hub with chargers (and optionally merchants).
    
    Args:
        db: Database session
    """
    from app.domains.domain_hub import DOMAIN_CHARGERS, HUB_ID, HUB_NAME
    
    print(f'🏢 Seeding {HUB_NAME} hub...')
    
    chargers_inserted = 0
    chargers_updated = 0
    
    for charger_config in DOMAIN_CHARGERS:
        # Check if charger already exists
        existing = db.query(Charger).filter(Charger.id == charger_config["id"]).first()
        
        if existing:
            # Update existing charger
            existing.name = charger_config["name"]
            existing.network_name = charger_config["network_name"]
            existing.lat = charger_config["lat"]
            existing.lng = charger_config["lng"]
            existing.address = charger_config.get("address")
            existing.city = charger_config.get("city", "Austin")
            existing.state = charger_config.get("state", "TX")
            existing.zip_code = charger_config.get("zip_code")
            existing.connector_types = charger_config.get("connector_types", [])
            existing.power_kw = charger_config.get("power_kw")
            existing.is_public = charger_config.get("is_public", True)
            existing.status = charger_config.get("status", "available")
            existing.external_id = charger_config.get("external_id")
            chargers_updated += 1
            print(f'  ✓ Updated charger: {charger_config["name"]}')
        else:
            # Insert new charger
            charger = Charger(
                id=charger_config["id"],
                external_id=charger_config.get("external_id"),
                name=charger_config["name"],
                network_name=charger_config["network_name"],
                lat=charger_config["lat"],
                lng=charger_config["lng"],
                address=charger_config.get("address"),
                city=charger_config.get("city", "Austin"),
                state=charger_config.get("state", "TX"),
                zip_code=charger_config.get("zip_code"),
                connector_types=charger_config.get("connector_types", []),
                power_kw=charger_config.get("power_kw"),
                is_public=charger_config.get("is_public", True),
                status=charger_config.get("status", "available"),
            )
            db.add(charger)
            chargers_inserted += 1
            print(f'  ✓ Inserted charger: {charger_config["name"]}')
    
    db.commit()
    print(f'✅ Domain hub seed complete: {chargers_inserted} inserted, {chargers_updated} updated')
    
    return {
        "hub_id": HUB_ID,
        "hub_name": HUB_NAME,
        "chargers_inserted": chargers_inserted,
        "chargers_updated": chargers_updated,
        "total_chargers": len(DOMAIN_CHARGERS)
    }


def seed_generic_demo(db: Session):
    """
    Seed generic demo data (user reputation and demo intent).
    This is the legacy behavior when hub mode is not specified.
    
    Args:
        db: Database session
    """
    # Demo user ID
    me = os.getenv('DEMO_ME_ID', str(uuid.uuid4()))
    
    try:
        # First, insert a user_reputation record if it doesn't exist
        db.execute(text('''
            INSERT OR IGNORE INTO user_reputation (user_id, score, tier, streak_days, followers_count, following_count)
            VALUES (:user_id, 180, 'Silver', 7, 12, 8)
        '''), {'user_id': me})
        
        # Update reputation with counts
        db.execute(text('''
            UPDATE user_reputation 
            SET followers_count = 12, following_count = 8 
            WHERE user_id = :user_id
        '''), {'user_id': me})
        
        # Insert demo intent
        db.execute(text('''
            INSERT OR IGNORE INTO charge_intents
            (id, user_id, station_id, station_name, merchant_name, perk_title, address, eta_minutes,
             merchant_lat, merchant_lng, station_lat, station_lng)
            VALUES (:id, :user_id, 'TESLA_AUS_001', 'Tesla Supercharger – Domain',
                    'Starbucks', 'Free coffee 2–4pm', '310 E 5th St, Austin, TX', 15,
                    30.2653, -97.7393, 30.4021, -97.7266)
        '''), {'id': str(uuid.uuid4()), 'user_id': me})
        
        db.commit()
        print(f'✅ Generic demo seed complete: me={me}, added counts and demo intent')
        
    except Exception as e:
        db.rollback()
        raise


def main():
    """Main entry point for seed script."""
    parser = argparse.ArgumentParser(
        description="Seed Nerava database with demo or hub-specific data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seed_data.py                    # Generic/demo mode
  python seed_data.py --hub=domain       # Domain hub mode
  PILOT_HUB=domain python seed_data.py   # Domain hub mode via env var
        """
    )
    parser.add_argument(
        '--hub',
        type=str,
        default=None,
        help='Hub to seed (e.g., "domain"). Can also be set via PILOT_HUB env var.'
    )
    
    args = parser.parse_args()
    
    # Determine hub mode from CLI arg or env var
    hub_mode = args.hub or os.getenv('PILOT_HUB')
    
    # Get database session
    db = next(get_db())
    
    try:
        if hub_mode == "domain":
            # Domain hub mode: seed only Domain hub data
            result = seed_domain_hub(db)
            print(f'\n📊 Summary:')
            print(f'   Hub: {result["hub_name"]} ({result["hub_id"]})')
            print(f'   Chargers: {result["total_chargers"]} total ({result["chargers_inserted"]} new, {result["chargers_updated"]} updated)')
        else:
            # Generic/demo mode: seed legacy demo data
            seed_generic_demo(db)
    
    except Exception as e:
        db.rollback()
        print(f'❌ Seed failed: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == '__main__':
    main()
