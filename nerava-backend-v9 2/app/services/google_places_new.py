"""
Google Places API (New) client
Uses the new Places API with SearchNearby and GetPhotoMedia endpoints
"""
import logging
import httpx
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from app.core.config import settings as core_settings
from app.config import settings
from app.cache.layers import LayeredCache
from app.core.retry import retry_with_backoff

logger = logging.getLogger(__name__)

# Initialize cache (use redis_url from app.config)
cache = LayeredCache(settings.redis_url, region="google_places_new")

# Google Places API (New) base URL
GOOGLE_PLACES_NEW_BASE_URL = "https://places.googleapis.com/v1"

# Required field masks for SearchNearby
REQUIRED_FIELD_MASK = "places.id,places.displayName,places.location,places.types,places.iconMaskBaseUri,places.photos"


def _get_geo_cell(lat: float, lng: float, precision: float = 0.001) -> Tuple[float, float]:
    """
    Calculate geo cell for caching (simple lat/lng rounding).
    
    Args:
        lat: Latitude
        lng: Longitude
        precision: Rounding precision (default 0.001 degree ≈ 111m)
    
    Returns:
        Tuple of (rounded_lat, rounded_lng)
    """
    return (round(lat / precision) * precision, round(lng / precision) * precision)


def _get_mock_merchants(user_lat: float, user_lng: float) -> List[Dict]:
    """
    Return fixture merchants for deterministic testing.
    
    Includes Asadas Grill and Eggman ATX at test coordinates.
    """
    # Fixture merchants at test location (Austin, TX)
    fixture_merchants = [
        {
            "name": "Asadas Grill",
            "lat": 30.2680,
            "lng": -97.7435,
            "place_id": "mock_asadas_grill",
            "types": ["restaurant", "food"],
        },
        {
            "name": "Eggman ATX",
            "lat": 30.2665,
            "lng": -97.7425,
            "place_id": "mock_eggman_atx",
            "types": ["restaurant", "cafe"],
        },
        {
            "name": "Test Coffee Shop",
            "lat": 30.2675,
            "lng": -97.7440,
            "place_id": "mock_coffee_shop",
            "types": ["cafe", "restaurant"],
        },
    ]
    
    # Transform to merchant format (using _haversine_distance defined later in file)
    results = []
    for merchant in fixture_merchants:
        # Calculate distance using haversine (will be defined later, but we can import it)
        from .google_places_new import _haversine_distance
        distance_m = _haversine_distance(user_lat, user_lng, merchant["lat"], merchant["lng"])
        results.append({
            "place_id": merchant["place_id"],
            "name": merchant["name"],
            "lat": merchant["lat"],
            "lng": merchant["lng"],
            "distance_m": round(distance_m),
            "types": merchant["types"],
            "photo_url": None,
            "icon_url": None,
            "badges": ["Happy Hour ⭐️"] if merchant["name"] in ["Asadas Grill", "Eggman ATX"] else [],
        })
    
    # Sort by distance
    results.sort(key=lambda x: x["distance_m"])
    return results


