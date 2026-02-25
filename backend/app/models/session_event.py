"""
Session Event & Incentive Grant Models

SessionEvent: The atomic unit — a verified charging session.
IncentiveGrant: Links a completed session to a campaign grant.

Key design decisions per review:
- Grants only created on session END (or min duration threshold crossed)
- One session = one grant max (highest priority campaign wins)
- idempotency_key on IncentiveGrant for atomic Nova grants
- ended_reason and quality_score fields for anti-fraud
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, Index, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from ..db import Base
from ..core.uuid_type import UUIDType

try:
    from sqlalchemy import JSON
except Exception:
    JSON = SQLITE_JSON


class SessionEvent(Base):
    """
    A verified EV charging session.

    Created when a driver starts charging (via Tesla API polling or webhook).
    Updated when session ends. Incentive evaluation happens on session end.
    """
    __tablename__ = "session_events"

    id = Column(UUIDType(), primary_key=True)
    driver_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # --- Charger info ---
    charger_id = Column(String, ForeignKey("chargers.id"), nullable=True, index=True)
    charger_network = Column(String, nullable=True)   # "Tesla", "ChargePoint", etc.
    zone_id = Column(String, nullable=True, index=True)
    connector_type = Column(String, nullable=True)     # "CCS", "Tesla", etc.
    power_kw = Column(Float, nullable=True)

    # --- Timing ---
    session_start = Column(DateTime, nullable=False, index=True)
    session_end = Column(DateTime, nullable=True)       # null = still charging
    duration_minutes = Column(Integer, nullable=True)   # computed on session_end

    # --- Energy ---
    kwh_delivered = Column(Float, nullable=True)

    # --- Source & verification ---
    source = Column(String, nullable=False, default="tesla_api")
    # Sources: tesla_api, chargepoint_api, evgo_api, ocpp, manual, demo
    source_session_id = Column(String, nullable=True)   # external ID from provider
    verified = Column(Boolean, default=False, nullable=False)
    verification_method = Column(String, nullable=True)
    # Methods: api_polling, webhook, manual, admin

    # --- Location ---
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # --- Vehicle telemetry ---
    battery_start_pct = Column(Integer, nullable=True)
    battery_end_pct = Column(Integer, nullable=True)
    vehicle_id = Column(String, nullable=True)
    vehicle_vin = Column(String, nullable=True)

    # --- Anti-fraud (per review) ---
    ended_reason = Column(String, nullable=True)
    # Reasons: unplugged, full, moved, timeout, unknown
    quality_score = Column(Integer, nullable=True)
    # 0-100, computed by anti-fraud heuristics. null = not yet scored.

    # --- Metadata ---
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    session_metadata = Column("metadata", JSON, nullable=True)

    # --- Relationships ---
    driver = relationship("User", foreign_keys=[driver_user_id])
    grant = relationship("IncentiveGrant", back_populates="session_event", uselist=False)

    __table_args__ = (
        Index("ix_session_events_driver_start", "driver_user_id", "session_start"),
        Index("ix_session_events_charger_start", "charger_id", "session_start"),
        UniqueConstraint("source", "source_session_id", name="uq_session_source"),
    )


class IncentiveGrant(Base):
    """
    Links a completed session event to a campaign grant.

    One session can earn at most one campaign grant (highest priority wins).
    Grant is created when session ends and meets minimum duration.
    """
    __tablename__ = "incentive_grants"

    id = Column(UUIDType(), primary_key=True)
    session_event_id = Column(UUIDType(), ForeignKey("session_events.id"), nullable=False, index=True)
    campaign_id = Column(UUIDType(), ForeignKey("campaigns.id"), nullable=False, index=True)
    driver_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    amount_cents = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="pending")
    # Statuses: pending, granted, clawed_back

    # Link to Nova ledger
    nova_transaction_id = Column(UUIDType(), ForeignKey("nova_transactions.id"), nullable=True)

    # Idempotency (per review: must be present for atomic Nova grants)
    idempotency_key = Column(String, nullable=False, unique=True, index=True)

    granted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    grant_metadata = Column("metadata", JSON, nullable=True)

    # --- Relationships ---
    session_event = relationship("SessionEvent", back_populates="grant")
    campaign = relationship("Campaign", back_populates="grants", foreign_keys=[campaign_id])
    driver = relationship("User", foreign_keys=[driver_user_id])
    nova_transaction = relationship("NovaTransaction", foreign_keys=[nova_transaction_id])

    __table_args__ = (
        # One grant per session (no stacking in MVP)
        UniqueConstraint("session_event_id", name="uq_one_grant_per_session"),
        Index("ix_incentive_grants_campaign", "campaign_id", "created_at"),
        Index("ix_incentive_grants_driver", "driver_user_id", "created_at"),
    )
