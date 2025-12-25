from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.dialects import sqlite
from ..db import Base

try:
    from sqlalchemy.dialects import postgresql
    UUID_TYPE = postgresql.UUID(as_uuid=False)
except Exception:
    UUID_TYPE = String(36)  # SQLite fallback


class OTPChallenge(Base):
    __tablename__ = "otp_challenges"
    
    id = Column(UUID_TYPE, primary_key=True)
    phone = Column(String, nullable=False, index=True)  # E.164 format
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    consumed = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)


