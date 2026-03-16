#!/usr/bin/env python3
"""
Seed US EV chargers from NREL AFDC API using a metro-area lat/lng grid.

The ZIP-based approach caps at ~25K chargers because NREL returns max 200
per query. This script uses fine grids (0.03° spacing, 2-mile radius) over
the ~100 densest US metro areas where most chargers are concentrated.

Estimated ~12,000 grid points → ~5 hours at 1.5s/query.
Designed to run in batches via the admin API endpoint.

Usage:
    python -m scripts.seed_chargers_grid                          # All metros
    python -m scripts.seed_chargers_grid --states CA TX            # Only metros in these states
    python -m scripts.seed_chargers_grid --batch-size 500          # Stop after 500 queries
"""
import logging
import asyncio
import json
import os
import httpx
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

NREL_API_KEY = "rBv6VXOAQbJemI6xw2QbqjceK5QdNUta8MpT50mY"
NREL_BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.json"

PROGRESS_FILE = "/tmp/nrel_grid_progress.json"

# Grid spacing and query radius
GRID_SPACING = 0.03    # ~2.1 miles between grid points
QUERY_RADIUS = 2.5     # miles — keeps results well under 200 per query

# ---------------------------------------------------------------------------
# Metro area bounding boxes: (name, state, south, north, west, east)
# Covers the ~100 largest US metro areas where charger density is highest.
# ---------------------------------------------------------------------------
METRO_AREAS = [
    # ── California (19,412 in NREL, we have 3,121) ──
    ("LA_Basin", "CA", 33.70, 34.20, -118.70, -117.70),
    ("LA_South", "CA", 33.40, 33.70, -118.50, -117.50),
    ("LA_SFV", "CA", 34.10, 34.40, -118.80, -118.20),
    ("OC_Inland", "CA", 33.60, 34.10, -117.70, -117.20),
    ("San_Diego", "CA", 32.55, 33.10, -117.30, -116.80),
    ("SF_Oakland", "CA", 37.60, 37.90, -122.55, -122.10),
    ("SF_Peninsula", "CA", 37.30, 37.60, -122.50, -122.05),
    ("San_Jose", "CA", 37.20, 37.50, -122.10, -121.70),
    ("East_Bay", "CA", 37.55, 37.95, -122.35, -121.80),
    ("Sacramento", "CA", 38.40, 38.75, -121.60, -121.10),
    ("Fresno", "CA", 36.60, 36.90, -119.95, -119.60),
    ("Bakersfield", "CA", 35.25, 35.50, -119.25, -118.85),
    ("SB_Ventura", "CA", 34.10, 34.50, -119.90, -119.10),
    ("Riverside_SB", "CA", 33.80, 34.20, -117.55, -116.90),
    ("Palm_Springs", "CA", 33.60, 33.95, -116.70, -116.20),
    ("Stockton_Modesto", "CA", 37.50, 38.00, -121.60, -120.80),
    ("Santa_Cruz_Monterey", "CA", 36.50, 37.10, -122.10, -121.60),
    ("Napa_Sonoma", "CA", 38.10, 38.60, -122.90, -122.20),
    ("Redding_Chico", "CA", 39.60, 40.70, -122.70, -121.60),
    ("Eureka", "CA", 40.60, 41.00, -124.30, -124.00),
    ("SLO", "CA", 35.10, 35.40, -120.80, -120.50),

    # ── New York (5,313 in NREL, we have 1,025) ──
    ("NYC_Manhattan", "NY", 40.70, 40.85, -74.05, -73.90),
    ("NYC_Brooklyn_Queens", "NY", 40.55, 40.75, -74.05, -73.70),
    ("NYC_Bronx", "NY", 40.80, 40.92, -73.95, -73.75),
    ("Staten_Island", "NY", 40.50, 40.65, -74.26, -74.05),
    ("Long_Island_W", "NY", 40.55, 40.85, -73.75, -73.30),
    ("Long_Island_E", "NY", 40.60, 41.00, -73.30, -72.50),
    ("Westchester", "NY", 40.85, 41.15, -73.90, -73.55),
    ("Hudson_Valley", "NY", 41.10, 41.60, -74.20, -73.70),
    ("Albany", "NY", 42.55, 42.80, -73.95, -73.60),
    ("Syracuse", "NY", 42.90, 43.15, -76.30, -75.95),
    ("Rochester", "NY", 43.05, 43.25, -77.80, -77.40),
    ("Buffalo", "NY", 42.80, 43.05, -78.95, -78.65),
    ("Ithaca", "NY", 42.35, 42.55, -76.60, -76.35),

    # ── Florida (4,292 in NREL, we have 911) ──
    ("Miami_Dade", "FL", 25.60, 25.95, -80.45, -80.10),
    ("Fort_Lauderdale", "FL", 25.95, 26.25, -80.35, -80.05),
    ("West_Palm", "FL", 26.55, 26.85, -80.25, -80.00),
    ("Orlando", "FL", 28.30, 28.70, -81.60, -81.10),
    ("Tampa", "FL", 27.80, 28.15, -82.65, -82.30),
    ("St_Pete", "FL", 27.65, 27.85, -82.80, -82.55),
    ("Jacksonville", "FL", 30.15, 30.50, -81.85, -81.40),
    ("Naples_FtMyers", "FL", 26.10, 26.70, -82.00, -81.60),
    ("Sarasota", "FL", 27.20, 27.50, -82.65, -82.35),
    ("Gainesville", "FL", 29.55, 29.75, -82.50, -82.20),
    ("Tallahassee", "FL", 30.35, 30.55, -84.40, -84.15),
    ("Melbourne_Space", "FL", 28.00, 28.40, -80.80, -80.50),
    ("Pensacola", "FL", 30.35, 30.55, -87.35, -87.05),

    # ── Texas (3,843 in NREL, we have 1,134) ──
    ("Houston_Core", "TX", 29.60, 29.90, -95.60, -95.20),
    ("Houston_N", "TX", 29.85, 30.15, -95.70, -95.20),
    ("Houston_SW", "TX", 29.50, 29.70, -95.80, -95.40),
    ("Houston_SE", "TX", 29.40, 29.65, -95.30, -94.90),
    ("Dallas_Core", "TX", 32.65, 32.95, -97.00, -96.60),
    ("Dallas_N", "TX", 32.90, 33.25, -97.00, -96.50),
    ("Fort_Worth", "TX", 32.60, 32.90, -97.50, -97.10),
    ("Austin", "TX", 30.15, 30.50, -97.90, -97.55),
    ("San_Antonio", "TX", 29.30, 29.60, -98.70, -98.30),
    ("El_Paso", "TX", 31.65, 31.90, -106.55, -106.30),
    ("Corpus_Christi", "TX", 27.70, 27.85, -97.50, -97.30),

    # ── Washington (2,877 in NREL, we have 1,011) ──
    ("Seattle_Core", "WA", 47.50, 47.75, -122.45, -122.25),
    ("Seattle_N", "WA", 47.70, 47.95, -122.45, -122.15),
    ("Seattle_S", "WA", 47.30, 47.55, -122.50, -122.15),
    ("Eastside_Bellevue", "WA", 47.50, 47.75, -122.25, -121.95),
    ("Tacoma_Olympia", "WA", 46.95, 47.30, -122.65, -122.30),
    ("Spokane", "WA", 47.55, 47.80, -117.55, -117.25),
    ("Vancouver_WA", "WA", 45.55, 45.75, -122.80, -122.50),

    # ── Colorado (2,702 in NREL, we have 862) ──
    ("Denver_Core", "CO", 39.60, 39.85, -105.15, -104.80),
    ("Denver_S", "CO", 39.45, 39.65, -105.10, -104.70),
    ("Denver_N", "CO", 39.80, 40.10, -105.20, -104.80),
    ("Boulder", "CO", 39.95, 40.15, -105.40, -105.15),
    ("CoSprings", "CO", 38.75, 39.00, -104.90, -104.65),
    ("Fort_Collins", "CO", 40.45, 40.65, -105.20, -105.00),

    # ── Massachusetts (4,231 in NREL, we have 855) ──
    ("Boston_Core", "MA", 42.30, 42.45, -71.15, -70.95),
    ("Boston_W", "MA", 42.25, 42.50, -71.40, -71.10),
    ("Boston_N", "MA", 42.40, 42.65, -71.20, -70.85),
    ("Boston_S", "MA", 42.05, 42.30, -71.20, -70.85),
    ("Worcester", "MA", 42.20, 42.40, -71.90, -71.65),
    ("Springfield", "MA", 42.05, 42.25, -72.70, -72.45),
    ("Cape_Cod", "MA", 41.55, 41.85, -70.70, -69.90),

    # ── Georgia (2,351 in NREL, we have 652) ──
    ("Atlanta_Core", "GA", 33.65, 33.90, -84.55, -84.25),
    ("Atlanta_N", "GA", 33.85, 34.15, -84.60, -84.10),
    ("Atlanta_S", "GA", 33.40, 33.70, -84.70, -84.15),
    ("Savannah", "GA", 31.95, 32.15, -81.25, -81.00),
    ("Augusta", "GA", 33.35, 33.55, -82.10, -81.85),

    # ── Illinois (1,726 in NREL, we have 409) ──
    ("Chicago_Core", "IL", 41.75, 42.00, -87.80, -87.55),
    ("Chicago_N", "IL", 41.95, 42.25, -88.00, -87.60),
    ("Chicago_W", "IL", 41.75, 42.00, -88.30, -87.80),
    ("Chicago_S", "IL", 41.45, 41.80, -87.85, -87.50),
    ("Springfield_IL", "IL", 39.70, 39.90, -89.75, -89.55),
    ("Champaign", "IL", 40.05, 40.20, -88.35, -88.15),

    # ── Pennsylvania (1,997 in NREL, we have 570) ──
    ("Philly_Core", "PA", 39.85, 40.10, -75.30, -75.05),
    ("Philly_Suburbs", "PA", 39.95, 40.25, -75.55, -75.15),
    ("Pittsburgh", "PA", 40.35, 40.55, -80.10, -79.85),
    ("Allentown", "PA", 40.55, 40.70, -75.55, -75.35),
    ("Harrisburg", "PA", 40.20, 40.35, -76.95, -76.70),

    # ── Ohio (1,939 in NREL, we have 530) ──
    ("Columbus", "OH", 39.85, 40.15, -83.15, -82.75),
    ("Cleveland", "OH", 41.35, 41.60, -81.85, -81.50),
    ("Cincinnati", "OH", 39.05, 39.25, -84.65, -84.35),
    ("Dayton", "OH", 39.70, 39.90, -84.30, -84.05),
    ("Toledo", "OH", 41.55, 41.75, -83.70, -83.45),
    ("Akron", "OH", 40.95, 41.15, -81.60, -81.35),

    # ── Michigan (2,026 in NREL, we have 517) ──
    ("Detroit_Core", "MI", 42.25, 42.50, -83.25, -82.90),
    ("Detroit_Suburbs", "MI", 42.35, 42.70, -83.55, -83.05),
    ("Grand_Rapids", "MI", 42.85, 43.05, -85.80, -85.55),
    ("Ann_Arbor", "MI", 42.20, 42.35, -83.85, -83.65),
    ("Lansing", "MI", 42.65, 42.80, -84.65, -84.45),

    # ── Virginia (1,846 in NREL, we have 566) ──
    ("NoVA", "VA", 38.75, 39.05, -77.55, -77.00),
    ("Richmond", "VA", 37.45, 37.65, -77.60, -77.30),
    ("VA_Beach_Norfolk", "VA", 36.75, 37.05, -76.40, -75.95),
    ("Charlottesville", "VA", 37.95, 38.15, -78.55, -78.40),

    # ── North Carolina (1,939 in NREL, we have 571) ──
    ("Charlotte", "NC", 35.10, 35.40, -81.00, -80.65),
    ("Raleigh_Durham", "NC", 35.70, 36.05, -79.00, -78.50),
    ("Greensboro", "NC", 35.95, 36.15, -80.00, -79.70),
    ("Asheville", "NC", 35.45, 35.65, -82.70, -82.40),
    ("Wilmington_NC", "NC", 34.15, 34.30, -77.95, -77.80),

    # ── New Jersey (1,805 in NREL, we have 503) ──
    ("NJ_North", "NJ", 40.70, 41.10, -74.40, -73.95),
    ("NJ_Central", "NJ", 40.20, 40.60, -74.65, -74.15),
    ("NJ_South", "NJ", 39.60, 40.00, -75.20, -74.60),
    ("NJ_Shore", "NJ", 39.90, 40.40, -74.20, -73.90),

    # ── Maryland (1,694 in NREL, we have 629) ──
    ("Baltimore", "MD", 39.20, 39.45, -76.80, -76.45),
    ("DC_Suburbs_MD", "MD", 38.85, 39.15, -77.25, -76.85),
    ("Annapolis", "MD", 38.90, 39.05, -76.60, -76.40),

    # ── Oregon (1,655 in NREL, we have 618) ──
    ("Portland_OR", "OR", 45.35, 45.65, -122.85, -122.45),
    ("Eugene", "OR", 43.95, 44.15, -123.20, -122.95),
    ("Salem_OR", "OR", 44.85, 45.05, -123.15, -122.85),
    ("Bend", "OR", 43.95, 44.15, -121.40, -121.20),
    ("Medford", "OR", 42.25, 42.45, -122.90, -122.65),

    # ── Connecticut (we have 456) ──
    ("Hartford", "CT", 41.70, 41.85, -72.80, -72.55),
    ("New_Haven", "CT", 41.25, 41.40, -73.00, -72.80),
    ("Stamford_Norwalk", "CT", 41.00, 41.20, -73.65, -73.35),

    # ── Arizona (we have 541) ──
    ("Phoenix", "AZ", 33.30, 33.70, -112.30, -111.80),
    ("Tucson", "AZ", 32.10, 32.35, -111.10, -110.80),
    ("Scottsdale_Mesa", "AZ", 33.35, 33.65, -111.90, -111.55),

    # ── Minnesota (we have 383) ──
    ("Minneapolis", "MN", 44.85, 45.10, -93.45, -93.15),
    ("St_Paul", "MN", 44.90, 45.05, -93.20, -93.00),

    # ── Missouri (we have 391) ──
    ("StLouis", "MO", 38.50, 38.75, -90.45, -90.10),
    ("KC_MO", "MO", 38.95, 39.20, -94.70, -94.40),

    # ── Tennessee (we have 505) ──
    ("Nashville", "TN", 36.05, 36.30, -87.00, -86.60),
    ("Memphis_TN", "TN", 35.00, 35.25, -90.15, -89.85),
    ("Knoxville", "TN", 35.90, 36.05, -84.05, -83.80),

    # ── Indiana (we have 278) ──
    ("Indianapolis", "IN", 39.65, 39.90, -86.30, -86.00),

    # ── Wisconsin (we have ?) ──
    ("Milwaukee", "WI", 42.90, 43.15, -88.05, -87.80),
    ("Madison_WI", "WI", 42.95, 43.15, -89.55, -89.30),

    # ── South Carolina (we have 308) ──
    ("Charleston_SC", "SC", 32.70, 32.90, -80.10, -79.85),
    ("Columbia_SC", "SC", 33.90, 34.10, -81.15, -80.90),
    ("Greenville_SC", "SC", 34.80, 35.00, -82.50, -82.30),

    # ── Nevada (we have 311) ──
    ("Las_Vegas", "NV", 35.95, 36.30, -115.40, -115.00),
    ("Reno", "NV", 39.45, 39.65, -119.95, -119.70),

    # ── Louisiana (we have 212) ──
    ("New_Orleans", "LA", 29.90, 30.10, -90.20, -89.90),
    ("Baton_Rouge", "LA", 30.35, 30.55, -91.25, -91.05),

    # ── Kentucky (we have 267) ──
    ("Louisville", "KY", 38.15, 38.35, -85.85, -85.55),
    ("Lexington", "KY", 37.95, 38.15, -84.60, -84.40),

    # ── Oklahoma (we have 269) ──
    ("OKC", "OK", 35.35, 35.60, -97.70, -97.35),
    ("Tulsa", "OK", 35.95, 36.25, -96.10, -95.80),

    # ── DC ──
    ("DC", "DC", 38.80, 38.98, -77.12, -76.91),

    # ── Hawaii ──
    ("Honolulu", "HI", 21.25, 21.45, -157.95, -157.70),

    # ── Utah ──
    ("SLC", "UT", 40.55, 40.85, -112.05, -111.70),

    # ── New Mexico ──
    ("Albuquerque", "NM", 34.95, 35.20, -106.75, -106.45),

    # ── Kansas ──
    ("KC_KS", "KS", 38.90, 39.15, -94.90, -94.55),

    # ── Iowa ──
    ("Des_Moines", "IA", 41.50, 41.70, -93.75, -93.45),

    # ── Nebraska ──
    ("Omaha", "NE", 41.15, 41.35, -96.10, -95.80),

    # ── Alabama ──
    ("Birmingham", "AL", 33.40, 33.60, -86.95, -86.65),

    # ── New Hampshire ──
    ("Manchester_NH", "NH", 42.95, 43.10, -71.55, -71.35),

    # ── Delaware ──
    ("Wilmington_DE", "DE", 39.65, 39.85, -75.65, -75.45),
]


