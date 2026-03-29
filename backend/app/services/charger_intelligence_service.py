"""
Charger Intelligence Service

Background data service that enriches chargers with real-time and historical intelligence
from TomTom, NEVI, NREL, and OpenChargeMap. Computes cluster scores nightly.
"""
import re
import math
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.charger_intelligence import (
    ChargerAvailability,
    ClusterScore,
    ChargerAvailabilityHistory,
)
from app.models.while_you_charge import Charger, Merchant

logger = logging.getLogger(__name__)

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
NEVI_API_BASE = os.getenv("NEVI_API_BASE", "https://developer.nrel.gov/api/alt-fuel-stations/v1")
NREL_API_KEY = os.getenv("NREL_API_KEY", "")
CLUSTER_RADIUS_M = 500
HISTORY_RETENTION_DAYS = 90


# ─── Pricing Parser ─────────────────────────────────────────────────────────

def parse_pricing(raw_text: Optional[str]) -> Dict[str, Any]:
    """Parse pricing from raw text into structured fields.

    Returns dict with: pricing_per_kwh, session_fee, pricing_model
    """
    if not raw_text:
        return {"pricing_per_kwh": None, "session_fee": None, "pricing_model": None}

    text = raw_text.lower().strip()

    if "free" in text:
        return {"pricing_per_kwh": 0.0, "session_fee": 0.0, "pricing_model": "per_kwh"}

    pricing_per_kwh = None
    session_fee = None
    pricing_model = None

    # Match "$X.XX/kWh"
    kwh_match = re.search(r'\$?(\d+\.?\d*)\s*/?\s*kwh', text)
    if kwh_match:
        pricing_per_kwh = float(kwh_match.group(1))
        pricing_model = "per_kwh"

    # Match "$X.XX/min"
    min_match = re.search(r'\$?(\d+\.?\d*)\s*/?\s*min', text)
    if min_match and not pricing_per_kwh:
        pricing_per_kwh = float(min_match.group(1))
        pricing_model = "per_minute"

    # Match "$X.XX session fee"
    fee_match = re.search(r'\$?(\d+\.?\d*)\s*session\s*fee', text)
    if fee_match:
        session_fee = float(fee_match.group(1))
        if pricing_model:
            pricing_model = "mixed"
        else:
            pricing_model = "session_flat"

    return {
        "pricing_per_kwh": pricing_per_kwh,
        "session_fee": session_fee,
        "pricing_model": pricing_model,
    }


# ─── TomTom Integration ─────────────────────────────────────────────────────

def fetch_tomtom_availability(charger_id: str, lat: float, lng: float) -> Optional[Dict]:
    """Fetch charging availability from TomTom EV Charging Availability API.

    Endpoint: https://api.tomtom.com/search/2/chargingAvailability.json
    Free tier, no credit card required.
    """
    if not TOMTOM_API_KEY:
        return None

    try:
        import httpx
        url = f"https://api.tomtom.com/search/2/chargingAvailability.json"
        params = {
            "key": TOMTOM_API_KEY,
            "chargingPark": f"{lat},{lng}",
        }
        resp = httpx.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            connectors = data.get("connectors", [])
            available = sum(c.get("availability", {}).get("current", {}).get("available", 0) for c in connectors)
            total = sum(c.get("availability", {}).get("current", {}).get("total", 0) for c in connectors)
            status = "available" if available > 0 else "occupied" if total > 0 else "unknown"
            return {
                "tomtom_id": data.get("id"),
                "availability_status": status,
                "available_ports": available,
                "total_ports": total,
            }
    except Exception as e:
        logger.warning("TomTom API error for charger %s: %s", charger_id, e)
    return None


# ─── NEVI Integration ────────────────────────────────────────────────────────

def fetch_nevi_status(charger_id: str, external_id: Optional[str] = None) -> Optional[Dict]:
    """Fetch NEVI station status from AFDC API."""
    if not NREL_API_KEY or not external_id:
        return None

    try:
        import httpx
        url = f"{NEVI_API_BASE}/{external_id}.json"
        params = {"api_key": NREL_API_KEY}
        resp = httpx.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json().get("alt_fuel_station", {})
            return {
                "nevi_funded": data.get("nrel_network") == "NEVI",
                "nevi_station_id": str(data.get("id", "")),
                "real_time_status": data.get("ev_connector_types"),
            }
    except Exception as e:
        logger.warning("NEVI API error for charger %s: %s", charger_id, e)
    return None


