#!/usr/bin/env python3
"""
Final verification that production database is correctly configured.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

# Production database URL
DATABASE_URL = "postgresql://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"

def verify_production():
    """Verify production database has correct charger configuration."""
    try:
        print("🔌 Connecting to production database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check for the specific charger ID the frontend expects
        cur.execute("SELECT id, name, lat, lng, is_public FROM chargers WHERE id = 'canyon_ridge_tesla'")
        canyon_ridge = cur.fetchone()
        
        if canyon_ridge:
            print(f"✅ Found expected charger: {canyon_ridge[0]} - {canyon_ridge[1]}")
            print(f"   Location: ({canyon_ridge[2]}, {canyon_ridge[3]})")
            print(f"   Public: {canyon_ridge[4]}")
        else:
            print("❌ Charger 'canyon_ridge_tesla' not found!")
            return False
        
        # Check total public chargers
        cur.execute("SELECT COUNT(*) FROM chargers WHERE is_public = true")
        public_count = cur.fetchone()[0]
        print(f"\n📊 Total public chargers: {public_count}")
        
        if public_count == 0:
            print("❌ No public chargers found!")
            return False
        
        # Check charger-merchant links for canyon_ridge_tesla
        cur.execute("""
            SELECT COUNT(*) FROM charger_merchants 
            WHERE charger_id = 'canyon_ridge_tesla'
        """)
        link_count = cur.fetchone()[0]
        print(f"📊 Charger-merchant links for canyon_ridge_tesla: {link_count}")
        
        # List all public chargers
        cur.execute("SELECT id, name FROM chargers WHERE is_public = true ORDER BY id")
        chargers = cur.fetchall()
        print(f"\n📋 All public chargers:")
        for charger_id, name in chargers:
            print(f"  - {charger_id}: {name}")
        
        cur.close()
        conn.close()
        
        print("\n✅ Production database verification complete!")
        print("✅ Discovery endpoint should now return chargers")
        print("✅ Frontend should be able to find canyon_ridge_tesla")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error verifying production: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_production()
    sys.exit(0 if success else 1)




