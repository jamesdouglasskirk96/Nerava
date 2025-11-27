"""
Domain Charge Party MVP Driver Router
Driver-specific endpoints for charging sessions and Nova operations
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import uuid
import math

from app.db import get_db
from app.models import User
from app.models_domain import DomainMerchant, DomainChargingSession
from app.services.nova_service import NovaService
from app.dependencies_domain import require_driver, get_current_user
from app.services.auth_service import AuthService

router = APIRouter(prefix="/v1/drivers", tags=["drivers"])


# Request/Response Models
class JoinChargePartyRequest(BaseModel):
    charger_id: Optional[str] = None  # event_slug comes from path parameter
    merchant_id: Optional[str] = None  # Optional merchant for the session
    user_lat: Optional[float] = None  # Optional user location for verify_dwell initialization
    user_lng: Optional[float] = None


class JoinChargePartyResponse(BaseModel):
    session_id: str
    event_id: str
    status: str


class NearbyMerchantResponse(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    zone_slug: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    # Additional fields for frontend compatibility
    merchant_id: Optional[str] = None
    nova_reward: Optional[int] = None
    walk_time_s: Optional[int] = None
    walk_time_seconds: Optional[int] = None
    distance_m: Optional[int] = None
    logo_url: Optional[str] = None
    category: Optional[str] = None


class RedeemNovaRequest(BaseModel):
    merchant_id: str
    amount: int
    session_id: Optional[str] = None


class RedeemNovaResponse(BaseModel):
    transaction_id: str
    driver_balance: int
    merchant_balance: int
    amount: int


@router.post("/charge_events/{event_slug}/join", response_model=JoinChargePartyResponse)
def join_charge_party(
    event_slug: str,
    request: JoinChargePartyRequest,
    user: User = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """
    Join a charge party event and create a charging session.
    
    New events are configured via EnergyEvent rows (event_slug, zone_slug),
    not by adding new endpoints. This endpoint works for any active event.
    """
    from app.models_domain import EnergyEvent
    
    # Look up event by slug
    event = db.query(EnergyEvent).filter(
        EnergyEvent.slug == event_slug,
        EnergyEvent.status == "active"
    ).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_slug}' not found or not active"
        )
    
    # Create charging session with event_id
    session_id = str(uuid.uuid4())
    session = DomainChargingSession(
        id=session_id,
        driver_user_id=user.id,
        charger_provider="tesla" if request.charger_id else "manual",
        start_time=datetime.utcnow(),
        event_id=event.id,
        verified=False
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Initialize old sessions table entry for verify_dwell bridge
    # TODO: Migrate verify_dwell to work directly with DomainChargingSession
    from app.services.session_service import SessionService
    SessionService.initialize_verify_dwell_session(
        db=db,
        session_id=session_id,
        driver_user_id=user.id,
        charger_id=request.charger_id,
        merchant_id=request.merchant_id,
        user_lat=request.user_lat,
        user_lng=request.user_lng
    )
    
    return JoinChargePartyResponse(
        session_id=session_id,
        event_id=event_slug,
        status="started"
    )


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


@router.get("/merchants/nearby")
async def get_nearby_merchants(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    zone_slug: str = Query(..., description="Zone slug (e.g., domain_austin)"),
    radius_m: float = Query(5000, description="Radius in meters"),
    user: User = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """
    Get nearby merchants in a zone.
    
    Bridge to while_you_charge service to get full merchant data with perks, logos, walk times.
    Returns the same shape as the pilot while_you_charge endpoint for compatibility.
    
    Zones are data-scoped (configured via Zone rows), not path-scoped.
    New zones/events don't require new endpoints.
    """
    # For now, bridge to the Domain hub view which has all the merchant data we need
    # TODO: Eventually refactor to query DomainMerchant + enrich with perks/logo/walk_time
    if zone_slug == "domain_austin":
        from app.services.while_you_charge import get_domain_hub_view_async, build_recommended_merchants_from_chargers
        from app.utils.pwa_responses import shape_charger, shape_merchant
        
        # Get Domain hub view with chargers and merchants
        hub_view = await get_domain_hub_view_async(db)
        
        # Get shaped chargers with merchants
        shaped_chargers = []
        for charger in hub_view.get("chargers", []):
            shaped = shape_charger(
                charger,
                user_lat=lat,
                user_lng=lng
            )
            # Attach merchants if present
            if "merchants" in charger:
                shaped_merchants = []
                for merchant in charger["merchants"]:
                    # Convert walk_minutes to walk_time_s if needed
                    if "walk_minutes" in merchant and "walk_time_s" not in merchant:
                        merchant["walk_time_s"] = merchant["walk_minutes"] * 60
                    shaped_m = shape_merchant(
                        merchant,
                        user_lat=lat,
                        user_lng=lng
                    )
                    # Ensure walk_time_seconds for aggregation
                    if "walk_time_s" in shaped_m:
                        shaped_m["walk_time_seconds"] = shaped_m["walk_time_s"]
                    elif "walk_minutes" in merchant:
                        shaped_m["walk_time_seconds"] = int(merchant["walk_minutes"] * 60)
                    # Ensure merchant_id for aggregation
                    if "id" in shaped_m and "merchant_id" not in shaped_m:
                        shaped_m["merchant_id"] = shaped_m["id"]
                    shaped_merchants.append(shaped_m)
                shaped["merchants"] = shaped_merchants
            shaped_chargers.append(shaped)
        
        # Build recommended merchants from chargers (same logic as pilot endpoint)
        recommended_merchants = build_recommended_merchants_from_chargers(shaped_chargers, limit=20)
        
        # Filter by distance if user location provided
        if lat and lng:
            from app.services.verify_dwell import haversine_m
            filtered = []
            for merchant in recommended_merchants:
                merchant_lat = merchant.get("lat")
                merchant_lng = merchant.get("lng")
                if merchant_lat and merchant_lng:
                    distance = haversine_m(lat, lng, merchant_lat, merchant_lng)
                    if distance <= radius_m:
                        merchant["distance_m"] = int(round(distance))
                        filtered.append(merchant)
            return filtered
        
        return recommended_merchants
    else:
        # For other zones, fall back to DomainMerchant query
        # TODO: Enrich with perks/logo/walk_time data
        merchants = db.query(DomainMerchant).filter(
            DomainMerchant.zone_slug == zone_slug,
            DomainMerchant.status == "active"
        ).all()
        
        nearby = []
        for merchant in merchants:
            distance = haversine_distance(lat, lng, merchant.lat, merchant.lng)
            if distance <= radius_m:
                address = merchant.addr_line1
                if merchant.city:
                    address = f"{address}, {merchant.city}, {merchant.state}" if address else f"{merchant.city}, {merchant.state}"
                
                nearby.append({
                    "id": merchant.id,
                    "merchant_id": merchant.id,
                    "name": merchant.name,
                    "lat": merchant.lat,
                    "lng": merchant.lng,
                    "zone_slug": merchant.zone_slug,
                    "address": address,
                    "phone": merchant.public_phone,
                    "nova_reward": 10,  # Default
                    "walk_time_s": 0,
                    "walk_time_seconds": 0,
                    "distance_m": int(round(distance))
                })
        
        return nearby


@router.post("/nova/redeem", response_model=RedeemNovaResponse)
def redeem_nova(
    request: RedeemNovaRequest,
    user: User = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """Redeem Nova from driver to merchant"""
    try:
        result = NovaService.redeem_from_driver(
            db=db,
            driver_id=user.id,
            merchant_id=request.merchant_id,
            amount=request.amount,
            session_id=request.session_id
        )
        return RedeemNovaResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Redemption failed: {str(e)}"
        )


@router.get("/me/wallet")
def get_driver_wallet(
    user: User = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """Get driver wallet balance"""
    wallet = NovaService.get_driver_wallet(db, user.id)
    return {
        "nova_balance": wallet.nova_balance,
        "energy_reputation_score": wallet.energy_reputation_score
    }


# Session ping/cancel endpoints
class SessionPingRequest(BaseModel):
    lat: float
    lng: float


class SessionPingResponse(BaseModel):
    verified: bool
    reward_earned: bool
    verified_at_charger: bool
    ready_to_claim: bool
    nova_awarded: int = 0
    wallet_balance_nova: int = 0
    distance_to_charger_m: int = 0
    dwell_seconds: int = 0
    needed_seconds: Optional[int] = None
    charger_radius_m: Optional[int] = None
    distance_to_merchant_m: Optional[int] = None
    within_merchant_radius: Optional[bool] = None
    verification_score: Optional[int] = None


@router.post("/sessions/{session_id}/ping", response_model=SessionPingResponse)
def ping_session_v1(
    session_id: str,
    payload: SessionPingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_driver),
):
    """
    Ping a session to update location and verification status.
    
    Canonical v1 endpoint - replaces /v1/pilot/verify_ping
    """
    from app.services.session_service import SessionService
    
    result = SessionService.ping_session(
        db=db,
        session_id=session_id,
        driver_user_id=current_user.id,
        lat=payload.lat,
        lng=payload.lng,
        accuracy_m=50.0  # Default accuracy
    )
    
    return SessionPingResponse(**result)


@router.post("/sessions/{session_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
def cancel_session_v1(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_driver),
):
    """
    Cancel a charging session.
    
    Canonical v1 endpoint - replaces /v1/pilot/session/cancel
    """
    from app.services.session_service import SessionService
    
    SessionService.cancel_session(
        db=db,
        session_id=session_id,
        driver_user_id=current_user.id
    )
    
    return None  # 204 No Content

