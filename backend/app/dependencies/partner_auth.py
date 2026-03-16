"""
Partner API authentication dependencies.

Authenticates partners via X-Partner-Key header containing a raw API key.
The key is SHA-256 hashed and matched against partner_api_keys.key_hash.
"""
import hashlib
import logging
from datetime import datetime
from typing import Callable, Tuple

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..models.partner import Partner, PartnerAPIKey

logger = logging.getLogger(__name__)


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def get_current_partner(
    x_partner_key: str = Header(None, alias="X-Partner-Key"),
    db: Session = Depends(get_db),
) -> Tuple[Partner, PartnerAPIKey]:
    """
    Validate X-Partner-Key header and return (Partner, PartnerAPIKey).
    Raises 401 if key is missing/invalid/expired or partner is not active.
    """
    if not x_partner_key:
        raise HTTPException(status_code=401, detail="Missing X-Partner-Key header")

    key_hash = _hash_key(x_partner_key)
    api_key = db.query(PartnerAPIKey).filter(
        PartnerAPIKey.key_hash == key_hash,
        PartnerAPIKey.is_active == True,
    ).first()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="API key expired")

    partner = db.query(Partner).filter(Partner.id == api_key.partner_id).first()
    if not partner or partner.status != "active":
        raise HTTPException(status_code=403, detail="Partner account not active")

    # Update last_used_at
    api_key.last_used_at = datetime.utcnow()
    db.commit()

    return (partner, api_key)


def require_partner_scope(scope: str) -> Callable:
    """
    Factory that returns a dependency checking the API key has the required scope.

    Usage:
        @router.post("/sessions", dependencies=[Depends(require_partner_scope("sessions:write"))])
    """
    def _check_scope(
        partner_and_key: Tuple[Partner, PartnerAPIKey] = Depends(get_current_partner),
    ) -> Tuple[Partner, PartnerAPIKey]:
        partner, api_key = partner_and_key
        if scope not in (api_key.scopes or []):
            raise HTTPException(
                status_code=403,
                detail=f"API key missing required scope: {scope}",
            )
        return (partner, api_key)

    return _check_scope
