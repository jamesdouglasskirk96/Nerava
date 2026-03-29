"""
Sponsor Campaign Management Router

CRUD for sponsor campaigns + impression tracking + simple dashboard.
"""
import csv
import io
import uuid
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.sponsor_campaign import SponsorCampaign, SponsorImpression

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/sponsor-campaigns", tags=["sponsor-campaigns"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class SponsorCampaignCreate(BaseModel):
    sponsor_name: str
    sponsor_category: Optional[str] = None
    message_title: str
    message_body: str
    cta_label: Optional[str] = None
    cta_url: Optional[str] = None
    target_clusters: Optional[List[str]] = None
    target_vehicle_types: Optional[List[str]] = None
    target_min_session_minutes: int = 5
    budget_total: float
    cost_per_impression: float
    trigger_type: str = "session_start"


class SponsorCampaignUpdate(BaseModel):
    message_title: Optional[str] = None
    message_body: Optional[str] = None
    cta_label: Optional[str] = None
    cta_url: Optional[str] = None
    target_clusters: Optional[List[str]] = None
    target_vehicle_types: Optional[List[str]] = None
    target_min_session_minutes: Optional[int] = None
    status: Optional[str] = None


class SponsorCampaignResponse(BaseModel):
    id: str
    sponsor_name: str
    sponsor_category: Optional[str]
    message_title: str
    message_body: str
    cta_label: Optional[str]
    cta_url: Optional[str]
    target_clusters: Optional[list]
    target_vehicle_types: Optional[list]
    target_min_session_minutes: int
    budget_total: float
    budget_remaining: float
    cost_per_impression: float
    impressions_served: int
    clicks: int
    ctr: float
    status: str
    trigger_type: str
    created_at: str


class SponsorDashboard(BaseModel):
    campaigns: List[SponsorCampaignResponse]
    total_impressions: int
    total_clicks: int
    total_budget_spent: float


class ImpressionClickRequest(BaseModel):
    impression_id: str


# ─── Endpoints ───────────────────────────────────────────────────────────────

@router.post("", response_model=SponsorCampaignResponse)
def create_campaign(req: SponsorCampaignCreate, db: Session = Depends(get_db)):
    """Create a new sponsor campaign."""
    campaign = SponsorCampaign(
        id=uuid.uuid4(),
        sponsor_name=req.sponsor_name,
        sponsor_category=req.sponsor_category,
        message_title=req.message_title,
        message_body=req.message_body,
        cta_label=req.cta_label,
        cta_url=req.cta_url,
        target_clusters=req.target_clusters or [],
        target_vehicle_types=req.target_vehicle_types or [],
        target_min_session_minutes=req.target_min_session_minutes,
        budget_total=req.budget_total,
        budget_remaining=req.budget_total,
        cost_per_impression=req.cost_per_impression,
        trigger_type=req.trigger_type,
        status="active",
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return _to_response(campaign)


@router.get("", response_model=SponsorDashboard)
def list_campaigns(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all sponsor campaigns with dashboard metrics."""
    query = db.query(SponsorCampaign)
    if status:
        query = query.filter(SponsorCampaign.status == status)
    campaigns = query.order_by(SponsorCampaign.created_at.desc()).all()

    total_impressions = sum(c.impressions_served for c in campaigns)
    total_clicks = sum(c.clicks for c in campaigns)
    total_spent = sum(c.budget_total - c.budget_remaining for c in campaigns)

    return SponsorDashboard(
        campaigns=[_to_response(c) for c in campaigns],
        total_impressions=total_impressions,
        total_clicks=total_clicks,
        total_budget_spent=total_spent,
    )


@router.get("/{campaign_id}", response_model=SponsorCampaignResponse)
def get_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Get a specific sponsor campaign."""
    campaign = db.query(SponsorCampaign).filter(SponsorCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _to_response(campaign)


@router.patch("/{campaign_id}", response_model=SponsorCampaignResponse)
def update_campaign(campaign_id: str, req: SponsorCampaignUpdate, db: Session = Depends(get_db)):
    """Update a sponsor campaign (edit or pause/resume)."""
    campaign = db.query(SponsorCampaign).filter(SponsorCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    for field, value in req.dict(exclude_unset=True).items():
        setattr(campaign, field, value)
    db.commit()
    db.refresh(campaign)
    return _to_response(campaign)


@router.post("/click")
def record_impression_click(req: ImpressionClickRequest, db: Session = Depends(get_db)):
    """Record that a sponsor notification was tapped."""
    from app.services.sponsor_notification_service import record_click
    success = record_click(db, req.impression_id)
    db.commit()
    return {"success": success}


@router.get("/{campaign_id}/impressions/export")
def export_impressions_csv(campaign_id: str, db: Session = Depends(get_db)):
    """Export impression logs as CSV."""
    campaign = db.query(SponsorCampaign).filter(SponsorCampaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    impressions = db.query(SponsorImpression).filter(
        SponsorImpression.campaign_id == campaign_id
    ).order_by(SponsorImpression.delivered_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["impression_id", "driver_hash", "cluster_id", "session_id", "delivered_at", "clicked_at"])
    for imp in impressions:
        writer.writerow([
            str(imp.id), imp.driver_id_hash, imp.cluster_id or "",
            imp.session_id or "", imp.delivered_at.isoformat(),
            imp.clicked_at.isoformat() if imp.clicked_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=impressions_{campaign_id}.csv"},
    )


def _to_response(c: SponsorCampaign) -> SponsorCampaignResponse:
    ctr = (c.clicks / c.impressions_served * 100) if c.impressions_served > 0 else 0.0
    return SponsorCampaignResponse(
        id=str(c.id),
        sponsor_name=c.sponsor_name,
        sponsor_category=c.sponsor_category,
        message_title=c.message_title,
        message_body=c.message_body,
        cta_label=c.cta_label,
        cta_url=c.cta_url,
        target_clusters=c.target_clusters,
        target_vehicle_types=c.target_vehicle_types,
        target_min_session_minutes=c.target_min_session_minutes,
        budget_total=c.budget_total,
        budget_remaining=c.budget_remaining,
        cost_per_impression=c.cost_per_impression,
        impressions_served=c.impressions_served,
        clicks=c.clicks,
        ctr=round(ctr, 2),
        status=c.status,
        trigger_type=c.trigger_type,
        created_at=c.created_at.isoformat(),
    )
