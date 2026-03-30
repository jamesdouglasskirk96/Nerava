"""
Background worker that collects charger availability from TomTom every 5 minutes.

Runs as an asyncio task inside the FastAPI process. Lightweight: ~10 API calls per cycle.
Stores snapshots in charger_availability_snapshots for historical pattern analysis.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
POLL_INTERVAL_SECONDS = 300  # 5 minutes

# Austin Domain area ChargePoint stations with TomTom availability IDs
# These are the initial 10 stations to monitor. More can be added via admin API.
MONITORED_STATIONS: List[Dict[str, str]] = [
    {"charger_id": "tomtom_domain_1", "name": "ChargePoint @ 11505 Domain Dr", "avail_id": "a70292d8-fde5-41eb-b9c0-61829cda02c0"},
    {"charger_id": "tomtom_domain_2", "name": "ChargePoint @ 11811 Domain Dr", "avail_id": "3b359414-28af-48c6-9554-29bd34aee61c"},
    {"charger_id": "tomtom_domain_3", "name": "ChargePoint @ 11600 Alterra Pkwy", "avail_id": "b0c3386d-89ba-4b46-95a8-58b0f6a44b44"},
    {"charger_id": "tomtom_domain_4", "name": "ChargePoint @ 3004 Palm Way (A)", "avail_id": "623d43b7-7768-4739-add0-4f9f859fbff7"},
    {"charger_id": "tomtom_domain_5", "name": "ChargePoint @ 3004 Palm Way (B)", "avail_id": "1283fbc0-6385-4b8b-8432-7ba103a7e5cf"},
    {"charger_id": "tomtom_domain_6", "name": "ChargePoint @ 3000 Kramer Ln", "avail_id": "b1e3f371-8538-4839-b940-d50673105ba4"},
    {"charger_id": "tomtom_domain_7", "name": "ChargePoint @ 11500 N MoPac", "avail_id": "edfce375-5a14-4943-ac46-32c582963b3b"},
    {"charger_id": "tomtom_domain_8", "name": "ChargePoint @ 11800 Alterra Pkwy", "avail_id": "3c75c68f-934b-40fa-926b-98d699cd7c47"},
    {"charger_id": "tomtom_domain_9", "name": "ChargePoint @ 11920 Domain Dr", "avail_id": "91e497ef-bbb5-476b-885f-2d220ee9e4de"},
    {"charger_id": "tomtom_domain_10", "name": "ChargePoint @ Domain Dr", "avail_id": "3f909562-f9b1-4377-890d-92265c55442c"},
]


async def _fetch_availability(avail_id: str) -> Optional[Dict[str, Any]]:
    """Fetch availability from TomTom for a single station."""
    import httpx

    url = f"https://api.tomtom.com/search/2/chargingAvailability.json?chargingAvailability={avail_id}&key={TOMTOM_API_KEY}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(f"[AvailCollector] TomTom returned {resp.status_code} for {avail_id}")
            return None
    except Exception as e:
        logger.error(f"[AvailCollector] Failed to fetch {avail_id}: {e}")
        return None


def _parse_availability(data: Dict[str, Any]) -> Dict[str, Any]:
    """Parse TomTom availability response into summary."""
    connectors = data.get("connectors", [])
    total = 0
    available = 0
    occupied = 0
    out_of_service = 0
    details = []

    for c in connectors:
        count = c.get("total", 0)
        current = c.get("availability", {}).get("current", {})
        a = current.get("available", 0)
        o = current.get("occupied", 0)
        oos = current.get("outOfService", 0)
        power_levels = c.get("availability", {}).get("perPowerLevel", [])

        total += count
        available += a
        occupied += o
        out_of_service += oos

        details.append({
            "type": c.get("type"),
            "total": count,
            "available": a,
            "occupied": o,
            "out_of_service": oos,
            "power_kw": power_levels[0].get("powerKW") if power_levels else None,
        })

    return {
        "total_ports": total,
        "available_ports": available,
        "occupied_ports": occupied,
        "out_of_service_ports": out_of_service,
        "connector_details": details,
    }


async def _collect_once():
    """Run one collection cycle for all monitored stations."""
    from app.db import SessionLocal
    from app.models.charger_availability import ChargerAvailabilitySnapshot

    if not TOMTOM_API_KEY:
        logger.warning("[AvailCollector] TOMTOM_API_KEY not set, skipping collection")
        return

    db = SessionLocal()
    collected = 0
    try:
        for station in MONITORED_STATIONS:
            data = await _fetch_availability(station["avail_id"])
            if not data:
                continue

            parsed = _parse_availability(data)
            snapshot = ChargerAvailabilitySnapshot(
                id=str(uuid.uuid4()),
                charger_id=station["charger_id"],
                tomtom_availability_id=station["avail_id"],
                source="tomtom",
                total_ports=parsed["total_ports"],
                available_ports=parsed["available_ports"],
                occupied_ports=parsed["occupied_ports"],
                out_of_service_ports=parsed["out_of_service_ports"],
                connector_details=parsed["connector_details"],
                recorded_at=datetime.utcnow(),
            )
            db.add(snapshot)
            collected += 1

        db.commit()
        logger.info(f"[AvailCollector] Collected {collected}/{len(MONITORED_STATIONS)} stations")
    except Exception as e:
        db.rollback()
        logger.error(f"[AvailCollector] Collection failed: {e}")
    finally:
        db.close()


async def run_collector():
    """Main loop: collect availability every 5 minutes."""
    logger.info(f"[AvailCollector] Starting — monitoring {len(MONITORED_STATIONS)} stations every {POLL_INTERVAL_SECONDS}s")
    while True:
        try:
            await _collect_once()
        except Exception as e:
            logger.error(f"[AvailCollector] Unexpected error: {e}")
        await asyncio.sleep(POLL_INTERVAL_SECONDS)
