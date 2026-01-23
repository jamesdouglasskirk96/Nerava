"""
Service for fetching merchant details
"""
import os
import math
import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.while_you_charge import Merchant, MerchantPerk
from app.models.intent import IntentSession
from app.schemas.merchants import MerchantDetailsResponse, MerchantInfo, MomentInfo, PerkInfo, WalletInfo, ActionsInfo


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in miles"""
    R = 3959  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def get_hours_today(opening_hours: Optional[Dict[str, Any]]) -> Optional[str]:
    """Get today's hours from opening_hours JSON."""
    if not opening_hours or 'weekday_text' not in opening_hours:
        return None

    # Get today's day of week (0=Monday, 6=Sunday)
    today = datetime.datetime.now().weekday()

    weekday_text = opening_hours.get('weekday_text', [])
    if today < len(weekday_text):
        # Parse "Monday: 11:00 AM – 10:00 PM" -> "11 AM–10 PM"
        full_text = weekday_text[today]
        if ':' in full_text:
            hours_part = full_text.split(':', 1)[1].strip()
            # Simplify format: remove :00, normalize spacing
            hours_part = hours_part.replace(':00', '').replace(' AM', ' AM').replace(' PM', ' PM')
            hours_part = hours_part.replace(' – ', '–').replace(' - ', '–')
            return hours_part
    return None


def _get_mock_merchant_for_details(merchant_id: str) -> Optional[Merchant]:
    """
    Return mock Merchant object for fixture merchants when MOCK_PLACES is enabled.
    Creates a temporary Merchant object (not persisted to DB).
    """
    mock_merchants = {
        "mock_asadas_grill": Merchant(
            id="m_mock_asadas",
            external_id="mock_asadas_grill",
            name="Asadas Grill",
            category="Restaurant",
            primary_category="food",
            lat=30.2680,
            lng=-97.7435,
            address="123 Main St, Austin, TX",
            rating=4.5,
            price_level=2,
            photo_url=None,
        ),
        "mock_eggman_atx": Merchant(
            id="m_mock_eggman",
            external_id="mock_eggman_atx",
            name="Eggman ATX",
            category="Restaurant",
            primary_category="food",
            lat=30.2665,
            lng=-97.7425,
            address="456 Main St, Austin, TX",
            rating=4.7,
            price_level=2,
            photo_url=None,
        ),
        "mock_coffee_shop": Merchant(
            id="m_mock_coffee",
            external_id="mock_coffee_shop",
            name="Test Coffee Shop",
            category="Coffee",
            primary_category="coffee",
            lat=30.2675,
            lng=-97.7440,
            address="789 Main St, Austin, TX",
            rating=4.3,
            price_level=1,
            photo_url=None,
        ),
    }
    return mock_merchants.get(merchant_id)


