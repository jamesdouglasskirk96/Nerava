"""
Domain Charge Party MVP Merchant Router
Merchant-specific endpoints for registration, dashboard, and redemption
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid

from app.db import get_db
from app.models import User
from app.models_domain import DomainMerchant, NovaTransaction
from app.services.auth_service import AuthService
from app.services.nova_service import NovaService
from app.dependencies_domain import require_merchant_admin, get_current_user
from app.routers.drivers_domain import haversine_distance

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
    from app.models_domain import Zone
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

