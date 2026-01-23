"""
Domain Charge Party MVP Merchant Router
Merchant-specific endpoints for registration, dashboard, and redemption
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from app.db import get_db
from app.models import User
from app.models.domain import DomainMerchant, NovaTransaction, MerchantFeeLedger
from app.models.while_you_charge import FavoriteMerchant, Merchant as WYCMerchant
from app.dependencies.driver import get_current_driver
from app.services.auth_service import AuthService
from app.services.nova_service import NovaService
from app.services.merchant_share_card import generate_share_card
from app.dependencies_domain import require_merchant_admin, get_current_user
from app.routers.drivers_domain import haversine_distance
from app.services.analytics import get_analytics_client
from fastapi import Request
from datetime import date, datetime
from calendar import monthrange

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


# IMPORTANT: Static routes must be defined BEFORE dynamic /{merchant_id} routes
@router.get("/favorites")
def list_favorites(
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """List user's favorite merchants"""
    favorites = db.query(FavoriteMerchant).filter(
        FavoriteMerchant.user_id == driver.id
    ).all()

    merchant_ids = [f.merchant_id for f in favorites]
    merchants = db.query(WYCMerchant).filter(WYCMerchant.id.in_(merchant_ids)).all() if merchant_ids else []

    return {
        "favorites": [
            {
                "merchant_id": m.id,
                "name": m.name,
                "category": m.category,
                "photo_url": m.primary_photo_url or m.photo_url,
            }
            for m in merchants
        ]
    }


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


# Exclusive Management Endpoints
# Response model must be defined before use
class ExclusiveResponse(BaseModel):
    id: str
    merchant_id: str
    title: str
    description: Optional[str]
    daily_cap: Optional[int]
    session_cap: Optional[int]
    eligibility: str
    is_active: bool
    created_at: str
    updated_at: str


@router.get("/{merchant_id}/exclusives", response_model=List[ExclusiveResponse])
def list_exclusives(
    merchant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant_admin)
):
    """
    List all exclusives for a merchant.
    """
    # Verify merchant belongs to user
    merchant = AuthService.get_user_merchant(db, current_user.id)
    if not merchant or str(merchant.id) != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )
    
    from app.models.while_you_charge import MerchantPerk
    import json
    
    # Query perks that are exclusives (check description for is_exclusive flag)
    perks = db.query(MerchantPerk).filter(
        MerchantPerk.merchant_id == merchant_id
    ).all()
    
    exclusives = []
    for perk in perks:
        try:
            metadata = json.loads(perk.description or "{}")
            if metadata.get("is_exclusive"):
                exclusives.append(ExclusiveResponse(
                    id=str(perk.id),
                    merchant_id=merchant_id,
                    title=perk.title,
                    description=metadata.get("description") or perk.description,
                    daily_cap=metadata.get("daily_cap"),
                    session_cap=metadata.get("session_cap"),
                    eligibility=metadata.get("eligibility", "charging_only"),
                    is_active=perk.is_active,
                    created_at=perk.created_at.isoformat(),
                    updated_at=perk.updated_at.isoformat()
                ))
        except:
            # Skip if not valid JSON or not an exclusive
            continue
    
    return exclusives


class CreateExclusiveRequest(BaseModel):
    title: str
    description: Optional[str] = None
    daily_cap: Optional[int] = None  # Max activations per day
    session_cap: Optional[int] = None  # Max concurrent sessions
    eligibility: Optional[str] = "charging_only"  # charging_only, pre_charging_routing, all


class UpdateExclusiveRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    daily_cap: Optional[int] = None
    session_cap: Optional[int] = None
    eligibility: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/{merchant_id}/exclusives", response_model=ExclusiveResponse)
