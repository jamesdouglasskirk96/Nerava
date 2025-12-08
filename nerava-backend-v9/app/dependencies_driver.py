"""
Driver-specific dependency injection
Provides get_current_driver with dev fallback support
"""
import os
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import jwt

from app.db import get_db
from app.models import User
from app.core.config import settings
from app.dependencies_domain import oauth2_scheme
from app.services.auth_service import AuthService

# Dev-only flag: allow anonymous driver access in local dev
# DO NOT enable in production
DEV_ALLOW_ANON_DRIVER = os.getenv("NERAVA_DEV_ALLOW_ANON_DRIVER", "false").lower() == "true"


def get_current_driver_id(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> int:
    """
    Resolve the current driver ID from the request.
    
    In production, this requires valid authentication (JWT token).
    In local/dev, when NERAVA_DEV_ALLOW_ANON_DRIVER=true, uses driver_id=1 as fallback.
    
    Args:
        request: FastAPI Request object
        token: Optional OAuth2 token from header
        db: Database session
        
    Returns:
        int: Driver user ID
        
    Raises:
        HTTPException: 401 if authentication fails and dev fallback is not enabled
    """
    # 1. Try to get token from Authorization header first
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    # 2. Try to get from cookie if no header token
    if not token:
        token = request.cookies.get("access_token")
    
    # 3. If we have a token, decode it and extract user_id
    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id_str = payload.get("sub")
            if user_id_str:
                user_id = int(user_id_str)
                return user_id
        except jwt.ExpiredSignatureError:
            # Token expired - fall through to dev fallback or raise
            pass
        except Exception:
            # Invalid token - fall through to dev fallback or raise
            pass
    
    # 4. Dev fallback: if NERAVA_DEV_ALLOW_ANON_DRIVER=true, use default driver
    if DEV_ALLOW_ANON_DRIVER:
        print("[AUTH][DEV] NERAVA_DEV_ALLOW_ANON_DRIVER=true -> using driver_id=1")
        return 1
    
    # 5. Production: authentication required
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Driver authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_driver(
    driver_id: int = Depends(get_current_driver_id),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current driver User object.
    
    Uses get_current_driver_id to resolve the driver ID (with dev fallback),
    then fetches and validates the User object.
    
    Args:
        driver_id: Driver user ID from get_current_driver_id
        db: Database session
        
    Returns:
        User: Driver user object
        
    Raises:
        HTTPException: 401 if user not found or inactive
    """
    user = AuthService.get_user_by_id(db, driver_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Driver user not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver account is inactive"
        )
    return user

