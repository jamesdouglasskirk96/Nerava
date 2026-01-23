"""
Domain Charge Party MVP Admin Router
Admin endpoints for overview, merchant management, and manual Nova grants
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Literal

from app.db import get_db
from app.models import User
from app.models_domain import (
    DriverWallet,
    DomainMerchant,
    NovaTransaction,
    StripePayment
)
from app.models_extra import CreditLedger
from app.services.nova_service import NovaService
from app.services.stripe_service import StripeService
from app.services.audit import log_admin_action, log_wallet_mutation
from app.dependencies_domain import require_admin, get_current_user
from app.routers.drivers_wallet import _balance, _add_ledger
from sqlalchemy import text, or_, String as sa_String
from sqlalchemy.orm import Session
from fastapi import Path
from typing import List
from app.utils.log import get_logger
from collections import defaultdict
from datetime import datetime

router = APIRouter(prefix="/v1/admin", tags=["admin-v1"])

# Simple in-memory rate limiter (per merchant per minute)
_portal_link_timestamps: dict = defaultdict(list)
PORTAL_LINK_RATE_LIMIT = 3  # max 3 emails per merchant per minute

logger = get_logger(__name__)


class GrantNovaRequest(BaseModel):
    target: Literal["driver", "merchant"]
    driver_user_id: Optional[int] = None
    merchant_id: Optional[str] = None
    amount: int
    reason: str
    idempotency_key: Optional[str] = None  # Optional idempotency key for deduplication


class AdminOverviewResponse(BaseModel):
    total_drivers: int
    total_merchants: int
    total_driver_nova: int
    total_merchant_nova: int
    total_nova_outstanding: int
    total_stripe_usd: int


@router.get("/health")
def get_admin_health(
    admin: User = Depends(require_admin)
):
    """
    Get system health status for admin console.
    
    Returns /readyz status to surface system health in admin UI.
    """
    from fastapi.responses import JSONResponse
    from sqlalchemy import text
    from app.db import get_engine
    from app.config import settings
    import redis
    from urllib.parse import urlparse
    
    checks = {
        "startup_validation": {"status": "ok", "error": None},
        "database": {"status": "unknown", "error": None},
        "redis": {"status": "unknown", "error": None}
    }
    
    # Check database with timeout
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"]["status"] = "ok"
    except Exception as e:
        checks["database"]["status"] = "error"
        checks["database"]["error"] = str(e)
    
    # Check Redis with timeout
    try:
        redis_url = settings.redis_url
        parsed = urlparse(redis_url)
        r = redis.Redis(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            db=int(parsed.path.lstrip('/')) if parsed.path else 0,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        r.ping()
        checks["redis"]["status"] = "ok"
    except Exception as e:
        checks["redis"]["status"] = "error"
        checks["redis"]["error"] = str(e)
    
    # Determine overall ready status
    all_ok = all(check["status"] == "ok" for check in checks.values())
    status_code = 200 if all_ok else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ok,
            "checks": checks
        }
    )


@router.get("/overview", response_model=AdminOverviewResponse)
def get_overview(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin overview statistics"""
    # Count drivers (users with driver role)
    total_drivers = db.query(User).filter(
        User.role_flags.contains("driver")
    ).count()
    
    # Count merchants
    total_merchants = db.query(DomainMerchant).count()
    
    # Sum driver Nova balances
    driver_nova_result = db.query(func.sum(DriverWallet.nova_balance)).scalar()
    total_driver_nova = int(driver_nova_result) if driver_nova_result else 0
    
    # Sum merchant Nova balances
    merchant_nova_result = db.query(func.sum(DomainMerchant.nova_balance)).scalar()
    total_merchant_nova = int(merchant_nova_result) if merchant_nova_result else 0
    
    # Total outstanding Nova
    total_nova_outstanding = total_driver_nova + total_merchant_nova
    
    # Sum Stripe payments (successful)
    stripe_usd_result = db.query(func.sum(StripePayment.amount_usd)).filter(
        StripePayment.status == "paid"
    ).scalar()
    total_stripe_usd = int(stripe_usd_result) if stripe_usd_result else 0
    
    return AdminOverviewResponse(
        total_drivers=total_drivers,
        total_merchants=total_merchants,
        total_driver_nova=total_driver_nova,
        total_merchant_nova=total_merchant_nova,
        total_nova_outstanding=total_nova_outstanding,
        total_stripe_usd=total_stripe_usd
    )