# ─── Availability Update ────────────────────────────────────────────────────

def update_charger_availability(db: Session, charger_id: str, **kwargs) -> ChargerAvailability:
    """Create or update availability record for a charger."""
    record = db.query(ChargerAvailability).filter(
        ChargerAvailability.charger_id == charger_id
    ).first()

    if not record:
        record = ChargerAvailability(charger_id=charger_id)
        db.add(record)

    for key, value in kwargs.items():
        if hasattr(record, key) and value is not None:
            setattr(record, key, value)

    record.updated_at = datetime.utcnow()
    db.flush()
    return record


def persist_nrel_pricing(db: Session, charger_id: str, raw_text: str):
    """Persist NREL pricing data that was previously discarded."""
    parsed = parse_pricing(raw_text)
    update_charger_availability(
        db, charger_id,
        pricing_raw_text=raw_text,
        pricing_per_kwh=parsed["pricing_per_kwh"],
        session_fee=parsed["session_fee"],
        pricing_model=parsed["pricing_model"],
        pricing_last_updated=datetime.utcnow(),
    )


def persist_ocm_pricing(db: Session, charger_id: str, usage_cost: str):
    """Persist OpenChargeMap pricing data that was previously discarded."""
    parsed = parse_pricing(usage_cost)
    update_charger_availability(
        db, charger_id,
        ocm_usage_cost=usage_cost,
        ocm_usage_cost_parsed=parsed["pricing_per_kwh"],
        ocm_last_updated=datetime.utcnow(),
    )


# ─── Cluster Scoring ────────────────────────────────────────────────────────

def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in meters between two lat/lng points."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _geohash_simple(lat: float, lng: float, precision: int = 6) -> str:
    """Simple geohash for cluster ID. Not a full geohash — just a grid key."""
    lat_bin = round(lat * (10 ** precision))
    lng_bin = round(lng * (10 ** precision))
    return f"g{lat_bin}_{lng_bin}"


def build_clusters(db: Session) -> List[Dict]:
    """Build charger clusters (all chargers within 500m of each other).

    Uses greedy clustering: pick unassigned charger, find all within 500m, form cluster.
    """
    chargers = db.query(Charger).all()
    assigned = set()
    clusters = []

    for charger in chargers:
        if charger.id in assigned:
            continue
        cluster_members = [charger]
        assigned.add(charger.id)

        for other in chargers:
            if other.id in assigned:
                continue
            dist = _haversine_m(charger.lat, charger.lng, other.lat, other.lng)
            if dist <= CLUSTER_RADIUS_M:
                cluster_members.append(other)
                assigned.add(other.id)

        # Compute centroid
        avg_lat = sum(c.lat for c in cluster_members) / len(cluster_members)
        avg_lng = sum(c.lng for c in cluster_members) / len(cluster_members)

        clusters.append({
            "charger_ids": [c.id for c in cluster_members],
            "centroid_lat": avg_lat,
            "centroid_lng": avg_lng,
            "cluster_id": _geohash_simple(avg_lat, avg_lng),
            "total_ports": sum(c.num_evse or 1 for c in cluster_members),
        })

    return clusters


