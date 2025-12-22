#!/usr/bin/env python3
"""
Backfill script for merchant category and nearest charger fields.

Idempotent script that populates:
- primary_category (derived from place_types)
- nearest_charger_id (computed from nearest charger)
- nearest_charger_distance_m (cached distance in meters)

Usage:
    python scripts/backfill_merchant_nearest_charger.py
    python scripts/backfill_merchant_nearest_charger.py --zone_slug domain_austin
    python scripts/backfill_merchant_nearest_charger.py --limit 10 --dry-run
"""

import os
import sys
import argparse
from typing import Optional

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import SessionLocal
from app.models.while_you_charge import Merchant
from app.services.merchant_categories import to_primary_category
from app.services.merchant_charger_map import compute_nearest_charger


def backfill_merchants(
    zone_slug: Optional[str] = None,
    limit: Optional[int] = None,
    dry_run: bool = False
):
    """Backfill merchant category and nearest charger fields."""
    db = SessionLocal()
    
    try:
        # Query merchants
        query = db.query(Merchant)
        
        if zone_slug:
            # Note: Merchant model doesn't have zone_slug, but we can filter by other criteria if needed
            # For now, process all merchants
            print(f"⚠️  zone_slug filter not yet implemented, processing all merchants")
        
        merchants = query.all()
        
        if limit:
            merchants = merchants[:limit]
        
        print(f"Processing {len(merchants)} merchants...")
        
        updated_count = 0
        skipped_count = 0
        
        for merchant in merchants:
            updates = {}
            
            # Compute primary_category from place_types
            if merchant.place_types:
                primary_category = to_primary_category(merchant.place_types)
                if merchant.primary_category != primary_category:
                    updates['primary_category'] = primary_category
            elif not merchant.primary_category:
                # Set default if no place_types
                updates['primary_category'] = 'other'
            
            # Compute nearest charger
            if merchant.lat and merchant.lng:
                charger_id, distance_m = compute_nearest_charger(
                    db,
                    merchant.lat,
                    merchant.lng
                )
                
                if charger_id != merchant.nearest_charger_id:
                    updates['nearest_charger_id'] = charger_id
                
                if distance_m != merchant.nearest_charger_distance_m:
                    updates['nearest_charger_distance_m'] = distance_m
            else:
                print(f"⚠️  Merchant {merchant.id} missing lat/lng, skipping charger computation")
            
            # Apply updates
            if updates:
                if dry_run:
                    print(f"[DRY RUN] Would update {merchant.id} ({merchant.name}): {updates}")
                else:
                    for key, value in updates.items():
                        setattr(merchant, key, value)
                    db.commit()
                    updated_count += 1
                    print(f"✅ Updated {merchant.id} ({merchant.name}): {updates}")
            else:
                skipped_count += 1
        
        print(f"\n✅ Backfill complete:")
        print(f"   Updated: {updated_count}")
        print(f"   Skipped: {skipped_count}")
        print(f"   Total: {len(merchants)}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during backfill: {e}")
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Backfill merchant category and nearest charger fields')
    parser.add_argument('--zone_slug', type=str, help='Filter by zone slug (not yet implemented)')
    parser.add_argument('--limit', type=int, help='Limit number of merchants to process')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No changes will be made\n")
    
    backfill_merchants(
        zone_slug=args.zone_slug,
        limit=args.limit,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

