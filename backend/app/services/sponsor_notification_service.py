"""
Sponsor Notification Pipeline

Delivers contextually triggered push notifications to drivers during active
charging sessions. Handles campaign matching, budget decrement, impression
tracking, and per-driver rate limiting.
"""
import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from sqlalchemy.orm import Session

from app.models.sponsor_campaign import SponsorCampaign, SponsorImpression, SponsorDriverLimit

logger = logging.getLogger(__name__)

MAX_SPONSOR_PER_SESSION = 1
MAX_SPONSOR_PER_WEEK = 3


def _hash_driver_id(driver_id: int) -> str:
    return hashlib.sha256(str(driver_id).encode()).hexdigest()[:16]


def _current_week_start() -> str:
    now = datetime.utcnow()
    monday = now - timedelta(days=now.weekday())
    return monday.strftime("%Y-%m-%d")


def match_campaigns_for_session(
    db: Session,
    cluster_id: Optional[str],
    vehicle_type: Optional[str] = None,
    session_minutes: int = 0,
    trigger_type: str = "session_start",
) -> List[SponsorCampaign]:
    """Find active campaigns matching session context."""
    query = db.query(SponsorCampaign).filter(
        SponsorCampaign.status == "active",
        SponsorCampaign.trigger_type == trigger_type,
        SponsorCampaign.budget_remaining > SponsorCampaign.cost_per_impression,
    )

    campaigns = query.all()
    matched = []

    for campaign in campaigns:
        # Check min session time
        if session_minutes < campaign.target_min_session_minutes:
            continue

        # Check cluster targeting
        targets = campaign.target_clusters or []
        if targets and cluster_id and cluster_id not in targets:
            continue

        # Check vehicle type targeting
        vehicle_targets = campaign.target_vehicle_types or []
        if vehicle_targets and vehicle_type and vehicle_type not in vehicle_targets:
            continue

        matched.append(campaign)

    return matched


def can_deliver_to_driver(db: Session, driver_id: int, session_id: str) -> bool:
    """Check per-driver rate limits: max 1/session, max 3/week."""
    driver_hash = _hash_driver_id(driver_id)

    # Check session limit
    session_impression = db.query(SponsorImpression).filter(
        SponsorImpression.session_id == session_id,
        SponsorImpression.driver_id_hash == driver_hash,
    ).first()
    if session_impression:
        return False

    # Check weekly limit
    week_start = _current_week_start()
    limit_record = db.query(SponsorDriverLimit).filter(
        SponsorDriverLimit.driver_id_hash == driver_hash,
        SponsorDriverLimit.week_start == week_start,
    ).first()
    if limit_record and limit_record.impression_count >= MAX_SPONSOR_PER_WEEK:
        return False

    return True


def deliver_sponsor_notification(
    db: Session,
    campaign: SponsorCampaign,
    driver_id: int,
    session_id: str,
    cluster_id: Optional[str] = None,
) -> Optional[SponsorImpression]:
    """Deliver a sponsor notification and track the impression.

    Returns the impression record if delivered, None if skipped.
    """
    if not can_deliver_to_driver(db, driver_id, session_id):
        return None

    driver_hash = _hash_driver_id(driver_id)

    # Atomic budget decrement
    if campaign.budget_remaining < campaign.cost_per_impression:
        return None

    campaign.budget_remaining -= campaign.cost_per_impression
    campaign.impressions_served += 1

    if campaign.budget_remaining <= 0:
        campaign.status = "completed"

    # Create impression
    impression = SponsorImpression(
        id=uuid.uuid4(),
        campaign_id=str(campaign.id),
        driver_id_hash=driver_hash,
        cluster_id=cluster_id,
        session_id=session_id,
        delivered_at=datetime.utcnow(),
    )
    db.add(impression)

    # Update weekly limit
    week_start = _current_week_start()
    limit_record = db.query(SponsorDriverLimit).filter(
        SponsorDriverLimit.driver_id_hash == driver_hash,
        SponsorDriverLimit.week_start == week_start,
    ).first()
    if limit_record:
        limit_record.impression_count += 1
    else:
        db.add(SponsorDriverLimit(
            driver_id_hash=driver_hash,
            week_start=week_start,
            impression_count=1,
        ))

    db.flush()

    # Send push notification
    try:
        from app.services.push_service import send_push_to_user
        send_push_to_user(
            db, driver_id,
            title=campaign.message_title,
            body=campaign.message_body,
            data={
                "type": "sponsor_notification",
                "campaign_id": str(campaign.id),
                "impression_id": str(impression.id),
                "cta_url": campaign.cta_url or "",
                "cta_label": campaign.cta_label or "",
            },
        )
    except Exception as e:
        logger.warning("Failed to send sponsor push to driver %d: %s", driver_id, e)

    return impression


def record_click(db: Session, impression_id: str) -> bool:
    """Record that a sponsor notification was tapped."""
    impression = db.query(SponsorImpression).filter(
        SponsorImpression.id == impression_id
    ).first()
    if not impression or impression.clicked_at:
        return False

    impression.clicked_at = datetime.utcnow()

    # Increment campaign clicks
    campaign = db.query(SponsorCampaign).filter(
        SponsorCampaign.id == impression.campaign_id
    ).first()
    if campaign:
        campaign.clicks += 1

    db.flush()
    return True


def process_demand_spike_campaigns(db: Session, spikes: List[Dict]):
    """Process demand_spike trigger campaigns when spikes are detected."""
    for spike in spikes:
        cluster_id = spike["cluster_id"]
        campaigns = match_campaigns_for_session(
            db, cluster_id=cluster_id, trigger_type="demand_spike"
        )
        if campaigns:
            logger.info(
                "Found %d demand_spike campaigns for cluster %s",
                len(campaigns), cluster_id,
            )
            # Actual delivery happens when individual drivers poll
