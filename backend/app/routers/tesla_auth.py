"""
Tesla OAuth and EV Verification Router.

Handles Tesla account connection and charging verification for EV rewards.
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.models.tesla_connection import TeslaConnection, EVVerificationCode
from app.dependencies.domain import get_current_user_optional, get_current_user
from app.services.tesla_oauth import (
    get_tesla_oauth_service,
    get_valid_access_token,
    generate_ev_code,
    TeslaOAuthService,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/tesla", tags=["Tesla"])

# In-memory state storage (use Redis in production)
_oauth_states: dict = {}


# ==================== Request/Response Models ====================

class TeslaConnectionStatus(BaseModel):
    connected: bool
    vehicle_name: Optional[str] = None
    vehicle_model: Optional[str] = None
    vin: Optional[str] = None


class TeslaConnectResponse(BaseModel):
    authorization_url: str
    state: str


class VerifyChargingRequest(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    merchant_place_id: Optional[str] = None
    merchant_name: Optional[str] = None
    charger_id: Optional[str] = None


class VerifyChargingResponse(BaseModel):
    is_charging: bool
    battery_level: Optional[int] = None
    charge_rate_kw: Optional[int] = None
    ev_code: Optional[str] = None
    message: str


class EVCodeResponse(BaseModel):
    code: str
    merchant_name: Optional[str] = None
    expires_at: datetime
    status: str


# ==================== Endpoints ====================

@router.get("/status", response_model=TeslaConnectionStatus)
async def get_tesla_connection_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if user has connected their Tesla account."""
    connection = db.query(TeslaConnection).filter(
        TeslaConnection.user_id == current_user.id,
        TeslaConnection.is_active == True
    ).first()

    if not connection:
        return TeslaConnectionStatus(connected=False)

    return TeslaConnectionStatus(
        connected=True,
        vehicle_name=connection.vehicle_name,
        vehicle_model=connection.vehicle_model,
        vin=connection.vin[-4:] if connection.vin else None  # Only last 4 chars
    )


@router.get("/connect", response_model=TeslaConnectResponse)
async def initiate_tesla_connection(
    current_user: User = Depends(get_current_user),
):
    """
    Start Tesla OAuth flow.

    Returns authorization URL to redirect user to Tesla login.
    """
    oauth_service = get_tesla_oauth_service()

    # Generate state token for CSRF protection
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "user_id": current_user.id,
        "created_at": datetime.utcnow(),
    }

    auth_url = oauth_service.get_authorization_url(state)

    return TeslaConnectResponse(
        authorization_url=auth_url,
        state=state
    )