def create_exclusive(
    merchant_id: str,
    request: CreateExclusiveRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant_admin)
):
    """
    Create an exclusive for a merchant.
    MVP: Uses MerchantPerk model with is_exclusive flag (to be added).
    """
    # Verify merchant belongs to user
    merchant = AuthService.get_user_merchant(db, current_user.id)
    if not merchant or str(merchant.id) != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )
    
    # For MVP, create a MerchantPerk with exclusive flag
    # TODO: Create dedicated Exclusive model in future
    from app.models.while_you_charge import MerchantPerk
    
    perk = MerchantPerk(
        merchant_id=merchant_id,
        title=request.title,
        description=request.description,
        nova_reward=0,  # Exclusives don't have Nova rewards
        is_active=True
    )
    db.add(perk)
    db.commit()
    db.refresh(perk)
    
    # Store exclusive metadata in perk description or create separate table
    # For MVP, we'll use description field to store JSON metadata
    import json
    metadata = {
        "daily_cap": request.daily_cap,
        "session_cap": request.session_cap,
        "eligibility": request.eligibility,
        "is_exclusive": True
    }
    perk.description = json.dumps(metadata)
    db.commit()
    
    # Analytics: Capture exclusive creation
    request_id = getattr(http_request.state, "request_id", None)
    analytics = get_analytics_client()
    analytics.capture(
        event="server.merchant.exclusive.create",
        distinct_id=current_user.public_id,
        request_id=request_id,
        user_id=current_user.public_id,
        merchant_id=merchant_id,
        ip=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
        properties={
            "exclusive_id": str(perk.id),
        }
    )
    
    return ExclusiveResponse(
        id=str(perk.id),
        merchant_id=merchant_id,
        title=perk.title,
        description=perk.description,
        daily_cap=request.daily_cap,
        session_cap=request.session_cap,
        eligibility=request.eligibility,
        is_active=perk.is_active,
        created_at=perk.created_at.isoformat(),
        updated_at=perk.updated_at.isoformat()
    )


@router.put("/{merchant_id}/exclusives/{exclusive_id}", response_model=ExclusiveResponse)
def update_exclusive(
    merchant_id: str,
    exclusive_id: str,
    request: UpdateExclusiveRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant_admin)
):
    """Update an exclusive."""
    # Verify merchant belongs to user
    merchant = AuthService.get_user_merchant(db, current_user.id)
    if not merchant or str(merchant.id) != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )
    
    from app.models.while_you_charge import MerchantPerk
    perk = db.query(MerchantPerk).filter(
        MerchantPerk.id == int(exclusive_id),
        MerchantPerk.merchant_id == merchant_id
    ).first()
    
    if not perk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exclusive not found"
        )
    
    # Update fields
    if request.title is not None:
        perk.title = request.title
    if request.description is not None:
        perk.description = request.description
    if request.is_active is not None:
        perk.is_active = request.is_active
    
    # Update metadata
    import json
    try:
        metadata = json.loads(perk.description or "{}")
    except:
        metadata = {}
    
    if request.daily_cap is not None:
        metadata["daily_cap"] = request.daily_cap
    if request.session_cap is not None:
        metadata["session_cap"] = request.session_cap
    if request.eligibility is not None:
        metadata["eligibility"] = request.eligibility
    
    perk.description = json.dumps(metadata)
    db.commit()
    db.refresh(perk)
    
    # Analytics: Capture exclusive update
    request_id = getattr(http_request.state, "request_id", None)
    analytics = get_analytics_client()
    analytics.capture(
        event="server.merchant.exclusive.update",
        distinct_id=current_user.public_id,
        request_id=request_id,
        user_id=current_user.public_id,
        merchant_id=merchant_id,
        ip=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
        properties={
            "exclusive_id": exclusive_id,
        }
    )
    
    return ExclusiveResponse(
        id=str(perk.id),
        merchant_id=merchant_id,
        title=perk.title,
        description=perk.description,
        daily_cap=metadata.get("daily_cap"),
        session_cap=metadata.get("session_cap"),
        eligibility=metadata.get("eligibility", "charging_only"),
        is_active=perk.is_active,
        created_at=perk.created_at.isoformat(),
        updated_at=perk.updated_at.isoformat()
    )


@router.post("/{merchant_id}/exclusives/{exclusive_id}/enable")
def toggle_exclusive(
    merchant_id: str,
    exclusive_id: str,
    http_request: Request,
    enabled: bool = Query(..., description="Enable or disable"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant_admin)
):
    """Enable or disable an exclusive."""
    # Verify merchant belongs to user
    merchant = AuthService.get_user_merchant(db, current_user.id)
    if not merchant or str(merchant.id) != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )
    
    from app.models.while_you_charge import MerchantPerk
    perk = db.query(MerchantPerk).filter(
        MerchantPerk.id == int(exclusive_id),
        MerchantPerk.merchant_id == merchant_id
    ).first()
    
    if not perk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exclusive not found"
        )
    
    perk.is_active = enabled
    db.commit()
    
    # Analytics: Capture exclusive toggle
    request_id = getattr(http_request.state, "request_id", None)
    analytics = get_analytics_client()
    analytics.capture(
        event="server.merchant.exclusive.toggle",
        distinct_id=current_user.public_id,
        request_id=request_id,
        user_id=current_user.public_id,
        merchant_id=merchant_id,
        ip=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
        properties={
            "exclusive_id": exclusive_id,
            "enabled": enabled,
        }
    )
    
    # HubSpot: Merchant exclusive enable is not a standard lifecycle event
    # Per design, only driver lifecycle events are tracked
    # Merchant events can be added later if needed
    
    return {"ok": True, "is_active": enabled}


