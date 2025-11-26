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


class JoinChargePartyResponse(BaseModel):
    session_id: str
    event_id: str
    status: str


class NearbyMerchantResponse(BaseModel):
    id: str
    name: str
    lat: float
    lng: float
    zone_slug: str
    address: Optional[str] = None
    phone: Optional[str] = None


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


@router.get("/merchants/nearby", response_model=List[NearbyMerchantResponse])
def get_nearby_merchants(
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    zone_slug: str = Query(..., description="Zone slug (e.g., domain_austin)"),
    radius_m: float = Query(5000, description="Radius in meters"),
    user: User = Depends(require_driver),
    db: Session = Depends(get_db)
):
    """
    Get nearby merchants in a zone.
    
    Zones are data-scoped (configured via Zone rows), not path-scoped.
    New zones/events don't require new endpoints.
    """
    # Query active merchants in the zone
    merchants = db.query(DomainMerchant).filter(
        DomainMerchant.zone_slug == zone_slug,
        DomainMerchant.status == "active"
    ).all()
    
    # Filter by distance
    nearby = []
    for merchant in merchants:
        distance = haversine_distance(lat, lng, merchant.lat, merchant.lng)
        if distance <= radius_m:
            address = merchant.addr_line1
            if merchant.city:
                address = f"{address}, {merchant.city}, {merchant.state}" if address else f"{merchant.city}, {merchant.state}"
            
            nearby.append(NearbyMerchantResponse(
                id=merchant.id,
                name=merchant.name,
                lat=merchant.lat,
                lng=merchant.lng,
                zone_slug=merchant.zone_slug,
                address=address,
                phone=merchant.public_phone
            ))
    
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

