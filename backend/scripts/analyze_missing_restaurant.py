#!/usr/bin/env python3
"""
Analyze why Las Palapas wasn't included - check if it's the 20 result limit
"""
import json
import math
from pathlib import Path

CHARGER_LAT = 29.726346
CHARGER_LNG = -98.078351
LAS_PALAPAS_LAT = 29.727577
LAS_PALAPAS_LNG = -98.075816


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters"""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def main():
    # Read the results
    json_file = Path("backend/merchants_near_charger.json")
    if not json_file.exists():
        json_file = Path("merchants_near_charger.json")
    
    if not json_file.exists():
        print("ERROR: Could not find merchants_near_charger.json")
        return 1
    
    with open(json_file, "r") as f:
        data = json.load(f)
    
    merchants = data.get("merchants", [])
    
    # Calculate Las Palapas distance
    las_palapas_distance = haversine_distance(CHARGER_LAT, CHARGER_LNG, LAS_PALAPAS_LAT, LAS_PALAPAS_LNG)
    
    print("=" * 80)
    print("ANALYZING WHY LAS PALAPAS WASN'T INCLUDED")
    print("=" * 80)
    print(f"Las Palapas - Town Center")
    print(f"  Distance: {las_palapas_distance:.0f}m")
    print(f"  Walking time: ~{round(las_palapas_distance/83, 1)} minutes")
    print()
    print(f"Total merchants found: {len(merchants)}")
    print(f"API limit: 20 results")
    print()
    
    # Check distances of all found merchants
    print("Merchants found (sorted by distance):")
    distances = []
    for i, merchant in enumerate(merchants, 1):
        name = merchant.get("name", "Unknown")
        distance_m = merchant.get("distance_m", 0)
        distances.append((name, distance_m))
        print(f"{i:2d}. {name:40s} - {distance_m:4.0f}m")
    
    print()
    
    # Check where Las Palapas would rank
    distances.append(("Las Palapas - Town Center", las_palapas_distance))
    distances.sort(key=lambda x: x[1])
    
    las_palapas_rank = next(i for i, (name, _) in enumerate(distances, 1) if "Las Palapas" in name)
    
    print(f"Las Palapas would rank: #{las_palapas_rank} by distance")
    print()
    
    if las_palapas_rank <= 20:
        print("✓ Las Palapas SHOULD have been included (within top 20 by distance)")
        print()
        print("Possible reasons it wasn't:")
        print("1. Google Places API doesn't sort strictly by distance")
        print("2. API may prioritize certain business types or ratings")
        print("3. The search may have hit exactly 20 results before reaching Las Palapas")
        print("4. There might be multiple results for the same location (like Buc-ee's)")
    else:
        print(f"✗ Las Palapas is ranked #{las_palapas_rank}, outside the top 20")
        print(f"  There are {las_palapas_rank - 20} businesses closer to the charger")
    
    print()
    print("=" * 80)
    print("SOLUTION")
    print("=" * 80)
    print("To include Las Palapas and other nearby restaurants, we could:")
    print("1. Increase maxResultCount (but API limit is 20)")
    print("2. Use multiple searches with different type filters")
    print("3. Use text-based search instead of type-based search")
    print("4. Combine nearby search with text search for specific businesses")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)






