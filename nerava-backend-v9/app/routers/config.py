"""
Public configuration endpoint

Returns non-sensitive configuration values that the frontend needs.
"""
import os
from fastapi import APIRouter
from pydantic import BaseModel
from ..core.config import settings

router = APIRouter(prefix="/v1/public", tags=["config"])


class ConfigResponse(BaseModel):
    """Public configuration response"""
    google_client_id: str
    apple_client_id: str
    env: str
    api_base: str


@router.get("/config", response_model=ConfigResponse)
def get_public_config():
    """
    Get public configuration values for frontend.
    
    Returns Google Client ID, Apple Client ID, and other non-sensitive configuration.
    """
    # Get api_base from PUBLIC_BASE_URL or FRONTEND_URL
    api_base = os.getenv("PUBLIC_BASE_URL", "") or settings.FRONTEND_URL
    
    return ConfigResponse(
        google_client_id=settings.GOOGLE_CLIENT_ID or "",
        apple_client_id=settings.APPLE_CLIENT_ID or "",
        env=settings.ENV,
        api_base=api_base
    )

