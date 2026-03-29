"""
Charger Intelligence Data Layer models.

Stores real-time availability, pricing, cluster scores, and historical snapshots
sourced from TomTom, NEVI, NREL, and OpenChargeMap.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from ..db import Base

try:
    from sqlalchemy import JSON
except Exception:
    JSON = SQLITE_JSON


class ChargerAvailability(Base):
    """Real-time charger availability from TomTom and NEVI APIs."""
    __tablename__ = "charger_availability"

    id = Column(Integer, primary_key=True, autoincrement=True)
    charger_id = Column(String, nullable=False, index=True)

    # TomTom fields
    tomtom_id = Column(String, nullable=True, index=True)
    availability_status = Column(String(20), nullable=True)  # available|occupied|out_of_service|unknown
    available_ports = Column(Integer, nullable=True)
    total_ports = Column(Integer, nullable=True)
    last_availability_update = Column(DateTime, nullable=True)

    # NEVI fields
    nevi_funded = Column(Boolean, default=False, nullable=False, server_default="false")
    nevi_station_id = Column(String, nullable=True, index=True)
    real_time_status = Column(JSON, nullable=True)  # per NEVI spec
    last_nevi_update = Column(DateTime, nullable=True)

    # NREL pricing (previously discarded, now persisted)
    pricing_raw_text = Column(Text, nullable=True)
    pricing_per_kwh = Column(Float, nullable=True)
    session_fee = Column(Float, nullable=True)
    pricing_model = Column(String(20), nullable=True)  # per_kwh|per_minute|session_flat|mixed
    pricing_last_updated = Column(DateTime, nullable=True)

    # OpenChargeMap pricing
    ocm_usage_cost = Column(Text, nullable=True)  # raw string
    ocm_usage_cost_parsed = Column(Float, nullable=True)
    ocm_last_updated = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_charger_avail_charger", "charger_id"),
        Index("idx_charger_avail_tomtom", "tomtom_id"),
    )


class ClusterScore(Base):
    """Computed cluster intelligence scores for groups of nearby chargers."""
    __tablename__ = "cluster_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(String, unique=True, nullable=False, index=True)  # geohash of centroid
    charger_ids = Column(JSON, nullable=False, default=list)  # array of charger IDs
    centroid_lat = Column(Float, nullable=False)
    centroid_lng = Column(Float, nullable=False)

    total_ports = Column(Integer, default=0, nullable=False)
    avg_weekly_occupancy_pct = Column(Float, default=0.0, nullable=False)
    peak_hour_start = Column(Integer, nullable=True)  # 0-23
    peak_hour_end = Column(Integer, nullable=True)
    peak_day_of_week = Column(Integer, nullable=True)  # 0=Sunday

    nearby_nerava_merchants = Column(Integer, default=0, nullable=False)
    pricing_tier = Column(String(10), nullable=True)  # free|low|mid|high
    tier_score = Column(Integer, default=1, nullable=False)  # 1-3

    last_scored = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_cluster_score_tier", "tier_score"),
        Index("idx_cluster_score_location", "centroid_lat", "centroid_lng"),
    )


class ChargerAvailabilityHistory(Base):
    """Daily snapshots of cluster availability. Retained 90 days rolling."""
    __tablename__ = "charger_availability_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(String, nullable=False, index=True)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    peak_occupancy_pct = Column(Float, nullable=True)
    avg_occupancy_pct = Column(Float, nullable=True)
    out_of_service_count = Column(Integer, default=0, nullable=False)
    total_sessions_observed = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_avail_history_cluster_date", "cluster_id", "date", unique=True),
    )
