"""
Service layer for "While You Charge" search and ranking
"""
import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from math import radians, cos, sin, asin, sqrt
import uuid

from app.models_while_you_charge import Charger, Merchant, ChargerMerchant, MerchantPerk
from app.integrations.nrel_client import fetch_chargers_in_bbox, ChargerData
from app.integrations.google_places_client import (
    search_places_near, normalize_category_to_google_type, PlaceData, get_place_details
)
from app.integrations.google_distance_matrix_client import get_walk_times

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two lat/lng points"""
    R = 6371000  # Earth radius in meters
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    return R * c


def normalize_query_to_category(query: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalize query to canonical category or treat as merchant name.
    
    Returns:
        (category, merchant_name) - one will be None
    """
    query_lower = query.lower().strip()
    
    category_map = {
        "coffee": "coffee",
        "cafe": "coffee",
        "food": "food",
        "restaurant": "food",
        "dining": "food",
        "groceries": "groceries",
        "grocery": "groceries",
        "supermarket": "groceries",
        "gym": "gym",
        "fitness": "gym",
        "workout": "gym"
    }
    
    for key, category in category_map.items():
        if key in query_lower:
            return (category, None)
    
    # Not a category, treat as merchant name
    return (None, query)


async def find_chargers_near(
    db: Session,
    user_lat: float,
    user_lng: float,
    radius_m: float = 10000,
    max_drive_minutes: int = 15
) -> List[Charger]:
    """
    Find chargers near user location.
    If none found in DB, fetch from API and seed.
    """
    logger.info(f"[WhileYouCharge] Finding chargers near ({user_lat}, {user_lng}) within {radius_m}m")
    
    # Rough bounding box (not perfect circle, but good enough)
    # 1 degree lat ≈ 111km, 1 degree lng ≈ 111km * cos(lat)
    lat_deg = radius_m / 111000
    lng_deg = radius_m / (111000 * abs(cos(radians(user_lat))))
    
    min_lat = user_lat - lat_deg
    max_lat = user_lat + lat_deg
    min_lng = user_lng - lng_deg
    max_lng = user_lng + lng_deg
    
    # Query DB
    chargers = db.query(Charger).filter(
        and_(
            Charger.lat >= min_lat,
            Charger.lat <= max_lat,
            Charger.lng >= min_lng,
            Charger.lng <= max_lng,
            Charger.is_public == True
        )
    ).limit(50).all()
    
    logger.info(f"[WhileYouCharge] Found {len(chargers)} chargers in DB")
    
    # If no chargers in DB, fetch from API
    if not chargers:
        logger.info("[WhileYouCharge] No chargers in DB, fetching from NREL API...")
        bbox = (min_lat, min_lng, max_lat, max_lng)
        charger_data_list = await fetch_chargers_in_bbox(bbox, limit=50)
        logger.info(f"[WhileYouCharge] Fetched {len(charger_data_list)} chargers from NREL API")
        
        # Save to DB
        for charger_data in charger_data_list:
            charger = Charger(
                id=f"ch_{uuid.uuid4().hex[:12]}",
                external_id=charger_data.external_id,
                name=charger_data.name,
                network_name=charger_data.network_name,
                lat=charger_data.lat,
                lng=charger_data.lng,
                address=charger_data.address,
                city=charger_data.city,
                state=charger_data.state,
                zip_code=charger_data.zip_code,
                connector_types=charger_data.connector_types,
                power_kw=charger_data.power_kw,
                is_public=charger_data.is_public,
                access_code=charger_data.access_code,
                status=charger_data.status
            )
            db.add(charger)
        
        db.commit()
        logger.info(f"[WhileYouCharge] Saved {len(charger_data_list)} new chargers to DB")
        
        # Requery
        chargers = db.query(Charger).filter(
            and_(
                Charger.lat >= min_lat,
                Charger.lat <= max_lat,
                Charger.lng >= min_lng,
                Charger.lng <= max_lng,
                Charger.is_public == True
            )
        ).limit(50).all()
    
    # Filter by drive time (rough estimate: 60 km/h average)
    # This is approximate - in production you might use routing API
    filtered = []
    for charger in chargers:
        distance_m = haversine_distance(user_lat, user_lng, charger.lat, charger.lng)
        drive_time_min = (distance_m / 1000) / (60 / 60)  # km / (km/min) = minutes
        if drive_time_min <= max_drive_minutes:
            filtered.append(charger)
    
    logger.info(f"[WhileYouCharge] Filtered to {len(filtered)} chargers within {max_drive_minutes} min drive time")
    return filtered


