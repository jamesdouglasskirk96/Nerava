"""
Tesla OAuth and EV Verification Router.

Handles Tesla account connection and charging verification for EV rewards.
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.models.tesla_connection import TeslaConnection, EVVerificationCode
from app.models.domain import DomainMerchant
from app.models.while_you_charge import Merchant
from app.dependencies.domain import get_current_user
from app.services.tesla_oauth import (
    get_tesla_oauth_service,
    get_valid_access_token,
    generate_ev_code,
)
from app.services.geo import haversine_m
from app.core.config import settings

PROXIMITY_THRESHOLD_METERS = 500

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

        # Try to get user's vehicles (may fail with 412 if partner registration incomplete)
        vehicle = None
        try:
            vehicles = await oauth_service.get_vehicles(access_token)
            if vehicles:
                vehicle = vehicles[0]
        except Exception as ve:
            logger.warning(f"Could not fetch Tesla vehicles (partner registration may be incomplete): {ve}")
            # Continue without vehicle data — tokens are still valid

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
            if vehicle:
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
                vehicle_id=str(vehicle.get("id")) if vehicle else None,
                vin=vehicle.get("vin") if vehicle else None,
                vehicle_name=vehicle.get("display_name") if vehicle else None,
                vehicle_model=vehicle.get("vehicle_config", {}).get("car_type", "Tesla") if vehicle else None,
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
    Verify Tesla charging via Fleet API and generate an EV reward code.

    Attempts real Fleet API charging verification. If the vehicle is asleep
    or unreachable, falls back to issuing a code based on valid Tesla
    connection + location proximity (enforced by frontend).
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

    # Verify the token is still valid (refresh if needed)
    access_token = await get_valid_access_token(db, connection, oauth_service)
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Tesla session expired. Please reconnect your Tesla."
        )

    # --- Location validation ---
    if request.lat is None or request.lng is None:
        raise HTTPException(
            status_code=400,
            detail="Location (lat/lng) is required to verify charging."
        )

    if request.merchant_place_id:
        # Look up merchant coordinates from either table
        merchant_lat: Optional[float] = None
        merchant_lng: Optional[float] = None

        domain_merchant = db.query(DomainMerchant).filter(
            DomainMerchant.google_place_id == request.merchant_place_id
        ).first()
        if domain_merchant:
            merchant_lat = domain_merchant.lat
            merchant_lng = domain_merchant.lng

        if merchant_lat is None:
            wyc_merchant = db.query(Merchant).filter(
                Merchant.place_id == request.merchant_place_id
            ).first()
            if wyc_merchant:
                merchant_lat = wyc_merchant.lat
                merchant_lng = wyc_merchant.lng

        if merchant_lat is not None and merchant_lng is not None:
            distance = haversine_m(request.lat, request.lng, merchant_lat, merchant_lng)
            if distance > PROXIMITY_THRESHOLD_METERS:
                logger.info(
                    f"User {current_user.id} too far from merchant "
                    f"{request.merchant_place_id} ({distance:.0f}m)"
                )
                raise HTTPException(
                    status_code=400,
                    detail="You need to be near the merchant to get a code"
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
            ev_code=existing_code.code,
            message="You're connected! Show this code to redeem your reward."
        )

    # --- Fleet API charging verification (all vehicles) ---
    try:
        is_charging, charge_data, charging_vehicle = (
            await oauth_service.verify_charging_all_vehicles(access_token)
        )
    except Exception as e:
        logger.error(f"Fleet API verification failed for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=502,
            detail="Unable to reach your Tesla right now. Please make sure your vehicle is online and try again."
        )

    # Backfill primary vehicle_id if missing and we found vehicles
    if not connection.vehicle_id and charging_vehicle:
        connection.vehicle_id = str(charging_vehicle.get("id"))
        connection.vin = charging_vehicle.get("vin")
        connection.vehicle_name = charging_vehicle.get("display_name") or "Tesla"
        connection.vehicle_model = (
            charging_vehicle.get("vehicle_config", {}).get("car_type", "Tesla")
        )
        connection.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Backfilled vehicle_id {connection.vehicle_id} for user {current_user.id}")

    battery_level = charge_data.get("battery_level")
    charge_rate_kw = charge_data.get("charger_power")

    if not is_charging:
        charging_state = charge_data.get("charging_state", "unknown")
        logger.info(f"Fleet API: no vehicle charging (state={charging_state}) for user {current_user.id}")
        return VerifyChargingResponse(
            is_charging=False,
            battery_level=battery_level,
            message="Your Tesla isn't currently charging. Plug in to verify your session and unlock your reward."
        )

    # Charging confirmed — generate EV code
    charging_vin = charging_vehicle.get("vin") if charging_vehicle else connection.vin
    logger.info(f"Fleet API confirmed charging for user {current_user.id} "
               f"(vin={charging_vin}, battery={battery_level}%, power={charge_rate_kw}kW)")

    ev_code = generate_ev_code()

    # Ensure code is unique
    while db.query(EVVerificationCode).filter(EVVerificationCode.code == ev_code).first():
        ev_code = generate_ev_code()

    code_record = EVVerificationCode(
        user_id=current_user.id,
        tesla_connection_id=connection.id,
        code=ev_code,
        charger_id=request.charger_id,
        merchant_place_id=request.merchant_place_id,
        merchant_name=request.merchant_name,
        charging_verified=True,
        battery_level=battery_level,
        charge_rate_kw=charge_rate_kw,
        lat=str(request.lat) if request.lat else None,
        lng=str(request.lng) if request.lng else None,
        expires_at=datetime.utcnow() + timedelta(hours=2),
    )
    db.add(code_record)

    connection.last_used_at = datetime.utcnow()
    db.commit()

    logger.info(f"Generated EV code {ev_code} for user {current_user.id} "
               f"at merchant {request.merchant_name} (Fleet API verified)")

    return VerifyChargingResponse(
        is_charging=True,
        battery_level=battery_level,
        charge_rate_kw=charge_rate_kw,
        ev_code=ev_code,
        message="Charging verified! Show this code to the merchant to redeem your reward.",
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
