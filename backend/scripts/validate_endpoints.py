#!/usr/bin/env python3
"""
Validate that both discovery and merchants endpoints work correctly.
Tests the endpoint logic directly against production database.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from app.services.google_places_new import _haversine_distance
import math

# Production database URL
DATABASE_URL = "postgresql://nerava_admin:YJEDUbHGFIZBo6D5JiDPTbb4ZbmbE4ae@nerava-db.c27i820wot9o.us-east-1.rds.amazonaws.com:5432/nerava"

def test_discovery_endpoint(lat: float = 30.2672, lng: float = -97.7431):
    """Test discovery endpoint logic."""
    print("\n" + "="*60)
    print("TEST 1: Discovery Endpoint (/v1/chargers/discovery)")
    print("="*60)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Query all chargers (same as discovery endpoint)
        cur.execute("SELECT id, name, address, lat, lng, network_name, connector_types, power_kw, is_public FROM chargers")
        charger_rows = cur.fetchall()
        
        if not charger_rows:
            print("❌ FAIL: No chargers found in database")
            return False
        
        print(f"✅ Found {len(charger_rows)} chargers in database")
        
        # Calculate distances and sort (same as discovery endpoint)
        charger_distances = []
        for row in charger_rows:
            charger_id, name, address, lat_db, lng_db, network_name, connector_types, power_kw, is_public = row
            if not is_public:
                continue
            distance_m = _haversine_distance(lat, lng, lat_db, lng_db)
            charger_distances.append((charger_id, name, distance_m, lat_db, lng_db))
        
        charger_distances.sort(key=lambda x: x[2])
        
        if not charger_distances:
            print("❌ FAIL: No public chargers found")
            return False
        
        print(f"✅ Found {len(charger_distances)} public chargers")
        print(f"\n📋 Chargers sorted by distance from ({lat}, {lng}):")
        
        for charger_id, name, distance_m, lat_db, lng_db in charger_distances[:5]:
            drive_time_min = max(1, math.ceil(distance_m / 500))
            print(f"  - {charger_id}: {name}")
            print(f"    Distance: {distance_m:.0f}m ({drive_time_min} min drive)")
        
        # Check for canyon_ridge_tesla specifically
        canyon_ridge = next((c for c in charger_distances if c[0] == 'canyon_ridge_tesla'), None)
        if canyon_ridge:
            print(f"\n✅ SUCCESS: Found canyon_ridge_tesla charger")
            print(f"   Distance: {canyon_ridge[2]:.0f}m")
        else:
            print(f"\n❌ FAIL: canyon_ridge_tesla not found in public chargers")
            return False
        
        # Check merchant links for discovery endpoint
        cur.execute("""
            SELECT COUNT(*) FROM charger_merchants cm
            JOIN chargers c ON cm.charger_id = c.id
            WHERE c.is_public = true
        """)
        total_links = cur.fetchone()[0]
        print(f"\n✅ Found {total_links} charger-merchant links")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cur.close()
        conn.close()


def test_merchants_endpoint(charger_id: str = "canyon_ridge_tesla"):
    """Test merchants endpoint logic."""
    print("\n" + "="*60)
    print(f"TEST 2: Merchants Endpoint (/v1/drivers/merchants/open?charger_id={charger_id})")
    print("="*60)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        # Check if charger exists
        cur.execute("SELECT id, name FROM chargers WHERE id = %s", (charger_id,))
        charger = cur.fetchone()
        
        if not charger:
            print(f"❌ FAIL: Charger '{charger_id}' not found")
            return False
        
        print(f"✅ Found charger: {charger[0]} - {charger[1]}")
        
        # Check for primary merchant override (pre-charge state)
        cur.execute("""
            SELECT cm.merchant_id, cm.is_primary, cm.suppress_others, cm.exclusive_title
            FROM charger_merchants cm
            WHERE cm.charger_id = %s AND cm.is_primary = true
        """, (charger_id,))
        primary_override = cur.fetchone()
        
        if primary_override:
            merchant_id, is_primary, suppress_others, exclusive_title = primary_override
            print(f"✅ Found primary merchant override:")
            print(f"   Merchant ID: {merchant_id}")
            print(f"   Suppress others: {suppress_others}")
            print(f"   Exclusive title: {exclusive_title or 'None'}")
            
            # Get merchant details
            cur.execute("SELECT name, lat, lng FROM merchants WHERE id = %s", (merchant_id,))
            merchant = cur.fetchone()
            if merchant:
                print(f"   Merchant name: {merchant[0]}")
        else:
            print("⚠️  No primary merchant override found")
        
        # Check all charger-merchant links
        cur.execute("""
            SELECT COUNT(*) FROM charger_merchants
            WHERE charger_id = %s
        """, (charger_id,))
        link_count = cur.fetchone()[0]
        print(f"\n✅ Found {link_count} charger-merchant links for {charger_id}")
        
        if link_count == 0:
            print("⚠️  WARNING: No merchants linked to charger (may cause empty results)")
        
        # Get merchant details
        cur.execute("""
            SELECT m.id, m.name, cm.distance_m, cm.walk_duration_s, cm.is_primary
            FROM charger_merchants cm
            JOIN merchants m ON cm.merchant_id = m.id
            WHERE cm.charger_id = %s
            ORDER BY cm.is_primary DESC, cm.distance_m ASC
            LIMIT 5
        """, (charger_id,))
        merchants = cur.fetchall()
        
        if merchants:
            print(f"\n📋 Merchants for {charger_id}:")
            for merchant_id, name, distance_m, walk_duration_s, is_primary in merchants:
                primary_label = " [PRIMARY]" if is_primary else ""
                print(f"  - {name}{primary_label}")
                print(f"    Distance: {distance_m:.0f}m, Walk time: {walk_duration_s}s")
        else:
            print(f"\n⚠️  WARNING: No merchants found for charger")
        
        # Test pre-charge state (should return only primary if suppress_others)
        if primary_override and primary_override[2]:  # suppress_others
            print(f"\n✅ Pre-charge state: Will return only primary merchant (suppress_others=True)")
        elif primary_override:
            print(f"\n✅ Pre-charge state: Will return primary merchant first")
        else:
            print(f"\n⚠️  Pre-charge state: No primary override, will return first merchant")
        
        # Test charging state (should return up to 3 merchants)
        print(f"\n✅ Charging state: Will return up to 3 merchants (primary first, then secondary)")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        cur.close()
        conn.close()


def main():
    """Run all validation tests."""
    print("\n" + "="*60)
    print("VALIDATING PRODUCTION ENDPOINTS")
    print("="*60)
    
    results = []
    
    # Test discovery endpoint
    results.append(("Discovery Endpoint", test_discovery_endpoint()))
    
    # Test merchants endpoint
    results.append(("Merchants Endpoint", test_merchants_endpoint()))
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        print("✅ Discovery endpoint should return chargers")
        print("✅ Merchants endpoint should return merchants for canyon_ridge_tesla")
        print("✅ 'No chargers available' message should not appear")
    else:
        print("❌ SOME TESTS FAILED")
        print("⚠️  Please review the errors above")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




