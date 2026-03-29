"""
Charger Intelligence Background Workers

- availability_refresh_job: Polls TomTom every 3 min, NEVI every 60s
- nightly_cluster_scoring_job: Recomputes cluster scores and saves daily snapshot
- demand_spike_check_job: Checks for occupancy spikes that trigger notifications
"""
import logging
import asyncio
from datetime import datetime

from app.db import SessionLocal
from app.services.charger_intelligence_service import (
    fetch_tomtom_availability,
    fetch_nevi_status,
    update_charger_availability,
    compute_cluster_scores,
    save_daily_snapshot,
    check_demand_spike,
)
from app.models.while_you_charge import Charger
from app.models.charger_intelligence import ClusterScore

logger = logging.getLogger(__name__)


async def availability_refresh_job():
    """Poll TomTom and NEVI for charger availability. Runs every 3 minutes."""
    while True:
        try:
            db = SessionLocal()
            try:
                chargers = db.query(Charger).limit(500).all()
                updated = 0

                for charger in chargers:
                    # TomTom
                    tomtom_data = fetch_tomtom_availability(charger.id, charger.lat, charger.lng)
                    if tomtom_data:
                        update_charger_availability(
                            db, charger.id,
                            last_availability_update=datetime.utcnow(),
                            **tomtom_data,
                        )
                        updated += 1

                    # NEVI
                    nevi_data = fetch_nevi_status(charger.id, charger.external_id)
                    if nevi_data:
                        update_charger_availability(
                            db, charger.id,
                            last_nevi_update=datetime.utcnow(),
                            **nevi_data,
                        )

                db.commit()
                logger.info("Availability refresh: updated %d/%d chargers", updated, len(chargers))
            finally:
                db.close()
        except Exception as e:
            logger.error("Availability refresh error: %s", e)

        await asyncio.sleep(180)  # 3 minutes


async def nightly_cluster_scoring_job():
    """Recompute cluster scores and save daily snapshot. Runs at midnight UTC."""
    while True:
        try:
            now = datetime.utcnow()
            # Sleep until next midnight
            next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if now >= next_midnight:
                next_midnight = next_midnight.replace(day=now.day + 1)
            sleep_seconds = (next_midnight - now).total_seconds()
            await asyncio.sleep(max(sleep_seconds, 60))

            db = SessionLocal()
            try:
                count = compute_cluster_scores(db)
                save_daily_snapshot(db)
                logger.info("Nightly scoring complete: %d clusters", count)
            finally:
                db.close()
        except Exception as e:
            logger.error("Nightly cluster scoring error: %s", e)
            await asyncio.sleep(3600)  # Retry in 1 hour on failure


async def demand_spike_check_job():
    """Check all clusters for demand spikes. Runs every 5 minutes."""
    while True:
        try:
            db = SessionLocal()
            try:
                scores = db.query(ClusterScore).all()
                spikes = []

                for score in scores:
                    spike = check_demand_spike(db, score.cluster_id)
                    if spike:
                        spikes.append(spike)
                        logger.info(
                            "Demand spike detected: cluster=%s occupancy=%.0f%% merchants=%d",
                            spike["cluster_id"], spike["occupancy_pct"],
                            spike["nearby_merchant_count"],
                        )

                if spikes:
                    # Import here to avoid circular dependency
                    from app.services.merchant_flash_offer_service import process_demand_spikes
                    from app.services.sponsor_notification_service import process_demand_spike_campaigns
                    process_demand_spikes(db, spikes)
                    process_demand_spike_campaigns(db, spikes)
            finally:
                db.close()
        except Exception as e:
            logger.error("Demand spike check error: %s", e)

        await asyncio.sleep(300)  # 5 minutes
