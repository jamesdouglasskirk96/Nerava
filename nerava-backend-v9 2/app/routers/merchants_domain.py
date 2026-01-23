"""
Domain Charge Party MVP Merchant Router
Merchant-specific endpoints for registration, dashboard, and redemption
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from app.db import get_db
from app.models import User
from app.models.domain import DomainMerchant, NovaTransaction, MerchantFeeLedger
from app.models.while_you_charge import Merchant, MerchantFavorite
from app.services.auth_service import AuthService
from app.services.nova_service import NovaService
from app.services.merchant_share_card import generate_share_card
from app.dependencies_domain import require_merchant_admin, get_current_user
from app.routers.drivers_domain import haversine_distance
from datetime import date, datetime, timedelta
from calendar import monthrange
from app.models.exclusive_session import ExclusiveSession, ExclusiveSessionStatus

router = APIRouter(prefix="/v1/merchants", tags=["merchants-v1"])

# Domain center coordinates (Domain area, Austin)
DOMAIN_CENTER_LAT = 30.4021
DOMAIN_CENTER_LNG = -97.7266
DOMAIN_RADIUS_M = 1000  # 1km radius


# Request/Response Models
class MerchantRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    business_name: str
    google_place_id: Optional[str] = None
    addr_line1: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    lat: float
    lng: float
    public_phone: Optional[str] = None
    zone_slug: str = "domain_austin"
    invite_code: Optional[str] = None  # For future invite system


class MerchantDashboardResponse(BaseModel):
    merchant: dict
    transactions: List[dict]


class RedeemFromDriverRequest(BaseModel):
    driver_code: Optional[str] = None
    driver_user_id: Optional[int] = None
    driver_email: Optional[EmailStr] = None
    amount: int


class RedeemFromDriverResponse(BaseModel):
    transaction_id: str
    driver_balance: int
    merchant_balance: int
    amount: int


@router.post("/register")
def register_merchant(
    request: MerchantRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new merchant (creates user + merchant)"""
    # Validate zone exists and location is within zone bounds
    from app.models.domain import Zone
    zone = db.query(Zone).filter(Zone.slug == request.zone_slug).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid zone: {request.zone_slug}"
        )
    
    # Validate location is within zone radius
    distance = haversine_distance(
        zone.center_lat, zone.center_lng,
        request.lat, request.lng
    )
    if distance > zone.radius_m:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Location must be within {zone.radius_m}m of {zone.name} center"
        )
    
    # Create user with merchant_admin role
    try:
        user = AuthService.register_user(
            db=db,
            email=request.email,
            password=request.password,
            display_name=request.display_name or request.business_name,
            roles=["merchant_admin", "driver"]  # Merchants can also be drivers
        )
        
        # Create merchant
        merchant_id = str(uuid.uuid4())
        merchant = DomainMerchant(
            id=merchant_id,
            name=request.business_name,
            google_place_id=request.google_place_id,
            addr_line1=request.addr_line1,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            country=request.country,
            lat=request.lat,
            lng=request.lng,
            public_phone=request.public_phone,
            owner_user_id=user.id,
            status="active",  # Auto-activate for MVP
            zone_slug=request.zone_slug,
            nova_balance=0
        )
        db.add(merchant)
        db.commit()
        db.refresh(user)
        db.refresh(merchant)
        
        # Create session token
        token = AuthService.create_session_token(user)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "role_flags": user.role_flags
            },
            "merchant": {
                "id": merchant.id,
                "name": merchant.name,
                "nova_balance": merchant.nova_balance
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.get("/me", response_model=MerchantDashboardResponse)
def get_merchant_dashboard(
    user: User = Depends(require_merchant_admin),
    db: Session = Depends(get_db)
):
    """Get merchant dashboard data"""
    merchant = AuthService.get_user_merchant(db, user.id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for user"
        )
    
    # Get recent transactions
    transactions = NovaService.get_merchant_transactions(db, merchant.id, limit=10)
    
    return MerchantDashboardResponse(
        merchant={
            "id": merchant.id,
            "name": merchant.name,
            "nova_balance": merchant.nova_balance,
            "zone_slug": merchant.zone_slug,
            "status": merchant.status
        },
        transactions=[
            {
                "id": txn.id,
                "type": txn.type,
                "amount": txn.amount,
                "driver_user_id": txn.driver_user_id,
                "created_at": txn.created_at.isoformat(),
                "metadata": txn.transaction_meta
            }
            for txn in transactions
        ]
    )


@router.post("/redeem_from_driver", response_model=RedeemFromDriverResponse)
def redeem_from_driver(
    request: RedeemFromDriverRequest,
    user: User = Depends(require_merchant_admin),
    db: Session = Depends(get_db)
):
    """Merchant redeems Nova from a driver (by email or user_id)"""
    merchant = AuthService.get_user_merchant(db, user.id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    # Find driver by email or user_id
    driver_id = None
    if request.driver_user_id:
        driver_id = request.driver_user_id
    elif request.driver_email:
        driver = db.query(User).filter(User.email == request.driver_email).first()
        if not driver:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Driver not found with email: {request.driver_email}"
            )
        driver_id = driver.id
    elif request.driver_code:
        # For MVP, treat code as user_id if numeric, or email otherwise
        try:
            driver_id = int(request.driver_code)
        except ValueError:
            driver = db.query(User).filter(User.email == request.driver_code).first()
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Driver not found with code: {request.driver_code}"
                )
            driver_id = driver.id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide driver_user_id, driver_email, or driver_code"
        )
    
    # Perform redemption
    try:
        result = NovaService.redeem_from_driver(
            db=db,
            driver_id=driver_id,
            merchant_id=merchant.id,
            amount=request.amount
        )
        return RedeemFromDriverResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/transactions")
