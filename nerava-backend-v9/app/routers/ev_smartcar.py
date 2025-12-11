"""
Smartcar EV integration router
Handles OAuth flow and telemetry endpoints

Configuration:
- Set SMARTCAR_CLIENT_ID, SMARTCAR_CLIENT_SECRET, and SMARTCAR_REDIRECT_URI environment variables
- SMARTCAR_MODE defaults to "sandbox" for local dev (set to "live" for production)
- Register the callback URL in Smartcar dashboard: {your-backend-url}/oauth/smartcar/callback
- For local dev, use a tunnel (Cloudflare Tunnel, ngrok, etc.) to expose localhost:8001

Example .env:
  SMARTCAR_CLIENT_ID=your_client_id
  SMARTCAR_CLIENT_SECRET=your_client_secret
  SMARTCAR_MODE=sandbox
  SMARTCAR_REDIRECT_URI=https://your-tunnel-domain/oauth/smartcar/callback
  FRONTEND_URL=http://localhost:8001/app
  NERAVA_DEV_ALLOW_ANON_USER=true

Local Testing Flow:
1. Start local backend with migrations:
   - Delete nerava.db if schema is stale (or let migrations upgrade it)
   - Run: python3 -m uvicorn app.main_simple:app --host 0.0.0.0 --port 8001 --reload
   - Migrations will run on startup and create/update the DB schema

2. Start local UI at http://localhost:8001/app

3. Set env vars in .env:
   - NERAVA_DEV_ALLOW_ANON_USER=true (allows user_id=1 fallback)
   - FRONTEND_URL=http://localhost:8001/app
   - SMARTCAR_REDIRECT_URI=https://<your-tunnel-host>/oauth/smartcar/callback
   - SMARTCAR_CLIENT_ID, SMARTCAR_CLIENT_SECRET, SMARTCAR_MODE=sandbox

4. Start a tunnel (e.g., cloudflared tunnel --url http://localhost:8001) and update
   SMARTCAR_REDIRECT_URI with the tunnel URL

5. Register the callback URL in Smartcar dashboard

6. In the UI, go to the EV connect screen, click "Connect EV", complete Smartcar/Tesla login

7. Verify:
   - /oauth/smartcar/callback returns 302 redirect back to the app (no 500)
   - A row exists in vehicle_accounts and vehicle_tokens for user_id=1
   - /v1/ev/me/telemetry/latest returns 200 with telemetry data or clean 404 if unavailable
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
from app.config import settings
from app.services.smartcar_service import (
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
    
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


# Helper: Verify and decode state token
def verify_state_token(token: str) -> int:
    """Verify state token and return user_id"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        
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
    if not settings.smartcar_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Smartcar integration is not configured. Set SMARTCAR_CLIENT_ID, SMARTCAR_CLIENT_SECRET, and SMARTCAR_REDIRECT_URI."
        )
    
    # Create signed state token
    state = create_state_token(current_user.id)
    
    # Build Smartcar Connect URL
    base_url = f"{settings.smartcar_connect_url}/oauth/authorize"
    
    # Default scope - can be extended later
    scope = "read_vehicle_info read_location read_charge"
    
    params = {
        "response_type": "code",
        "client_id": settings.smartcar_client_id,
        "redirect_uri": settings.smartcar_redirect_uri,
        "scope": scope,
        "mode": settings.smartcar_mode,
        "state": state,
    }
    
    connect_url = f"{base_url}?{urlencode(params)}"
    
    # Log mode and redirect_uri (but NOT client_secret)
    logger.info(
        f"Generated Smartcar Connect URL for user {current_user.id} "
        f"(mode={settings.smartcar_mode}, redirect_uri={settings.smartcar_redirect_uri})"
    )
    
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
        frontend_url = f"{settings.frontend_url.rstrip('/')}/#profile?error={error}"
        return RedirectResponse(url=frontend_url, status_code=302)
    
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
        # Smartcar API returns: {"vehicles": ["vehicle_id_1", "vehicle_id_2", ...]}
        # The vehicles array contains vehicle ID strings, not objects
        vehicles_data = await list_vehicles(access_token)
        vehicles = vehicles_data.get("vehicles", [])
        
        logger.info(f"[Smartcar] vehicles_resp keys: {list(vehicles_data.keys())}")
        
        if not vehicles:
            logger.warning(f"No vehicles found for user {user_id}")
            frontend_url = f"{settings.frontend_url}/#profile?error=no_vehicles"
            return RedirectResponse(url=frontend_url)
        
        # Use first vehicle (can extend to multi-vehicle later)
        # vehicles[0] is already the vehicle ID string, not an object
        vehicle_id = vehicles[0] if isinstance(vehicles[0], str) else vehicles[0].get("id", vehicles[0])
        
        logger.info(f"[Smartcar] Selected vehicle_id={vehicle_id} for user_id={user_id}")
        
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
        frontend_url = f"{settings.frontend_url.rstrip('/')}/#profile?vehicle=connected"
        
        return RedirectResponse(url=frontend_url, status_code=302)
        
    except Exception as e:
        logger.error(f"Error in Smartcar callback: {e}", exc_info=True)
        db.rollback()
        
        # Redirect to frontend with error
        frontend_url = f"{settings.frontend_url.rstrip('/')}/#profile?error=connection_failed"
        
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

