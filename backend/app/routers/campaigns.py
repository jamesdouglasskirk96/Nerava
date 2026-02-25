"""
Campaigns Router — Sponsor/admin campaign management.

CRUD for campaigns, grant listing, budget management.
Used by the campaign portal (console.nerava.network).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..db import get_db
from ..dependencies.domain import get_current_user
from ..models.user import User
from ..models.campaign import Campaign
from ..models.session_event import IncentiveGrant, SessionEvent
from ..services.campaign_service import CampaignService

router = APIRouter(prefix="/v1/campaigns", tags=["campaigns"])


# --- Request/Response Schemas ---

class CampaignRulesInput(BaseModel):
    charger_ids: Optional[List[str]] = None
    charger_networks: Optional[List[str]] = None
    zone_ids: Optional[List[str]] = None
    geo_center_lat: Optional[float] = None
    geo_center_lng: Optional[float] = None
    geo_radius_m: Optional[int] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    days_of_week: Optional[List[int]] = None
    min_duration_minutes: Optional[int] = 15
    max_duration_minutes: Optional[int] = None
    min_power_kw: Optional[float] = None
    connector_types: Optional[List[str]] = None
    driver_session_count_min: Optional[int] = None
    driver_session_count_max: Optional[int] = None
    driver_allowlist: Optional[List[str]] = None


class CampaignCapsInput(BaseModel):
    per_day: Optional[int] = None
    per_campaign: Optional[int] = None
    per_charger: Optional[int] = None


class CreateCampaignRequest(BaseModel):
    sponsor_name: str
    sponsor_email: Optional[str] = None
    sponsor_logo_url: Optional[str] = None
    sponsor_type: Optional[str] = None
    name: str
    description: Optional[str] = None
    campaign_type: str = "custom"
    priority: int = 100
    budget_cents: int
    cost_per_session_cents: int
    max_sessions: Optional[int] = None
    start_date: str  # ISO format
    end_date: Optional[str] = None
    auto_renew: bool = False
    auto_renew_budget_cents: Optional[int] = None
    rules: Optional[CampaignRulesInput] = None
    caps: Optional[CampaignCapsInput] = None


class UpdateCampaignRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    priority: Optional[int] = None
    budget_cents: Optional[int] = None
    cost_per_session_cents: Optional[int] = None
    max_sessions: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    auto_renew: Optional[bool] = None
    auto_renew_budget_cents: Optional[int] = None
    rules: Optional[CampaignRulesInput] = None
    caps: Optional[CampaignCapsInput] = None


# --- Endpoints ---

@router.post("/")
async def create_campaign(
    req: CreateCampaignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new campaign (draft status)."""
    if not current_user.admin_role:
        raise HTTPException(status_code=403, detail="Admin access required")

    start_date = datetime.fromisoformat(req.start_date)
    end_date = datetime.fromisoformat(req.end_date) if req.end_date else None

    campaign = CampaignService.create_campaign(
        db,
        sponsor_name=req.sponsor_name,
        sponsor_email=req.sponsor_email,
        sponsor_logo_url=req.sponsor_logo_url,
        sponsor_type=req.sponsor_type,
        name=req.name,
        description=req.description,
        campaign_type=req.campaign_type,
        priority=req.priority,
        budget_cents=req.budget_cents,
        cost_per_session_cents=req.cost_per_session_cents,
        start_date=start_date,
        end_date=end_date,
        rules=req.rules.model_dump() if req.rules else None,
        caps=req.caps.model_dump() if req.caps else None,
        created_by_user_id=current_user.id,
    )
    return {"campaign": _campaign_to_dict(campaign)}


@router.get("/")
async def list_campaigns(
    status: Optional[str] = None,
    sponsor_name: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List campaigns. Admin sees all, sponsors see their own."""
    campaigns = CampaignService.list_campaigns(
        db,
        sponsor_name=sponsor_name,
        status=status,
        limit=limit,
        offset=offset,
    )
    return {
        "campaigns": [_campaign_to_dict(c) for c in campaigns],
        "count": len(campaigns),
    }


@router.get("/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get campaign details."""
    campaign = CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"campaign": _campaign_to_dict(campaign)}


