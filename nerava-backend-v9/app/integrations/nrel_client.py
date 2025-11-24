"""
NREL Alternative Fuels Data Center API client
https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/
"""
import logging
import httpx
from typing import List, Dict, Optional, Tuple
from math import radians, cos

logger = logging.getLogger(__name__)

# Hardcoded API key
NREL_API_KEY = "rBv6VXOAQbJemI6xw2QbqjceK5QdNUta8MpT50mY"

NREL_BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1"


class ChargerData:
    """Data class for charger information"""
    def __init__(self, data: Dict):
        self.external_id = data.get("id")
        self.name = data.get("station_name", "Unknown Charger")
        self.network_name = data.get("ev_network", "Unknown")
        self.lat = float(data.get("latitude", 0))
        self.lng = float(data.get("longitude", 0))
        self.address = data.get("street_address", "")
        self.city = data.get("city", "")
        self.state = data.get("state", "")
        self.zip_code = data.get("zip", "")
        self.connector_types = data.get("ev_connector_types", [])
        self.power_kw = self._extract_power_kw(data)
        self.is_public = data.get("access_code") != "PRIVATE"
        self.access_code = data.get("access_code")
        self.status = self._determine_status(data)
    
    def _extract_power_kw(self, data: Dict) -> Optional[float]:
        """Extract power rating from NREL data"""
        # NREL may have ev_dc_fast_num_ports or similar
        # For now, return None (can be enhanced)
        return None
    
    def _determine_status(self, data: Dict) -> str:
        """Determine charger status from NREL data"""
        # NREL doesn't always have real-time status
        # Check for common indicators
        if data.get("status_code") == "E":
            return "broken"
        elif data.get("status_code") == "P":
            return "available"
        return "unknown"


async def fetch_chargers_in_bbox(
    bbox: Tuple[float, float, float, float],
    limit: int = 100
) -> List[ChargerData]:
    """
    Fetch chargers within a bounding box.
    
    Args:
        bbox: (min_lat, min_lng, max_lat, max_lng)
        limit: Maximum number of results
    
    Returns:
        List of ChargerData objects
    """
    min_lat, min_lng, max_lat, max_lng = bbox
    
    # NREL API requires latitude, longitude, and radius (in miles)
    center_lat = (min_lat + max_lat) / 2
    center_lng = (min_lng + max_lng) / 2
    radius_miles = _calculate_radius(bbox)
    
    params = {
        "api_key": NREL_API_KEY,
        "fuel_type": "ELEC",  # Electric only
        "latitude": center_lat,
        "longitude": center_lng,
        "radius": radius_miles,
        "limit": limit,
        "format": "json"
    }
    
    logger.info(f"[WhileYouCharge] NREL API call: lat={center_lat}, lng={center_lng}, radius={radius_miles}mi")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{NREL_BASE_URL}/nearest.json", params=params)
            logger.debug(f"[WhileYouCharge] NREL API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"[WhileYouCharge] NREL API error {response.status_code}: {response.text[:200]}")
                response.raise_for_status()
            
            data = response.json()
            
            stations = data.get("fuel_stations", [])
            
            # Filter by bounding box
            filtered = []
            for station in stations:
                lat = float(station.get("latitude", 0))
                lng = float(station.get("longitude", 0))
                if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
                    filtered.append(ChargerData(station))
            
            return filtered[:limit]
    
    except Exception as e:
        logger.error(f"NREL API error: {e}", exc_info=True)
        return []


def _calculate_radius(bbox: Tuple[float, float, float, float]) -> float:
    """Calculate approximate radius in miles from bounding box"""
    min_lat, min_lng, max_lat, max_lng = bbox
    # Rough approximation: 1 degree lat ≈ 69 miles, 1 degree lng ≈ 69 * cos(lat) miles
    lat_diff = max_lat - min_lat
    lng_diff = max_lng - min_lng
    avg_lat = (min_lat + max_lat) / 2
    lat_miles = lat_diff * 69
    lng_miles = lng_diff * 69 * abs(cos(radians(avg_lat)))  # Use proper cosine
    radius_miles = max(lat_miles, lng_miles) * 1.2  # Add 20% buffer
    # NREL API has a max radius of 500 miles
    return min(radius_miles, 500.0)

