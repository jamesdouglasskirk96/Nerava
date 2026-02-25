#!/usr/bin/env python3
"""
Bulk seed US EV chargers from NREL AFDC API into the chargers table.

Uses the free NREL API (key already in nrel_client.py) to fetch all public
EV chargers by state. Upserts by external_id, batch commits every 500 rows.

Usage:
    # From backend/
    python -m scripts.seed_chargers_bulk                  # All states
    python -m scripts.seed_chargers_bulk --states VT NH   # Specific states
"""
import logging
import asyncio
import httpx
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

NREL_API_KEY = "rBv6VXOAQbJemI6xw2QbqjceK5QdNUta8MpT50mY"
NREL_BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"

ALL_STATES = [
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
]

# Map NREL ev_network values to logo URLs (free network logos)
NETWORK_LOGOS = {
    "Tesla": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Tesla_Motors.svg/120px-Tesla_Motors.svg.png",
    "Tesla Destination": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Tesla_Motors.svg/120px-Tesla_Motors.svg.png",
    "ChargePoint Network": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d1/ChargePoint_logo.svg/120px-ChargePoint_logo.svg.png",
    "Electrify America": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Electrify_America_logo.svg/120px-Electrify_America_logo.svg.png",
    "EVgo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6e/EVgo_Logo.svg/120px-EVgo_Logo.svg.png",
    "Blink Network": "https://upload.wikimedia.org/wikipedia/en/thumb/b/b7/Blink_Charging_logo.svg/120px-Blink_Charging_logo.svg.png",
}


async def _fetch_state(
    client: httpx.AsyncClient, state: str, offset: int = 0, limit: int = 200
) -> tuple[list[dict], int]:
    """Fetch one page of chargers for a state. Returns (stations, total_results)."""
    params = {
        "api_key": NREL_API_KEY,
        "fuel_type": "ELEC",
        "status": "E",
        "access": "public",
        "state": state,
        "limit": limit,
        "offset": offset,
    }
    max_retries = 6
    for attempt in range(max_retries):
        response = await client.get(NREL_BASE_URL, params=params)
        if response.status_code == 429:
            # Exponential backoff: 60s, 120s, 180s, 240s, 300s, 360s
            wait = 60 * (attempt + 1)
            logger.warning(f"[NREL] Rate limited for {state} offset={offset}, waiting {wait}s (attempt {attempt+1}/{max_retries})")
            await asyncio.sleep(wait)
            continue
        response.raise_for_status()
        data = response.json()
        return data.get("fuel_stations", []), data.get("total_results", 0)
    # Final attempt after all retries
    response = await client.get(NREL_BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    return data.get("fuel_stations", []), data.get("total_results", 0)


async def _fetch_all_for_state(client: httpx.AsyncClient, state: str) -> list[dict]:
    """Fetch ALL chargers for a state, handling pagination with rate limiting."""
    all_stations = []
    offset = 0
    limit = 200

    while True:
        stations, total = await _fetch_state(client, state, offset=offset, limit=limit)
        all_stations.extend(stations)
        if len(stations) < limit or len(all_stations) >= total:
            break
        offset += limit
        # Rate limit: 4s between pages keeps us well under 1000 req/hr
        await asyncio.sleep(4.0)

    return all_stations


def _map_nrel_to_charger(station: dict) -> dict:
    """Map NREL station dict to Charger model fields."""
    nrel_id = str(station.get("id", ""))
    network = station.get("ev_network") or "Unknown"

    # NREL status codes: E=Open, P=Planned, T=Temp Unavailable
    status_map = {"E": "available", "P": "planned", "T": "broken"}
    status_code = station.get("status_code", "E")
    status = status_map.get(status_code, "unknown")

    # Extract max power (kW) from NREL fields
    power_kw = None
    if station.get("ev_dc_fast_num"):
        # DC fast chargers are typically 50-350 kW
        power_kw = 150.0  # reasonable default for DC fast
    elif station.get("ev_level2_evse_num"):
        power_kw = 7.2  # Level 2 default

    connector_types = station.get("ev_connector_types") or []
    logo_url = NETWORK_LOGOS.get(network)

    return {
        "external_id": nrel_id,
        "name": station.get("station_name", "Unknown Charger"),
        "network_name": network,
        "lat": float(station.get("latitude", 0)),
        "lng": float(station.get("longitude", 0)),
        "address": station.get("street_address", ""),
        "city": station.get("city", ""),
        "state": station.get("state", ""),
        "zip_code": station.get("zip", ""),
        "connector_types": connector_types,
        "power_kw": power_kw,
        "is_public": station.get("access_code") != "PRIVATE",
        "access_code": station.get("access_code"),
        "status": status,
        "logo_url": logo_url,
    }


async def seed_chargers(
    db,
    states: Optional[list[str]] = None,
    progress_callback=None,
) -> dict:
    """
    Fetch all US EV chargers from NREL AFDC and upsert into chargers table.

    Args:
        db: SQLAlchemy Session
        states: List of state codes (default: all 50 + DC)
        progress_callback: Optional callable(state, fetched, total_states)

    Returns:
        {total_fetched, inserted, updated, skipped, errors, states_processed}
    """
    from app.models.while_you_charge import Charger

    target_states = states or ALL_STATES
    total_states = len(target_states)

    result = {
        "total_fetched": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
        "states_processed": 0,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx, state in enumerate(target_states):
            try:
                stations = await _fetch_all_for_state(client, state)
                result["total_fetched"] += len(stations)

                # Deduplicate by NREL station ID (pagination can return overlaps)
                seen_ids = set()
                unique_stations = []
                for s in stations:
                    sid = str(s.get("id", ""))
                    if sid and sid not in seen_ids:
                        seen_ids.add(sid)
                        unique_stations.append(s)
                stations = unique_stations
                logger.info(f"[Seed] {state}: fetched {len(stations)} unique chargers")

                batch_count = 0
                for station in stations:
                    mapped = _map_nrel_to_charger(station)

                    # Skip invalid coords
                    if mapped["lat"] == 0 or mapped["lng"] == 0:
                        result["skipped"] += 1
                        continue

                    charger_id = f"nrel_{mapped['external_id']}"

                    # Use merge for true upsert (handles both insert and update)
                    charger = Charger(
                        id=charger_id,
                        **mapped,
                    )
                    charger.updated_at = datetime.utcnow()
                    db.merge(charger)
                    result["inserted"] += 1  # merge handles insert-or-update

                    batch_count += 1
                    if batch_count % 500 == 0:
                        db.flush()

                db.commit()
                result["states_processed"] += 1

                if progress_callback:
                    progress_callback(state, result["total_fetched"], total_states)

                # Rate limit: 5s delay between states
                await asyncio.sleep(5.0)

            except Exception as e:
                error_msg = f"{state}: {str(e)}"
                logger.error(f"[Seed] Error for {state}: {e}")
                result["errors"].append(error_msg)
                db.rollback()

    logger.info(
        f"[Seed] Complete: {result['inserted']} inserted, "
        f"{result['updated']} updated, {result['skipped']} skipped, "
        f"{len(result['errors'])} errors"
    )
    return result


if __name__ == "__main__":
    import argparse
    import sys

    sys.path.insert(0, ".")

    parser = argparse.ArgumentParser(description="Seed EV chargers from NREL")
    parser.add_argument("--states", nargs="*", help="State codes (default: all)")
    args = parser.parse_args()

    from app.db import SessionLocal

    db = SessionLocal()
    try:
        result = asyncio.run(seed_chargers(db, states=args.states))
        print(f"\nResult: {result}")
    finally:
        db.close()
