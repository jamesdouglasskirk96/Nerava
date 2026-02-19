#!/usr/bin/env python3
"""
Quick script to check if chargers exist in production database.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

# Production database URL (same as seed_production.py)
DATABASE_URL = "postgresql://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"

def check_chargers():
    """Check if any chargers exist in the database."""
    try:
        print("🔌 Connecting to production database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check charger count
        cur.execute("SELECT COUNT(*) FROM chargers")
        charger_count = cur.fetchone()[0]
        
        print(f"\n📊 Current charger count: {charger_count}")
        
        if charger_count > 0:
            # List chargers
            cur.execute("SELECT id, name, lat, lng, is_public FROM chargers ORDER BY id")
            chargers = cur.fetchall()
            print("\n📋 Existing chargers:")
            for charger_id, name, lat, lng, is_public in chargers:
                print(f"  - {charger_id}: {name} ({lat}, {lng}) - Public: {is_public}")
        else:
            print("\n⚠️  No chargers found in database. Seed script needs to be run.")
        
        # Check merchant count
        cur.execute("SELECT COUNT(*) FROM merchants")
        merchant_count = cur.fetchone()[0]
        print(f"\n📊 Current merchant count: {merchant_count}")
        
        # Check charger-merchant links
        cur.execute("SELECT COUNT(*) FROM charger_merchants")
        link_count = cur.fetchone()[0]
        print(f"📊 Current charger-merchant links: {link_count}")
        
        cur.close()
        conn.close()
        
        return charger_count == 0
        
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    needs_seeding = check_chargers()
    sys.exit(0 if not needs_seeding else 1)




