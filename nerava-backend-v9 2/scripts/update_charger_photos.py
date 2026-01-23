#!/usr/bin/env python3
"""
Update charger photos with real Unsplash images.
This script adds photo_url to charger records (if the column exists) or can be used
to prepare data for a future migration that adds the photo_url column.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import get_db
from app.models.while_you_charge import Charger

# Real photos for each charger (high-quality Unsplash images)
CHARGER_PHOTOS = {
    "ch_domain_tesla_001": "https://images.unsplash.com/photo-1593941707882-a5bac6861d75?w=800&q=80",  # Tesla Supercharger
    "ch_domain_chargepoint_001": "https://images.unsplash.com/photo-1558346490-a72e53ae2d4f?w=800&q=80",  # ChargePoint station
    "tesla_canyon_ridge": "https://images.unsplash.com/photo-1647166545674-ce28ce93bdca?w=800&q=80",  # Tesla charging
    "tesla_market_heights": "https://images.unsplash.com/photo-1620714223084-8fcacc6dfd8d?w=800&q=80",  # EV charging station
}

def main():
    db = next(get_db())

    try:
        for charger_id, photo_url in CHARGER_PHOTOS.items():
            charger = db.query(Charger).filter(Charger.id == charger_id).first()
            if charger:
                # Check if photo_url attribute exists (may not be in schema yet)
                if hasattr(charger, 'photo_url'):
                    old_url = getattr(charger, 'photo_url', None)
                    charger.photo_url = photo_url
                    print(f"Updated {charger_id}:")
                    print(f"  Old: {old_url}")
                    print(f"  New: {photo_url}")
                else:
                    print(f"Charger {charger_id} found, but photo_url column doesn't exist yet.")
                    print(f"  Would set photo_url to: {photo_url}")
                    print(f"  Note: Backend fallback logic will use Unsplash URLs automatically.")
            else:
                print(f"Charger not found: {charger_id}")

        db.commit()
        print("\n✅ Charger photo update complete!")
        print("\nNote: If photo_url column doesn't exist, the backend fallback logic")
        print("will automatically use Unsplash URLs based on network type.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == '__main__':
    main()


