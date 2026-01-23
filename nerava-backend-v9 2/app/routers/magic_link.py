"""
Magic Link Authentication Router
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.services.magic_link_service import (
    generate_magic_link_token,
    consume_magic_link_token,
)
from app.core.security import create_access_token
from app.models import User

router = APIRouter(prefix="/v1/magic", tags=["magic-link"])


class MagicLinkRequest(BaseModel):
    phone: str
    exclusive_session_id: str
    merchant_id: str
    charger_id: str


class MagicLinkResponse(BaseModel):
    token: str
    link: str
    expires_in_minutes: int = 30


@router.post("/generate", response_model=MagicLinkResponse)
async def generate_magic_link(
    request: MagicLinkRequest,
    db: Session = Depends(get_db),
):
    """
    Generate a magic link for SMS authentication.
    """
    token = generate_magic_link_token(
        phone=request.phone,
        exclusive_session_id=request.exclusive_session_id,
        merchant_id=request.merchant_id,
        charger_id=request.charger_id,
    )

    # Build the magic link URL
    base_url = "https://app.nerava.network"
    link = f"{base_url}/magic?token={token}"

    return MagicLinkResponse(
        token=token,
        link=link,
        expires_in_minutes=30,
    )


@router.get("/verify")
async def verify_magic_link(
    token: str = Query(..., description="Magic link token"),
    db: Session = Depends(get_db),
):
    """
    Verify magic link and redirect to exclusive pass.
    This is called when user clicks the SMS link.
    """
    data = consume_magic_link_token(token)

    if not data:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired magic link"
        )

    # Find or create user by phone
    phone = data["phone"]
    user = db.query(User).filter(User.phone == phone).first()

    if not user:
        # Create new user for this phone
        user = User(phone=phone)
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate JWT access token
    # Use public_id for JWT subject (external identifier)
    access_token = create_access_token(subject=str(user.public_id))

    # Redirect to app with token and exclusive info
    redirect_url = (
        f"https://app.nerava.network/exclusive/{data['merchant_id']}"
        f"?token={access_token}"
        f"&session={data['exclusive_session_id']}"
        f"&charger={data['charger_id']}"
    )

    return RedirectResponse(url=redirect_url)

