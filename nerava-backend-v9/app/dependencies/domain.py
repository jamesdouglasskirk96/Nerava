"""
Dependency injection for Domain Charge Party MVP
Role-based access control dependencies
"""
import os
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from jose import jwt
from fastapi.security import OAuth2PasswordBearer

from ..db import get_db
from ..models import User
from ..services.auth_service import AuthService
from ..core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

# Dev-only flag: allow anonymous user access in local dev
# DO NOT enable in production
DEV_ALLOW_ANON_USER = os.getenv("NERAVA_DEV_ALLOW_ANON_USER", "false").lower() == "true"


def get_current_user_id(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> int:
    """Get current user ID from token or cookie"""
    # Try to get token from Authorization header first
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
    
    # Try to get from cookie if no header token
    if not token:
        token = request.cookies.get("access_token")
    
    # If we have a token, decode it and extract user_id
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
    
    # Dev fallback: if NERAVA_DEV_ALLOW_ANON_USER=true, use default user
    if DEV_ALLOW_ANON_USER:
        print("[AUTH][DEV] NERAVA_DEV_ALLOW_ANON_USER=true -> using user_id=1")
        return 1
    
    # Production: authentication required
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> User:
    """Get current user object"""
    user = AuthService.get_user_by_id(db, user_id)
    
    # Dev fallback: create default user if it doesn't exist
    if not user and DEV_ALLOW_ANON_USER and user_id == 1:
        try:
            from ..models import User as UserModel
            # Create a default user for dev
            default_user = UserModel(
                id=1,
                email="dev@nerava.local",
                password_hash="dev",  # Not used in dev mode
                is_active=True,
                role_flags="driver",
                auth_provider="local"
            )
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
            print(f"[AUTH][DEV] Created default user (id=1)")
            user = default_user
        except Exception as e:
            # If creation fails (e.g., user already exists), try to fetch again
            db.rollback()
            user = AuthService.get_user_by_id(db, user_id)
            if not user:
                print(f"[AUTH][DEV] Failed to create/fetch dev user: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Dev mode: could not create or fetch user: {str(e)}"
                )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )
    return user


def require_role(role: str):
    """Dependency factory for requiring a specific role"""
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if not AuthService.has_role(user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {role}"
            )
        return user
    return role_checker


# Convenience dependencies for common roles
require_driver = require_role("driver")
require_merchant_admin = require_role("merchant_admin")
require_admin = require_role("admin")