async def find_and_link_merchants(
    db: Session,
    chargers: List[Charger],
    category: Optional[str],
    merchant_name: Optional[str],
    max_walk_minutes: int = 10
) -> List[Merchant]:
    """
    Find merchants linked to chargers, or fetch new ones from Google Places.
    """
    logger.info(f"[WhileYouCharge] Finding merchants for {len(chargers)} chargers, category={category}, name={merchant_name}")
    
    charger_ids = [c.id for c in chargers]
    
    # Query existing linked merchants
    query = db.query(Merchant).join(ChargerMerchant).filter(
        ChargerMerchant.charger_id.in_(charger_ids),
        ChargerMerchant.walk_duration_s <= max_walk_minutes * 60
    )
    
    if category:
        query = query.filter(Merchant.category == category)
    elif merchant_name:
        query = query.filter(Merchant.name.ilike(f"%{merchant_name}%"))
    
    existing_merchants = query.distinct().all()
    logger.info(f"[WhileYouCharge] Found {len(existing_merchants)} existing merchants in DB")
    
    # If we have enough merchants, return them
    if len(existing_merchants) >= 5:
        logger.info(f"[WhileYouCharge] Returning {len(existing_merchants)} existing merchants (sufficient)")
        return existing_merchants
    
    # Otherwise, fetch from Google Places
    # Search around each charger
    logger.info(f"[WhileYouCharge] Not enough merchants in DB ({len(existing_merchants)} < 5), fetching from Google Places...")
    all_new_merchants = []
    
    for charger in chargers[:10]:  # Limit to avoid too many API calls
        logger.debug(f"Searching merchants near charger {charger.id} ({charger.name})")
        # Determine Google Places types / keyword
        if category:
            place_types, keyword = normalize_category_to_google_type(category)
        else:
            place_types = []
            keyword = merchant_name.lower() if merchant_name else None
        
        # Search for places
        places = await search_places_near(
            lat=charger.lat,
            lng=charger.lng,
            query=merchant_name,
            types=place_types if place_types else None,
            radius_m=800,  # 800m radius - reasonable walking distance
            limit=20,  # Get more results to filter down by walk time
            keyword=keyword
        )
        
        logger.warning(
            "[WhileYouCharge] Charger %s (%s): Got %d places from Google, types=%s, keyword=%s, location=(%s,%s)",
            charger.id,
            charger.name,
            len(places),
            place_types,
            keyword,
            charger.lat,
            charger.lng
        )
        
        if not places:
            logger.error(
                "[WhileYouCharge] ⚠️ No places returned for charger %s (%s) at (%s,%s) - check [PLACES] logs above",
                charger.id,
                charger.name,
                charger.lat,
                charger.lng
            )
            continue
        
        # Get walk times for all places
        origins = [(charger.lat, charger.lng)]
        destinations = [(p.lat, p.lng) for p in places]
        
        if destinations:
            logger.error(
                "[WhileYouCharge] 📍 Getting walk times for %d places from charger %s at (%s,%s)",
                len(destinations),
                charger.id,
                charger.lat,
                charger.lng
            )
            walk_times = await get_walk_times(origins, destinations)
            logger.error(
                "[WhileYouCharge] 📍 Walk times received: %d/%d places have walk info",
                len([k for k in walk_times.keys() if walk_times[k].get("status") == "OK"]),
                len(destinations)
            )
            
            places_filtered_by_walk = 0
            places_filtered_by_straight_distance = 0
            for place in places:
                # First, check straight-line distance (cheap check before walk time API call)
                straight_distance_m = haversine_distance(
                    charger.lat, charger.lng,
                    place.lat, place.lng
                )
                # Filter out places more than 1.5km straight-line (walk distance will be longer)
                if straight_distance_m > 1500:
                    logger.error(
                        "[WhileYouCharge] ❌ Dropping place '%s': too far (straight-line distance=%dm, max=1500m)",
                        place.name,
                        int(straight_distance_m)
                    )
                    places_filtered_by_straight_distance += 1
                    continue
                
                dest = (place.lat, place.lng)
                walk_info = walk_times.get((origins[0], dest))
                
                if not walk_info:
                    logger.error(
                        "[WhileYouCharge] ❌ Dropping place '%s': no walk info from Distance Matrix. Place location=(%s,%s), charger=(%s,%s), straight_distance=%dm",
                        place.name,
                        place.lat,
                        place.lng,
                        charger.lat,
                        charger.lng,
                        int(straight_distance_m)
                    )
                    places_filtered_by_walk += 1
                    continue
                
                walk_seconds = walk_info["duration_s"]
                if walk_seconds > max_walk_minutes * 60:
                    logger.error(
                        "[WhileYouCharge] ❌ Dropping place '%s': walk_time=%ds (max=%ds). Walk distance: %dm, straight distance: %dm",
                        place.name,
                        walk_seconds,
                        max_walk_minutes * 60,
                        walk_info.get("distance_m", 0),
                        int(straight_distance_m)
                    )
                    places_filtered_by_walk += 1
                    continue
                
                logger.error(
                    "[WhileYouCharge] ✅ Keeping place '%s': walk_time=%ds, distance=%dm, location=(%s,%s)",
                    place.name,
                    walk_seconds,
                    walk_info.get("distance_m", 0),
                    place.lat,
                    place.lng
                )
                
                # Check if merchant already exists
                existing = db.query(Merchant).filter(
                    Merchant.external_id == place.place_id
                ).first()
                
                if existing:
                    merchant = existing
                else:
                    # Get place details for more info (optional, may fail)
                    details = None
                    try:
                        details = await get_place_details(place.place_id)
                    except Exception as e:
                        logger.debug(f"Could not get place details for {place.place_id}: {e}")
                    
                    # Create new merchant
                    merchant = Merchant(
                        id=f"m_{uuid.uuid4().hex[:12]}",
                        external_id=place.place_id,
                        name=place.name,
                        category=category or "other",
                        lat=place.lat,
                        lng=place.lng,
                        address=place.address or (details.get("formatted_address") if details else ""),
                        rating=place.rating or (details.get("rating") if details else None),
                        price_level=place.price_level or (details.get("price_level") if details else None),
                        place_types=place.types,
                        logo_url=place.icon,
                        photo_url=details.get("photos", [{}])[0].get("photo_reference") if details and details.get("photos") else None,
                        phone=details.get("formatted_phone_number") if details else None,
                        website=details.get("website") if details else None
                    )
                    db.add(merchant)
                    db.flush()
                
                # Create or update charger-merchant link
                link = db.query(ChargerMerchant).filter(
                    and_(
                        ChargerMerchant.charger_id == charger.id,
                        ChargerMerchant.merchant_id == merchant.id
                    )
                ).first()
                
                if not link:
                    link = ChargerMerchant(
                        charger_id=charger.id,
                        merchant_id=merchant.id,
                        distance_m=haversine_distance(
                            charger.lat, charger.lng, merchant.lat, merchant.lng
                        ),
                        walk_duration_s=walk_info["duration_s"],
                        walk_distance_m=walk_info.get("distance_m")
                    )
                    db.add(link)
                
                all_new_merchants.append(merchant)
                logger.error(
                    "[WhileYouCharge] ✅ Added merchant '%s' (id=%s) for charger %s",
                    merchant.name,
                    merchant.id,
                    charger.id
                )
    
    logger.error(
        "[WhileYouCharge] 📊 Before commit: %d merchants in all_new_merchants list",
        len(all_new_merchants)
    )
    db.commit()
    
    # Combine existing and new
    all_merchants = list(existing_merchants) + all_new_merchants
    # Deduplicate by ID
    seen = set()
    unique_merchants = []
    for m in all_merchants:
        if m.id not in seen:
            seen.add(m.id)
            unique_merchants.append(m)
    
    logger.warning(
        "[WhileYouCharge] SUMMARY: %d unique merchants total (%d existing from DB, %d newly created/linked). "
        "Check [PLACES] logs above for Google API status and [WhileYouCharge] logs for filtering details.",
        len(unique_merchants),
        len(existing_merchants),
        len(all_new_merchants)
    )
    return unique_merchants


