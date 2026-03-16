"""
Partner Service — CRUD for partners and API key management.

Handles partner registration, API key generation (nrv_pk_ prefix),
and key validation.
"""
import hashlib
import logging
import secrets
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.partner import Partner, PartnerAPIKey

logger = logging.getLogger(__name__)

KEY_PREFIX = "nrv_pk_"


class PartnerService:

    @staticmethod
    def create_partner(
        db: Session,
        name: str,
        slug: str,
        partner_type: str,
        trust_tier: int = 3,
        contact_name: Optional[str] = None,
        contact_email: Optional[str] = None,
        webhook_url: Optional[str] = None,
        rate_limit_rpm: int = 60,
    ) -> Partner:
        partner = Partner(
            id=str(uuid.uuid4()),
            name=name,
            slug=slug,
            partner_type=partner_type,
            trust_tier=trust_tier,
            status="pending",
            contact_name=contact_name,
            contact_email=contact_email,
            webhook_url=webhook_url,
            rate_limit_rpm=rate_limit_rpm,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(partner)
        db.commit()
        db.refresh(partner)
        logger.info(f"Created partner '{name}' (slug={slug}, type={partner_type})")
        return partner

    @staticmethod
    def create_api_key(
        db: Session,
        partner_id: str,
        name: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> Tuple[PartnerAPIKey, str]:
        """
        Generate a new API key for a partner.
        Returns (PartnerAPIKey, plaintext_key). Plaintext is shown once only.
        """
        if scopes is None:
            scopes = ["sessions:write", "sessions:read", "grants:read", "campaigns:read"]

        raw_key = KEY_PREFIX + secrets.token_hex(16)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]

        api_key = PartnerAPIKey(
            id=str(uuid.uuid4()),
            partner_id=partner_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            name=name,
            scopes=scopes,
            is_active=True,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        logger.info(f"Created API key {key_prefix}... for partner {partner_id}")
        return (api_key, raw_key)

    @staticmethod
    def get_partner(db: Session, partner_id: str) -> Optional[Partner]:
        return db.query(Partner).filter(Partner.id == partner_id).first()

    @staticmethod
    def get_partner_by_slug(db: Session, slug: str) -> Optional[Partner]:
        return db.query(Partner).filter(Partner.slug == slug).first()

    @staticmethod
    def list_partners(
        db: Session,
        status: Optional[str] = None,
    ) -> List[Partner]:
        q = db.query(Partner)
        if status:
            q = q.filter(Partner.status == status)
        return q.order_by(Partner.created_at.desc()).all()

    @staticmethod
    def update_partner(db: Session, partner_id: str, **kwargs) -> Optional[Partner]:
        partner = db.query(Partner).filter(Partner.id == partner_id).first()
        if not partner:
            return None
        for key, val in kwargs.items():
            if hasattr(partner, key):
                setattr(partner, key, val)
        partner.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(partner)
        return partner

    @staticmethod
    def revoke_api_key(db: Session, key_id: str) -> bool:
        api_key = db.query(PartnerAPIKey).filter(PartnerAPIKey.id == key_id).first()
        if not api_key:
            return False
        api_key.is_active = False
        db.commit()
        logger.info(f"Revoked API key {api_key.key_prefix}...")
        return True

    @staticmethod
    def list_api_keys(db: Session, partner_id: str) -> List[PartnerAPIKey]:
        return db.query(PartnerAPIKey).filter(
            PartnerAPIKey.partner_id == partner_id,
        ).order_by(PartnerAPIKey.created_at.desc()).all()
