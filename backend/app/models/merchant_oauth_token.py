"""
MerchantOAuthToken model — stores encrypted OAuth tokens for merchant Google Business Profile access.
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from ..db import Base
from ..core.uuid_type import UUIDType


class MerchantOAuthToken(Base):
    __tablename__ = "merchant_oauth_tokens"

    id = Column(UUIDType(), primary_key=True)
    merchant_account_id = Column(String, ForeignKey("merchant_accounts.id"), nullable=False, index=True)
    provider = Column(String, nullable=False, default="google_gbp")

    # Encrypted via core.token_encryption
    access_token_encrypted = Column(Text, nullable=True)
    refresh_token_encrypted = Column(Text, nullable=True)
    token_expiry = Column(DateTime, nullable=True)
    scopes = Column(String, nullable=True)

    # Google Business Profile specific
    gbp_account_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)

    __table_args__ = (
        Index("uq_merchant_oauth_account_provider", "merchant_account_id", "provider", unique=True),
    )