def get_merchant_details(
    db: Session,
    merchant_id: str,
    session_id: Optional[str] = None
) -> MerchantDetailsResponse:
    """
    Get merchant details for a given merchant ID.
    
    Args:
        db: Database session
        merchant_id: Merchant ID (can be internal ID or Google Places external_id)
        session_id: Optional intent session ID for context (distance calculation)
    
    Returns:
        MerchantDetailsResponse with merchant info, moment, perk, wallet state, and actions
    """
    # Try to find merchant by ID or external_id
    merchant = db.query(Merchant).filter(
        (Merchant.id == merchant_id) | (Merchant.external_id == merchant_id)
    ).first()
    
    # MOCK_PLACES support: return mock data for fixture merchants if not in DB
    if not merchant and os.getenv('MOCK_PLACES', 'false').lower() == 'true':
        merchant = _get_mock_merchant_for_details(merchant_id)
    
    if not merchant:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    # Get active perk (first active perk)
    # For mock merchants, skip DB query
    perk = None
    if merchant.id and not merchant.id.startswith("m_mock_"):
        perk = db.query(MerchantPerk).filter(
            MerchantPerk.merchant_id == merchant.id,
            MerchantPerk.is_active == True
        ).first()
    
    # Default perk if none exists
    # Check for Asadas Grill special case
    merchant_name_lower = merchant.name.lower() if merchant.name else ""
    perk_options = None
    if not perk:
        if "asadas" in merchant_name_lower and "grill" in merchant_name_lower:
            perk_title = "Free Beverage Exclusive"
            perk_badge = "Exclusive"
            perk_description = "Get a free beverage with any meal during charging hours. Show your pass to redeem."
            perk_options = "Soda, Coffee, or Margarita"
        else:
            perk_title = "Happy Hour"
            perk_badge = "Happy Hour ⭐️"
            perk_description = "Show your pass to access Happy Hour."
    else:
        perk_title = perk.title
        perk_badge = "Happy Hour ⭐️"  # Default badge format
        perk_description = perk.description or f"Show your pass to access {perk.title}."
        # Add options for Asadas Grill
        if "asadas" in merchant_name_lower and "grill" in merchant_name_lower:
            perk_options = "Soda, Coffee, or Margarita"
    
    # Calculate distance if session provided
    distance_miles = 0.0
    moment_label = "Nearby"
    moment_copy = "Fits your charge window"
    
    if session_id:
        session = db.query(IntentSession).filter(IntentSession.id == session_id).first()
        if session:
            distance_miles = haversine_distance(
                session.lat, session.lng,
                merchant.lat, merchant.lng
            )
            walk_time = int(distance_miles * 20)  # Approximate walk time in minutes (3 mph)
            if distance_miles < 0.3:  # Less than 0.3 miles
                moment_label = f"{walk_time} min walk"
            else:
                moment_label = "On your way out"
            moment_copy = "Fits your charge window"
    
    # Format category - match Figma design (simple category, not combined)
    category = merchant.category or "Restaurant"
    # Don't transform category for Asadas Grill - it should just be "Restaurant"
    if "asadas" in merchant_name_lower and "grill" in merchant_name_lower:
        category = "Restaurant"
    elif merchant.primary_category:
        category_map = {
            "coffee": "Coffee • Bakery",
            "food": "Restaurant • Food",
            "other": "Shop • Services"
        }
        category = category_map.get(merchant.primary_category, category)
    
    # Calculate hours today and open_now from opening_hours
    hours_today = None
    open_now = None
    weekday_hours = None
    if merchant.opening_hours:
        hours_today = get_hours_today(merchant.opening_hours)
        open_now = merchant.opening_hours.get('open_now')
        weekday_hours = merchant.opening_hours.get('weekday_text')
    
    # Build merchant info
    merchant_info = MerchantInfo(
        id=merchant.id,
        name=merchant.name,
        category=category,
        photo_url=merchant.photo_url,
        photo_urls=merchant.photo_urls,
        address=merchant.address,
        rating=merchant.rating,
        user_rating_count=merchant.user_rating_count,
        price_level=merchant.price_level,
        description=merchant.description,
        hours_today=hours_today,
        open_now=open_now,
        weekday_hours=weekday_hours
    )
    
    # Build moment info
    moment_info = MomentInfo(
        label=moment_label,
        distance_miles=round(distance_miles, 1),
        moment_copy=moment_copy
    )
    
    # Build perk info
    perk_info = PerkInfo(
        title=perk_title,
        badge=perk_badge,
        description=perk_description,
        options=perk_options
    )
    
    # Build wallet info (check if wallet pass exists for this session+merchant)
    wallet_state = "INACTIVE"
    can_add = True
    if session_id:
        # Check if wallet pass already exists
        from app.models.wallet_pass import WalletPassActivation, WalletPassStateEnum
        from datetime import datetime
        existing_pass = db.query(WalletPassActivation).filter(
            WalletPassActivation.session_id == session_id,
            WalletPassActivation.merchant_id == merchant.id,
            WalletPassActivation.state == WalletPassStateEnum.ACTIVE,
            WalletPassActivation.expires_at > datetime.utcnow()
        ).first()
        if existing_pass:
            wallet_state = "ACTIVE"
            can_add = False
        else:
            wallet_state = "INACTIVE"
            can_add = True
    
    wallet_info = WalletInfo(
        can_add=can_add,
        state=wallet_state,
        active_copy="Active while charging" if wallet_state == "ACTIVE" else None
    )
    
    # Build actions info
    directions_url = None
    if merchant.lat and merchant.lng:
        directions_url = f"https://maps.google.com/?q={merchant.lat},{merchant.lng}"
    
    actions_info = ActionsInfo(
        add_to_wallet=True,
        get_directions_url=directions_url
    )
    
    return MerchantDetailsResponse(
        merchant=merchant_info,
        moment=moment_info,
        perk=perk_info,
        wallet=wallet_info,
        actions=actions_info
    )

