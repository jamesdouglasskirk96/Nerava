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
    
    # Get recent transactions (wrapped — nova_transactions may have schema drift)
    transactions = []
    try:
        transactions = NovaService.get_merchant_transactions(db, merchant.id, limit=10)
    except Exception:
        pass

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


@router.get("/me/insights")
def get_merchant_insights(
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    user: User = Depends(require_merchant_admin),
    db: Session = Depends(get_db),
):
    """Merchant insights — nearby charging sessions, dwell time, peak hours."""
    merchant = AuthService.get_user_merchant(db, user.id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found for user")

    from app.models.session_event import SessionEvent
    from datetime import timedelta
    from sqlalchemy import func

    days = 30
    if period.endswith("d"):
        try:
            days = int(period[:-1])
        except ValueError:
            days = 30

    since = datetime.utcnow() - timedelta(days=days)

    # Count nearby sessions (sessions at chargers linked to this merchant)
    # If no charger links, fall back to 0
    from app.models.while_you_charge import ChargerMerchant
    wyc = db.query(WYCMerchant).filter(WYCMerchant.place_id == merchant.google_place_id).first() if merchant.google_place_id else None
    charger_ids = []
    if wyc:
        links = db.query(ChargerMerchant.charger_id).filter(ChargerMerchant.merchant_id == wyc.id).all()
        charger_ids = [l[0] for l in links]

    ev_sessions = 0
    unique_drivers = 0
    avg_duration = None
    avg_kwh = None
    peak_hours = []

    if charger_ids:
        base = db.query(SessionEvent).filter(
            SessionEvent.charger_id.in_(charger_ids),
            SessionEvent.session_start >= since,
        )
        ev_sessions = base.count()
        unique_drivers = base.with_entities(SessionEvent.driver_user_id).distinct().count()

        dur = base.with_entities(func.avg(SessionEvent.duration_seconds)).scalar()
        if dur:
            avg_duration = round(dur / 60, 1)

        kwh = base.with_entities(func.avg(SessionEvent.kwh_added)).scalar()
        if kwh:
            avg_kwh = round(float(kwh), 1)

        # Peak hours
        hour_counts = (
            base.with_entities(
                func.extract("hour", SessionEvent.session_start).label("hr"),
                func.count().label("cnt"),
            )
            .group_by("hr")
            .order_by("hr")
            .all()
        )
        peak_hours = [{"hour": int(h), "sessions": c} for h, c in hour_counts]

    return {
        "period": period,
        "ev_sessions_nearby": ev_sessions,
        "unique_drivers": unique_drivers,
        "avg_duration_minutes": avg_duration,
        "avg_kwh": avg_kwh,
        "peak_hours": peak_hours,
        "dwell_distribution": None,
        "walk_traffic": None,
    }


@router.put("/me/profile")
def update_merchant_profile(
    request: dict,
    user: User = Depends(require_merchant_admin),
    db: Session = Depends(get_db),
):
    """
    Update merchant profile fields.
    Accepts: name, description, photo_url, website, hours_text, perk_label, custom_perk_cents.
    """
    merchant = AuthService.get_user_merchant(db, user.id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found for user",
        )

    allowed_fields = {"name", "description", "photo_url", "website", "hours_text", "perk_label", "custom_perk_cents"}
    updated = []
    for field in allowed_fields:
        if field in request:
            setattr(merchant, field, request[field])
            updated.append(field)

    if updated:
        from datetime import datetime
        merchant.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(merchant)

    return {
        "ok": True,
        "updated_fields": updated,
        "merchant": {
            "id": merchant.id,
            "name": merchant.name,
            "description": merchant.description,
            "photo_url": merchant.photo_url,
            "website": merchant.website,
            "hours_text": merchant.hours_text,
            "perk_label": merchant.perk_label,
            "custom_perk_cents": merchant.custom_perk_cents,
        },
    }


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


def _find_all_charger_merchant_links(db: Session, merchant: DomainMerchant):
    """
    Find ALL ChargerMerchant links for a DomainMerchant using the same
    place_id + name matching as list_exclusives. Returns a flat list.
    """
    from app.models.while_you_charge import ChargerMerchant
    from sqlalchemy import func as sqlfunc

    wyc_ids = set()
    if merchant.google_place_id:
        wyc_by_place = db.query(WYCMerchant).filter(
            WYCMerchant.place_id == merchant.google_place_id
        ).all()
        for w in wyc_by_place:
            wyc_ids.add(w.id)

    merchant_name = merchant.name or ""
    if not merchant_name and merchant.google_place_id:
        wyc = db.query(WYCMerchant).filter(
            WYCMerchant.place_id == merchant.google_place_id
        ).first()
        if wyc:
            merchant_name = wyc.name or ""

    if merchant_name:
        wyc_by_name = db.query(WYCMerchant).filter(
            sqlfunc.lower(WYCMerchant.name) == merchant_name.lower()
        ).all()
        for w in wyc_by_name:
            wyc_ids.add(w.id)

    if not wyc_ids:
        return []

    return db.query(ChargerMerchant).filter(
        ChargerMerchant.merchant_id.in_(list(wyc_ids)),
    ).all()


def _sync_exclusive_to_driver_app(db: Session, merchant: DomainMerchant, title: str, description: str = "", is_active: bool = True):
    """
    Sync an exclusive offer to the driver-facing tables so it shows in the driver app.
    Updates: DomainMerchant perk_label, WYC Merchant perk_label, ChargerMerchant exclusive fields.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Update DomainMerchant perk_label
    merchant.perk_label = title if is_active else None
    db.flush()

    # Update ALL matching WYC Merchants (by place_id and by name — may be different records)
    from app.models.while_you_charge import ChargerMerchant
    wyc_merchants = []
    if merchant.google_place_id:
        wyc_by_place = db.query(WYCMerchant).filter(WYCMerchant.place_id == merchant.google_place_id).first()
        if wyc_by_place:
            wyc_merchants.append(wyc_by_place)
    if merchant.name:
        from sqlalchemy import func as sqlfunc
        wyc_by_name_all = db.query(WYCMerchant).filter(
            sqlfunc.lower(WYCMerchant.name) == merchant.name.lower()
        ).all()
        existing_ids = {w.id for w in wyc_merchants}
        for w in wyc_by_name_all:
            if w.id not in existing_ids:
                wyc_merchants.append(w)

    for wyc_merchant in wyc_merchants:
        wyc_merchant.perk_label = title if is_active else None
        db.flush()
        logger.info(f"Synced exclusive to WYC merchant {wyc_merchant.id}: {title}")

        charger_links = db.query(ChargerMerchant).filter(
            ChargerMerchant.merchant_id == wyc_merchant.id
        ).all()
        for link in charger_links:
            link.exclusive_title = title if is_active else None
            link.exclusive_description = description if is_active else None
        if charger_links:
            db.flush()
            logger.info(f"Synced exclusive to {len(charger_links)} charger-merchant links for WYC {wyc_merchant.id}")


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
    merchant = AuthService.get_user_merchant(db, current_user.id, merchant_id=merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )

    from app.models.while_you_charge import ChargerMerchant
    import logging as _log
    _logger = _log.getLogger(__name__)

    # Find all ChargerMerchant links via the shared helper (place_id + name matching)
    all_cm_links = _find_all_charger_merchant_links(db, merchant)
    charger_links = [l for l in all_cm_links if l.exclusive_title]
    _logger.info(f"list_exclusives: merchant={merchant.name!r}, place_id={merchant.google_place_id!r}, total_links={len(all_cm_links)}, with_title={len(charger_links)}")

    # Deduplicate by title — multiple charger links may share the same exclusive offer
    exclusives = []
    now_str = datetime.utcnow().isoformat()
    seen_titles = set()
    for link in charger_links:
        title = link.exclusive_title or ""
        if title.lower() in seen_titles:
            continue
        seen_titles.add(title.lower())
        exclusives.append(ExclusiveResponse(
            id=f"cm_{link.id}",
            merchant_id=merchant_id,
            title=title,
            description=link.exclusive_description or "",
            daily_cap=None,
            session_cap=None,
            eligibility="charging_only",
            is_active=True,
            created_at=now_str,
            updated_at=now_str,
        ))

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
    merchant = AuthService.get_user_merchant(db, current_user.id, merchant_id=merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )
    
    # Set exclusive_title on ALL ChargerMerchant links for this merchant.
    # This is the same data the driver app reads — no FK issues.
    all_links = _find_all_charger_merchant_links(db, merchant)
    if not all_links:
        raise HTTPException(
            status_code=400,
            detail="No charger links found for this merchant. A charger must be nearby to create an exclusive."
        )
    for cm_link in all_links:
        cm_link.exclusive_title = request.title
        cm_link.exclusive_description = request.description or ""
    # Update WYC merchant perk_labels
    wyc_ids = {cm_link.merchant_id for cm_link in all_links}
    for wyc_id in wyc_ids:
        wyc = db.query(WYCMerchant).filter(WYCMerchant.id == wyc_id).first()
        if wyc:
            wyc.perk_label = request.title
    merchant.perk_label = request.title
    db.commit()

    # Use first link's ID for the response
    first_link = all_links[0]

    # Analytics
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
            "exclusive_id": f"cm_{first_link.id}",
        }
    )

    now_str = datetime.utcnow().isoformat()
    return ExclusiveResponse(
        id=f"cm_{first_link.id}",
        merchant_id=merchant_id,
        title=request.title,
        description=request.description or "",
        daily_cap=request.daily_cap,
        session_cap=request.session_cap,
        eligibility=request.eligibility,
        is_active=True,
        created_at=now_str,
        updated_at=now_str,
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
    merchant = AuthService.get_user_merchant(db, current_user.id, merchant_id=merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )

    # Handle charger_merchant-based exclusives (cm_ prefix)
    if exclusive_id.startswith("cm_"):
        from app.models.while_you_charge import ChargerMerchant
        import logging as _logging
        _logger = _logging.getLogger(__name__)
        cm_pk = exclusive_id[3:]  # strip "cm_" prefix to get integer PK
        try:
            link = db.query(ChargerMerchant).filter(
                ChargerMerchant.id == int(cm_pk),
            ).first()
        except (ValueError, TypeError):
            link = None
        if not link:
            raise HTTPException(status_code=404, detail="Exclusive not found")
        new_title = request.title if request.title is not None else link.exclusive_title
        new_desc = request.description if request.description is not None else (link.exclusive_description or "")
        is_active = True
        if request.is_active is not None and not request.is_active:
            is_active = False
        # Update ALL charger-merchant links across ALL matching WYC merchants
        all_links = _find_all_charger_merchant_links(db, merchant)
        for cm_link in all_links:
            cm_link.exclusive_title = new_title if is_active else None
            cm_link.exclusive_description = new_desc if is_active else None
        # Update ALL WYC merchants' perk_labels
        wyc_ids = {cm_link.merchant_id for cm_link in all_links}
        for wyc_id in wyc_ids:
            wyc = db.query(WYCMerchant).filter(WYCMerchant.id == wyc_id).first()
            if wyc:
                wyc.perk_label = new_title if is_active else None
        merchant.perk_label = new_title if is_active else None
        db.commit()
        _logger.info(f"Updated {len(all_links)} charger-merchant links across {len(wyc_ids)} WYC merchants: title={new_title!r}, active={is_active}")
        now_str = datetime.utcnow().isoformat()
        return ExclusiveResponse(
            id=exclusive_id,
            merchant_id=merchant_id,
            title=new_title or "",
            description=new_desc,
            daily_cap=None, session_cap=None,
            eligibility="charging_only", is_active=is_active,
            created_at=now_str, updated_at=now_str,
        )

    from app.models.while_you_charge import MerchantPerk
    perk = db.query(MerchantPerk).filter(
        MerchantPerk.id == int(exclusive_id),
        MerchantPerk.merchant_id == merchant_id
    ).first()

    if not perk:
        raise HTTPException(status_code=404, detail="Exclusive not found")

    if request.title is not None:
        perk.title = request.title
    if request.is_active is not None:
        perk.is_active = request.is_active

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
    if request.description is not None:
        metadata["description"] = request.description

    perk.description = json.dumps(metadata)

    final_title = request.title if request.title is not None else perk.title
    final_active = request.is_active if request.is_active is not None else perk.is_active
    _sync_exclusive_to_driver_app(db, merchant, final_title, request.description or "", final_active)
    db.commit()
    db.refresh(perk)

    return ExclusiveResponse(
        id=str(perk.id),
        merchant_id=merchant_id,
        title=perk.title,
        description=metadata.get("description", ""),
        daily_cap=metadata.get("daily_cap"),
        session_cap=metadata.get("session_cap"),
        eligibility=metadata.get("eligibility", "charging_only"),
        is_active=perk.is_active,
        created_at=perk.created_at.isoformat(),
        updated_at=perk.updated_at.isoformat()
    )


@router.get("/{merchant_id}/visits")
def get_merchant_visits_portal(
    merchant_id: str,
    period: str = Query("week", description="week, month, or all"),
    status_filter: str = Query(None, alias="status", description="VERIFIED, PARTIAL, or REJECTED"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_merchant_admin),
):
    """
    List visits for a merchant (merchant portal view).
    Queries ExclusiveSessions as a proxy for visits.
    """
    merchant = AuthService.get_user_merchant(db, current_user.id, merchant_id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=403, detail="Merchant not found or access denied")

    from app.models.exclusive_session import ExclusiveSession, ExclusiveSessionStatus
    from datetime import timedelta

    query = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == merchant_id
    )

    # Period filter
    now = datetime.utcnow()
    if period == "week":
        query = query.filter(ExclusiveSession.created_at >= now - timedelta(days=7))
    elif period == "month":
        query = query.filter(ExclusiveSession.created_at >= now - timedelta(days=30))

    # Status filter
    if status_filter == "VERIFIED":
        query = query.filter(ExclusiveSession.status == ExclusiveSessionStatus.COMPLETED)
    elif status_filter == "REJECTED":
        query = query.filter(ExclusiveSession.status == ExclusiveSessionStatus.EXPIRED)

    total = query.count()
    verified_count = query.filter(
        ExclusiveSession.status == ExclusiveSessionStatus.COMPLETED
    ).count()

    sessions = query.order_by(ExclusiveSession.created_at.desc()).offset(offset).limit(limit).all()

    visits = []
    for s in sessions:
        v_status = "VERIFIED" if s.status == ExclusiveSessionStatus.COMPLETED else (
            "REJECTED" if s.status == ExclusiveSessionStatus.EXPIRED else "PARTIAL"
        )
        visits.append({
            "id": str(s.id),
            "timestamp": s.created_at.isoformat() if s.created_at else now.isoformat(),
            "exclusive_id": s.exclusive_id,
            "exclusive_title": "",
            "driver_id_anonymized": f"driver_{s.driver_id}" if s.driver_id else "unknown",
            "verification_status": v_status,
            "duration_minutes": None,
            "charger_id": s.charger_id,
            "location_name": None,
        })

    return {
        "visits": visits,
        "total": total,
        "verified_count": verified_count,
        "period": period,
        "limit": limit,
        "offset": offset,
    }


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
    merchant = AuthService.get_user_merchant(db, current_user.id, merchant_id=merchant_id)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Merchant not found or access denied"
        )
    
    # Handle charger_merchant-based exclusives (cm_ prefix)
    if exclusive_id.startswith("cm_"):
        from app.models.while_you_charge import ChargerMerchant
        import logging as _logging
        _logger = _logging.getLogger(__name__)
        cm_pk = exclusive_id[3:]
        try:
            link = db.query(ChargerMerchant).filter(
                ChargerMerchant.id == int(cm_pk),
            ).first()
        except (ValueError, TypeError):
            link = None
        if not link:
            raise HTTPException(status_code=404, detail="Exclusive not found")
        title = link.exclusive_title or "Exclusive Offer"
        # Update ALL charger-merchant links across ALL matching WYC merchants
        all_links = _find_all_charger_merchant_links(db, merchant)
        for cm_link in all_links:
            cm_link.exclusive_title = title if enabled else None
            cm_link.exclusive_description = None if not enabled else cm_link.exclusive_description
        wyc_ids = {cm_link.merchant_id for cm_link in all_links}
        for wyc_id in wyc_ids:
            wyc = db.query(WYCMerchant).filter(WYCMerchant.id == wyc_id).first()
            if wyc:
                wyc.perk_label = title if enabled else None
        merchant.perk_label = title if enabled else None
        db.commit()
        _logger.info(f"Toggled {len(all_links)} charger-merchant links across {len(wyc_ids)} WYC merchants: enabled={enabled}")
        return {"ok": True, "is_active": enabled}

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
    # Sync to driver-facing tables
    _sync_exclusive_to_driver_app(db, merchant, perk.title, "", enabled)
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
    merchant = AuthService.get_user_merchant(db, current_user.id, merchant_id=merchant_id)
    if not merchant:
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
    merchant = AuthService.get_user_merchant(db, current_user.id, merchant_id=merchant_id)
    if not merchant:
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

