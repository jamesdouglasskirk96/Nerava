"""
Production Auth v1 Router
Implements Google SSO, Apple SSO, Phone OTP, refresh token rotation, /me, logout
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from ..db import get_db
from ..models import User, UserPreferences
from ..dependencies.domain import get_current_user
from ..core.security import create_access_token
from ..core.config import settings
from ..services.refresh_token_service import RefreshTokenService

router = APIRouter(prefix="/auth", tags=["auth"])


# ============================================
# Request/Response Models
# ============================================

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class LogoutResponse(BaseModel):
    ok: bool


class GoogleAuthRequest(BaseModel):
    id_token: str


class AppleAuthRequest(BaseModel):
    id_token: str


class OTPStartRequest(BaseModel):
    phone: str


class OTPStartResponse(BaseModel):
    otp_sent: bool


class OTPVerifyRequest(BaseModel):
    phone: str
    code: str


class UserMeResponse(BaseModel):
    public_id: str
    auth_provider: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================
# Core Auth Endpoints
# ============================================

@router.get("/me", response_model=UserMeResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get current user information"""
    return UserMeResponse(
        public_id=current_user.public_id,
        auth_provider=current_user.auth_provider,
        email=current_user.email,
        phone=current_user.phone,
        created_at=current_user.created_at
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    Implements token rotation: old token is revoked, new token is issued.
    """
    plain_refresh_token = payload.refresh_token
    
    # Validate refresh token
    old_token = RefreshTokenService.validate_refresh_token(db, plain_refresh_token)
    if not old_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Check if token was already revoked (reuse detection)
    if old_token.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected",
            headers={"X-Error-Code": "refresh_reuse_detected"}
        )
    
    # Rotate token: revoke old, create new
    new_plain_token, new_refresh_token = RefreshTokenService.rotate_refresh_token(db, old_token)
    
    # Get user
    user = db.query(User).filter(User.id == old_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create new access token
    access_token = create_access_token(user.public_id, auth_provider=user.auth_provider)
    
    db.commit()
    
    return RefreshResponse(
        access_token=access_token,
        refresh_token=new_plain_token,
        token_type="bearer"
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Logout: revoke refresh token(s).
    If refresh_token is provided, revoke that specific token.
    Otherwise, revoke all tokens for the current user.
    """
    if payload.refresh_token:
        # Revoke specific token
        token = RefreshTokenService.validate_refresh_token(db, payload.refresh_token)
        if token:
            RefreshTokenService.revoke_refresh_token(db, token)
            db.commit()
    elif current_user:
        # Revoke all tokens for current user
        RefreshTokenService.revoke_all_user_tokens(db, current_user.id)
        db.commit()
    
    return LogoutResponse(ok=True)


# ============================================
# Provider Auth Endpoints (to be implemented)
# ============================================

@router.post("/google", response_model=TokenResponse)
async def auth_google(
    payload: GoogleAuthRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate with Google ID token.
    Priority 1 - must work end-to-end.
    """
    # Import here to avoid circular dependencies
    from ..services.google_auth import verify_google_id_token
    
    try:
        # Verify Google ID token
        google_user_info = verify_google_id_token(payload.id_token)
        
        # Extract user info
        email = google_user_info.get("email")
        provider_sub = google_user_info.get("sub")  # Google subject ID
        
        if not provider_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google ID token: missing sub"
            )
        
        # Find or create user by (auth_provider, provider_sub)
        user = db.query(User).filter(
            User.auth_provider == "google",
            User.provider_sub == provider_sub
        ).first()
        
        if not user:
            # Create new user
            import uuid
            user = User(
                public_id=str(uuid.uuid4()),
                email=email,
                auth_provider="google",
                provider_sub=provider_sub,
                is_active=True
            )
            db.add(user)
            db.flush()
            db.add(UserPreferences(user_id=user.id))
            db.commit()
            db.refresh(user)
        
        # Create tokens
        access_token = create_access_token(user.public_id, auth_provider=user.auth_provider)
        refresh_token_plain, refresh_token_model = RefreshTokenService.create_refresh_token(db, user)
        
        db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_plain,
            token_type="bearer",
            user={
                "public_id": user.public_id,
                "auth_provider": user.auth_provider,
                "email": user.email,
                "phone": user.phone
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google authentication failed: {str(e)}"
        )


@router.post("/apple", response_model=TokenResponse)
async def auth_apple(
    payload: AppleAuthRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate with Apple ID token.
    Priority 2.
    """
    # Import here to avoid circular dependencies
    from ..services.apple_auth import verify_apple_id_token
    
    try:
        # Verify Apple ID token
        apple_user_info = verify_apple_id_token(payload.id_token)
        
        # Extract user info
        email = apple_user_info.get("email")
        provider_sub = apple_user_info.get("sub")  # Apple subject ID
        
        if not provider_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Apple ID token: missing sub"
            )
        
        # Find or create user by (auth_provider, provider_sub)
        user = db.query(User).filter(
            User.auth_provider == "apple",
            User.provider_sub == provider_sub
        ).first()
        
        if not user:
            # Create new user
            import uuid
            user = User(
                public_id=str(uuid.uuid4()),
                email=email,
                auth_provider="apple",
                provider_sub=provider_sub,
                is_active=True
            )
            db.add(user)
            db.flush()
            db.add(UserPreferences(user_id=user.id))
            db.commit()
            db.refresh(user)
        
        # Create tokens
        access_token = create_access_token(user.public_id, auth_provider=user.auth_provider)
        refresh_token_plain, refresh_token_model = RefreshTokenService.create_refresh_token(db, user)
        
        db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_plain,
            token_type="bearer",
            user={
                "public_id": user.public_id,
                "auth_provider": user.auth_provider,
                "email": user.email,
                "phone": user.phone
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Apple authentication failed: {str(e)}"
        )


@router.post("/otp/start", response_model=OTPStartResponse)
async def otp_start(
    payload: OTPStartRequest,
    db: Session = Depends(get_db),
):
    """
    Start phone OTP flow: generate and send OTP code.
    Priority 3.
    """
    # Import here to avoid circular dependencies
    from ..services.otp_service import OTPService
    
    try:
        otp_sent = await OTPService.send_otp(db, payload.phone)
        return OTPStartResponse(otp_sent=otp_sent)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP send failed: {str(e)}"
        )