@router.put("/{campaign_id}")
async def update_campaign(
    campaign_id: str,
    req: UpdateCampaignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a draft/paused campaign."""
    if not current_user.admin_role:
        raise HTTPException(status_code=403, detail="Admin access required")

    update_data = req.model_dump(exclude_none=True)

    # Flatten rules into rule_ columns
    if "rules" in update_data:
        rules = update_data.pop("rules")
        if rules:
            for key, val in rules.items():
                update_data[f"rule_{key}"] = val

    # Flatten caps
    if "caps" in update_data:
        caps = update_data.pop("caps")
        if caps:
            if caps.get("per_day") is not None:
                update_data["max_grants_per_driver_per_day"] = caps["per_day"]
            if caps.get("per_campaign") is not None:
                update_data["max_grants_per_driver_per_campaign"] = caps["per_campaign"]
            if caps.get("per_charger") is not None:
                update_data["max_grants_per_driver_per_charger"] = caps["per_charger"]

    # Parse dates
    if "start_date" in update_data:
        update_data["start_date"] = datetime.fromisoformat(update_data["start_date"])
    if "end_date" in update_data:
        update_data["end_date"] = datetime.fromisoformat(update_data["end_date"])

    try:
        campaign = CampaignService.update_campaign(db, campaign_id, **update_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"campaign": _campaign_to_dict(campaign)}


@router.post("/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a draft campaign."""
    if not current_user.admin_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        campaign = CampaignService.activate_campaign(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"campaign": _campaign_to_dict(campaign)}


@router.post("/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause an active campaign."""
    if not current_user.admin_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        campaign = CampaignService.pause_campaign(db, campaign_id, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"campaign": _campaign_to_dict(campaign)}


@router.post("/{campaign_id}/resume")
async def resume_campaign(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resume a paused campaign."""
    if not current_user.admin_role:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        campaign = CampaignService.resume_campaign(db, campaign_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return {"campaign": _campaign_to_dict(campaign)}


@router.get("/{campaign_id}/grants")
async def list_campaign_grants(
    campaign_id: str,
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List grants for a campaign."""
    campaign = CampaignService.get_campaign(db, campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    grants = (
        db.query(IncentiveGrant)
        .filter(IncentiveGrant.campaign_id == campaign_id)
        .order_by(IncentiveGrant.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    total = (
        db.query(IncentiveGrant)
        .filter(IncentiveGrant.campaign_id == campaign_id)
        .count()
    )

    return {
        "grants": [_grant_to_dict(g, db) for g in grants],
        "total": total,
        "count": len(grants),
    }


@router.get("/{campaign_id}/budget")
async def get_campaign_budget(
    campaign_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get campaign budget status."""
    budget = CampaignService.check_budget(db, campaign_id)
    if not budget:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return budget


# --- Charger utilization endpoint (for Charger Explorer) ---

@router.get("/utilization/chargers")
async def get_charger_utilization(
    charger_ids: Optional[str] = None,  # comma-separated
    since_days: int = Query(default=30, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get session counts per charger for utilization dashboard."""
    from sqlalchemy import func
    from datetime import timedelta

    since = datetime.utcnow() - timedelta(days=since_days)
    query = (
        db.query(
            SessionEvent.charger_id,
            func.count(SessionEvent.id).label("total_sessions"),
            func.count(func.distinct(SessionEvent.driver_user_id)).label("unique_drivers"),
            func.avg(SessionEvent.duration_minutes).label("avg_duration_minutes"),
        )
        .filter(
            SessionEvent.session_start >= since,
            SessionEvent.session_end.is_not(None),
            SessionEvent.charger_id.is_not(None),
        )
        .group_by(SessionEvent.charger_id)
    )

    if charger_ids:
        ids = [c.strip() for c in charger_ids.split(",")]
        query = query.filter(SessionEvent.charger_id.in_(ids))

    rows = query.all()
    return {
        "chargers": [
            {
                "charger_id": row.charger_id,
                "total_sessions": row.total_sessions,
                "unique_drivers": row.unique_drivers,
                "avg_duration_minutes": round(row.avg_duration_minutes, 1) if row.avg_duration_minutes else 0,
            }
            for row in rows
        ]
    }


# --- Helpers ---

def _campaign_to_dict(c: Campaign) -> dict:
    return {
        "id": c.id,
        "sponsor_name": c.sponsor_name,
        "sponsor_email": c.sponsor_email,
        "sponsor_logo_url": c.sponsor_logo_url,
        "sponsor_type": c.sponsor_type,
        "name": c.name,
        "description": c.description,
        "campaign_type": c.campaign_type,
        "status": c.status,
        "priority": c.priority,
        "budget_cents": c.budget_cents,
        "spent_cents": c.spent_cents,
        "cost_per_session_cents": c.cost_per_session_cents,
        "max_sessions": c.max_sessions,
        "sessions_granted": c.sessions_granted,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "auto_renew": c.auto_renew,
        "auto_renew_budget_cents": c.auto_renew_budget_cents,
        "max_grants_per_driver_per_day": c.max_grants_per_driver_per_day,
        "max_grants_per_driver_per_campaign": c.max_grants_per_driver_per_campaign,
        "max_grants_per_driver_per_charger": c.max_grants_per_driver_per_charger,
        "rules": {
            "charger_ids": c.rule_charger_ids,
            "charger_networks": c.rule_charger_networks,
            "zone_ids": c.rule_zone_ids,
            "geo_center_lat": c.rule_geo_center_lat,
            "geo_center_lng": c.rule_geo_center_lng,
            "geo_radius_m": c.rule_geo_radius_m,
            "time_start": c.rule_time_start,
            "time_end": c.rule_time_end,
            "days_of_week": c.rule_days_of_week,
            "min_duration_minutes": c.rule_min_duration_minutes,
            "max_duration_minutes": c.rule_max_duration_minutes,
            "min_power_kw": c.rule_min_power_kw,
            "connector_types": c.rule_connector_types,
            "driver_session_count_min": c.rule_driver_session_count_min,
            "driver_session_count_max": c.rule_driver_session_count_max,
            "driver_allowlist": c.rule_driver_allowlist,
        },
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _grant_to_dict(g: IncentiveGrant, db: Session) -> dict:
    session = db.query(SessionEvent).filter(SessionEvent.id == g.session_event_id).first()
    return {
        "id": g.id,
        "session_event_id": g.session_event_id,
        "campaign_id": g.campaign_id,
        "driver_user_id": g.driver_user_id,
        "amount_cents": g.amount_cents,
        "status": g.status,
        "granted_at": g.granted_at.isoformat() if g.granted_at else None,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "charger_id": session.charger_id if session else None,
        "duration_minutes": session.duration_minutes if session else None,
    }
