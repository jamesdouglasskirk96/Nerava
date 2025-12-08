"""
Smartcar API client service
Handles OAuth token exchange, refresh, and vehicle API calls
"""
import logging
import httpx
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.models_vehicle import VehicleAccount, VehicleToken

logger = logging.getLogger(__name__)

# Timeout for Smartcar API calls
SMARTCAR_TIMEOUT = 30.0


async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access and refresh tokens
    
    Args:
        code: Authorization code from Smartcar callback
        
    Returns:
        Dict with access_token, refresh_token, expires_in, scope, etc.
        
    Raises:
        httpx.HTTPStatusError: If Smartcar API returns an error
    """
    url = f"{settings.SMARTCAR_AUTH_URL}/oauth/token"
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.SMARTCAR_REDIRECT_URI,
        "client_id": settings.SMARTCAR_CLIENT_ID,
        "client_secret": settings.SMARTCAR_CLIENT_SECRET,
    }
    
    async with httpx.AsyncClient(timeout=SMARTCAR_TIMEOUT) as client:
        try:
            response = await client.post(url, data=data)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Smartcar token exchange failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            raise


async def refresh_tokens(db: Session, vehicle_account: VehicleAccount) -> VehicleToken:
    """
    Refresh access token for a vehicle account if needed
    
    Args:
        db: Database session
        vehicle_account: VehicleAccount to refresh tokens for
        
    Returns:
        VehicleToken (existing if still valid, or newly refreshed)
        
    Raises:
        httpx.HTTPStatusError: If Smartcar API returns an error
    """
    # Get the most recent token
    latest_token = (
        db.query(VehicleToken)
        .filter(VehicleToken.vehicle_account_id == vehicle_account.id)
        .order_by(desc(VehicleToken.created_at))
        .first()
    )
    
    if not latest_token:
        raise ValueError(f"No token found for vehicle account {vehicle_account.id}")
    
    # Check if token expires in more than 5 minutes
    if latest_token.expires_at > datetime.utcnow() + timedelta(minutes=5):
        logger.debug(f"Token for vehicle {vehicle_account.id} still valid, returning existing token")
        return latest_token
    
    # Refresh the token
    url = f"{settings.SMARTCAR_AUTH_URL}/oauth/token"
    
    data = {
        "grant_type": "refresh_token",
        "refresh_token": latest_token.refresh_token,
        "client_id": settings.SMARTCAR_CLIENT_ID,
        "client_secret": settings.SMARTCAR_CLIENT_SECRET,
    }
    
    async with httpx.AsyncClient(timeout=SMARTCAR_TIMEOUT) as client:
        try:
            response = await client.post(url, data=data)
            response.raise_for_status()
            token_data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Smartcar token refresh failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            raise
    
    # Create new token record
    import uuid
    new_token = VehicleToken(
        id=str(uuid.uuid4()),
        vehicle_account_id=vehicle_account.id,
        access_token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token", latest_token.refresh_token),  # May not be returned
        expires_at=datetime.utcnow() + timedelta(seconds=token_data.get("expires_in", 3600)),
        scope=token_data.get("scope", latest_token.scope),
    )
    
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    
    logger.info(f"Refreshed token for vehicle account {vehicle_account.id}")
    return new_token


async def list_vehicles(access_token: str) -> Dict[str, Any]:
    """
    List vehicles for the authenticated user
    
    Args:
        access_token: Smartcar access token
        
    Returns:
        Dict with vehicles array
        
    Raises:
        httpx.HTTPStatusError: If Smartcar API returns an error
    """
    url = f"{settings.SMARTCAR_BASE_URL}/v2.0/vehicles"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=SMARTCAR_TIMEOUT) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Smartcar list vehicles failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing vehicles: {e}")
            raise


async def get_vehicle_location(access_token: str, vehicle_id: str) -> Dict[str, Any]:
    """
    Get vehicle location
    
    Args:
        access_token: Smartcar access token
        vehicle_id: Smartcar vehicle ID
        
    Returns:
        Dict with latitude, longitude, etc.
        
    Raises:
        httpx.HTTPStatusError: If Smartcar API returns an error
    """
    url = f"{settings.SMARTCAR_BASE_URL}/v2.0/vehicles/{vehicle_id}/location"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=SMARTCAR_TIMEOUT) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Smartcar get location failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting location: {e}")
            raise


async def get_vehicle_charge(access_token: str, vehicle_id: str) -> Dict[str, Any]:
    """
    Get vehicle charge state
    
    Args:
        access_token: Smartcar access token
        vehicle_id: Smartcar vehicle ID
        
    Returns:
        Dict with stateOfCharge, isPluggedIn, etc.
        
    Raises:
        httpx.HTTPStatusError: If Smartcar API returns an error
    """
    url = f"{settings.SMARTCAR_BASE_URL}/v2.0/vehicles/{vehicle_id}/charge"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    async with httpx.AsyncClient(timeout=SMARTCAR_TIMEOUT) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Smartcar get charge failed: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting charge: {e}")
            raise

