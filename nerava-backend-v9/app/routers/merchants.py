"""
Merchant endpoints - registration, dashboard, and redemption
Consolidates merchant onboarding and management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid
import secrets

from ..db import get_db
from ..models import User
from ..models.domain import DomainMerchant, NovaTransaction
from ..services.auth_service import AuthService
from ..services.nova_service import NovaService
from ..services.square_service import (
    get_square_oauth_authorize_url, 
    exchange_square_oauth_code,
    create_oauth_state,
    validate_oauth_state,
    OAuthStateInvalidError
)
from ..services.merchant_onboarding import onboard_merchant_via_square
from ..services.qr_service import create_or_get_merchant_qr
from ..services.merchant_signs import generate_merchant_sign_pdf
from ..services.merchant_reporting import get_merchant_summary, get_shareable_stats
from ..services.merchant_analytics import merchant_billing_summary
from ..dependencies_domain import require_merchant_admin, get_current_user
from ..routers.drivers_domain import haversine_distance

router = APIRouter(prefix="/v1/merchants", tags=["merchants"])


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
    from ..models.domain import Zone
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
            "metadata": txn.transaction_meta
        }
        for txn in transactions
    ]


# Square OAuth onboarding endpoints
@router.get("/square/connect")
async def square_connect(
    db: Session = Depends(get_db)
):
    """
    Get Square OAuth authorization URL for merchant onboarding.
    
    This endpoint:
    1. Creates and persists an OAuth state for CSRF protection
    2. Returns a URL that merchants can visit to connect their Square account
    3. The merchant will be redirected back to SQUARE_REDIRECT_URL with an authorization code
    
    Returns:
        Dict with "url" and "state" keys
    """
    try:
        # Create and persist OAuth state
        state = create_oauth_state(db)
        
        # Generate OAuth URL with state
        url = await get_square_oauth_authorize_url(state)
        
        return {
            "url": url,
            "state": state
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/square/sandbox/connect")
async def square_sandbox_connect(
    db: Session = Depends(get_db)
):
    """
    Get Square SANDBOX OAuth authorization URL for testing.
    
    This endpoint is for SANDBOX testing only:
    1. Generates random state (uuid4) and stores it using OAuth state logic
    2. Returns Square sandbox OAuth URL with redirect_uri
    
    Use this endpoint to test Square OAuth flow locally with a public tunnel.
    
    Returns:
        Dict with "url" (Square sandbox OAuth URL) and "redirect_uri" keys
    """
    from ..config import get_square_sandbox_config
    
    try:
        # Create and persist OAuth state
        state = create_oauth_state(db)
        
        # Generate OAuth URL with state
        url = await get_square_oauth_authorize_url(state)
        
        # Get redirect URI from config
        cfg = get_square_sandbox_config()
        
        return {
            "url": url,
            "redirect_uri": cfg["redirect_url"]
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/square/callback")
async def square_callback(
    code: str = Query(..., description="OAuth authorization code from Square"),
    state: str = Query(..., description="OAuth state parameter"),
    db: Session = Depends(get_db)
):
    """
    Handle Square OAuth callback and onboard merchant.
    
    This endpoint:
    1. Validates OAuth state (CSRF protection)
    2. Exchanges the OAuth code for an access token
    3. Fetches merchant location stats (AOV)
    4. Creates or updates the merchant
    5. Calculates recommended perk
    6. Generates QR token
    
    Returns:
        Dict with merchant info, perk details, and QR info
    """
    # Validate OAuth state first
    try:
        validate_oauth_state(db, state)
    except OAuthStateInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "OAUTH_STATE_MISMATCH",
                "message": "Square OAuth state is invalid or expired."
            }
        )
    
    try:
        # Exchange code for access token
        square_result = await exchange_square_oauth_code(code)
        
        # Onboard merchant (or update if exists)
        # Note: user_id is None for now - can be added later if we have authenticated merchant users
        merchant = await onboard_merchant_via_square(
            db=db,
            user_id=None,
            square_result=square_result
        )
        
        # Get QR info (should already be set, but ensure it exists)
        qr_result = create_or_get_merchant_qr(db, merchant)
        
        # Return success response for sandbox testing
        return {
            "success": True,
            "merchant_id": merchant.id,
            "message": "Square sandbox connected",
            "name": merchant.name,
            "perk": {
                "avg_order_value_cents": merchant.avg_order_value_cents,
                "recommended_perk_cents": merchant.recommended_perk_cents,
                "perk_label": merchant.perk_label
            },
            "qr": {
                "token": qr_result["token"],
                "url": qr_result["url"]
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "SQUARE_AUTH_FAILED",
                "message": str(e)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "SQUARE_AUTH_FAILED",
                "message": f"Square onboarding failed: {str(e)}"
            }
        )


@router.get("/{merchant_id}/sign.pdf")
async def get_merchant_sign_pdf(
    merchant_id: str,
    db: Session = Depends(get_db)
):
    """
    Generate and download printable QR sign PDF for merchant.
    
    Returns a PDF that merchants can print and display at their counter.
    The PDF includes the merchant name and a QR code for driver checkout.
    
    Args:
        merchant_id: Merchant ID
        
    Returns:
        PDF file response
    """
    # Validate merchant_id format
    if not merchant_id or len(merchant_id) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_MERCHANT_ID",
                "message": "Invalid merchant ID format"
            }
        )
    
    merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MERCHANT_NOT_FOUND",
                "message": f"Merchant {merchant_id} not found"
            }
        )
    
    # Ensure merchant has a QR token
    qr_result = create_or_get_merchant_qr(db, merchant)
    qr_url = qr_result["url"]
    
    try:
        # Generate PDF
        pdf_bytes = generate_merchant_sign_pdf(merchant, qr_url)
        
        # Return PDF response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="nerava-sign-{merchant_id}.pdf"'
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF generation failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sign PDF: {str(e)}"
        )


@router.get("/{merchant_id}/summary")
def get_merchant_summary_endpoint(
    merchant_id: str,
    db: Session = Depends(get_db)
):
    """
    Get merchant summary statistics.
    
    Returns aggregated redemption statistics:
    - Total redemptions
    - Total discount amount
    - Unique driver count
    - Last 7 days and 30 days redemptions
    - Average discount amount
    
    Args:
        merchant_id: Merchant ID
        
    Returns:
        Dict with summary statistics
    """
    # Validate merchant_id format
    if not merchant_id or len(merchant_id) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_MERCHANT_ID",
                "message": "Invalid merchant ID format"
            }
        )
    
    merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MERCHANT_NOT_FOUND",
                "message": f"Merchant {merchant_id} not found"
            }
        )
    
    summary = get_merchant_summary(db, merchant_id)
    return summary


@router.get("/{merchant_id}/billing/summary")
def get_merchant_billing_summary(
    merchant_id: str,
    db: Session = Depends(get_db)
):
    """
    Get billing summary for a merchant.
    
    Merchants only pay the platform fee on redeemed Nova, not the full redemption amount.
    
    Args:
        merchant_id: Merchant ID
        
    Returns:
        {
            "period_start": "2025-12-01",
            "period_end": "2025-12-31",
            "nova_redeemed_cents": 200,
            "platform_fee_bps": 1500,
            "platform_fee_cents": 30,
            "status": "pending",
            "settlement_method": "invoice"
        }
    """
    # Validate merchant exists
    merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MERCHANT_NOT_FOUND",
                "message": f"Merchant {merchant_id} not found"
            }
        )
    
    try:
        summary = merchant_billing_summary(db, merchant_id)
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get billing summary: {str(e)}"
        )


@router.get("/{merchant_id}/shareables")
def get_merchant_shareables(
    merchant_id: str,
    db: Session = Depends(get_db)
):
    """
    Get shareable social media stats for merchant.
    
    Returns human-readable stat lines that merchants can share on social media.
    
    Args:
        merchant_id: Merchant ID
        
    Returns:
        Dict with "lines" key containing list of shareable stat strings
    """
    # Validate merchant_id format
    if not merchant_id or len(merchant_id) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_MERCHANT_ID",
                "message": "Invalid merchant ID format"
            }
        )
    
    merchant = db.query(DomainMerchant).filter(DomainMerchant.id == merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MERCHANT_NOT_FOUND",
                "message": f"Merchant {merchant_id} not found"
            }
        )
    
    lines = get_shareable_stats(db, merchant_id)
    return {
        "lines": lines
    }