def get_merchant_transactions(
    limit: int = 50,
    user: User = Depends(require_merchant_admin),
    db: Session = Depends(get_db)
):
    """Get merchant transaction history"""
    merchant = AuthService.get_user_merchant(db, user.id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    transactions = NovaService.get_merchant_transactions(db, merchant.id, limit=limit)
    
    return [
        {
            "id": txn.id,
            "type": txn.type,
            "amount": txn.amount,
            "driver_user_id": txn.driver_user_id,
            "created_at": txn.created_at.isoformat(),
            "metadata": txn.metadata
        }
        for txn in transactions
    ]


@router.get("/favorites")
async def get_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's favorite merchants"""
    favorites = db.query(MerchantFavorite).filter(
        MerchantFavorite.user_id == current_user.id
    ).all()
    merchant_ids = [f.merchant_id for f in favorites]
    if not merchant_ids:
        return {"favorites": []}
    
    merchants = db.query(Merchant).filter(Merchant.id.in_(merchant_ids)).all()
    return {
        "favorites": [
            {
                "merchant_id": m.id,
                "name": m.name,
                "category": m.category,
                "photo_url": m.photo_url or getattr(m, 'primary_photo_url', None) or "",
            }
            for m in merchants
        ]
    }


@router.post("/{merchant_id}/favorite")
async def add_favorite(
    merchant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add merchant to favorites"""
    # Verify merchant exists
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")
    
    # Check if already favorited
    existing = db.query(MerchantFavorite).filter(
        MerchantFavorite.user_id == current_user.id,
        MerchantFavorite.merchant_id == merchant_id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Already favorited")
    
    fav = MerchantFavorite(user_id=current_user.id, merchant_id=merchant_id)
    db.add(fav)
    db.commit()
    return {"success": True}


@router.delete("/{merchant_id}/favorite")
async def remove_favorite(
    merchant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove merchant from favorites"""
    fav = db.query(MerchantFavorite).filter(
        MerchantFavorite.user_id == current_user.id,
        MerchantFavorite.merchant_id == merchant_id
    ).first()
    if fav:
        db.delete(fav)
        db.commit()
    return {"success": True}


@router.get("/{merchant_id}/share-card.png")
def get_merchant_share_card(
    merchant_id: str,
    range: str = Query("7d", description="Time range: 7d, 30d, etc."),
    db: Session = Depends(get_db)
):
    """
    Generate shareable PNG social card for merchant.
    
    Returns a 1200x630 PNG image with merchant stats.
    Works even when 0 redemptions (returns valid card).
    """
    # Parse range (e.g., "7d" -> 7 days)
    days = 7
    if range.endswith('d'):
        try:
            days = int(range[:-1])
        except ValueError:
            days = 7
    
    try:
        png_bytes = generate_share_card(db, merchant_id, days=days)
        
        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MERCHANT_NOT_FOUND",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "SHARE_CARD_GENERATION_FAILED",
                "message": "Failed to generate share card"
            }
        )


class BillingSummaryResponse(BaseModel):
    """Response for merchant billing summary"""
    period_start: str  # ISO date string
    period_end: str  # ISO date string
    nova_redeemed_cents: int
    fee_cents: int
    status: str


