#!/usr/bin/env python3
"""
Test the discovery endpoint logic to verify it returns chargers correctly.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import SessionLocal
from app.models.while_you_charge import Charger
from app.services.google_places_new import _haversine_distance
import math

def test_discovery_logic(lat: float = 30.2672, lng: float = -97.7431):
    """Test the discovery endpoint logic."""
    db = SessionLocal()
    try:
        # Query all chargers (same as discovery endpoint)
        chargers = db.query(Charger).all()
        
        print(f"📊 Found {len(chargers)} chargers in database")
        
        if not chargers:
            print("⚠️  No chargers found - discovery endpoint would return empty list")
            return False
        
        # Calculate distances and sort (same as discovery endpoint)
        charger_distances = []
        for charger in chargers:
            distance_m = _haversine_distance(lat, lng, charger.lat, charger.lng)
            charger_distances.append((charger, distance_m))
        
        charger_distances.sort(key=lambda x: x[1])
        
        print(f"\n📋 Chargers sorted by distance from ({lat}, {lng}):")
        for charger, distance_m in charger_distances[:5]:  # Show top 5
            drive_time_min = max(1, math.ceil(distance_m / 500))
            print(f"  - {charger.id}: {charger.name}")
            print(f"    Distance: {distance_m:.0f}m ({drive_time_min} min drive)")
            print(f"    Location: ({charger.lat}, {charger.lng})")
            print(f"    Public: {charger.is_public}")
        
        # Check if any chargers are public
        public_chargers = [c for c, d in charger_distances if c.is_public]
        print(f"\n✅ Found {len(public_chargers)} public chargers")
        
        if len(public_chargers) == 0:
            print("⚠️  No public chargers found - intent capture would fail")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing discovery logic: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Test with Austin coordinates (default browse mode location)
    success = test_discovery_logic()
    sys.exit(0 if success else 1)




