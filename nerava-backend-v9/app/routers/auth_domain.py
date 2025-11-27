"""
Domain Charge Party MVP Auth Router
Extends existing auth with role-based access and session management
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import timedelta
import logging

from app.db import get_db
from app.models import User
from app.services.auth_service import AuthService
from app.dependencies_domain import (
    get_current_user,
    get_current_user_id,
    require_driver,
    require_merchant_admin
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/auth", tags=["auth-v1"])


# Request/Response Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    role: Optional[str] = "driver"  # driver, merchant_admin, admin


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: Optional[str]
    role_flags: Optional[str]
    linked_merchant: Optional[dict] = None


@router.post("/register", response_model=TokenResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (driver or merchant_admin)"""
    try:
        roles = [request.role] if request.role else ["driver"]
        user = AuthService.register_user(
            db=db,
            email=request.email,
            password=request.password,
            display_name=request.display_name,
            roles=roles
        )
        
        token = AuthService.create_session_token(user)
        
        response = TokenResponse(access_token=token)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"Registration failed: {error_detail}\n{error_traceback}")
        # Include more detail in response for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {error_detail}. Check server logs for full traceback."
        )


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    response: Response = None
):
    """Login user and return JWT token (accepts JSON body)"""
    try:
        user = AuthService.authenticate_user(db, request.email, request.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        token = AuthService.create_session_token(user)
        
        # Set HTTP-only cookie for better security
        if response:
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=False,  # Set to False for localhost/HTTP, True in production with HTTPS
                samesite="lax",
                max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        
        return TokenResponse(access_token=token)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        logger.error(f"Login failed: {error_detail}\n{error_traceback}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {error_detail}"
        )


@router.post("/logout")
def logout(response: Response):
    """Logout user (clear cookie)"""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user info including linked merchant if merchant_admin"""
    linked_merchant = None
    
    if AuthService.has_role(user, "merchant_admin"):
        merchant = AuthService.get_user_merchant(db, user.id)
        if merchant:
            linked_merchant = {
                "id": merchant.id,
                "name": merchant.name,
                "nova_balance": merchant.nova_balance
            }
    
    return UserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role_flags=user.role_flags,
        linked_merchant=linked_merchant
    )

