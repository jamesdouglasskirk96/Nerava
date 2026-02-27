#!/usr/bin/env python3
"""
Check if charger data is sparse and seed from NREL + Overpass if needed.
Designed to run in background during container startup.
"""
import os
import sys
import asyncio
import logging
import time

sys.path.insert(0, '/app')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_if_needed")

MIN_CHARGERS = 100  # Trigger bulk seed if fewer than this


def main():
    from sqlalchemy import create_engine, text

    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.info("DATABASE_URL not set, skipping seed check")
        return

    engine = create_engine(database_url)

    # Check current charger count
    with engine.connect() as conn:
        try:
            result = conn.execute(text("SELECT COUNT(*) FROM chargers"))
            count = result.scalar()
        except Exception:
            logger.info("chargers table doesn't exist yet, skipping")
            return

    logger.info(f"Current charger count: {count}")
    if count >= MIN_CHARGERS:
        logger.info(f"Already have {count} chargers, no seeding needed")
        return

    # --- Seed chargers from NREL ---
    logger.info("=== Starting bulk charger seed from NREL ===")
    start = time.time()
    try:
        from scripts.seed_chargers_bulk import seed_chargers
        from app.db import SessionLocal

        db = SessionLocal()
        try:
            result = asyncio.run(seed_chargers(db))
            elapsed = time.time() - start
            logger.info(f"Charger seed complete in {elapsed:.0f}s: {result}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Charger seeding failed: {e}")
        import traceback
        traceback.print_exc()

    # --- Seed merchants from Overpass (depends on chargers) ---
    logger.info("=== Starting merchant seed from Overpass ===")
    start = time.time()
    try:
        from scripts.seed_merchants_free import seed_merchants
        from app.db import SessionLocal

        db = SessionLocal()
        try:
            result = asyncio.run(seed_merchants(db))
            elapsed = time.time() - start
            logger.info(f"Merchant seed complete in {elapsed:.0f}s: {result}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Merchant seeding failed: {e}")
        import traceback
        traceback.print_exc()

    logger.info("=== Seeding complete ===")


if __name__ == "__main__":
    main()