def rank_merchants(
    db: Session,
    merchants: List[Merchant],
    chargers: List[Charger],
    user_lat: float,
    user_lng: float
) -> List[Dict]:
    """
    Rank merchants by drive time, walk time, rating, and active perks.
    
    Returns list of dicts with merchant info and scores.
    """
    logger.info(f"[WhileYouCharge] Ranking {len(merchants)} merchants for {len(chargers)} chargers")
    
    charger_ids = [c.id for c in chargers]
    merchant_ids = [m.id for m in merchants]
    
    # Get all charger-merchant links
    links = db.query(ChargerMerchant).filter(
        ChargerMerchant.merchant_id.in_(merchant_ids),
        ChargerMerchant.charger_id.in_(charger_ids)
    ).all()
    logger.debug(f"[WhileYouCharge] Found {len(links)} charger-merchant links")
    
    # Get active perks
    perks = db.query(MerchantPerk).filter(
        MerchantPerk.merchant_id.in_(merchant_ids),
        MerchantPerk.is_active == True
    ).all()
    perks_by_merchant = {p.merchant_id: p for p in perks}
    logger.debug(f"[WhileYouCharge] Found {len(perks)} active perks")
    
    # Build merchant data with scores
    merchant_scores = []
    skipped_no_link = 0
    
    for merchant in merchants:
        # Find best charger link (shortest walk time)
        best_link = None
        best_walk_time = float('inf')
        linked_charger = None
        
        for link in links:
            if link.merchant_id == merchant.id:
                if link.walk_duration_s < best_walk_time:
                    best_walk_time = link.walk_duration_s
                    best_link = link
                    linked_charger = next((c for c in chargers if c.id == link.charger_id), None)
        
        if not best_link:
            skipped_no_link += 1
            continue  # Skip merchants without charger links
        
        # Calculate drive time to charger (rough estimate)
        if linked_charger:
            drive_distance_m = haversine_distance(
                user_lat, user_lng, linked_charger.lat, linked_charger.lng
            )
            drive_time_min = (drive_distance_m / 1000) / (60 / 60)  # Approximate
        else:
            drive_time_min = 999
        
        # Get perk
        perk = perks_by_merchant.get(merchant.id)
        nova_reward = perk.nova_reward if perk else 10  # Default 10 Nova
        
        # Calculate score (lower is better)
        # Weight: drive time (40%), walk time (30%), rating (20%), perk bonus (10%)
        drive_score = drive_time_min * 0.4
        walk_score = (best_walk_time / 60) * 0.3
        rating_score = (5 - (merchant.rating or 3.5)) * 0.2  # Lower rating = higher score
        perk_bonus = (20 - nova_reward) * 0.1  # Higher reward = lower score
        
        total_score = drive_score + walk_score + rating_score + perk_bonus
        
        merchant_scores.append({
            "merchant": merchant,
            "charger": linked_charger,
            "walk_time_s": best_walk_time,
            "walk_time_min": int(best_walk_time / 60),
            "drive_time_min": int(drive_time_min),
            "nova_reward": nova_reward,
            "perk": perk,
            "score": total_score
        })
    
    # Sort by score (ascending)
    merchant_scores.sort(key=lambda x: x["score"])
    
    logger.info(f"[WhileYouCharge] Ranked {len(merchant_scores)} merchants (skipped {skipped_no_link} without charger links)")
    return merchant_scores


