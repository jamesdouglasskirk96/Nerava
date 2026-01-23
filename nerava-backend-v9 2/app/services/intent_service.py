"""
Intent Service
Handles intent capture logic: confidence tier assignment, charger lookup, session creation
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import IntentSession, Charger, MerchantCache
from app.core.config import settings
from app.services.google_places_new import search_nearby, _get_geo_cell

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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


def find_nearest_charger(db: Session, lat: float, lng: float) -> Optional[Tuple[Charger, float]]:
    """
    Find the nearest public charger to the given location.
    
    Args:
        db: Database session
        lat: Latitude
        lng: Longitude
    
    Returns:
        Tuple of (Charger, distance_m) or None if no charger found
    """
    # Query all public chargers
    chargers = db.query(Charger).filter(Charger.is_public == True).all()
    
    if not chargers:
        return None
    
    # Find nearest charger using Haversine distance
    nearest = None
    min_distance = float('inf')
    
    for charger in chargers:
        distance = haversine_distance(lat, lng, charger.lat, charger.lng)
        if distance < min_distance:
            min_distance = distance
            nearest = charger
    
    if nearest:
        return (nearest, min_distance)
    
    return None


def assign_confidence_tier(distance_m: Optional[float]) -> str:
    """
    Assign confidence tier based on distance to nearest charger.
    
    Args:
        distance_m: Distance to nearest charger in meters (None if no charger)
    
    Returns:
        Confidence tier: "A", "B", or "C"
    """
    if distance_m is None:
        return "C"
    
    if distance_m <= settings.CONFIDENCE_TIER_A_THRESHOLD_M:
        return "A"
    elif distance_m <= settings.CONFIDENCE_TIER_B_THRESHOLD_M:
        return "B"
    else:
        return "C"


def validate_location_accuracy(accuracy_m: Optional[float]) -> bool:
    """
    Validate that location accuracy meets threshold.
    
    Args:
        accuracy_m: Location accuracy in meters (None if not provided)
    
    Returns:
        True if accuracy is acceptable, False otherwise
    """
    if accuracy_m is None:
        # If accuracy not provided, allow but log warning
        logger.warning("Location accuracy not provided, allowing request")
        return True
    
    threshold = settings.LOCATION_ACCURACY_THRESHOLD_M
    if accuracy_m > threshold:
        logger.warning(f"Location accuracy {accuracy_m}m exceeds threshold {threshold}m")
        return False
    
    return True


async def create_intent_session(
    db: Session,
    user_id: int,
    lat: float,
    lng: float,
    accuracy_m: Optional[float] = None,
    client_ts: Optional[datetime] = None,
    source: str = "web",
) -> IntentSession:
    """
    Create an intent session with confidence tier assignment.
    
    Args:
        db: Database session
        user_id: User ID
        lat: Latitude
        lng: Longitude
        accuracy_m: Location accuracy in meters
        client_ts: Client timestamp
        source: Source of the intent (default "web")
    
    Returns:
        Created IntentSession
    """
    # Validate location accuracy
    if not validate_location_accuracy(accuracy_m):
        raise ValueError(f"Location accuracy {accuracy_m}m exceeds threshold {settings.LOCATION_ACCURACY_THRESHOLD_M}m")
    
    # Find nearest charger
    charger_result = find_nearest_charger(db, lat, lng)
    charger_id = None
    charger_distance_m = None
    
    if charger_result:
        charger, distance = charger_result
        charger_id = charger.id
        charger_distance_m = distance
    
    # Assign confidence tier
    confidence_tier = assign_confidence_tier(charger_distance_m)
    
    # Create intent session
    session = IntentSession(
        id=str(uuid.uuid4()),
        user_id=user_id,
        lat=lat,
        lng=lng,
        accuracy_m=accuracy_m,
        client_ts=client_ts,
        charger_id=charger_id,
        charger_distance_m=charger_distance_m,
        confidence_tier=confidence_tier,
        source=source,
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    logger.info(
        f"Created intent session {session.id} for user {user_id}: "
        f"tier={confidence_tier}, charger_distance={charger_distance_m}m"
    )
    
    return session


async def get_merchants_for_intent(
    db: Session,
    lat: float,
    lng: float,
    confidence_tier: str,
) -> List[Dict]:
    """
    Get merchants for intent session based on confidence tier.
    
    Applies placement rules (boost_weight, badges, daily_cap_cents) if available.
    
    Args:
        db: Database session
        lat: Latitude
        lng: Longitude
        confidence_tier: Confidence tier ("A", "B", or "C")
    
    Returns:
        List of merchant dictionaries with placement rules applied
    """
    # Only search for merchants if Tier A or B
    if confidence_tier == "C":
        return []
    
    # Search Google Places
    radius = settings.GOOGLE_PLACES_SEARCH_RADIUS_M
    merchants = await search_nearby(
        lat=lat,
        lng=lng,
        radius_m=radius,
        max_results=20,
    )
    
    # Cache merchants in database
    geo_cell_lat, geo_cell_lng = _get_geo_cell(lat, lng)
    expires_at = datetime.utcnow() + timedelta(seconds=settings.MERCHANT_CACHE_TTL_SECONDS)
    
    for merchant in merchants:
        place_id = merchant.get("place_id")
        if place_id:
            # Check if already cached
            cached = (
                db.query(MerchantCache)
                .filter(
                    MerchantCache.place_id == place_id,
                    MerchantCache.geo_cell_lat == geo_cell_lat,
                    MerchantCache.geo_cell_lng == geo_cell_lng,
                )
                .first()
            )
            
            if not cached:
                # Create cache entry
                cache_entry = MerchantCache(
                    place_id=place_id,
                    geo_cell_lat=geo_cell_lat,
                    geo_cell_lng=geo_cell_lng,
                    merchant_data=merchant,
                    photo_url=merchant.get("photo_url"),
                    expires_at=expires_at,
                )
                db.add(cache_entry)
            else:
                # Update existing cache
                cached.merchant_data = merchant
                cached.photo_url = merchant.get("photo_url")
                cached.expires_at = expires_at
                cached.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Query placement rules for all merchants
    from app.models import MerchantPlacementRule
    place_ids = [m.get("place_id") for m in merchants if m.get("place_id")]
    placement_rules = {}
    if place_ids:
        rules = (
            db.query(MerchantPlacementRule)
            .filter(
                MerchantPlacementRule.place_id.in_(place_ids),
                MerchantPlacementRule.status == "ACTIVE",
            )
            .all()
        )
        placement_rules = {rule.place_id: rule for rule in rules}
    
    # Apply placement rules and calculate boosted scores
    merchants_with_scores = []
    for merchant in merchants:
        place_id = merchant.get("place_id")
        if not place_id:
            continue
        
        # Base score is inverse of distance (closer = higher score)
        base_score = 1000.0 / max(merchant.get("distance_m", 1), 1)
        
        # Apply placement rule if exists
        rule = placement_rules.get(place_id)
        badges = []
        daily_cap_cents = None
        
        if rule:
            # Apply boost_weight additively
            boosted_score = base_score + rule.boost_weight
            
            # Add badges
            if rule.boost_weight > 0:
                badges.append("Boosted")
            if rule.perks_enabled:
                badges.append("Perks available")
            
            # Include daily_cap_cents (internal use only)
            daily_cap_cents = rule.daily_cap_cents
        else:
            boosted_score = base_score
        
        merchants_with_scores.append({
            **merchant,
            "_boosted_score": boosted_score,
            "badges": badges if badges else None,
            "daily_cap_cents": daily_cap_cents,
        })
    
    # Sort by boosted score (descending)
    merchants_sorted = sorted(
        merchants_with_scores,
        key=lambda m: m.get("_boosted_score", 0),
        reverse=True
    )
    
    # Remove internal score field
    for merchant in merchants_sorted:
        merchant.pop("_boosted_score", None)
    
    return merchants_sorted[:20]  # Return top 20


def get_intent_session_count(db: Session, user_id: int) -> int:
    """
    Get count of intent sessions for a user.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        Count of intent sessions
    """
    return db.query(IntentSession).filter(IntentSession.user_id == user_id).count()


def requires_vehicle_onboarding(db: Session, user_id: int, confidence_tier: str) -> bool:
    """
    Check if user requires vehicle onboarding based on session count, completion status, and confidence tier.
    
    Only requires onboarding when:
    - User has >= N intent sessions (configurable via INTENT_SESSION_ONBOARDING_THRESHOLD)
    - User has NOT completed onboarding (no APPROVED status in VehicleOnboarding)
    - Confidence tier is A or B (not C)
    
    Args:
        db: Database session
        user_id: User ID
        confidence_tier: Current confidence tier ("A", "B", or "C")
    
    Returns:
        True if onboarding required, False otherwise
    """
    # Don't require onboarding for Tier C (avoid annoying low-confidence cases)
    if confidence_tier == "C":
        return False
    
    # Check session count
    session_count = get_intent_session_count(db, user_id)
    threshold = settings.INTENT_SESSION_ONBOARDING_THRESHOLD
    if session_count < threshold:
        return False
    
    # Check if user has already completed onboarding
    from app.models import VehicleOnboarding
    completed = (
        db.query(VehicleOnboarding)
        .filter(
            VehicleOnboarding.user_id == user_id,
            VehicleOnboarding.status == "APPROVED",
        )
        .first()
    )
    
    if completed:
        return False
    
    return True

