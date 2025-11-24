"""
Google Places API client
https://developers.google.com/maps/documentation/places/web-service
"""
import json
import logging
import os
import httpx
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Hardcoded API key (no longer reads from environment variables)
GOOGLE_PLACES_API_KEY = "AIzaSyAs0PVYXj3-ztRXCjdd0ztUGUSjQR73FFg"

GOOGLE_PLACES_BASE_URL = "https://maps.googleapis.com/maps/api/place"


class PlaceData:
    """Data class for Google Places result"""
    def __init__(self, data: Dict):
        self.place_id = data.get("place_id")
        self.name = data.get("name", "")
        self.lat = data.get("geometry", {}).get("location", {}).get("lat", 0)
        self.lng = data.get("geometry", {}).get("location", {}).get("lng", 0)
        self.address = data.get("formatted_address", "")
        self.rating = data.get("rating")
        self.price_level = data.get("price_level")
        self.types = data.get("types", [])
        self.photos = data.get("photos", [])
        self.icon = data.get("icon")
        self.business_status = data.get("business_status", "OPERATIONAL")


async def search_places_near(
    lat: float,
    lng: float,
    query: Optional[str] = None,
    types: Optional[List[str]] = None,
    radius_m: int = 2000,
    limit: int = 20,
    keyword: Optional[str] = None,
) -> List[PlaceData]:
    """
    Search for places near a location.
    
    Args:
        lat: Latitude
        lng: Longitude
        query: Text search query (optional)
        types: List of place types (e.g., ["cafe", "restaurant"])
        radius_m: Search radius in meters
        limit: Maximum results
        keyword: Keyword filter (used for categories)
    
    Returns:
        List of PlaceData objects
    """
    # Use Nearby Search if types are provided, otherwise Text Search
    if types and not query:
        return await _nearby_search(lat, lng, types, radius_m, limit, keyword)
    else:
        return await _text_search(lat, lng, query, types, radius_m, limit)


async def _nearby_search(
    lat: float,
    lng: float,
    types: List[str],
    radius_m: int,
    limit: int,
    keyword: Optional[str] = None,
) -> List[PlaceData]:
    """Use Places Nearby Search API"""
    results: List[PlaceData] = []

    if not GOOGLE_PLACES_API_KEY:
        logger.error("[GooglePlaces] Cannot call Nearby Search: missing API key")
        return results

    for place_type in types[:1] or [None]:  # Google only allows one type per request
        params = {
            "key": GOOGLE_PLACES_API_KEY,
            "location": f"{lat},{lng}",
            "radius": radius_m,  # Use radius instead of rankby=distance to limit search area
        }
        if place_type:
            params["type"] = place_type
        if keyword:
            params["keyword"] = keyword
        elif place_type:
            params["keyword"] = place_type
        else:
            params["keyword"] = "nearby"
        
        # Note: When using radius, results are ranked by prominence, not distance
        # But we'll filter by walk time after getting results

        logger.info(
            "[GooglePlaces][Nearby] Searching: lat=%s lng=%s type=%s radius=%s keyword=%s",
            lat,
            lng,
            place_type,
            radius_m,
            keyword,
        )

        try:
            logger.error("[PLACES] 🔍 Making request to Google Places API: %s", f"{GOOGLE_PLACES_BASE_URL}/nearbysearch/json")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{GOOGLE_PLACES_BASE_URL}/nearbysearch/json",
                    params=params,
                )
                logger.error("[PLACES] 🔍 HTTP Response status: %d", response.status_code)
                response.raise_for_status()
                data = response.json()
                logger.error("[PLACES] 🔍 Got JSON response, parsing...")
                
                status = data.get("status")
                raw_results = data.get("results", [])
                
                # Log status and results count prominently (WARNING level so it shows up)
                logger.error(
                    "[PLACES] 🔍 Status: %s, results=%d, location=(%s,%s), type=%s, keyword=%s",
                    status,
                    len(raw_results),
                    lat,
                    lng,
                    place_type,
                    keyword or "none"
                )
                
                # Log first result details if available
                if raw_results and len(raw_results) > 0:
                    first_result = raw_results[0]
                    logger.error(
                        "[PLACES] ✅ First result: name='%s', place_id=%s, location=(%s,%s)",
                        first_result.get("name", "N/A"),
                        first_result.get("place_id", "N/A"),
                        first_result.get("geometry", {}).get("location", {}).get("lat", "N/A"),
                        first_result.get("geometry", {}).get("location", {}).get("lng", "N/A"),
                    )
                    
                    # Log a few more if available
                    if len(raw_results) > 1:
                        result_names = [r.get("name", "N/A") for r in raw_results[:5]]
                        logger.error("[PLACES] Sample results: %s", ", ".join(result_names))
                else:
                    logger.error("[PLACES] ❌ NO RESULTS (status=%s). Full response: %s", status, json.dumps(data)[:500])
                    if status == "OK":
                        logger.error("[PLACES] ❌ Status is OK but no results - check query params")

                if status in {"REQUEST_DENIED", "ZERO_RESULTS"}:
                    logger.error(f"[PLACES_ERROR] Status: {status}, Full response: {json.dumps(data)[:500]}")

                if status != "OK":
                    logger.warning(
                        "[GooglePlaces][Nearby] Non-OK status: %s error_message=%s",
                        status,
                        data.get("error_message"),
                    )
                    continue

                for place in raw_results[:limit]:
                    results.append(PlaceData(place))
                    logger.debug("[PLACES] Added place: %s (lat=%s, lng=%s)", place.get("name"), place.get("geometry", {}).get("location", {}).get("lat"), place.get("geometry", {}).get("location", {}).get("lng"))

        except Exception as e:
            logger.error(
                "[PLACES] ❌ EXCEPTION in Nearby Search: %s, location=(%s,%s), type=%s", 
                str(e), 
                lat, 
                lng, 
                place_type,
                exc_info=True
            )

    return results[:limit]


