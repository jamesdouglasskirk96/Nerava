"""
Tesla Connection model for OAuth tokens and vehicle data.

Stores user's Tesla OAuth credentials and linked vehicle information.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import relationship
from ..db import Base


def _uuid_str():
    return str(uuid.uuid4())


class TeslaConnection(Base):
    """Tesla OAuth connection and vehicle data."""
    __tablename__ = "tesla_connections"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # OAuth tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    token_expires_at = Column(DateTime, nullable=False)

    # Tesla account info
    tesla_user_id = Column(String(100), nullable=True)

    # Primary vehicle (can have multiple, but one primary for verification)
    vehicle_id = Column(String(100), nullable=True)  # Tesla's vehicle ID
    vin = Column(String(17), nullable=True)
    vehicle_name = Column(String(100), nullable=True)
    vehicle_model = Column(String(50), nullable=True)  # e.g., "Model 3", "Model Y"

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("idx_tesla_connection_user", "user_id"),
        Index("idx_tesla_connection_vehicle", "vehicle_id"),
    )


class EVVerificationCode(Base):
    """EV verification codes generated when user enters merchant geofence while charging."""
    __tablename__ = "ev_verification_codes"

    id = Column(String(36), primary_key=True, default=_uuid_str)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tesla_connection_id = Column(String(36), ForeignKey("tesla_connections.id"), nullable=True)

    # Code format: EV-XXXX (4 alphanumeric characters)
    code = Column(String(10), unique=True, nullable=False, index=True)

    # Context
    charger_id = Column(String(100), nullable=True)
    merchant_place_id = Column(String(255), nullable=True)
    merchant_name = Column(String(255), nullable=True)

    # Verification data at time of code generation
    charging_verified = Column(Boolean, default=False)
    battery_level = Column(Integer, nullable=True)  # Percentage
    charge_rate_kw = Column(Integer, nullable=True)

    # Location at verification
    lat = Column(String(20), nullable=True)
    lng = Column(String(20), nullable=True)

    # Status: 'active', 'redeemed', 'expired'
    status = Column(String(20), default='active', nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    redeemed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    tesla_connection = relationship("TeslaConnection", foreign_keys=[tesla_connection_id])

    __table_args__ = (
        Index("idx_ev_code_user_status", "user_id", "status"),
    )
