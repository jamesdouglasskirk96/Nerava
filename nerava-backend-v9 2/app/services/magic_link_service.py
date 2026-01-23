"""
Magic Link Service - Generate and validate magic link tokens for SMS auth
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

# In-memory store for demo (use Redis in production)
_magic_links: dict = {}

TOKEN_EXPIRY_MINUTES = 30


def generate_magic_link_token(
    phone: str,
    exclusive_session_id: str,
    merchant_id: str,
    charger_id: str,
) -> str:
    """
    Generate a magic link token for SMS authentication.
    Returns the token to include in the SMS link.
    """
    # Generate secure random token
    token = secrets.token_urlsafe(32)

    # Store token data with expiry
    _magic_links[token] = {
        "phone": phone,
        "exclusive_session_id": exclusive_session_id,
        "merchant_id": merchant_id,
        "charger_id": charger_id,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRY_MINUTES),
        "used": False,
    }

    return token


def validate_magic_link_token(token: str) -> Optional[dict]:
    """
    Validate a magic link token.
    Returns token data if valid, None if invalid/expired.
    """
    if token not in _magic_links:
        return None

    data = _magic_links[token]

    # Check expiry
    if datetime.utcnow() > data["expires_at"]:
        del _magic_links[token]
        return None

    # Check if already used
    if data["used"]:
        return None

    return data


def consume_magic_link_token(token: str) -> Optional[dict]:
    """
    Validate and consume a magic link token (one-time use).
    Returns token data if valid.
    """
    data = validate_magic_link_token(token)
    if data:
        _magic_links[token]["used"] = True
    return data


