"""
Google Business Profile OAuth Client

Handles OAuth flow for Google Business Profile API.
Supports mock mode for local development.
"""
import logging
import os
import secrets
import httpx
from typing import List, Dict, Optional
from urllib.parse import urlencode

from app.core.config import settings

logger = logging.getLogger(__name__)

# Check if MERCHANT_AUTH_MOCK is set
import os
MERCHANT_AUTH_MOCK = os.getenv("MERCHANT_AUTH_MOCK", "false").lower() == "true"

# Google OAuth configuration
GOOGLE_AUTH_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_BUSINESS_PROFILE_SCOPE = "https://www.googleapis.com/auth/business.manage"



def get_oauth_authorize_url(state: str, redirect_uri: str) -> str:
    """
    Generate Google OAuth authorization URL.
    
    Args:
        state: CSRF protection state token
        redirect_uri: OAuth callback redirect URI
    
    Returns:
        Authorization URL
    """
    if MERCHANT_AUTH_MOCK:
        # In mock mode, return a fake URL
        return f"http://localhost:8001/mock-oauth-callback?state={state}"
    
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": GOOGLE_BUSINESS_PROFILE_SCOPE,
        "response_type": "code",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    
    return f"{GOOGLE_AUTH_BASE_URL}?{urlencode(params)}"


async def exchange_oauth_code(code: str, redirect_uri: str) -> Dict[str, str]:
    """
    Exchange OAuth authorization code for access token.
    
    Args:
        code: Authorization code from callback
        redirect_uri: OAuth callback redirect URI
    
    Returns:
        Dict with access_token, refresh_token, etc.
    
    TODO: In production, encrypt tokens before storing (use TOKEN_ENCRYPTION_KEY pattern)
    """
    if MERCHANT_AUTH_MOCK:
        # In mock mode, return fake tokens
        return {
            "access_token": f"mock_access_token_{secrets.token_urlsafe(16)}",
            "refresh_token": f"mock_refresh_token_{secrets.token_urlsafe(16)}",
            "expires_in": "3600",
            "token_type": "Bearer",
        }
    
    if not settings.GOOGLE_CLIENT_ID:
        raise ValueError("Google OAuth not configured (GOOGLE_CLIENT_ID missing)")
    
    # TODO: Get Google Client Secret from config
    # For now, raise error if not in mock mode
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
    if not google_client_secret:
        raise ValueError("Google OAuth not configured (GOOGLE_CLIENT_SECRET missing)")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return response.json()


async def list_locations(access_token: str) -> List[Dict[str, str]]:
    """
    List Google Business Profile locations for the authenticated merchant.
    
    Args:
        access_token: OAuth access token
    
    Returns:
        List of location dictionaries with location_id, name, address, place_id
    """
    if MERCHANT_AUTH_MOCK:
        # Return seeded fake locations for local dev
        return [
            {
                "location_id": "mock_location_1",
                "name": "Mock Coffee Shop",
                "address": "123 Main St, Austin, TX 78701",
                "place_id": "ChIJMockPlace1",
            },
            {
                "location_id": "mock_location_2",
                "name": "Mock Restaurant",
                "address": "456 Oak Ave, Austin, TX 78702",
                "place_id": "ChIJMockPlace2",
            },
        ]
    
    # TODO: Implement real Google Business Profile API call
    # For now, raise NotImplementedError if not in mock mode
    raise NotImplementedError(
        "Real Google Business Profile API integration not yet implemented. "
        "Set MERCHANT_AUTH_MOCK=true for local development."
    )