def _generate_grid(south: float, north: float, west: float, east: float) -> list[tuple[float, float]]:
    """Generate lat/lng grid points within bounding box at GRID_SPACING."""
    points = []
    lat = south
    while lat <= north:
        lng = west
        while lng <= east:
            points.append((round(lat, 4), round(lng, 4)))
            lng += GRID_SPACING
        lat += GRID_SPACING
    return points


def _load_progress() -> dict:
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_progress(progress: dict):
    try:
        with open(PROGRESS_FILE, "w") as f:
            json.dump(progress, f)
    except Exception as e:
        logger.warning(f"Failed to save progress: {e}")


async def _fetch_by_latlng(
    client: httpx.AsyncClient,
    lat: float,
    lng: float,
    radius_miles: float,
) -> list[dict]:
    """Fetch chargers near a lat/lng point with retry on 429."""
    params = {
        "api_key": NREL_API_KEY,
        "fuel_type": "ELEC",
        "access": "public",
        "latitude": lat,
        "longitude": lng,
        "radius": radius_miles,
        "limit": 200,
    }
    for attempt in range(4):
        try:
            response = await client.get(NREL_BASE_URL, params=params)
        except Exception as e:
            logger.warning(f"[Grid] Request error at ({lat},{lng}): {e} (attempt {attempt+1})")
            await asyncio.sleep(15)
            continue
        if response.status_code == 429:
            wait = 60 * (attempt + 1)
            logger.warning(f"[Grid] Rate limited at ({lat},{lng}), waiting {wait}s")
            await asyncio.sleep(wait)
            continue
        response.raise_for_status()
        return response.json().get("fuel_stations", [])
    return []