def compute_cluster_scores(db: Session):
    """Recompute cluster scores nightly. Called by background job."""
    clusters = build_clusters(db)
    now = datetime.utcnow()

    for cluster_data in clusters:
        cluster_id = cluster_data["cluster_id"]
        charger_ids = cluster_data["charger_ids"]

        # Get availability data for cluster chargers
        avail_records = db.query(ChargerAvailability).filter(
            ChargerAvailability.charger_id.in_(charger_ids)
        ).all()

        # Compute occupancy
        total_ports = cluster_data["total_ports"]
        occupied = sum(
            (a.total_ports or 0) - (a.available_ports or 0)
            for a in avail_records
            if a.total_ports and a.available_ports is not None
        )
        occupancy_pct = (occupied / total_ports * 100) if total_ports > 0 else 0.0

        # Count nearby Nerava merchants (ordering_enabled within 500m)
        lat, lng = cluster_data["centroid_lat"], cluster_data["centroid_lng"]
        nearby_merchants = 0
        merchants = db.query(Merchant).filter(
            Merchant.ordering_enabled == True,
            Merchant.lat.between(lat - 0.005, lat + 0.005),
            Merchant.lng.between(lng - 0.005, lng + 0.005),
        ).all()
        for m in merchants:
            if _haversine_m(lat, lng, m.lat, m.lng) <= CLUSTER_RADIUS_M:
                nearby_merchants += 1

        # Compute pricing tier from avg pricing
        avg_pricing = None
        pricing_records = [a for a in avail_records if a.pricing_per_kwh is not None]
        if pricing_records:
            avg_pricing = sum(a.pricing_per_kwh for a in pricing_records) / len(pricing_records)

        if avg_pricing is None:
            pricing_tier = None
        elif avg_pricing == 0:
            pricing_tier = "free"
        elif avg_pricing < 0.20:
            pricing_tier = "low"
        elif avg_pricing < 0.40:
            pricing_tier = "mid"
        else:
            pricing_tier = "high"

        # Compute tier score
        if occupancy_pct > 70 and nearby_merchants > 0:
            tier_score = 3
        elif occupancy_pct > 40:
            tier_score = 2
        else:
            tier_score = 1

        # Upsert cluster score
        score = db.query(ClusterScore).filter(ClusterScore.cluster_id == cluster_id).first()
        if not score:
            score = ClusterScore(cluster_id=cluster_id)
            db.add(score)

        score.charger_ids = charger_ids
        score.centroid_lat = lat
        score.centroid_lng = lng
        score.total_ports = total_ports
        score.avg_weekly_occupancy_pct = occupancy_pct
        score.nearby_nerava_merchants = nearby_merchants
        score.pricing_tier = pricing_tier
        score.tier_score = tier_score
        score.last_scored = now

    db.commit()
    logger.info("Cluster scores recomputed for %d clusters", len(clusters))
    return len(clusters)


def check_demand_spike(db: Session, cluster_id: str) -> Optional[Dict]:
    """Check if a cluster has transitioned from <60% to >80% occupancy.

    Returns spike event data if detected, None otherwise.
    """
    score = db.query(ClusterScore).filter(ClusterScore.cluster_id == cluster_id).first()
    if not score:
        return None

    # Check current live occupancy from availability records
    avail_records = db.query(ChargerAvailability).filter(
        ChargerAvailability.charger_id.in_(score.charger_ids or [])
    ).all()

    total = sum(a.total_ports or 0 for a in avail_records)
    occupied = sum((a.total_ports or 0) - (a.available_ports or 0) for a in avail_records
                   if a.total_ports and a.available_ports is not None)
    current_pct = (occupied / total * 100) if total > 0 else 0

    # Spike: was below 60% (weekly avg), now above 80%
    if score.avg_weekly_occupancy_pct < 60 and current_pct > 80:
        return {
            "cluster_id": cluster_id,
            "occupancy_pct": current_pct,
            "timestamp": datetime.utcnow().isoformat(),
            "nearby_merchant_count": score.nearby_nerava_merchants,
        }

    return None


def save_daily_snapshot(db: Session):
    """Save daily availability snapshot for all clusters. Retain 90 days."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    cutoff = (datetime.utcnow() - timedelta(days=HISTORY_RETENTION_DAYS)).strftime("%Y-%m-%d")

    # Purge old history
    db.query(ChargerAvailabilityHistory).filter(
        ChargerAvailabilityHistory.date < cutoff
    ).delete()

    scores = db.query(ClusterScore).all()
    for score in scores:
        existing = db.query(ChargerAvailabilityHistory).filter(
            ChargerAvailabilityHistory.cluster_id == score.cluster_id,
            ChargerAvailabilityHistory.date == today,
        ).first()
        if existing:
            continue

        snapshot = ChargerAvailabilityHistory(
            cluster_id=score.cluster_id,
            date=today,
            peak_occupancy_pct=score.avg_weekly_occupancy_pct,
            avg_occupancy_pct=score.avg_weekly_occupancy_pct,
            out_of_service_count=0,
            total_sessions_observed=0,
        )
        db.add(snapshot)

    db.commit()
    logger.info("Daily snapshots saved for %d clusters", len(scores))