@router.get("/{merchant_id}/billing/summary", response_model=BillingSummaryResponse)
def get_billing_summary(
    merchant_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current month's billing summary for a merchant.
    
    Returns the current month's ledger row or defaults if not found.
    
    Args:
        merchant_id: Merchant ID
        db: Database session
        
    Returns:
        BillingSummaryResponse with period, nova_redeemed_cents, fee_cents, and status
    """
    # Verify merchant exists
    merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MERCHANT_NOT_FOUND",
                "message": f"Merchant {merchant_id} not found"
            }
        )
    
    # Determine current month period
    now = datetime.utcnow()
    period_start = date(now.year, now.month, 1)
    last_day = monthrange(now.year, now.month)[1]
    period_end = date(now.year, now.month, last_day)
    
    # Get ledger row for current month
    ledger = db.query(MerchantFeeLedger).filter(
        MerchantFeeLedger.merchant_id == merchant_id,
        MerchantFeeLedger.period_start == period_start
    ).first()
    
    if ledger:
        return BillingSummaryResponse(
            period_start=ledger.period_start.isoformat(),
            period_end=ledger.period_end.isoformat() if ledger.period_end else period_end.isoformat(),
            nova_redeemed_cents=ledger.nova_redeemed_cents,
            fee_cents=ledger.fee_cents,
            status=ledger.status
        )
    else:
        # Return defaults if no ledger row exists yet
        return BillingSummaryResponse(
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            nova_redeemed_cents=0,
            fee_cents=0,
            status="accruing"
        )


@router.get("/{merchant_id}/visits")
def get_merchant_visits(
    merchant_id: str,
    period: str = Query("week", description="Period: week, month, or all"),
    status: Optional[str] = Query(None, description="Filter by verification status: VERIFIED, PARTIAL, REJECTED"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get verified visits (billable events) for a merchant.
    This is the core billing proof endpoint.
    """
    # Verify merchant ownership
    merchant = AuthService.get_user_merchant(db, current_user.id)
    if not merchant or str(merchant.id) != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )
    
    # Calculate date range
    now = datetime.utcnow()
    if period == "week":
        start_date = now - timedelta(days=7)
    elif period == "month":
        start_date = now - timedelta(days=30)
    else:
        start_date = None
    
    # Query exclusive sessions as "visits"
    query = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == merchant_id
    )
    
    if start_date:
        query = query.filter(ExclusiveSession.activated_at >= start_date)
    
    if status:
        # Map to session status
        status_map = {
            "VERIFIED": [ExclusiveSessionStatus.COMPLETED],
            "PARTIAL": [ExclusiveSessionStatus.ACTIVE, ExclusiveSessionStatus.EXPIRED],
            "REJECTED": [ExclusiveSessionStatus.FORCE_CLOSED, ExclusiveSessionStatus.CANCELED]
        }
        query = query.filter(ExclusiveSession.status.in_(status_map.get(status, [])))
    
    query = query.order_by(ExclusiveSession.activated_at.desc())
    
    total = query.count()
    visits = query.offset(offset).limit(limit).all()
    
    # Calculate summary stats
    verified_query = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == merchant_id,
        ExclusiveSession.status == ExclusiveSessionStatus.COMPLETED
    )
    if start_date:
        verified_query = verified_query.filter(ExclusiveSession.activated_at >= start_date)
    verified_count = verified_query.count()
    
    # Helper function to map session status to verification status
    def map_session_to_verification(session_status: ExclusiveSessionStatus) -> str:
        mapping = {
            ExclusiveSessionStatus.COMPLETED: "VERIFIED",
            ExclusiveSessionStatus.ACTIVE: "PARTIAL",
            ExclusiveSessionStatus.EXPIRED: "PARTIAL",
            ExclusiveSessionStatus.FORCE_CLOSED: "REJECTED",
            ExclusiveSessionStatus.CANCELED: "REJECTED"
        }
        return mapping.get(session_status, "PARTIAL")
    
    # Helper function to calculate duration
    def calculate_duration(session: ExclusiveSession) -> Optional[int]:
        if session.completed_at and session.activated_at:
            delta = session.completed_at - session.activated_at
            return int(delta.total_seconds() / 60)
        return None
    
    # Helper function to anonymize driver ID
    def anonymize_driver_id(driver_id: int) -> str:
        hash_val = hash(str(driver_id)) % 10000
        return f"DRV-{hash_val:04d}"
    
    # Get exclusive titles and location names
    from app.models.while_you_charge import MerchantPerk, Charger
    import json
    
    visit_items = []
    for v in visits:
        # Get exclusive title if available
        exclusive_title = "General Visit"
        if v.merchant_id:
            # Try to find an exclusive/perk for this merchant
            perks = db.query(MerchantPerk).filter(MerchantPerk.merchant_id == v.merchant_id).limit(1).all()
            if perks:
                try:
                    metadata = json.loads(perks[0].description or "{}")
                    if metadata.get("is_exclusive"):
                        exclusive_title = perks[0].title
                except:
                    pass
        
        # Get charger/location name
        location_name = None
        if v.charger_id:
            charger = db.query(Charger).filter(Charger.id == v.charger_id).first()
            if charger:
                location_name = charger.name if hasattr(charger, 'name') else None
        
        visit_items.append({
            "id": str(v.id),
            "timestamp": v.activated_at.isoformat() if v.activated_at else None,
            "exclusive_id": None,  # Not stored in session currently
            "exclusive_title": exclusive_title,
            "driver_id_anonymized": anonymize_driver_id(v.driver_id),
            "verification_status": map_session_to_verification(v.status),
            "duration_minutes": calculate_duration(v),
            "charger_id": v.charger_id,
            "location_name": location_name
        })
    
    return {
        "visits": visit_items,
        "total": total,
        "verified_count": verified_count,
        "period": period,
        "limit": limit,
        "offset": offset
    }

