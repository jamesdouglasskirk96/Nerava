#!/usr/bin/env python3
"""
Seed known network pricing for chargers.

Sets approximate pricing_per_kwh based on network_name.
Marks pricing_source = 'network_average'.

Usage:
    cd backend && python -m scripts.seed_charger_pricing
    cd backend && python -m scripts.seed_charger_pricing --dry-run
"""
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal
from app.models.while_you_charge import Charger

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Approximate per-kWh pricing by network (US average, 2025-2026)
NETWORK_PRICING = {
    "tesla": 0.42,
    "supercharger": 0.42,
    "chargepoint": 0.35,
    "evgo": 0.39,
    "electrify america": 0.45,
    "blink": 0.49,
    "flo": 0.35,
    "semaconnect": 0.30,
    "volta": 0.00,  # Free (ad-supported)
    "greenlots": 0.32,
    "shell recharge": 0.42,
    "bp pulse": 0.40,
    "ev connect": 0.30,
}


def main():
    parser = argparse.ArgumentParser(description="Seed charger pricing from network averages")
    parser.add_argument("--dry-run", action="store_true", help="Don't commit changes")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        chargers = db.query(Charger).filter(
            Charger.pricing_per_kwh.is_(None),
            Charger.network_name.isnot(None),
        ).all()

        updated = 0
        for charger in chargers:
            network_lower = charger.network_name.lower().strip()

            price = None
            for key, value in NETWORK_PRICING.items():
                if key in network_lower:
                    price = value
                    break

            if price is not None:
                charger.pricing_per_kwh = price
                charger.pricing_source = "network_average"
                updated += 1
                logger.info(f"  {charger.name}: ${price:.2f}/kWh ({charger.network_name})")

        if args.dry_run:
            logger.info(f"DRY RUN: Would update {updated} chargers out of {len(chargers)}")
            db.rollback()
        else:
            db.commit()
            logger.info(f"Updated pricing for {updated} chargers")

    except Exception as e:
        db.rollback()
        logger.error(f"Script failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
