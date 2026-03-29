"""
Cluster Intelligence API endpoints.

Serves charger availability, cluster scores, and weekly merchant reports.
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.charger_intelligence import ChargerAvailability, ClusterScore, ChargerAvailabilityHistory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/intelligence", tags=["intelligence"])


class ChargerAvailabilityResponse(BaseModel):
    charger_id: str
    availability_status: Optional[str]
    available_ports: Optional[int]
    total_ports: Optional[int]
    pricing_per_kwh: Optional[float]
    pricing_model: Optional[str]
    nevi_funded: bool = False


class ClusterScoreResponse(BaseModel):
    cluster_id: str
    charger_ids: list
    centroid_lat: float
    centroid_lng: float
    total_ports: int
    avg_weekly_occupancy_pct: float
    peak_hour_start: Optional[int]
    peak_hour_end: Optional[int]
    nearby_nerava_merchants: int
    pricing_tier: Optional[str]
    tier_score: int
    last_scored: str


class HistoryEntry(BaseModel):
    date: str
    peak_occupancy_pct: Optional[float]
    avg_occupancy_pct: Optional[float]
    total_sessions_observed: int


@router.get("/chargers/{charger_id}/availability", response_model=ChargerAvailabilityResponse)
def get_charger_availability(charger_id: str, db: Session = Depends(get_db)):
    """Get real-time availability data for a charger."""
    record = db.query(ChargerAvailability).filter(
        ChargerAvailability.charger_id == charger_id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="No availability data for this charger")

    return ChargerAvailabilityResponse(
        charger_id=record.charger_id,
        availability_status=record.availability_status,
        available_ports=record.available_ports,
        total_ports=record.total_ports,
        pricing_per_kwh=record.pricing_per_kwh,
        pricing_model=record.pricing_model,
        nevi_funded=record.nevi_funded,
    )


@router.get("/clusters", response_model=List[ClusterScoreResponse])
def list_clusters(
    min_tier: int = Query(1, ge=1, le=3),
    db: Session = Depends(get_db),
):
    """List cluster scores, optionally filtered by minimum tier."""
    clusters = db.query(ClusterScore).filter(
        ClusterScore.tier_score >= min_tier
    ).order_by(ClusterScore.tier_score.desc()).all()

    return [
        ClusterScoreResponse(
            cluster_id=c.cluster_id,
            charger_ids=c.charger_ids or [],
            centroid_lat=c.centroid_lat,
            centroid_lng=c.centroid_lng,
            total_ports=c.total_ports,
            avg_weekly_occupancy_pct=c.avg_weekly_occupancy_pct,
            peak_hour_start=c.peak_hour_start,
            peak_hour_end=c.peak_hour_end,
            nearby_nerava_merchants=c.nearby_nerava_merchants,
            pricing_tier=c.pricing_tier,
            tier_score=c.tier_score,
            last_scored=c.last_scored.isoformat(),
        )
        for c in clusters
    ]


@router.get("/clusters/{cluster_id}/history", response_model=List[HistoryEntry])
def get_cluster_history(
    cluster_id: str,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Get daily availability history for a cluster."""
    from datetime import datetime, timedelta
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    entries = db.query(ChargerAvailabilityHistory).filter(
        ChargerAvailabilityHistory.cluster_id == cluster_id,
        ChargerAvailabilityHistory.date >= cutoff,
    ).order_by(ChargerAvailabilityHistory.date).all()

    return [
        HistoryEntry(
            date=e.date,
            peak_occupancy_pct=e.peak_occupancy_pct,
            avg_occupancy_pct=e.avg_occupancy_pct,
            total_sessions_observed=e.total_sessions_observed,
        )
        for e in entries
    ]


@router.get("/merchant-report/{merchant_place_id}")
def get_merchant_intelligence_report(merchant_place_id: str, db: Session = Depends(get_db)):
    """Get the latest intelligence report for a specific merchant."""
    from app.services.cluster_intelligence_report import generate_weekly_reports
    from app.models.while_you_charge import Merchant

    merchant = db.query(Merchant).filter(Merchant.place_id == merchant_place_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    # Generate on-demand report for this merchant
    reports = generate_weekly_reports(db)
    merchant_reports = [r for r in reports if r["merchant_place_id"] == merchant_place_id]

    if not merchant_reports:
        return {"message": "No cluster data available for this merchant yet", "reports": []}

    return {"reports": merchant_reports}