def get_domain_hub_view(db: Session) -> Dict:
    """
    Get Domain hub view with chargers and recommended merchants.
    
    Uses Domain hub configuration to fetch chargers and find linked merchants.
    
    Returns:
        Dict with hub_id, hub_name, chargers, and merchants
    """
    from app.domains.domain_hub import DOMAIN_CHARGERS, HUB_ID, HUB_NAME
    
    logger.info(f"[DomainHub] Fetching Domain hub view")
    
    # Get charger IDs from config
    charger_ids = [ch["id"] for ch in DOMAIN_CHARGERS]
    
    # Fetch chargers from DB
    chargers = db.query(Charger).filter(Charger.id.in_(charger_ids)).all()
    
    # Create a map of charger ID -> charger object
    chargers_by_id = {c.id: c for c in chargers}
    
    # Build charger list in config order (fallback to config if not in DB)
    charger_list = []
    for charger_config in DOMAIN_CHARGERS:
        charger_id = charger_config["id"]
        charger = chargers_by_id.get(charger_id)
        
        if charger:
            # Use DB charger data
            charger_list.append({
                "id": charger.id,
                "name": charger.name,
                "lat": charger.lat,
                "lng": charger.lng,
                "network_name": charger.network_name,
                "logo_url": charger.logo_url,
                "address": charger.address,
                "radius_m": charger_config.get("radius_m", 1000)
            })
        else:
            # Fallback to config data (charger not yet seeded)
            logger.warning(f"[DomainHub] Charger {charger_id} not found in DB, using config data")
            charger_list.append({
                "id": charger_config["id"],
                "name": charger_config["name"],
                "lat": charger_config["lat"],
                "lng": charger_config["lng"],
                "network_name": charger_config["network_name"],
                "logo_url": None,
                "address": charger_config.get("address"),
                "radius_m": charger_config.get("radius_m", 1000)
            })
    
    # Find merchants linked to Domain chargers
    merchant_ids = []
    if chargers:
        charger_ids_in_db = [c.id for c in chargers]
        links = db.query(ChargerMerchant).filter(
            ChargerMerchant.charger_id.in_(charger_ids_in_db)
        ).all()
        
        merchant_ids = list(set([link.merchant_id for link in links]))
    
    # Fetch merchants
    merchants = []
    if merchant_ids:
        merchants_query = db.query(Merchant).filter(Merchant.id.in_(merchant_ids)).all()
        
        # Get charger-merchant links for walk times
        links = db.query(ChargerMerchant).filter(
            ChargerMerchant.merchant_id.in_(merchant_ids),
            ChargerMerchant.charger_id.in_(charger_ids)
        ).all()
        
        # Create map of merchant_id -> best link (shortest walk time)
        links_by_merchant = {}
        for link in links:
            merchant_id = link.merchant_id
            if merchant_id not in links_by_merchant or link.walk_duration_s < links_by_merchant[merchant_id].walk_duration_s:
                links_by_merchant[merchant_id] = link
        
        # Get active perks
        perks = db.query(MerchantPerk).filter(
            MerchantPerk.merchant_id.in_(merchant_ids),
            MerchantPerk.is_active == True
        ).all()
        perks_by_merchant = {p.merchant_id: p for p in perks}
        
        # Build merchant list with walk times and perks
        for merchant in merchants_query:
            link = links_by_merchant.get(merchant.id)
            perk = perks_by_merchant.get(merchant.id)
            
            merchant_data = {
                "id": merchant.id,
                "name": merchant.name,
                "lat": merchant.lat,
                "lng": merchant.lng,
                "category": merchant.category,
                "logo_url": merchant.logo_url,
                "address": merchant.address,
                "nova_reward": perk.nova_reward if perk else 10,
                "walk_minutes": int(link.walk_duration_s / 60) if link else None,
                "walk_distance_m": link.walk_distance_m if link else None,
                "distance_m": link.distance_m if link else None
            }
            merchants.append(merchant_data)
        
        # Sort merchants by walk time (ascending)
        merchants.sort(key=lambda m: m.get("walk_minutes") or 999)
    
    logger.info(f"[DomainHub] Found {len(charger_list)} chargers, {len(merchants)} merchants")
    
    return {
        "hub_id": HUB_ID,
        "hub_name": HUB_NAME,
        "chargers": charger_list,
        "merchants": merchants
    }