async def search_nearby(
    lat: float,
    lng: float,
    radius_m: int = 800,
    included_types: Optional[List[str]] = None,
    max_results: int = 20,
) -> List[Dict]:
    """
    Search for places nearby using Google Places API (New) SearchNearby endpoint.
    
    Args:
        lat: Latitude
        lng: Longitude
        radius_m: Search radius in meters (default 800m)
        included_types: List of place types to include (e.g., ["restaurant", "cafe"])
        max_results: Maximum number of results to return
    
    Returns:
        List of place dictionaries with merchant data
    """
    # MOCK_PLACES support for deterministic testing
    import os
    if os.getenv('MOCK_PLACES', 'false').lower() == 'true':
        # Test location: Austin, TX (30.2672, -97.7431)
        test_lat, test_lng = 30.2672, -97.7431
        # Check if location is near test coordinates (within ~1km)
        if abs(lat - test_lat) < 0.01 and abs(lng - test_lng) < 0.01:
            logger.info("[GooglePlacesNew] MOCK_PLACES enabled, returning fixture merchants")
            return _get_mock_merchants(lat, lng)
    
    if not core_settings.GOOGLE_PLACES_API_KEY:
        logger.warning("[GooglePlacesNew] Missing API key, returning empty results")
        return []
    
    # Default included types for merchant search
    if included_types is None:
        included_types = [
            "restaurant",
            "cafe",
            "meal_takeaway",
            "shopping_mall",
            "clothing_store",
            "department_store",
            "supermarket",
            "bar",
            "tourist_attraction",
            "movie_theater",
            "book_store",
            "gym",
        ]
    
    # Check cache first
    geo_cell_lat, geo_cell_lng = _get_geo_cell(lat, lng)
    cache_key = f"places_nearby:{geo_cell_lat}:{geo_cell_lng}:{radius_m}"
    
    cached_result = await cache.get(cache_key)
    if cached_result is not None:
        logger.debug(f"[GooglePlacesNew] Cache hit for {cache_key}")
        return cached_result[:max_results]
    
    # Build request payload
    payload = {
        "includedTypes": included_types,
        "maxResultCount": min(max_results, 20),  # API limit is 20
        "locationRestriction": {
            "circle": {
                "center": {"latitude": lat, "longitude": lng},
                "radius": radius_m
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": core_settings.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": REQUIRED_FIELD_MASK,
    }
    
    url = f"{GOOGLE_PLACES_NEW_BASE_URL}/places:searchNearby"
    
    logger.info(
        f"[GooglePlacesNew] Searching nearby: lat={lat}, lng={lng}, radius={radius_m}m, types={included_types[:3]}..."
    )
    
    async def _make_request():
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    
    try:
        data = await retry_with_backoff(_make_request, max_attempts=3)
        
        places = data.get("places", [])
        logger.info(f"[GooglePlacesNew] Found {len(places)} places")
        
        # Transform to merchant format
        results = []
        for place in places[:max_results]:
            merchant_data = _transform_place_to_merchant(place, lat, lng)
            if merchant_data:
                # Resolve photo URL if it's a reference
                if merchant_data.get("photo_url", "").startswith("photo_ref:"):
                    photo_ref = merchant_data["photo_url"].replace("photo_ref:", "")
                    merchant_data["photo_url"] = await get_photo_url(photo_ref) or merchant_data.get("icon_url")
                results.append(merchant_data)
        
        # Cache results with TTL
        if results:
            ttl = core_settings.MERCHANT_CACHE_TTL_SECONDS
            await cache.set(cache_key, results, ttl=ttl)
            logger.debug(f"[GooglePlacesNew] Cached {len(results)} results for {ttl}s")
        
        return results
        
    except httpx.HTTPStatusError as e:
        logger.error(f"[GooglePlacesNew] HTTP error: {e.response.status_code} - {e.response.text}")
        return []
    except Exception as e:
        logger.error(f"[GooglePlacesNew] Error searching nearby: {e}", exc_info=True)
        return []


def _transform_place_to_merchant(place: Dict, user_lat: float, user_lng: float) -> Optional[Dict]:
    """
    Transform Google Places API (New) place data to merchant format.
    
    Args:
        place: Place data from Google Places API
        user_lat: User's latitude (for distance calculation)
        user_lng: User's longitude (for distance calculation)
    
    Returns:
        Merchant dictionary or None if invalid
    """
    try:
        place_id = place.get("id", "").replace("places/", "")
        display_name = place.get("displayName", {})
        name = display_name.get("text", "") if isinstance(display_name, dict) else str(display_name)
        
        if not name or not place_id:
            return None
        
        location = place.get("location", {})
        place_lat = location.get("latitude", 0)
        place_lng = location.get("longitude", 0)
        
        # Calculate distance (Haversine)
        distance_m = _haversine_distance(user_lat, user_lng, place_lat, place_lng)
        
        # Get types
        types = place.get("types", [])
        
        # Get photo URL (prefer photos over icon)
        photo_url = None
        photos = place.get("photos", [])
        if photos and len(photos) > 0:
            # Store photo reference for later retrieval (async call happens in search_nearby)
            photo_reference = photos[0].get("name", "").replace("places/", "").split("/photos/")[-1]
            if photo_reference:
                # Will be populated by async call
                photo_url = f"photo_ref:{photo_reference}"
        
        # Fallback to icon if no photo
        if not photo_url:
            icon_mask_base_uri = place.get("iconMaskBaseUri", "")
            if icon_mask_base_uri:
                photo_url = icon_mask_base_uri.replace("pinlet_v2", "pinlet")
        
        return {
            "place_id": place_id,
            "name": name,
            "lat": place_lat,
            "lng": place_lng,
            "distance_m": round(distance_m),
            "types": types,
            "photo_url": photo_url,
            "icon_url": place.get("iconMaskBaseUri", ""),
        }
    except Exception as e:
        logger.error(f"[GooglePlacesNew] Error transforming place: {e}", exc_info=True)
        return None


async def get_photo_url(photo_reference: str, max_width: int = 400) -> Optional[str]:
    """
    Get photo URL using Google Places API (New) GetPhotoMedia endpoint.
    
    Args:
        photo_reference: Photo reference from place data
        max_width: Maximum width in pixels
    
    Returns:
        Photo URL or None if error
    """
    if not core_settings.GOOGLE_PLACES_API_KEY or not photo_reference:
        return None
    
    # Check cache
    cache_key = f"photo_url:{photo_reference}:{max_width}"
    cached_url = await cache.get(cache_key)
    if cached_url:
        return cached_url
    
    # Build photo name (format: places/{place_id}/photos/{photo_reference})
    # Note: photo_reference might already be in this format
    if "/photos/" in photo_reference:
        photo_name = photo_reference
    else:
        # We need the place_id, but we don't have it here
        # For now, use the old API format as fallback
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={core_settings.GOOGLE_PLACES_API_KEY}"
    
    url = f"{GOOGLE_PLACES_NEW_BASE_URL}/{photo_name}/media"
    params = {
        "maxWidthPx": max_width,
        "key": core_settings.GOOGLE_PLACES_API_KEY,
    }
    
    headers = {
        "X-Goog-Api-Key": core_settings.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "photoUri",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            photo_uri = data.get("photoUri")
            
            if photo_uri:
                # Cache for 24 hours
                await cache.set(cache_key, photo_uri, ttl=86400)
                return photo_uri
    except Exception as e:
        logger.warning(f"[GooglePlacesNew] Error getting photo URL: {e}")
        # Fallback to old API format
        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth={max_width}&photoreference={photo_reference}&key={core_settings.GOOGLE_PLACES_API_KEY}"
    
    return None


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate Haversine distance between two points in meters.
    
    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
    
    Returns:
        Distance in meters
    """
    import math
    
    # Earth's radius in meters
    R = 6371000
    
    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (
        math.sin(delta_phi / 2) ** 2 +
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