@router.put("/{merchant_id}/brand-image")
def update_brand_image(
    merchant_id: str,
    http_request: Request,
    brand_image_url: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant_admin)
):
    """
    Update merchant brand image URL override.
    """
    # Verify merchant belongs to user
    merchant = AuthService.get_user_merchant(db, current_user.id)
    if not merchant or str(merchant.id) != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )
    
    from app.models.while_you_charge import Merchant
    merchant_model = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    merchant_model.brand_image_url = brand_image_url
    db.commit()
    
    # Analytics: Capture brand image update
    request_id = getattr(http_request.state, "request_id", None)
    analytics = get_analytics_client()
    analytics.capture(
        event="server.merchant.brand_image.set",
        distinct_id=current_user.public_id,
        request_id=request_id,
        user_id=current_user.public_id,
        merchant_id=merchant_id,
        ip=http_request.client.host if http_request.client else None,
        user_agent=http_request.headers.get("user-agent"),
        properties={
            "image_url": brand_image_url,
        }
    )
    
    return {"ok": True, "brand_image_url": brand_image_url}


@router.get("/{merchant_id}/analytics")
def get_merchant_analytics(
    merchant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant_admin)
):
    """
    Get merchant analytics (MVP: activations, completes, unique drivers).
    """
    # Verify merchant belongs to user
    merchant = AuthService.get_user_merchant(db, current_user.id)
    if not merchant or str(merchant.id) != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )
    
    from app.models.exclusive_session import ExclusiveSession, ExclusiveSessionStatus
    
    # Count activations (all exclusive sessions for this merchant)
    activations = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == merchant_id
    ).count()
    
    # Count completes
    completes = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == merchant_id,
        ExclusiveSession.status == ExclusiveSessionStatus.COMPLETED
    ).count()
    
    # Count unique drivers
    unique_drivers = db.query(ExclusiveSession.driver_id).filter(
        ExclusiveSession.merchant_id == merchant_id
    ).distinct().count()
    
    return {
        "merchant_id": merchant_id,
        "activations": activations,
        "completes": completes,
        "unique_drivers": unique_drivers,
        "completion_rate": round(completes / activations * 100, 2) if activations > 0 else 0
    }


# Favorites Endpoints
@router.post("/{merchant_id}/favorite")
def add_favorite(
    merchant_id: str,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Add a merchant to favorites (idempotent)"""
    # Verify merchant exists
    merchant = db.query(WYCMerchant).filter(WYCMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    # Check if already favorited
    favorite = db.query(FavoriteMerchant).filter(
        FavoriteMerchant.user_id == driver.id,
        FavoriteMerchant.merchant_id == merchant_id
    ).first()
    
    if favorite:
        # Already favorited, return success (idempotent)
        return {"ok": True, "is_favorite": True}
    
    # Create favorite
    favorite = FavoriteMerchant(
        user_id=driver.id,
        merchant_id=merchant_id
    )
    db.add(favorite)
    db.commit()
    
    return {"ok": True, "is_favorite": True}


@router.delete("/{merchant_id}/favorite")
def remove_favorite(
    merchant_id: str,
    driver: User = Depends(get_current_driver),
    db: Session = Depends(get_db)
):
    """Remove a merchant from favorites"""
    favorite = db.query(FavoriteMerchant).filter(
        FavoriteMerchant.user_id == driver.id,
        FavoriteMerchant.merchant_id == merchant_id
    ).first()
    
    if favorite:
        db.delete(favorite)
        db.commit()
    
    return {"ok": True, "is_favorite": False}


# Share Endpoint
@router.get("/{merchant_id}/share-link")
def get_share_link(
    merchant_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get shareable link for a merchant with optional referral param"""
    # Verify merchant exists
    merchant = db.query(WYCMerchant).filter(WYCMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    # Build share URL
    from app.core.config import settings
    from app.dependencies.driver import get_current_driver_optional
    from app.dependencies.domain import oauth2_scheme
    base_url = getattr(settings, 'FRONTEND_URL', 'https://app.nerava.network')
    url = f"{base_url}/merchant/{merchant_id}"
    
    # Try to get authenticated user (optional)
    try:
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
        if not token:
            token = request.cookies.get("access_token")
        
        if token:
            driver = get_current_driver_optional(request, token, db)
            if driver:
                url += f"?ref={driver.public_id}"
    except:
        # If auth fails, continue without ref param
        pass
    
    return {
        "url": url,
        "title": f"Check out {merchant.name}",
        "description": merchant.description or f"Visit {merchant.name} while you charge"
    }

