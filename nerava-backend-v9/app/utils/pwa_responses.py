"""
PWA Response Shaping Utilities

Helpers for normalizing API responses to be PWA-friendly:
- All numbers as integers (no floats)
- Consistent object shapes
- Remove internal fields
"""
from typing import Dict, Any, List, Optional


def normalize_number(value: Any) -> int:
    """Convert any number-like value to integer."""
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(round(value))
    try:
        return int(round(float(value)))
    except (ValueError, TypeError):
        return 0


def shape_charger(charger: Dict[str, Any], user_lat: Optional[float] = None, user_lng: Optional[float] = None) -> Dict[str, Any]:
    """
    Shape charger object for PWA consumption.
    
    Returns consistent shape:
    {
        "id": str,
        "name": str,
        "lat": float,
        "lng": float,
        "network_name": str (optional),
        "distance_m": int (if user_lat/lng provided),
        "walk_time_s": int (if user_lat/lng provided)
    }
    """
    result = {
        "id": str(charger.get("id", "")),
        "name": str(charger.get("name", "")),
        "lat": float(charger.get("lat", 0)),
        "lng": float(charger.get("lng", 0)),
    }
    
    # Optional fields
    if "network_name" in charger:
        result["network_name"] = str(charger.get("network_name", ""))
    
    # Distance if user location provided
    if user_lat is not None and user_lng is not None:
        from app.services.verify_dwell import haversine_m
        distance = haversine_m(
            user_lat, user_lng,
            result["lat"], result["lng"]
        )
        result["distance_m"] = normalize_number(distance)
    
    # Walk time (if provided in charger dict)
    if "walk_time_s" in charger:
        result["walk_time_s"] = normalize_number(charger.get("walk_time_s"))
    elif "walk_duration_s" in charger:
        result["walk_time_s"] = normalize_number(charger.get("walk_duration_s"))
    
    return result


def shape_merchant(merchant: Dict[str, Any], user_lat: Optional[float] = None, user_lng: Optional[float] = None) -> Dict[str, Any]:
    """
    Shape merchant object for PWA consumption.
    
    Returns consistent shape:
    {
        "id": str,
        "name": str,
        "lat": float,
        "lng": float,
        "category": str (optional),
        "nova_reward": int (optional),
        "logo_url": str (optional),
        "distance_m": int (if user_lat/lng provided),
        "walk_time_s": int (if user_lat/lng provided)
    }
    """
    result = {
        "id": str(merchant.get("id", "")),
        "name": str(merchant.get("name", "")),
        "lat": float(merchant.get("lat", 0)),
        "lng": float(merchant.get("lng", 0)),
    }
    
    # Optional fields
    if "category" in merchant:
        result["category"] = str(merchant.get("category", ""))
    
    # Nova reward (important for perk display)
    if "nova_reward" in merchant:
        result["nova_reward"] = normalize_number(merchant.get("nova_reward", 0))
    
    # Logo URL
    if "logo_url" in merchant:
        result["logo_url"] = str(merchant.get("logo_url", ""))
    
    # Distance if user location provided
    if user_lat is not None and user_lng is not None:
        from app.services.verify_dwell import haversine_m
        distance = haversine_m(
            user_lat, user_lng,
            result["lat"], result["lng"]
        )
        result["distance_m"] = normalize_number(distance)
    
    # Walk time (if provided)
    if "walk_time_s" in merchant:
        result["walk_time_s"] = normalize_number(merchant.get("walk_time_s"))
    elif "walk_duration_s" in merchant:
        result["walk_time_s"] = normalize_number(merchant.get("walk_duration_s"))
    elif "walk_minutes" in merchant:
        # Convert walk_minutes to walk_time_s
        result["walk_time_s"] = normalize_number(merchant.get("walk_minutes", 0) * 60)
    
    return result


def shape_error(error_type: str, message: str) -> Dict[str, Any]:
    """
    Shape error response for PWA consumption.
    
    Args:
        error_type: "NotFound" | "BadRequest" | "Unauthorized" | "Internal"
        message: Human-readable error message
    
    Returns:
        {
            "error": {
                "type": str,
                "message": str
            }
        }
    """
    return {
        "error": {
            "type": error_type,
            "message": message
        }
    }