async def seed_chargers_grid(
    db,
    states: Optional[list[str]] = None,
    batch_size: int = 0,
    progress_callback=None,
) -> dict:
    """
    Fetch US EV chargers from NREL using metro-area lat/lng grids.

    Args:
        db: SQLAlchemy Session
        states: Filter metros to these states only (default: all)
        batch_size: Max total queries before stopping (0 = unlimited)
        progress_callback: Optional callable(metro_name, total_unique, total_metros)

    Returns:
        {total_fetched, inserted, updated, skipped, errors, states_processed}
    """
    from app.models.while_you_charge import Charger
    from scripts.seed_chargers_bulk import _map_nrel_to_charger

    # Filter metros by state if requested
    metros = METRO_AREAS
    if states:
        state_set = {s.upper() for s in states}
        metros = [m for m in METRO_AREAS if m[1] in state_set]

    total_metros = len(metros)

    result = {
        "total_fetched": 0,
        "inserted": 0,
        "updated": 0,
        "skipped": 0,
        "errors": [],
        "states_processed": 0,
        "metros_processed": 0,
        "total_metros": total_metros,
    }

    progress = _load_progress()
    total_queries = 0
    all_stations_by_id: dict[str, dict] = {}  # Global dedup across all metros

    # Calculate total grid points for logging
    total_grid_points = 0
    for name, state, s, n, w, e in metros:
        if progress.get(name, {}).get("completed"):
            continue
        total_grid_points += len(_generate_grid(s, n, w, e))

    logger.info(f"[Grid] Starting: {total_metros} metros, ~{total_grid_points} grid points")

    async with httpx.AsyncClient(timeout=30.0) as client:
        for metro_idx, (name, state, south, north, west, east) in enumerate(metros):
            try:
                # Skip completed metros
                if progress.get(name, {}).get("completed"):
                    result["metros_processed"] += 1
                    continue

                grid_points = _generate_grid(south, north, west, east)
                total_points = len(grid_points)
                resume_idx = progress.get(name, {}).get("last_index", 0)

                if resume_idx >= total_points:
                    progress[name] = {"completed": True, "last_index": total_points}
                    result["metros_processed"] += 1
                    continue

                logger.info(f"[Grid] {name} ({state}): {total_points} grid points, resuming from {resume_idx}")

                metro_stations: dict[str, dict] = {}

                for i in range(resume_idx, total_points):
                    lat, lng = grid_points[i]
                    stations = await _fetch_by_latlng(client, lat, lng, QUERY_RADIUS)

                    for s_data in stations:
                        sid = str(s_data.get("id", ""))
                        if sid and sid not in all_stations_by_id:
                            all_stations_by_id[sid] = s_data
                            metro_stations[sid] = s_data

                    total_queries += 1

                    # Log every 50 points
                    if (total_queries) % 50 == 0:
                        logger.info(
                            f"[Grid] {name}: {i+1}/{total_points}, "
                            f"metro_unique={len(metro_stations)}, "
                            f"global_unique={len(all_stations_by_id)}, "
                            f"total_queries={total_queries}"
                        )

                    # Checkpoint every 200 queries
                    if total_queries % 200 == 0:
                        progress[name] = {"last_index": i + 1}
                        _save_progress(progress)

                    # Batch limit (total across all metros)
                    if batch_size > 0 and total_queries >= batch_size:
                        progress[name] = {"last_index": i + 1}
                        _save_progress(progress)
                        logger.info(f"[Grid] Batch limit {batch_size} reached. Saving and stopping.")
                        # Upsert what we have so far
                        _upsert_stations(db, metro_stations, result)
                        return result

                    await asyncio.sleep(3.0)

                # Upsert stations for this metro
                _upsert_stations(db, metro_stations, result)
                result["metros_processed"] += 1

                progress[name] = {"completed": True, "last_index": total_points}
                _save_progress(progress)

                logger.info(
                    f"[Grid] {name} ({state}): done, {len(metro_stations)} new chargers, "
                    f"global total={len(all_stations_by_id)}"
                )

                if progress_callback:
                    progress_callback(name, len(all_stations_by_id), total_metros)

                await asyncio.sleep(2.0)

            except Exception as e:
                error_msg = f"{name} ({state}): {str(e)}"
                logger.error(f"[Grid] Error for {name}: {e}", exc_info=True)
                result["errors"].append(error_msg)
                db.rollback()

    logger.info(
        f"[Grid] Complete: {result['total_fetched']} fetched, "
        f"{result['inserted']} upserted, {len(result['errors'])} errors, "
        f"{result['metros_processed']}/{total_metros} metros, "
        f"total_queries={total_queries}"
    )
    return result


