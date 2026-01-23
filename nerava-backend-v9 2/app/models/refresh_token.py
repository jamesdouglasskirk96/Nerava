from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects import sqlite
from ..db import Base
from ..core.uuid_type import UUIDType
UUID_TYPE = UUIDType  # Alias for backward compatibility


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID_TYPE, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked = Column(Boolean, nullable=False, default=False, index=True)
    replaced_by = Column(UUID_TYPE, ForeignKey("refresh_tokens.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", backref="refresh_tokens")


