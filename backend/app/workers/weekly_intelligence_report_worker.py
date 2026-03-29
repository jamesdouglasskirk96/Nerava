"""
Weekly Intelligence Report Worker

Generates and delivers cluster intelligence reports every Monday at 7am local time.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from app.db import SessionLocal
from app.services.cluster_intelligence_report import generate_weekly_reports, deliver_reports

logger = logging.getLogger(__name__)


async def weekly_intelligence_report_job():
    """Run every Monday at 7am UTC. Generates and delivers merchant intelligence reports."""
    while True:
        try:
            now = datetime.utcnow()
            # Find next Monday 7am UTC
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and now.hour >= 7:
                days_until_monday = 7
            next_monday = now.replace(hour=7, minute=0, second=0, microsecond=0) + timedelta(days=days_until_monday)
            sleep_seconds = (next_monday - now).total_seconds()
            logger.info("Next weekly report in %.1f hours", sleep_seconds / 3600)
            await asyncio.sleep(max(sleep_seconds, 60))

            db = SessionLocal()
            try:
                reports = generate_weekly_reports(db)
                if reports:
                    deliver_reports(db, reports)
                    logger.info("Weekly intelligence reports generated and delivered: %d", len(reports))
                else:
                    logger.info("No reports to generate this week")
            finally:
                db.close()
        except Exception as e:
            logger.error("Weekly intelligence report error: %s", e)
            await asyncio.sleep(3600)  # Retry in 1 hour