def _upsert_stations(db, stations: dict[str, dict], result: dict):
    """Upsert a batch of stations into the chargers table."""
    from app.models.while_you_charge import Charger
    from scripts.seed_chargers_bulk import _map_nrel_to_charger

    batch_count = 0
    for station in stations.values():
        mapped = _map_nrel_to_charger(station)

        if mapped["lat"] == 0 or mapped["lng"] == 0:
            result["skipped"] += 1
            continue

        charger_id = f"nrel_{mapped['external_id']}"
        charger = Charger(id=charger_id, **mapped)
        charger.updated_at = datetime.utcnow()
        db.merge(charger)
        result["inserted"] += 1

        batch_count += 1
        if batch_count % 500 == 0:
            db.flush()

    result["total_fetched"] += len(stations)
    db.commit()


if __name__ == "__main__":
    import argparse
    import sys

    sys.path.insert(0, ".")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="Seed EV chargers from NREL using metro-area grid")
    parser.add_argument("--states", nargs="*", help="Only seed metros in these states")
    parser.add_argument("--batch-size", type=int, default=0,
                        help="Max total queries before stopping (0=unlimited)")
    parser.add_argument("--reset-progress", action="store_true",
                        help="Clear checkpoint file and start fresh")
    args = parser.parse_args()

    if args.reset_progress and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print(f"Cleared progress file: {PROGRESS_FILE}")

    from app.db import SessionLocal

    db = SessionLocal()
    try:
        result = asyncio.run(seed_chargers_grid(
            db,
            states=args.states,
            batch_size=args.batch_size,
        ))
        print(f"\nResult: {result}")
    finally:
        db.close()
