#!/usr/bin/env python3
"""
Cleanup script to remove unwanted chargers from production.
Keeps only the 4 primary chargers.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import get_db
from app.models.while_you_charge import Charger

CHARGERS_TO_KEEP = [
    'ch_domain_tesla_001',
    'ch_domain_chargepoint_001',
    'tesla_market_heights',
    'tesla_canyon_ridge'
]

def main():
    db = next(get_db())

    try:
        # Get all chargers
        all_chargers = db.query(Charger).all()
        print(f"Found {len(all_chargers)} chargers in database")

        # Delete chargers not in keep list
        deleted_count = 0
        for charger in all_chargers:
            if charger.id not in CHARGERS_TO_KEEP:
                print(f"  Deleting: {charger.id} - {charger.name}")
                db.delete(charger)
                deleted_count += 1
            else:
                print(f"  Keeping: {charger.id} - {charger.name}")

        db.commit()
        print(f"\nDeleted {deleted_count} chargers")
        print(f"Remaining: {len(CHARGERS_TO_KEEP)} chargers")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()


