"""
Smartcar EV integration router
Handles OAuth flow and telemetry endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode
import uuid
from jose import jwt

from app.db import get_db
from app.models import User
from app.models_vehicle import VehicleAccount, VehicleToken
from app.dependencies_domain import get_current_user, get_current_user_id
from app.core.config import settings
from app.services.smartcar_client import (
    exchange_code_for_tokens,
    list_vehicles,
)
from app.services.ev_telemetry import poll_vehicle_telemetry_for_account

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ev"])


# Response models
class ConnectResponse(BaseModel):
    url: str


class TelemetryResponse(BaseModel):
    recorded_at: datetime
    soc_pct: Optional[float]
    charging_state: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]


# Helper: Create signed state token
def create_state_token(user_id: int) -> str:
    """Create a cryptographically signed state token for OAuth flow"""
    expires_delta = timedelta(minutes=15)
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "user_id": str(user_id),
        "purpose": "smartcar_oauth",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# Helper: Verify and decode state token
def verify_state_token(token: str) -> int:
    """Verify state token and return user_id"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        if payload.get("purpose") != "smartcar_oauth":
            raise ValueError("Invalid token purpose")
        
        user_id_str = payload.get("user_id")
        if not user_id_str:
            raise ValueError("Missing user_id in token")
        
        return int(user_id_str)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State token expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state token: {str(e)}"
        )


@router.get("/v1/ev/connect", response_model=ConnectResponse)
async def connect_vehicle(
    current_user: User = Depends(get_current_user),
):
    """
    Generate Smartcar Connect URL for the authenticated user
    
    Returns a URL that the frontend should redirect the user to.
    After OAuth, Smartcar will redirect to /oauth/smartcar/callback.
    """
    if not settings.SMARTCAR_CLIENT_ID or not settings.SMARTCAR_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Smartcar not configured"
        )
    
    # Create signed state token
    state = create_state_token(current_user.id)
    
    # Build Smartcar Connect URL
    base_url = f"{settings.SMARTCAR_CONNECT_URL}/oauth/authorize"
    
    params = {
        "response_type": "code",
        "client_id": settings.SMARTCAR_CLIENT_ID,
        "redirect_uri": settings.SMARTCAR_REDIRECT_URI,
        "scope": "read_vehicle_info read_location read_charge",
        "mode": settings.SMARTCAR_MODE,
        "state": state,
    }
    
    connect_url = f"{base_url}?{urlencode(params)}"
    
    logger.info(f"Generated Smartcar Connect URL for user {current_user.id}")
    
    return ConnectResponse(url=connect_url)


@router.get("/oauth/smartcar/callback")
async def smartcar_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Smartcar OAuth callback endpoint
    
    This is called by Smartcar after the user authorizes.
    We exchange the code for tokens, fetch vehicle info, and store everything.
    """
    # Handle OAuth errors
    if error:
        logger.error(f"Smartcar OAuth error: {error}")
        # Redirect to frontend with error
        frontend_url = f"{settings.FRONTEND_URL}/vehicle/connect?error={error}"
        return RedirectResponse(url=frontend_url)
    
    # Validate required parameters
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing authorization code"
        )
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing state parameter"
        )
    
    # Verify state token and get user_id
    try:
        user_id = verify_state_token(state)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"State token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state token"
        )
    
    # Fetch user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Exchange code for tokens
        token_data = await exchange_code_for_tokens(code)
        
        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data.get("expires_in", 3600)
        scope = token_data.get("scope", "")
        
        # List vehicles (get first one for now)
        vehicles_data = await list_vehicles(access_token)
        vehicles = vehicles_data.get("vehicles", [])
        
        if not vehicles:
            logger.warning(f"No vehicles found for user {user_id}")
            frontend_url = f"{settings.FRONTEND_URL}/vehicle/connect?error=no_vehicles"
            return RedirectResponse(url=frontend_url)
        
        # Use first vehicle (can extend to multi-vehicle later)
        vehicle_id = vehicles[0]["id"]
        
        # Upsert VehicleAccount
        existing_account = (
            db.query(VehicleAccount)
            .filter(
                VehicleAccount.user_id == user_id,
                VehicleAccount.provider == "smartcar",
                VehicleAccount.provider_vehicle_id == vehicle_id
            )
            .first()
        )
        
        if existing_account:
            account = existing_account
            account.is_active = True
            account.updated_at = datetime.utcnow()
        else:
            account = VehicleAccount(
                id=str(uuid.uuid4()),
                user_id=user_id,
                provider="smartcar",
                provider_vehicle_id=vehicle_id,
                display_name=None,  # Could fetch from vehicle info endpoint
                is_active=True,
            )
            db.add(account)
        
        db.flush()  # Get account.id
        
        # Create token record
        token_record = VehicleToken(
            id=str(uuid.uuid4()),
            vehicle_account_id=account.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            scope=scope,
        )
        
        db.add(token_record)
        db.commit()
        
        logger.info(f"Connected vehicle {vehicle_id} for user {user_id}")
        
        # Redirect to frontend account page with success indicator
        # Use FRONTEND_URL if set, otherwise construct from request
        if settings.FRONTEND_URL:
            frontend_url = f"{settings.FRONTEND_URL}/#profile?vehicle=connected"
        else:
            # Fallback: try to construct from request (for local dev)
            frontend_url = f"/#profile?vehicle=connected"
        
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error(f"Error in Smartcar callback: {e}", exc_info=True)
        db.rollback()
        
        # Redirect to frontend with error
        if settings.FRONTEND_URL:
            frontend_url = f"{settings.FRONTEND_URL}/#profile?error=connection_failed"
        else:
            frontend_url = f"/#profile?error=connection_failed"
        
        return RedirectResponse(url=frontend_url)


@router.get("/v1/ev/me/telemetry/latest", response_model=TelemetryResponse)
async def get_latest_telemetry(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get latest telemetry for the current user's connected vehicle
    
    This endpoint polls Smartcar for fresh data and returns it.
    This is the production test endpoint.
    """
    # Find user's active vehicle account
    account = (
        db.query(VehicleAccount)
        .filter(
            VehicleAccount.user_id == current_user.id,
            VehicleAccount.provider == "smartcar",
            VehicleAccount.is_active == True
        )
        .first()
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No connected vehicle found"
        )
    
    try:
        # Poll fresh telemetry
        telemetry = await poll_vehicle_telemetry_for_account(db, account)
        
        return TelemetryResponse(
            recorded_at=telemetry.recorded_at,
            soc_pct=telemetry.soc_pct,
            charging_state=telemetry.charging_state,
            latitude=telemetry.latitude,
            longitude=telemetry.longitude,
        )
        
    except Exception as e:
        logger.error(f"Error polling telemetry for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch vehicle telemetry: {str(e)}"
        )