@router.get("/callback")
async def tesla_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Handle Tesla OAuth callback.

    Exchanges authorization code for tokens and stores connection.
    """
    # Verify state
    state_data = _oauth_states.pop(state, None)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired state")

    # Check state age (max 10 minutes)
    if datetime.utcnow() - state_data["created_at"] > timedelta(minutes=10):
        raise HTTPException(status_code=400, detail="State expired")

    user_id = state_data["user_id"]
    oauth_service = get_tesla_oauth_service()

    try:
        # Exchange code for tokens
        token_response = await oauth_service.exchange_code_for_tokens(code)

        access_token = token_response["access_token"]
        refresh_token = token_response["refresh_token"]
        expires_in = token_response.get("expires_in", 3600)

        # Get user's vehicles
        vehicles = await oauth_service.get_vehicles(access_token)

        if not vehicles:
            raise HTTPException(status_code=400, detail="No vehicles found in Tesla account")

        # Use first vehicle as primary
        vehicle = vehicles[0]

        # Check for existing connection
        existing = db.query(TeslaConnection).filter(
            TeslaConnection.user_id == user_id,
            TeslaConnection.is_active == True
        ).first()

        if existing:
            # Update existing connection
            existing.access_token = access_token
            existing.refresh_token = refresh_token
            existing.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            existing.vehicle_id = str(vehicle.get("id"))
            existing.vin = vehicle.get("vin")
            existing.vehicle_name = vehicle.get("display_name")
            existing.vehicle_model = vehicle.get("vehicle_config", {}).get("car_type", "Tesla")
            existing.updated_at = datetime.utcnow()
        else:
            # Create new connection
            connection = TeslaConnection(
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                vehicle_id=str(vehicle.get("id")),
                vin=vehicle.get("vin"),
                vehicle_name=vehicle.get("display_name"),
                vehicle_model=vehicle.get("vehicle_config", {}).get("car_type", "Tesla"),
            )
            db.add(connection)

        db.commit()

        # Redirect to app with success
        app_url = settings.DRIVER_APP_URL or "https://app.nerava.network"
        return RedirectResponse(url=f"{app_url}/tesla-connected?success=true")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tesla OAuth callback failed: {e}")
        app_url = settings.DRIVER_APP_URL or "https://app.nerava.network"
        return RedirectResponse(url=f"{app_url}/tesla-connected?error=connection_failed")


@router.post("/verify-charging", response_model=VerifyChargingResponse)
async def verify_charging_and_generate_code(
    request: VerifyChargingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify that user's Tesla is currently charging and generate EV code.

    This is called when user enters a merchant's geofence while at a charger.
    If charging is verified, generates an EV-XXXX code for redemption.
    """
    # Get Tesla connection
    connection = db.query(TeslaConnection).filter(
        TeslaConnection.user_id == current_user.id,
        TeslaConnection.is_active == True
    ).first()

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="Tesla not connected. Please connect your Tesla first."
        )

    oauth_service = get_tesla_oauth_service()

    # Get valid access token (refresh if needed)
    access_token = await get_valid_access_token(db, connection, oauth_service)
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Tesla session expired. Please reconnect your Tesla."
        )

    # Verify charging status
    is_charging, charge_data = await oauth_service.verify_charging(
        access_token,
        connection.vehicle_id
    )

    if not is_charging:
        return VerifyChargingResponse(
            is_charging=False,
            battery_level=charge_data.get("battery_level"),
            message="Your Tesla is not currently charging. Start a charging session to unlock rewards."
        )

    # Check if user already has an active code for this merchant
    existing_code = db.query(EVVerificationCode).filter(
        EVVerificationCode.user_id == current_user.id,
        EVVerificationCode.merchant_place_id == request.merchant_place_id,
        EVVerificationCode.status == "active",
        EVVerificationCode.expires_at > datetime.utcnow()
    ).first()

    if existing_code:
        return VerifyChargingResponse(
            is_charging=True,
            battery_level=charge_data.get("battery_level"),
            charge_rate_kw=charge_data.get("charger_power"),
            ev_code=existing_code.code,
            message="Your charging is verified! Show this code to redeem your reward."
        )

    # Generate new EV code
    ev_code = generate_ev_code()

    # Ensure code is unique
    while db.query(EVVerificationCode).filter(EVVerificationCode.code == ev_code).first():
        ev_code = generate_ev_code()

    # Create verification code record
    code_record = EVVerificationCode(
        user_id=current_user.id,
        tesla_connection_id=connection.id,
        code=ev_code,
        charger_id=request.charger_id,
        merchant_place_id=request.merchant_place_id,
        merchant_name=request.merchant_name,
        charging_verified=True,
        battery_level=charge_data.get("battery_level"),
        charge_rate_kw=charge_data.get("charger_power"),
        lat=str(request.lat) if request.lat else None,
        lng=str(request.lng) if request.lng else None,
        expires_at=datetime.utcnow() + timedelta(hours=2),  # Code valid for 2 hours
    )
    db.add(code_record)

    # Update connection last used
    connection.last_used_at = datetime.utcnow()

    db.commit()

    return VerifyChargingResponse(
        is_charging=True,
        battery_level=charge_data.get("battery_level"),
        charge_rate_kw=charge_data.get("charger_power"),
        ev_code=ev_code,
        message="Charging verified! Show this code to the merchant to redeem your reward."
    )


@router.get("/codes", response_model=list[EVCodeResponse])
async def get_user_ev_codes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's active EV verification codes."""
    codes = db.query(EVVerificationCode).filter(
        EVVerificationCode.user_id == current_user.id,
        EVVerificationCode.status == "active",
        EVVerificationCode.expires_at > datetime.utcnow()
    ).order_by(EVVerificationCode.created_at.desc()).limit(10).all()

    return [
        EVCodeResponse(
            code=c.code,
            merchant_name=c.merchant_name,
            expires_at=c.expires_at,
            status=c.status
        )
        for c in codes
    ]


@router.post("/disconnect")
async def disconnect_tesla(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect Tesla account."""
    connection = db.query(TeslaConnection).filter(
        TeslaConnection.user_id == current_user.id,
        TeslaConnection.is_active == True
    ).first()

    if connection:
        connection.is_active = False
        connection.updated_at = datetime.utcnow()
        db.commit()

    return {"success": True, "message": "Tesla disconnected"}
