"""
Merchant Flash Offer Trigger

When cluster_demand_spike events fire for clusters with nearby Nerava merchants:
- Finds active merchants within 500m
- Sends push to merchant contacts for ordering-enabled merchants
- Logs spike notifications
"""
import logging
import math
from datetime import datetime
from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from app.models.while_you_charge import Merchant, ChargerMerchant, Charger
from app.models.charger_intelligence import ClusterScore

logger = logging.getLogger(__name__)


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearby_merchants_for_cluster(
    db: Session, cluster_id: str, radius_m: float = 500
) -> List[Merchant]:
    """Find all active merchants within radius of a cluster centroid."""
    score = db.query(ClusterScore).filter(ClusterScore.cluster_id == cluster_id).first()
    if not score:
        return []

    lat, lng = score.centroid_lat, score.centroid_lng
    # Bounding box filter first (fast), then haversine (accurate)
    deg_offset = radius_m / 111_000  # rough meters-to-degrees
    merchants = db.query(Merchant).filter(
        Merchant.lat.between(lat - deg_offset, lat + deg_offset),
        Merchant.lng.between(lng - deg_offset, lng + deg_offset),
    ).all()

    return [
        m for m in merchants
        if _haversine_m(lat, lng, m.lat, m.lng) <= radius_m
    ]


def process_demand_spikes(db: Session, spikes: List[Dict]):
    """Process demand spike events: notify merchants near spiking clusters.

    For each spike:
    1. Find all active merchants within 500m of cluster
    2. For merchants with ordering_enabled: send push to merchant contact
    3. Log spike_notification_sent
    """
    for spike in spikes:
        cluster_id = spike["cluster_id"]
        occupancy_pct = spike["occupancy_pct"]

        merchants = find_nearby_merchants_for_cluster(db, cluster_id)
        ordering_merchants = [m for m in merchants if m.ordering_enabled]

        if not ordering_merchants:
            logger.info("No ordering-enabled merchants near cluster %s", cluster_id)
            continue

        # Get cluster name from first charger
        score = db.query(ClusterScore).filter(ClusterScore.cluster_id == cluster_id).first()
        charger_name = "nearby charger"
        if score and score.charger_ids:
            first_charger = db.query(Charger).filter(
                Charger.id == score.charger_ids[0]
            ).first()
            if first_charger:
                charger_name = first_charger.name

        driver_count = spike.get("nearby_merchant_count", 0)

        for merchant in ordering_merchants:
            _send_merchant_flash_notification(
                db, merchant, charger_name, driver_count, cluster_id, occupancy_pct
            )

        logger.info(
            "Flash offer notifications sent: cluster=%s merchants=%d occupancy=%.0f%%",
            cluster_id, len(ordering_merchants), occupancy_pct,
        )


def _send_merchant_flash_notification(
    db: Session,
    merchant: Merchant,
    charger_name: str,
    driver_count: int,
    cluster_id: str,
    occupancy_pct: float,
):
    """Send push/email notification to merchant about demand spike."""
    title = f"Demand spike at {charger_name}"
    body = f"{driver_count} EV drivers nearby. Activate a flash offer?"

    logger.info(
        "spike_notification_sent: merchant_id=%s cluster_id=%s occupancy_pct=%.0f",
        merchant.id, cluster_id, occupancy_pct,
    )

    # Send push to merchant's device tokens if available
    try:
        from app.models.domain import DomainMerchant
        domain_merchant = db.query(DomainMerchant).filter(
            DomainMerchant.google_place_id == merchant.place_id
        ).first()
        if domain_merchant and domain_merchant.owner_user_id:
            from app.services.push_service import send_push_to_user
            send_push_to_user(
                db, domain_merchant.owner_user_id,
                title=title,
                body=body,
                data={
                    "type": "flash_offer_prompt",
                    "cluster_id": cluster_id,
                    "merchant_id": merchant.id,
                    "occupancy_pct": str(occupancy_pct),
                },
            )
    except Exception as e:
        logger.warning("Failed to send flash offer push to merchant %s: %s", merchant.id, e)