@router.post("/otp/verify", response_model=TokenResponse)
async def otp_verify(
    payload: OTPVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Verify OTP code and authenticate user.
    Creates user if phone number is new.
    """
    # Import here to avoid circular dependencies
    from ..services.otp_service import OTPService
    
    try:
        # Verify OTP
        phone = await OTPService.verify_otp(db, payload.phone, payload.code)
        
        # Find or create user by phone
        user = db.query(User).filter(User.phone == phone).first()
        
        if not user:
            # Create new user
            import uuid
            user = User(
                public_id=str(uuid.uuid4()),
                phone=phone,
                auth_provider="phone",
                is_active=True
            )
            db.add(user)
            db.flush()
            db.add(UserPreferences(user_id=user.id))
            db.commit()
            db.refresh(user)
        
        # Create tokens
        access_token = create_access_token(user.public_id, auth_provider=user.auth_provider)
        refresh_token_plain, refresh_token_model = RefreshTokenService.create_refresh_token(db, user)
        
        db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_plain,
            token_type="bearer",
            user={
                "public_id": user.public_id,
                "auth_provider": user.auth_provider,
                "email": user.email,
                "phone": user.phone
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP verification failed: {str(e)}"
        )


# ============================================
# Dev Mode Endpoints
# ============================================

@router.post("/dev/login", response_model=TokenResponse)
async def dev_login(
    db: Session = Depends(get_db),
):
    """
    Dev mode login - automatically logs in as dev@nerava.local user.
    Available in DEMO_MODE or when running on localhost (for development convenience).
    """
    # Allow dev login in DEMO_MODE or when running locally
    # Check multiple conditions to be permissive for development
    # Try to get region safely (may not exist in all config classes)
    region = getattr(settings, 'region', None) or getattr(settings, 'REGION', None) or "local"
    
    is_localhost = (
        settings.ENV == "dev" or 
        settings.ENV == "local" or
        settings.ENV.lower() == "dev" or
        settings.ENV.lower() == "local" or
        "localhost" in str(settings.FRONTEND_URL).lower() or 
        "127.0.0.1" in str(settings.FRONTEND_URL).lower() or
        (region and (region == "local" or str(region).lower() == "local"))
    )
    
    # Log for debugging
    import logging
    logger = logging.getLogger("nerava")
    region = getattr(settings, 'region', None) or getattr(settings, 'REGION', None) or "unknown"
    logger.info(f"Dev login attempt - DEMO_MODE: {settings.DEMO_MODE}, is_localhost: {is_localhost}, ENV: {settings.ENV}, region: {region}, FRONTEND_URL: {settings.FRONTEND_URL}")
    
    # Always allow in dev/local environments, or if DEMO_MODE is enabled
    if not settings.DEMO_MODE and not is_localhost:
        logger.warning("Dev login rejected - not in DEMO_MODE and not localhost")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dev login endpoint not available"
        )
    
    logger.info("Dev login allowed - proceeding with authentication")
    
    try:
        # Find or create dev user
        dev_email = "dev@nerava.local"
        # Try to find by email first (for existing dev users)
        user = db.query(User).filter(User.email == dev_email).first()
        
        # If not found by email, try by auth_provider + provider_sub
        if not user:
            user = db.query(User).filter(
                User.auth_provider == "dev",
                User.provider_sub == "dev-user-001"
            ).first()
        
        if not user:
            # Create dev user
            import uuid
            logger.info("Creating new dev user")
            user = User(
                public_id=str(uuid.uuid4()),
                email=dev_email,
                auth_provider="dev",
                provider_sub="dev-user-001",  # Unique identifier for dev user
                is_active=True,
                password_hash=None  # Explicitly set to None for OAuth/dev users
            )
            db.add(user)
            db.flush()
            
            # Create user preferences
            try:
                preferences = UserPreferences(user_id=user.id)
                db.add(preferences)
            except Exception as pref_error:
                logger.warning(f"Could not create user preferences (may already exist): {pref_error}")
            
            db.commit()
            db.refresh(user)
            logger.info(f"Created dev user: {user.public_id}")
        else:
            logger.info(f"Found existing dev user: {user.public_id}")
        
        # Create tokens
        access_token = create_access_token(user.public_id, auth_provider=user.auth_provider)
        refresh_token_plain, refresh_token_model = RefreshTokenService.create_refresh_token(db, user)
        
        db.commit()
        
        logger.info("Dev login successful - tokens created")
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_plain,
            token_type="bearer",
            user={
                "public_id": user.public_id,
                "auth_provider": user.auth_provider,
                "email": user.email,
                "phone": user.phone
            }
        )
    except Exception as e:
        logger.error(f"Dev login error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dev login failed: {str(e)}"
        )


# ============================================
# Legacy Endpoints (behind DEMO_MODE flag)
# ============================================

@router.post("/register")
def register_legacy(payload, db: Session = Depends(get_db)):
    """Legacy registration endpoint - only available in DEMO_MODE"""
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available"
        )
    # Keep old implementation for demo mode
    from ..schemas import Token, UserCreate
    from ..core.security import hash_password, create_access_token
    
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        return Token(access_token=create_access_token(existing.public_id))
    
    import uuid
    user = User(
        public_id=str(uuid.uuid4()),
        email=payload.email,
        password_hash=hash_password(payload.password)
    )
    db.add(user)
    db.flush()
    db.add(UserPreferences(user_id=user.id))
    db.commit()
    return Token(access_token=create_access_token(user.public_id))


@router.post("/login")
def login_legacy(form, db: Session = Depends(get_db)):
    """Legacy login endpoint - only available in DEMO_MODE"""
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not available"
        )
    # Keep old implementation for demo mode
    from ..schemas import Token
    from ..core.security import verify_password, create_access_token
    
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return Token(access_token=create_access_token(user.public_id))
