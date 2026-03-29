"""
Sponsor Campaign models for contextually triggered push notifications.

Sponsors create campaigns that deliver push notifications to drivers
during active charging sessions based on cluster, vehicle type, and timing rules.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from ..db import Base
from ..core.uuid_type import UUIDType

try:
    from sqlalchemy import JSON
except Exception:
    JSON = SQLITE_JSON


class SponsorCampaign(Base):
    """Sponsor campaign for push notification delivery during charging sessions."""
    __tablename__ = "sponsor_campaigns"

    id = Column(UUIDType(), primary_key=True)
    sponsor_name = Column(String, nullable=False)
    sponsor_category = Column(String(20), nullable=True)  # dealership|energy|insurance|hardware|other

    message_title = Column(String(50), nullable=False)
    message_body = Column(String(100), nullable=False)
    cta_label = Column(String(30), nullable=True)  # "Learn More", "Get Quote"
    cta_url = Column(String(500), nullable=True)

    # Targeting
    target_clusters = Column(JSON, default=list)  # array of cluster_ids (empty = all)
    target_vehicle_types = Column(JSON, default=list)  # array (empty = all)
    target_min_session_minutes = Column(Integer, default=5, nullable=False)

    # Budget
    budget_total = Column(Float, nullable=False)
    budget_remaining = Column(Float, nullable=False)
    cost_per_impression = Column(Float, nullable=False)  # CPM / 1000

    # Performance
    impressions_served = Column(Integer, default=0, nullable=False)
    clicks = Column(Integer, default=0, nullable=False)

    # Status and trigger
    status = Column(String(20), default="active", nullable=False)  # active|paused|completed
    trigger_type = Column(String(20), default="session_start", nullable=False)  # session_start|demand_spike|time_based|manual

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_sponsor_campaign_status", "status"),
        Index("idx_sponsor_campaign_trigger", "trigger_type"),
    )


class SponsorImpression(Base):
    """Individual sponsor notification impression record."""
    __tablename__ = "sponsor_impressions"

    id = Column(UUIDType(), primary_key=True)
    campaign_id = Column(String, nullable=False, index=True)
    driver_id_hash = Column(String, nullable=False)  # hashed driver ID for privacy
    cluster_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    delivered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    clicked_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_impression_campaign", "campaign_id", "delivered_at"),
        Index("idx_impression_driver", "driver_id_hash", "delivered_at"),
    )


class SponsorDriverLimit(Base):
    """Track per-driver weekly impression limits (max 3/week)."""
    __tablename__ = "sponsor_driver_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id_hash = Column(String, nullable=False, index=True)
    week_start = Column(String(10), nullable=False)  # YYYY-MM-DD of Monday
    impression_count = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        Index("idx_driver_limit_week", "driver_id_hash", "week_start", unique=True),
    )