async def _text_search(
    lat: float,
    lng: float,
    query: Optional[str],
    types: Optional[List[str]],
    radius_m: int,
    limit: int
) -> List[PlaceData]:
    """Use Places Text Search API"""
    if not query:
        logger.info("[GooglePlaces][Text] Skipping: empty query")
        return []

    if not GOOGLE_PLACES_API_KEY:
        logger.error("[GooglePlaces][Text] Cannot call Text Search: missing API key")
        return []

    # Build query string
    query_str = query
    if types:
        query_str = f"{query} {' '.join(types)}"

    params = {
        "key": GOOGLE_PLACES_API_KEY,
        "query": query_str,
        "location": f"{lat},{lng}",
        "radius": radius_m,
    }

    logger.info(
        "[GooglePlaces][Text] query=%s lat=%s lng=%s radius=%s types=%s",
        query_str,
        lat,
        lng,
        radius_m,
        types,
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{GOOGLE_PLACES_BASE_URL}/textsearch/json",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            
            status = data.get("status")
            raw_results = data.get("results", [])
            
            # Log status and results count prominently
            logger.info(
                "[PLACES][Text] Status: %s, results=%d, query=%s, location=(%s,%s)",
                status,
                len(raw_results),
                query_str,
                lat,
                lng
            )
            
            # Log first result details if available
            if raw_results and len(raw_results) > 0:
                first_result = raw_results[0]
                logger.info(
                    "[PLACES][Text] First result: name=%s, place_id=%s",
                    first_result.get("name", "N/A"),
                    first_result.get("place_id", "N/A"),
                )
            else:
                logger.warning("[PLACES][Text] No results in response (status=%s)", status)

            if status in {"REQUEST_DENIED", "ZERO_RESULTS"}:
                logger.error(f"[PLACES_ERROR][Text] Status: {status}, Full response: {json.dumps(data)[:500]}")

            if status != "OK":
                logger.warning(
                    "[GooglePlaces][Text] Non-OK status: %s error_message=%s",
                    status,
                    data.get("error_message"),
                )
                return []

            results: List[PlaceData] = []
            for place in raw_results[:limit]:
                results.append(PlaceData(place))
                logger.debug("[PLACES][Text] Added place: %s", place.get("name"))

            return results

    except Exception as e:
        logger.error("[GooglePlaces][Text] error: %s", e, exc_info=True)
        return []


async def get_place_details(place_id: str) -> Optional[Dict]:
    """Get detailed information about a place"""
    if not GOOGLE_PLACES_API_KEY:
        logger.error("[GooglePlaces][Details] Cannot call Details: missing API key")
        return None

    params = {
        "key": GOOGLE_PLACES_API_KEY,
        "place_id": place_id,
        "fields": (
            "name,formatted_address,geometry,rating,price_level,types,"
            "photos,website,formatted_phone_number,opening_hours"
        ),
    }

    logger.info("[GooglePlaces][Details] place_id=%s", place_id)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{GOOGLE_PLACES_BASE_URL}/details/json",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            logger.warning(f"[PLACES] Request params: {params}")
            logger.warning(f"[PLACES] Response: {json.dumps(data)[:500]}")

            status = data.get("status")
            logger.info("[GooglePlaces][Details] status=%s", status)

            if status in {"REQUEST_DENIED", "ZERO_RESULTS"}:
                logger.error(f"[PLACES_ERROR] {data}")

            if status != "OK":
                logger.warning(
                    "[GooglePlaces][Details] Non-OK status: %s error_message=%s",
                    status,
                    data.get("error_message"),
                )
                return None

            return data.get("result")

    except Exception as e:
        logger.error("[GooglePlaces][Details] error: %s", e, exc_info=True)
        return None


def normalize_category_to_google_type(category: str) -> Tuple[List[str], str]:
    """
    Convert our category keywords to Google Places types and keyword.
    
    Returns (types, keyword) tuple.
    """
    normalized = category.lower().strip() if category else ""
    mapping = {
        "coffee": {
            "types": ["cafe", "coffee_shop"],
            "keywords": ["coffee", "espresso", "cafe", "coffeeshop", "starbucks"],
        },
        "food": {
            "types": ["restaurant", "meal_takeaway", "food"],
            "keywords": ["lunch", "dinner", "restaurant", "food"],
        },
        "groceries": {
            "types": ["supermarket", "grocery_or_supermarket", "convenience_store"],
            "keywords": ["groceries", "grocery store", "supermarket", "whole foods"],
        },
        "gym": {
            "types": ["gym", "health", "fitness_center"],
            "keywords": ["gym", "fitness", "workout", "yoga"],
        },
    }
    entry = mapping.get(normalized, {"types": [], "keywords": [normalized or "nearby"]})
    types = entry["types"]
    keyword = " ".join([kw for kw in entry["keywords"] if kw]).strip() or normalized or "nearby"
    return types, keyword

