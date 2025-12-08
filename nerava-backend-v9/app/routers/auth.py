from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from ..db import get_db
from ..models import User, UserPreferences
from ..schemas import Token, UserCreate
from ..core.security import hash_password, verify_password, create_access_token
from ..core.config import settings
from ..core.email_sender import get_email_sender

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register", response_model=Token)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        # Issue a token anyway (idempotent) to reduce friction
        return Token(access_token=create_access_token(str(existing.id)))
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.flush()
    db.add(UserPreferences(user_id=user.id))
    db.commit()
    return Token(access_token=create_access_token(str(user.id)))

@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return Token(access_token=create_access_token(str(user.id)))

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise ValueError("missing sub")
        return int(sub)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


# ============================================
# Magic Link Auth Endpoints
# ============================================

class MagicLinkRequest(BaseModel):
    email: EmailStr


class MagicLinkVerify(BaseModel):
    token: str


def create_magic_link_token(user_id: int, email: str) -> str:
    """Create a time-limited magic link token (expires in 15 minutes)"""
    from datetime import datetime, timedelta
    
    expires_delta = timedelta(minutes=15)
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "sub": str(user_id),
        "email": email,
        "purpose": "magic_link",
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/magic_link/request")
async def request_magic_link(
    payload: MagicLinkRequest,
    db: Session = Depends(get_db),
):
    """
    Request a magic link for email-only authentication.
    
    - Looks up or creates user (without password)
    - Generates time-limited token
    - Sends email with magic link (console logger for dev)
    """
    email = payload.email.lower().strip()
    
    # Lookup or create user (without password requirement)
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user with placeholder password (magic-link only)
        # Use a dummy password hash - user can set real password later if needed
        placeholder_password = "magic-link-user-no-password"
        user = User(email=email, password_hash=hash_password(placeholder_password))
        db.add(user)
        db.flush()
        db.add(UserPreferences(user_id=user.id))
        db.commit()
        db.refresh(user)
    
    # Generate magic link token
    magic_token = create_magic_link_token(user.id, email)
    
    # Get frontend URL from settings (default to localhost:8001/app for mobile)
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    # If frontend_url doesn't include /app/, add it for mobile app hash routing
    if "/app" not in frontend_url:
        frontend_url = f"{frontend_url}/app"
    magic_link_url = f"{frontend_url}/#/auth/magic?token={magic_token}"
    
    # Send email via email sender abstraction
    email_sender = get_email_sender()
    email_sender.send_email(
        to_email=email,
        subject="Sign in to Nerava",
        body_text=f"Click this link to sign in to Nerava:\n\n{magic_link_url}\n\nThis link expires in 15 minutes.\n\nIf you didn't request this link, you can safely ignore this email.",
        body_html=f"""
        <html>
        <body>
            <h2>Sign in to Nerava</h2>
            <p>Click this link to sign in:</p>
            <p><a href="{magic_link_url}">{magic_link_url}</a></p>
            <p><small>This link expires in 15 minutes.</small></p>
            <p><small>If you didn't request this link, you can safely ignore this email.</small></p>
        </body>
        </html>
        """,
    )
    
    # Return success (don't expose token in response)
    return {"message": "Magic link sent to your email", "email": email}


@router.post("/magic_link/verify", response_model=Token)
async def verify_magic_link(
    payload: MagicLinkVerify,
    db: Session = Depends(get_db),
):
    """
    Verify a magic link token and create a session.
    
    - Verifies token signature and expiration
    - Checks token purpose is "magic_link"
    - Creates access token (same format as password login)
    - Returns Token for session creation
    """
    token = payload.token
    
    try:
        # Decode and verify token
        payload_data = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        
        # Verify token purpose
        if payload_data.get("purpose") != "magic_link":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token purpose",
            )
        
        # Get user ID from token
        user_id_str = payload_data.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token: missing user ID",
            )
        
        user_id = int(user_id_str)
        
        # Verify user exists
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        # Create access token (same as password login)
        access_token = create_access_token(str(user.id))
        
        return Token(access_token=access_token)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Magic link has expired. Please request a new one.",
        )
    except jwt.JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid magic link token: {str(e)}",
        )