@router.get("/merchants")
def list_merchants(
    zone_slug: Optional[str] = Query(None, description="Filter by zone slug"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List merchants with filters"""
    query = db.query(DomainMerchant)
    
    if zone_slug:
        query = query.filter(DomainMerchant.zone_slug == zone_slug)
    
    if status_filter:
        query = query.filter(DomainMerchant.status == status_filter)
    
    merchants = query.order_by(DomainMerchant.created_at.desc()).all()
    
    # Get last transaction timestamp for each merchant
    merchant_list = []
    for merchant in merchants:
        last_txn = db.query(NovaTransaction).filter(
            NovaTransaction.merchant_id == merchant.id
        ).order_by(NovaTransaction.created_at.desc()).first()
        
        merchant_list.append({
            "id": merchant.id,
            "name": merchant.name,
            "zone_slug": merchant.zone_slug,
            "status": merchant.status,
            "nova_balance": merchant.nova_balance,
            "last_active_at": last_txn.created_at.isoformat() if last_txn else None,
            "created_at": merchant.created_at.isoformat()
        })
    
    return {"merchants": merchant_list}


@router.post("/nova/grant")
def grant_nova(
    request: GrantNovaRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Manually grant Nova to driver or merchant (admin only)"""
    try:
        if request.target == "driver":
            if not request.driver_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="driver_user_id required for driver target"
                )
            
            # Require idempotency key in non-local environments
            from app.core.env import is_local_env
            
            idempotency_key = request.idempotency_key
            if not idempotency_key:
                if not is_local_env():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="idempotency_key is required in non-local environment"
                    )
                # In local, generate deterministic fallback for dev only
                idempotency_key = f"grant_driver_{request.driver_user_id}_{request.amount}"
            
            # Get wallet before grant
            from app.models_domain import DriverWallet
            wallet_before = db.query(DriverWallet).filter(DriverWallet.user_id == request.driver_user_id).first()
            before_balance = wallet_before.nova_balance if wallet_before else 0
            
            transaction = NovaService.grant_to_driver(
                db=db,
                driver_id=request.driver_user_id,
                amount=request.amount,
                type="admin_grant",
                idempotency_key=idempotency_key,
                metadata={"reason": request.reason, "granted_by": admin.id}
            )
            
            # Get wallet after grant
            db.refresh(wallet_before) if wallet_before else None
            wallet_after = db.query(DriverWallet).filter(DriverWallet.user_id == request.driver_user_id).first()
            after_balance = wallet_after.nova_balance if wallet_after else 0
            
            # P1-1: Admin audit log
            log_admin_action(
                db=db,
                actor_id=admin.id,
                action="admin_grant_driver",
                target_type="wallet",
                target_id=str(request.driver_user_id),
                before_json={"nova_balance": before_balance},
                after_json={"nova_balance": after_balance},
                metadata={"reason": request.reason, "amount": request.amount, "transaction_id": transaction.id}
            )
            db.commit()  # Commit audit log
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "target": "driver",
                "driver_user_id": request.driver_user_id,
                "amount": request.amount
            }
        
        elif request.target == "merchant":
            if not request.merchant_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="merchant_id required for merchant target"
                )
            
            # Require idempotency key in non-local environments
            from app.core.env import is_local_env
            
            idempotency_key = request.idempotency_key
            if not idempotency_key:
                if not is_local_env():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="idempotency_key is required in non-local environment"
                    )
                # In local, generate deterministic fallback for dev only
                idempotency_key = f"grant_merchant_{request.merchant_id}_{request.amount}"
            
            # Get merchant balance before grant
            from app.models_domain import DomainMerchant
            merchant_before = db.query(DomainMerchant).filter(DomainMerchant.id == request.merchant_id).first()
            before_balance = merchant_before.nova_balance if merchant_before else 0
            
            transaction = NovaService.grant_to_merchant(
                db=db,
                merchant_id=request.merchant_id,
                amount=request.amount,
                type="admin_grant",
                idempotency_key=idempotency_key,
                metadata={"reason": request.reason, "granted_by": admin.id}
            )
            
            # Get merchant balance after grant
            db.refresh(merchant_before) if merchant_before else None
            merchant_after = db.query(DomainMerchant).filter(DomainMerchant.id == request.merchant_id).first()
            after_balance = merchant_after.nova_balance if merchant_after else 0
            
            # P1-1: Admin audit log
            log_admin_action(
                db=db,
                actor_id=admin.id,
                action="admin_grant_merchant",
                target_type="merchant_balance",
                target_id=request.merchant_id,
                before_json={"nova_balance": before_balance},
                after_json={"nova_balance": after_balance},
                metadata={"reason": request.reason, "amount": request.amount, "transaction_id": transaction.id}
            )
            db.commit()  # Commit audit log
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "target": "merchant",
                "merchant_id": request.merchant_id,
                "amount": request.amount
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target must be 'driver' or 'merchant'"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/payments/{payment_id}/reconcile")
def reconcile_payment(
    payment_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to reconcile a payment with status 'unknown'.
    
    If payment status is not 'unknown', returns current payment summary (no-op).
    If payment is 'unknown', calls Stripe to check transfer status and updates accordingly.
    """
    try:
        # Call reconciliation logic
        result = StripeService.reconcile_payment(db, payment_id)
        
        # Fetch full payment details for response
        payment_row = db.execute(text("""
            SELECT id, status, stripe_transfer_id, stripe_status, 
                   error_code, error_message, reconciled_at, no_transfer_confirmed
            FROM payments
            WHERE id = :payment_id
        """), {"payment_id": payment_id}).first()
        
        if not payment_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found"
            )
        
        # Audit log
        logger.info(f"Admin reconciliation triggered: payment_id={payment_id}, admin_id={admin.id}, result_status={result.get('status')}")
        
        # Build response with all required fields
        response = {
            "payment_id": payment_row[0] or payment_id,
            "status": payment_row[1] or result.get("status"),
            "stripe_transfer_id": payment_row[2],
            "stripe_status": payment_row[3],
            "error_code": payment_row[4],
            "error_message": payment_row[5],
            "reconciled_at": payment_row[6].isoformat() if payment_row[6] else None,
            "no_transfer_confirmed": bool(payment_row[7]) if payment_row[7] is not None else None
        }
        
        # Add message from reconciliation result if present
        if "message" in result:
            response["message"] = result["message"]
        
        return response
        
    except ValueError as e:
        # Payment not found
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in admin reconcile endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation failed: {str(e)}"
        )


# P1-2: Admin API endpoints

class WalletAdjustRequest(BaseModel):
    """Request to manually adjust user wallet"""
    amount_cents: int  # Positive for credit, negative for debit
    reason: str


class UserResponse(BaseModel):
    """User response model"""
    id: int
    public_id: str
    email: str
    role_flags: str
    is_active: bool
    created_at: str


class UserWalletResponse(BaseModel):
    """User wallet response model"""
    user_id: int
    balance_cents: int
    nova_balance: int
    transactions: List[dict]


class MerchantStatusResponse(BaseModel):
    """Merchant status response model"""
    merchant_id: str
    name: str
    status: str
    square_connected: bool
    square_last_error: Optional[str]
    nova_balance: int


class GooglePlaceCandidatesResponse(BaseModel):
    """Google Places candidates response"""
    candidates: List[dict]


class GooglePlaceResolveRequest(BaseModel):
    """Request to resolve Google Place ID"""
    place_id: str


@router.get("/users", response_model=List[UserResponse])
def search_users(
    query: Optional[str] = Query(None, description="Search by name, email, or public_id"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Search users by name, email, or public_id.
    
    P1-2: Admin API endpoint for user search.
    """
    q = db.query(User)
    
    if query:
        # Search by email, public_id, or name (if name column exists)
        search_filter = or_(
            User.email.ilike(f"%{query}%"),
            User.public_id.ilike(f"%{query}%")
        )
        # Try to search by name if column exists
        try:
            if hasattr(User, 'name'):
                search_filter = or_(search_filter, User.name.ilike(f"%{query}%"))
        except:
            pass
        q = q.filter(search_filter)
    
    users = q.order_by(User.created_at.desc()).limit(50).all()
    
    return [
        UserResponse(
            id=user.id,
            public_id=user.public_id,
            email=user.email,
            role_flags=user.role_flags or "",
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else ""
        )
        for user in users
    ]


@router.get("/users/{user_id}/wallet", response_model=UserWalletResponse)
def get_user_wallet(
    user_id: int = Path(..., description="User ID"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get user wallet balance and transaction history.
    
    P1-2: Admin API endpoint for viewing user wallet.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # Get wallet balance from credit_ledger
    balance_cents = _balance(db, str(user_id))
    
    # Get Nova balance from DriverWallet
    wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user_id).first()
    nova_balance = wallet.nova_balance if wallet else 0
    
    # Get transaction history
    transactions = []
    try:
        ledger_entries = db.query(CreditLedger).filter(
            CreditLedger.user_ref == str(user_id)
        ).order_by(CreditLedger.id.desc()).limit(50).all()
        
        transactions = [
            {
                "id": entry.id,
                "cents": entry.cents,
                "reason": entry.reason,
                "meta": entry.meta or {},
                "created_at": entry.created_at.isoformat() if entry.created_at else ""
            }
            for entry in ledger_entries
        ]
    except Exception as e:
        logger.warning(f"Could not fetch transaction history: {e}")
    
    return UserWalletResponse(
        user_id=user_id,
        balance_cents=balance_cents,
        nova_balance=nova_balance,
        transactions=transactions
    )


@router.post("/users/{user_id}/wallet/adjust")
def adjust_user_wallet(
    user_id: int = Path(..., description="User ID"),
    request: WalletAdjustRequest = Body(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Manually adjust user wallet balance (creates ledger entry + audit log).
    
    P1-2: Admin API endpoint for manual wallet adjustments.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    
    # Get balance before adjustment
    before_balance = _balance(db, str(user_id))
    
    # Add ledger entry
    new_balance = _add_ledger(
        db,
        str(user_id),
        request.amount_cents,
        "ADMIN_ADJUST",
        {"reason": request.reason, "admin_id": admin.id}
    )
    
    # P1-1: Admin audit log
    log_wallet_mutation(
        db=db,
        actor_id=admin.id,
        action="admin_adjust",
        user_id=str(user_id),
        before_balance=before_balance,
        after_balance=new_balance,
        amount=request.amount_cents,
        metadata={"reason": request.reason, "admin_id": admin.id}
    )
    db.commit()
    
    return {
        "success": True,
        "user_id": user_id,
        "amount_cents": request.amount_cents,
        "before_balance_cents": before_balance,
        "after_balance_cents": new_balance
    }


@router.get("/merchants", response_model=dict)
def search_merchants(
    query: Optional[str] = Query(None, description="Search by merchant name or ID"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Search merchants by name or ID.
    
    P1-2: Admin API endpoint for merchant search.
    """
    q = db.query(DomainMerchant)
    
    if query:
        q = q.filter(
            or_(
                DomainMerchant.name.ilike(f"%{query}%"),
                DomainMerchant.id.ilike(f"%{query}%")
            )
        )
    
    merchants = q.order_by(DomainMerchant.created_at.desc()).limit(50).all()
    
    return {
        "merchants": [
            {
                "id": merchant.id,
                "name": merchant.name,
                "status": merchant.status,
                "zone_slug": merchant.zone_slug,
                "nova_balance": merchant.nova_balance,
                "created_at": merchant.created_at.isoformat() if merchant.created_at else ""
            }
            for merchant in merchants
        ]
    }


@router.get("/merchants/{merchant_id}/status", response_model=MerchantStatusResponse)
def get_merchant_status(
    merchant_id: str = Path(..., description="Merchant ID"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get merchant status including Square token status and last error.
    
    P1-2: Admin API endpoint for merchant status.
    """
    merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {merchant_id} not found"
        )
    
    # Check Square connection status
    square_connected = bool(merchant.square_access_token and merchant.square_connected_at)
    
    # Get last error from recent transactions or payments
    square_last_error = None
    try:
        # Check for failed Stripe payments (if any)
        last_payment = db.query(StripePayment).filter(
            StripePayment.merchant_id == merchant_id,
            StripePayment.status == "failed"
        ).order_by(StripePayment.created_at.desc()).first()
        
        if last_payment and last_payment.error_message:
            square_last_error = last_payment.error_message
    except Exception:
        pass
    
    return MerchantStatusResponse(
        merchant_id=merchant.id,
        name=merchant.name,
        status=merchant.status,
        square_connected=square_connected,
        square_last_error=square_last_error,
        nova_balance=merchant.nova_balance
    )


@router.get("/locations/{location_id}/google-place/candidates", response_model=GooglePlaceCandidatesResponse)
def get_google_place_candidates(
    location_id: str = Path(..., description="Location ID (merchant ID)"),
    query: Optional[str] = Query(None, description="Search query for Google Places"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get Google Places candidates for a merchant location.
    
    P1-2: Admin API endpoint for Google Places mapping.
    """
    merchant = db.query(DomainMerchant).filter(DomainMerchant.id == location_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {location_id} not found"
        )
    
    # Use merchant name and location for search
    search_query = query or merchant.name
    lat = merchant.lat
    lng = merchant.lng
    
    # Call Google Places API (if configured)
    candidates = []
    try:
        import os
        google_places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if google_places_api_key:
            import httpx
            # Use Places API Text Search
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": search_query,
                "location": f"{lat},{lng}",
                "radius": 5000,  # 5km radius
                "key": google_places_api_key
            }
            
            response = httpx.get(url, params=params, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                candidates = [
                    {
                        "place_id": result.get("place_id"),
                        "name": result.get("name"),
                        "formatted_address": result.get("formatted_address"),
                        "geometry": result.get("geometry", {}),
                        "rating": result.get("rating"),
                        "types": result.get("types", [])
                    }
                    for result in data.get("results", [])[:10]  # Limit to 10
                ]
        else:
            logger.warning("GOOGLE_PLACES_API_KEY not configured")
    except Exception as e:
        logger.error(f"Error fetching Google Places candidates: {e}")
    
    return GooglePlaceCandidatesResponse(candidates=candidates)


@router.post("/locations/{location_id}/google-place/resolve")
def resolve_google_place(
    location_id: str = Path(..., description="Location ID (merchant ID)"),
    request: GooglePlaceResolveRequest = Body(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Resolve Google Place ID for a merchant location.
    
    P1-2: Admin API endpoint for resolving Google Place ID.
    """
    merchant = db.query(DomainMerchant).filter(DomainMerchant.id == location_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant {location_id} not found"
        )
    
    # Fetch place details from Google Places API
    place_details = None
    try:
        import os
        google_places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if google_places_api_key:
            import httpx
            url = f"https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": request.place_id,
                "fields": "place_id,name,formatted_address,geometry,rating,types,website,international_phone_number",
                "key": google_places_api_key
            }
            
            response = httpx.get(url, params=params, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    place_details = data.get("result", {})
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GOOGLE_PLACES_API_KEY not configured"
            )
    except Exception as e:
        logger.error(f"Error fetching Google Place details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch place details: {str(e)}"
        )
    
    if not place_details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Place ID {request.place_id} not found"
        )
    
    # Update merchant with Google Place ID
    merchant.google_place_id = request.place_id
    # Optionally update other fields from place_details
    if place_details.get("formatted_address"):
        # Parse address if needed (simplified)
        merchant.addr_line1 = place_details.get("formatted_address", "").split(",")[0] if place_details.get("formatted_address") else None
    
    db.commit()
    
    # P1-1: Admin audit log
    log_admin_action(
        db=db,
        actor_id=admin.id,
        action="admin_resolve_google_place",
        target_type="merchant",
        target_id=location_id,
        before_json={"google_place_id": merchant.google_place_id},
        after_json={"google_place_id": request.place_id},
        metadata={"place_id": request.place_id, "place_name": place_details.get("name")}
    )
    db.commit()
    
    return {
        "success": True,
        "merchant_id": location_id,
        "google_place_id": request.place_id,
        "place_details": place_details
    }


@router.get("/sessions/active")
def get_active_sessions(
    limit: int = Query(100, le=500),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all currently active exclusive sessions for admin monitoring.
    """
    from app.models import ExclusiveSession, ExclusiveSessionStatus, Merchant, Charger
    from datetime import datetime
    
    now = datetime.utcnow()
    
    sessions = db.query(ExclusiveSession).filter(
        ExclusiveSession.status == ExclusiveSessionStatus.ACTIVE,
        ExclusiveSession.expires_at > now
    ).order_by(ExclusiveSession.activated_at.desc()).limit(limit).all()
    
    result = []
    for s in sessions:
        merchant = db.query(Merchant).filter(Merchant.id == s.merchant_id).first() if s.merchant_id else None
        charger = db.query(Charger).filter(Charger.id == s.charger_id).first() if s.charger_id else None
        
        result.append({
            "id": str(s.id),
            "driver_id": s.driver_id,
            "merchant_id": s.merchant_id,
            "merchant_name": merchant.name if merchant else None,
            "charger_id": s.charger_id,
            "charger_name": charger.name if charger else None,
            "status": s.status.value,
            "activated_at": s.activated_at.isoformat(),
            "expires_at": s.expires_at.isoformat(),
            "time_remaining_minutes": max(0, int((s.expires_at - now).total_seconds() / 60))
        })
    
    return {
        "sessions": result,
        "total_active": len(result)
    }


class SendPortalLinkRequest(BaseModel):
    email: str


@router.post("/merchants/{merchant_id}/send-portal-link")
async def send_merchant_portal_link(
    merchant_id: str = Path(...),
    request: SendPortalLinkRequest = Body(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Send merchant an email with a link to their portal.
    """
    from app.models_domain import DomainMerchant
    from app.services.email.factory import get_email_sender
    import os
    
    merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail=f"Merchant {merchant_id} not found")
    
    # Rate limiting: max 3 emails per merchant per minute
    now = datetime.utcnow()
    recent = [t for t in _portal_link_timestamps[merchant_id] if (now - t).total_seconds() < 60]
    if len(recent) >= PORTAL_LINK_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {PORTAL_LINK_RATE_LIMIT} emails per minute per merchant."
        )
    _portal_link_timestamps[merchant_id] = recent + [now]
    
    # Generate portal URL
    portal_base = os.getenv("MERCHANT_PORTAL_URL", "https://merchant.nerava.network")
    portal_url = f"{portal_base}?merchant_id={merchant_id}"
    
    # Test email override for safe testing
    admin_test_email = os.getenv("ADMIN_TEST_EMAIL")
    recipient_email = admin_test_email if admin_test_email else request.email
    
    # Send email
    sender = get_email_sender()
    html_body = f"""
    <h2>Welcome to Nerava Merchant Portal</h2>
    <p>Hi {merchant.name},</p>
    <p>You can now access your Nerava Merchant Portal to view customer visits and manage your exclusives.</p>
    <p><a href="{portal_url}" style="background-color: #171717; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; display: inline-block;">Access Your Portal</a></p>
    <p>If the button doesn't work, copy this link: {portal_url}</p>
    <p>- The Nerava Team</p>
    """
    
    success = await sender.send(
        to=recipient_email,
        subject=f"Access Your Nerava Merchant Portal - {merchant.name}",
        html_body=html_body,
        text_body=f"Access your Nerava Merchant Portal: {portal_url}"
    )
    
    # Audit log
    log_admin_action(
        db=db,
        actor_id=admin.id,
        action="send_portal_link",
        target_type="merchant",
        target_id=merchant_id,
        before_json={},
        after_json={"email": recipient_email[:3] + "***"},
        metadata={"merchant_name": merchant.name}
    )
    db.commit()
    
    return {
        "success": success,
        "merchant_id": merchant_id,
        "email_sent_to": recipient_email[:3] + "***",
        "test_override_active": bool(admin_test_email)
    }


# ============================================================================
# Admin Portal v1 Endpoints
# ============================================================================

from app.schemas.admin import (
    ToggleExclusiveRequest,
    ToggleExclusiveResponse,
    AdminExclusiveItem,
    AdminExclusivesResponse,
    MerchantActionRequest,
    MerchantActionResponse,
    ForceCloseRequest,
    ForceCloseResponse,
    EmergencyPauseRequest,
    EmergencyPauseResponse,
    AdminLogEntry,
    AdminLogsResponse
)
from app.services.admin_service import (
    get_exclusives_with_counts,
    toggle_exclusive,
    pause_merchant,
    resume_merchant
)
from app.models.while_you_charge import Merchant, MerchantPerk
from app.models.exclusive_session import ExclusiveSession, ExclusiveSessionStatus
from app.models.audit import AdminAuditLog
from fastapi import Request
from datetime import timedelta


@router.get("/exclusives", response_model=AdminExclusivesResponse)
def list_all_exclusives(
    status: Optional[str] = Query(None, description="Filter by status: active, paused, or all"),
    merchant_id: Optional[str] = Query(None, description="Filter by merchant ID"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """List all exclusives across merchants for admin oversight."""
    exclusives_data = get_exclusives_with_counts(db, merchant_id=merchant_id, status=status)
    
    # Apply pagination
    total = len(exclusives_data)
    paginated = exclusives_data[offset:offset + limit]
    
    exclusives = [
        AdminExclusiveItem(
            id=e["id"],
            merchant_id=e["merchant_id"],
            merchant_name=e["merchant_name"],
            title=e["title"],
            description=e.get("description"),
            nova_reward=e["nova_reward"],
            is_active=e["is_active"],
            daily_cap=e.get("daily_cap"),
            activations_today=e["activations_today"],
            activations_this_month=e["activations_this_month"],
            created_at=e["created_at"],
            updated_at=e["updated_at"]
        )
        for e in paginated
    ]
    
    return AdminExclusivesResponse(
        exclusives=exclusives,
        total=total,
        limit=limit,
        offset=offset
    )


@router.post("/exclusives/{exclusive_id}/toggle", response_model=ToggleExclusiveResponse)
def toggle_exclusive_endpoint(
    exclusive_id: str,
    request: ToggleExclusiveRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Admin toggle exclusive on/off with mandatory reason."""
    try:
        previous_state, new_state = toggle_exclusive(db, exclusive_id, admin.id)
        
        # Log action
        ip_address = http_request.client.host if http_request.client else None
        log_admin_action(
            db=db,
            actor_id=admin.id,
            action="exclusive_toggle",
            target_type="exclusive",
            target_id=exclusive_id,
            metadata={
                "reason": request.reason,
                "previous_state": previous_state,
                "new_state": new_state,
                "ip_address": ip_address
            }
        )
        db.commit()
        
        return ToggleExclusiveResponse(
            exclusive_id=exclusive_id,
            previous_state=previous_state,
            new_state=new_state,
            toggled_by=admin.email,
            reason=request.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/merchants/{merchant_id}/pause", response_model=MerchantActionResponse)
def pause_merchant_endpoint(
    merchant_id: str,
    request: MerchantActionRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Pause a merchant - disables all their exclusives and hides from discovery."""
    try:
        previous_status, new_status = pause_merchant(db, merchant_id, admin.id)
        
        # Log action
        ip_address = http_request.client.host if http_request.client else None
        log_admin_action(
            db=db,
            actor_id=admin.id,
            action="merchant_pause",
            target_type="merchant",
            target_id=merchant_id,
            metadata={
                "reason": request.reason,
                "previous_status": previous_status,
                "new_status": new_status,
                "ip_address": ip_address
            }
        )
        db.commit()
        
        return MerchantActionResponse(
            merchant_id=merchant_id,
            action="pause",
            previous_status=previous_status,
            new_status=new_status,
            reason=request.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/merchants/{merchant_id}/resume", response_model=MerchantActionResponse)
def resume_merchant_endpoint(
    merchant_id: str,
    request: MerchantActionRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Resume a paused merchant."""
    try:
        previous_status, new_status = resume_merchant(db, merchant_id, admin.id)
        
        # Log action
        ip_address = http_request.client.host if http_request.client else None
        log_admin_action(
            db=db,
            actor_id=admin.id,
            action="merchant_resume",
            target_type="merchant",
            target_id=merchant_id,
            metadata={
                "reason": request.reason,
                "previous_status": previous_status,
                "new_status": new_status,
                "ip_address": ip_address
            }
        )
        db.commit()
        
        return MerchantActionResponse(
            merchant_id=merchant_id,
            action="resume",
            previous_status=previous_status,
            new_status=new_status,
            reason=request.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sessions/force-close", response_model=ForceCloseResponse)
def force_close_sessions_endpoint(
    request: ForceCloseRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    Force-close all active exclusive sessions at a location.
    CRITICAL ACTION - requires reason and is logged.
    """
    from app.models.while_you_charge import ChargerMerchant
    
    # Find all chargers linked to this merchant (location_id is merchant_id)
    charger_merchants = db.query(ChargerMerchant).filter(
        ChargerMerchant.merchant_id == request.location_id
    ).all()
    charger_ids = [cm.charger_id for cm in charger_merchants]
    
    if not charger_ids:
        raise HTTPException(status_code=404, detail=f"Location {request.location_id} not found or has no chargers")
    
    # Find all active sessions at these chargers
    active_sessions = db.query(ExclusiveSession).filter(
        ExclusiveSession.charger_id.in_(charger_ids),
        ExclusiveSession.status == ExclusiveSessionStatus.ACTIVE
    ).all()
    
    closed_count = 0
    for session in active_sessions:
        session.status = ExclusiveSessionStatus.FORCE_CLOSED
        session.completed_at = datetime.utcnow()
        session.force_close_reason = request.reason
        session.force_closed_by = admin.id
        closed_count += 1
    
    # Log action
    ip_address = http_request.client.host if http_request.client else None
    log_admin_action(
        db=db,
        actor_id=admin.id,
        action="force_close_sessions",
        target_type="location",
        target_id=request.location_id,
        metadata={
            "reason": request.reason,
            "sessions_closed": closed_count,
            "ip_address": ip_address
        }
    )
    
    db.commit()
    
    return ForceCloseResponse(
        location_id=request.location_id,
        sessions_closed=closed_count,
        closed_by=admin.email,
        reason=request.reason,
        timestamp=datetime.utcnow()
    )


@router.post("/overrides/emergency-pause", response_model=EmergencyPauseResponse)
def emergency_pause_endpoint(
    request: EmergencyPauseRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """
    EMERGENCY: Pause all exclusive activations system-wide.
    Sets a global flag that prevents new activations.
    CRITICAL ACTION - requires reason and confirmation token.
    """
    # Verify confirmation token
    if request.confirmation != "CONFIRM-EMERGENCY-PAUSE":
        raise HTTPException(
            status_code=400,
            detail="Invalid confirmation. Send confirmation='CONFIRM-EMERGENCY-PAUSE'"
        )
    
    # Use Redis for emergency pause flag
    try:
        from app.services.cache import cache
        import json
        
        if request.action == "activate":
            cache.redis_client.set("emergency_pause_active", "1")
            cache.redis_client.set("emergency_pause_reason", request.reason)
            cache.redis_client.set("emergency_pause_by", str(admin.id))
            cache.redis_client.set("emergency_pause_at", datetime.utcnow().isoformat())
            action_taken = "activated"
        else:
            cache.redis_client.delete("emergency_pause_active")
            cache.redis_client.delete("emergency_pause_reason")
            cache.redis_client.delete("emergency_pause_by")
            cache.redis_client.delete("emergency_pause_at")
            action_taken = "deactivated"
    except Exception as e:
        logger.warning(f"Redis not available for emergency pause, using in-memory fallback: {e}")
        # Fallback to in-memory (not ideal but allows functionality)
        global _emergency_pause_state
        if '_emergency_pause_state' not in globals():
            _emergency_pause_state = {}
        
        if request.action == "activate":
            _emergency_pause_state = {
                "active": True,
                "reason": request.reason,
                "by": admin.id,
                "at": datetime.utcnow().isoformat()
            }
            action_taken = "activated"
        else:
            _emergency_pause_state = {}
            action_taken = "deactivated"
    
    # Log action
    ip_address = http_request.client.host if http_request.client else None
    log_admin_action(
        db=db,
        actor_id=admin.id,
        action=f"emergency_pause_{action_taken}",
        target_type="system",
        target_id="global",
        metadata={
            "reason": request.reason,
            "ip_address": ip_address
        }
    )
    
    db.commit()
    
    return EmergencyPauseResponse(
        action=action_taken,
        activated_by=admin.email,
        reason=request.reason,
        timestamp=datetime.utcnow()
    )


@router.get("/logs", response_model=AdminLogsResponse)
def get_admin_logs(
    type: Optional[str] = Query(None, description="Filter by action type"),
    search: Optional[str] = Query(None, description="Search in action_type, target_id, or reason"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Retrieve admin audit logs with filtering."""
    query = db.query(AdminAuditLog).order_by(AdminAuditLog.created_at.desc())
    
    if type:
        query = query.filter(AdminAuditLog.action.ilike(f"%{type}%"))
    
    if search:
        query = query.filter(
            or_(
                AdminAuditLog.action.ilike(f"%{search}%"),
                AdminAuditLog.target_id.ilike(f"%{search}%"),
                AdminAuditLog.metadata_json.cast(sa_String).ilike(f"%{search}%")
            )
        )
    
    if start_date:
        query = query.filter(AdminAuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AdminAuditLog.created_at <= end_date)
    
    total = query.count()
    logs = query.offset(offset).limit(limit).all()
    
    # Get operator emails
    operator_ids = {log.actor_id for log in logs}
    operators = {u.id: u.email for u in db.query(User).filter(User.id.in_(operator_ids)).all()}
    
    log_entries = []
    for log in logs:
        metadata = log.metadata_json or {}
        reason = metadata.get("reason")
        ip_address = metadata.get("ip_address")
        
        log_entries.append(AdminLogEntry(
            id=str(log.id),
            operator_id=log.actor_id,
            operator_email=operators.get(log.actor_id),
            action_type=log.action,
            target_type=log.target_type,
            target_id=log.target_id,
            reason=reason,
            ip_address=ip_address,
            created_at=log.created_at
        ))
    
    return AdminLogsResponse(
        logs=log_entries,
        total=total,
        limit=limit,
        offset=offset
    )

