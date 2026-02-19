#!/usr/bin/env python3
"""
Fix primary merchant flag for canyon_ridge_tesla charger.
Sets Asadas Grill as primary merchant with suppress_others for pre-charge state.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

# Production database URL
DATABASE_URL = "postgresql://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"

def fix_primary_merchant():
    """Set Asadas Grill as primary merchant for canyon_ridge_tesla."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        charger_id = "canyon_ridge_tesla"
        
        # Find Asadas Grill merchant linked to this charger
        cur.execute("""
            SELECT cm.merchant_id, m.name
            FROM charger_merchants cm
            JOIN merchants m ON cm.merchant_id = m.id
            WHERE cm.charger_id = %s
            AND (LOWER(m.name) LIKE '%%asadas%%' OR LOWER(m.name) LIKE '%%grill%%')
            LIMIT 1
        """, (charger_id,))
        result = cur.fetchone()
        
        if not result:
            print("⚠️  Asadas Grill not found for this charger, getting first merchant")
            # Get first merchant instead
            cur.execute("""
                SELECT cm.merchant_id, m.name
                FROM charger_merchants cm
                JOIN merchants m ON cm.merchant_id = m.id
                WHERE cm.charger_id = %s
                ORDER BY cm.distance_m ASC
                LIMIT 1
            """, (charger_id,))
            result = cur.fetchone()
        
        if not result:
            print("❌ No merchants found for charger")
            return False
        
        merchant_id = result[0]
        merchant_name = result[1]
        print(f"📋 Found merchant: {merchant_name} (ID: {merchant_id})")
        
        # Check current state
        cur.execute("""
            SELECT is_primary, suppress_others, exclusive_title
            FROM charger_merchants
            WHERE charger_id = %s AND merchant_id = %s
        """, (charger_id, merchant_id))
        current = cur.fetchone()
        
        if current and len(current) >= 2:
            is_primary, suppress_others = current[0], current[1]
            exclusive_title = current[2] if len(current) > 2 else None
            print(f"   Current: is_primary={is_primary}, suppress_others={suppress_others}")
        
        # Unset primary flag on all other merchants for this charger
        cur.execute("""
            UPDATE charger_merchants
            SET is_primary = false
            WHERE charger_id = %s AND merchant_id != %s
        """, (charger_id, merchant_id))
        unset_count = cur.rowcount
        print(f"✅ Unset primary flag on {unset_count} other merchants")
        
        # Set this merchant as primary with suppress_others and exclusive
        cur.execute("""
            UPDATE charger_merchants
            SET is_primary = true,
                suppress_others = true,
                override_mode = 'ALWAYS',
                exclusive_title = 'Free Welcome Offer',
                exclusive_description = 'Show this screen for a special welcome offer!'
            WHERE charger_id = %s AND merchant_id = %s
        """, (charger_id, merchant_id))
        
        if cur.rowcount > 0:
            conn.commit()
            print(f"✅ Set {merchant_name} as primary merchant")
            print(f"   - is_primary: true")
            print(f"   - suppress_others: true")
            print(f"   - override_mode: ALWAYS")
            print(f"   - exclusive_title: Free Welcome Offer")
            return True
        else:
            print("⚠️  No rows updated")
            conn.rollback()
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    success = fix_primary_merchant()
    sys.exit(0 if success else 1)

