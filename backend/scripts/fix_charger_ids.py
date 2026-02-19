#!/usr/bin/env python3
"""
Fix charger IDs to match frontend expectations.
Updates tesla_canyon_ridge to canyon_ridge_tesla.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

# Production database URL
DATABASE_URL = "postgresql://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"

def fix_charger_ids():
    """Update charger IDs to match frontend expectations."""
    try:
        print("🔌 Connecting to production database...")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Check if tesla_canyon_ridge exists
        cur.execute("SELECT id, name FROM chargers WHERE id = 'tesla_canyon_ridge'")
        existing = cur.fetchone()
        
        if existing:
            charger_id_old, charger_name = existing
            print(f"\n📋 Found charger: {charger_id_old} - {charger_name}")
            
            # Check if new ID already exists
            cur.execute("SELECT id FROM chargers WHERE id = 'canyon_ridge_tesla'")
            if cur.fetchone():
                print("⚠️  Charger 'canyon_ridge_tesla' already exists. Deleting old one...")
                # Delete old charger-merchant links first
                cur.execute("DELETE FROM charger_merchants WHERE charger_id = %s", (charger_id_old,))
                print(f"  ✅ Deleted charger-merchant links for {charger_id_old}")
                # Delete old charger
                cur.execute("DELETE FROM chargers WHERE id = %s", (charger_id_old,))
                print(f"  ✅ Deleted charger {charger_id_old}")
                conn.commit()
            else:
                print("🔄 Creating new charger with ID 'canyon_ridge_tesla'...")
                
                # Get full charger data
                cur.execute("""
                    SELECT name, address, lat, lng, network_name, connector_types::text, 
                           power_kw, is_public, status, external_id, city, state, zip_code
                    FROM chargers WHERE id = %s
                """, (charger_id_old,))
                charger_data = cur.fetchone()
                
                if charger_data:
                    name, address, lat, lng, network_name, connector_types_json, power_kw, is_public, status, external_id, city, state, zip_code = charger_data
                    
                    # Create new charger with correct ID (set external_id to NULL to avoid unique constraint)
                    cur.execute("""
                        INSERT INTO chargers (id, name, address, lat, lng, network_name, 
                                              connector_types, power_kw, is_public, status, 
                                              external_id, city, state, zip_code, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s::json, %s, %s, %s, NULL, %s, %s, %s, NOW(), NOW())
                    """, ('canyon_ridge_tesla', name, address, lat, lng, network_name, connector_types_json, power_kw, is_public, status, city, state, zip_code))
                    print("  ✅ Created new charger 'canyon_ridge_tesla'")
                    
                    # Update charger_merchants to point to new ID
                    cur.execute("""
                        UPDATE charger_merchants 
                        SET charger_id = 'canyon_ridge_tesla' 
                        WHERE charger_id = %s
                    """, (charger_id_old,))
                    updated_links = cur.rowcount
                    print(f"  ✅ Updated {updated_links} charger-merchant links")
                    
                    # Delete old charger
                    cur.execute("DELETE FROM chargers WHERE id = %s", (charger_id_old,))
                    print(f"  ✅ Deleted old charger {charger_id_old}")
                    
                    conn.commit()
                    print("\n✅ Charger ID migration completed successfully!")
                else:
                    print("  ⚠️  Could not fetch charger data")
                    conn.rollback()
        else:
            # Check if canyon_ridge_tesla already exists
            cur.execute("SELECT id, name FROM chargers WHERE id = 'canyon_ridge_tesla'")
            if cur.fetchone():
                print("\n✅ Charger 'canyon_ridge_tesla' already exists. No update needed.")
            else:
                print("\n⚠️  Charger 'tesla_canyon_ridge' not found. May need to seed.")
        
        # Verify final state
        cur.execute("SELECT id, name FROM chargers WHERE id IN ('canyon_ridge_tesla', 'tesla_canyon_ridge')")
        chargers = cur.fetchall()
        print("\n📋 Final charger state:")
        for charger_id, name in chargers:
            print(f"  - {charger_id}: {name}")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error updating charger IDs: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.rollback()
        return False
    
    return True

if __name__ == "__main__":
    success = fix_charger_ids()
    sys.exit(0 if success else 1)

