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


async def _fetch_by_zip(
    client: httpx.AsyncClient, zip_code: str, radius_miles: float = 25.0
) -> list[dict]:
    """Fetch chargers near a ZIP code. Returns list of stations."""
    params = {
        "api_key": NREL_API_KEY,
        "fuel_type": "ELEC",
        "status": "E",
        "access": "public",
        "zip": zip_code,
        "radius": radius_miles,
        "limit": 200,
    }
    max_retries = 4
    for attempt in range(max_retries):
        try:
            response = await client.get(NREL_BASE_URL, params=params)
        except Exception as e:
            logger.warning(f"[NREL] Request error for zip {zip_code}: {e} (attempt {attempt+1})")
            await asyncio.sleep(15)
            continue
        if response.status_code == 429:
            wait = 60 * (attempt + 1)
            logger.warning(f"[NREL] Rate limited for zip {zip_code}, waiting {wait}s")
            await asyncio.sleep(wait)
            continue
        response.raise_for_status()
        data = response.json()
        stations = data.get("fuel_stations", [])
        return stations
    return []


# ZIP codes covering major metro areas and corridors per state.
# Each ZIP gets a 25-mile radius query, providing good overlap for full coverage.
STATE_ZIPS = {
    "AL": [
        "35203", "35758", "36104", "36602", "35401", "36301", "35801", "36830",
        "35630", "35901", "36526", "36067", "35004", "35950", "36460", "36265",
    ],
    "AK": [
        "99501", "99701", "99801", "99611", "99654", "99577", "99669", "99645",
        "99901", "99835",
    ],
    "AZ": [
        "85001", "85201", "85251", "85281", "85301", "85701", "86001", "86301",
    ],
    "AR": [
        "72201", "72701", "72401", "72901", "71601", "72032", "71901", "72501",
        "72301", "71801", "72601", "71730", "72801", "72450", "71854",
    ],
    "CA": [
        "90012", "90024", "90045", "90210", "90401", "91001", "91107",
        "91301", "91601", "92101", "92618", "92660", "93003", "93101",
        "94102", "94301", "94538", "94612", "95112", "95401", "95814",
        "96001", "93301", "93401", "92801", "92264", "96150",
    ],
    "CO": [
        "80202", "80903", "80301", "80525", "81001", "81501", "80631", "81301",
        "80549", "81401", "80461", "81611", "80487", "81201", "81008", "80112",
        "80401", "80013", "81050", "80751", "81625", "81101", "80863", "81632",
    ],
    "CT": [
        "06103", "06510", "06604", "06901", "06320", "06702", "06040", "06360",
        "06790", "06801", "06410",
    ],
    "DE": [
        "19801", "19901", "19971", "19711", "19958", "19966", "19720",
    ],
    "FL": [
        "33101", "33132", "33155", "33186", "33010", "33060", "33160",
        "33301", "33309", "33324", "33071",
        "33401", "33411", "33431",
        "32801", "32819", "32835", "32746", "34747", "32703",
        "33601", "33609", "33647", "33701", "33760",
        "32099", "32207", "32256",
        "34102", "34236", "33950", "34950", "32301", "32501", "32901",
        "34601", "33480", "34201", "34786", "34231", "33316",
        "32136", "34482", "32605", "33870", "33801", "34109",
    ],
    "GA": [
        "30303", "30301", "31401", "30901", "31201", "31601", "30501", "30060",
        "31061", "30240", "31501", "31701", "30720", "31301", "30401", "30043",
        "31404", "30009", "30265", "31008", "30165", "30474", "31791", "30680",
    ],
    "HI": [
        "96813", "96732", "96720", "96740", "96766", "96786", "96734", "96707",
    ],
    "ID": [
        "83702", "83814", "83201", "83301", "83401", "83501", "83616", "83646",
        "83686", "83440", "83651", "83864", "83338", "83843", "83341", "83605",
        "83520", "83210", "83228",
    ],
    "IL": [
        "60601", "60605", "60007", "60540", "60115", "61801", "62701", "61602",
        "61101", "62901", "62002", "62801", "61265", "61350", "60901", "62521",
        "62301", "60435", "61701", "60085", "62864", "62040", "61401", "62959",
    ],
    "IN": [
        "46204", "46601", "46802", "47374", "47901", "47401", "47708", "46312",
        "47201", "47802", "46383", "47130", "46060", "47302", "46902", "46530",
        "46580", "47274", "47546", "46350",
    ],
    "IA": [
        "50309", "52241", "52401", "52001", "51501", "52801", "50701", "50010",
        "51101", "52501", "50401", "50801", "52240", "50501", "52601", "51301",
        "50036", "50158",
    ],
    "KS": [
        "67202", "66101", "66502", "66801", "67401", "66044", "66002", "67846",
        "67501", "67601", "66614", "67301", "67801", "66720", "66901", "67042",
        "67101", "67701", "67005", "66441",
    ],
    "KY": [
        "40202", "40507", "41011", "42001", "42101", "40601", "40701", "41501",
        "42301", "40353", "42071", "40509", "42503", "40422", "40475", "42701",
        "41042", "40342",
    ],
    "LA": [
        "70112", "70801", "71101", "70501", "70601", "71201", "70301", "70433",
        "71301", "70002", "71457", "70364", "71360", "71446", "70791", "70570",
        "71075", "70726",
    ],
    "ME": [
        "04101", "04401", "04330", "04240", "04901", "04769", "04074", "04605",
        "04841", "04473", "04730", "04276", "04938", "04353", "04736",
    ],
    "MD": [
        "21202", "20850", "21401", "21502", "21740", "21601", "20602", "21801",
        "21701", "20901", "21042", "20774", "21613", "21550", "20678", "21811",
    ],
    "MA": [
        "02108", "01545", "01101", "02740", "02601", "01002", "01841", "01201",
        "02169", "01701", "01960", "02301", "01420", "02532", "01060", "01501",
        "02360",
    ],
    "MI": [
        "48226", "49503", "48933", "48104", "49007", "48502", "48601", "49684",
        "49855", "49001", "48060", "49801", "49783", "48706", "49091", "49301",
        "48858", "49601", "49770", "48801", "49417", "48843", "48642", "49930",
    ],
    "MN": [
        "55401", "55101", "55901", "55802", "56301", "56001", "56601", "55912",
        "56560", "55060", "55987", "56401", "56201", "56701", "55744", "56258",
        "56501", "55025", "55303", "55372", "55379", "56073", "55731", "56308",
    ],
    "MS": [
        "39201", "39530", "38801", "39401", "39301", "38701", "39501", "39648",
        "39110", "39759", "38655", "39120", "38901", "39440", "39564", "38632",
    ],
    "MO": [
        "63101", "64106", "65806", "65201", "64801", "63701", "65401", "63501",
        "63601", "64501", "63401", "65301", "65101", "65605", "63901", "64093",
        "63005", "65616", "64068", "63141",
    ],
    "MT": [
        "59601", "59101", "59801", "59401", "59901", "59701", "59301", "59501",
        "59715", "59840", "59201", "59330", "59218", "59417", "59047", "59725",
        "59230",
    ],
    "NE": [
        "68102", "68502", "69101", "68801", "68901", "68601", "68701", "69001",
        "68310", "69361", "68847", "68025", "68301", "69162", "68467", "69153",
        "68761", "69301",
    ],
    "NV": [
        "89101", "89501", "89701", "89801", "89301", "89015", "89434", "89406",
        "89048", "89005", "89408", "89316", "89445", "89703", "89014", "89119",
        "89431", "89820",
    ],
    "NH": [
        "03101", "03301", "03801", "03431", "03246", "03570", "03766", "03060",
        "03753", "03838", "03584", "03110", "03242",
    ],
    "NJ": [
        "07102", "08608", "08901", "08401", "08002", "07030", "07601", "07724",
        "08360", "08854", "07960", "08816", "07302", "08075", "08210", "07801",
        "08205", "08520",
    ],
    "NM": [
        "87102", "87501", "88001", "88201", "87301", "87401", "88101", "87701",
        "87901", "88310", "87801", "88220", "87031", "88030", "87544", "88401",
        "87120", "87124", "88061", "87532",
    ],
    "NY": [
        "10001", "10019", "10301", "10601", "11201", "11501", "11735",
        "12203", "13202", "14201", "14850",
    ],
    "NC": [
        "27601", "28202", "27401", "27101", "27701", "28801", "28401", "28301",
        "27834", "28601", "28501", "28677", "27510", "28150", "28540", "27858",
        "28904", "27360", "28901", "27893", "28025", "27253", "28352", "27870",
        "28906", "28786", "27573",
    ],
    "ND": [
        "58102", "58501", "58201", "58701", "58601", "58801", "58401", "58301",
        "58078", "58540", "58854",
    ],
    "OH": [
        "43215", "44113", "45202", "45402", "44308", "43604", "44702", "44501",
        "45701", "43701", "44903", "45601", "45840", "44805", "45810", "43420",
        "44001", "43302", "43316", "44256", "43081", "45005", "43952", "45040",
        "43055",
    ],
    "OK": [
        "73102", "74103", "73071", "74401", "73501", "73401", "74601", "73601",
        "74801", "74701", "73701", "74501", "73801", "73901", "73942", "74301",
        "74074", "73644", "73003",
    ],
    "OR": [
        "97204", "97401", "97301", "97501", "97701", "97801", "97103", "97850",
        "97914", "97601", "97756", "97365", "97420", "97526", "97058", "97838",
        "97062", "97045", "97132", "97330",
    ],
    "PA": [
        "19102", "15222", "17101", "18015", "16501", "18503", "17601", "19601",
        "16801", "17701", "15701", "17815", "18840", "15301", "18301", "17013",
        "16001", "19464", "17042", "16335", "18201", "15401", "17901", "17331",
    ],
    "RI": [
        "02903", "02840", "02893", "02860", "02891", "02886", "02864",
    ],
    "SC": [
        "29201", "29401", "29601", "29501", "29801", "29577", "29707", "29360",
        "29150", "29302", "29445", "29649", "29841", "29108", "29440", "29902",
        "29550", "29706",
    ],
    "SD": [
        "57104", "57701", "57401", "57501", "57301", "57069", "57350", "57201",
        "57601", "57706", "57078", "57785", "57532", "57747", "57638",
    ],
    "TN": [
        "37203", "38103", "37902", "37402", "37040", "38301", "37601", "38501",
        "37130", "37660", "38401", "37801", "37355", "38002", "38351", "37311",
        "38242", "37110", "38555", "37771",
    ],
    "TX": [
        "77002", "77007", "77024", "77042", "77058", "77084", "77339", "77388",
        "77494", "77546", "77571", "77449", "77375", "77365", "77504",
        "75201", "75225", "75240", "75063", "76102", "76034", "75070", "75038",
        "75080", "75019", "75287", "76244", "75048", "75150",
        "78701", "78704", "78745", "78759", "78660", "78681", "78664", "78613",
        "78205", "78216", "78240", "78258", "78023", "78154",
        "79901", "79407", "76706", "78401", "79101", "75901", "75701", "77701",
        "76901", "78840", "78501", "78550", "79761", "79601", "76301", "75460",
        "75503", "76513", "78130", "76801", "77845", "75455",
    ],
    "UT": [
        "84101", "84601", "84401", "84720", "84301", "84532", "84701", "84770",
        "84003", "84501", "84078", "84057", "84098", "84321", "84741", "84021",
        "84337", "84761", "84648", "84621",
    ],
    "VT": [
        "05401", "05602", "05301", "05701", "05819", "05478", "05101", "05753",
        "05201", "05855", "05060", "05446",
    ],
    "VA": [
        "23219", "23510", "22201", "20190", "22901", "24011", "24501", "24060",
        "22801", "22980", "23185", "23803", "23434", "24210", "22601", "23860",
        "22701", "24301", "23320", "23601", "20171", "22554", "24141", "23901",
        "23669",
    ],
    "WA": [
        "98101", "98402", "99201", "98901", "98801", "98501", "98225", "99301",
        "98662", "98926", "98362", "98837", "98632", "99362", "98520", "99163",
        "98368", "98012", "98036", "98003", "98371", "98388", "99001", "98273",
    ],
    "WV": [
        "25301", "26505", "25401", "25701", "26003", "26301", "24701", "26101",
        "25801", "26241", "26651", "26508", "24901", "25413", "25177",
    ],
    "WI": [
        "53202", "53703", "54301", "54403", "54701", "53081", "54601", "54901",
        "53511", "54880", "54449", "53901", "54501", "54843", "54115", "53005",
        "53562", "54220", "54401", "53188", "54935", "53545", "54481", "54313",
    ],
    "WY": [
        "82001", "82601", "82801", "82414", "82501", "82901", "82701", "82301",
        "83001", "82070", "82201", "82401", "82520", "82240", "82435", "82716",
        "82009",
    ],
    "DC": [
        "20001", "20009", "20020", "20016",
    ],
}


async def _fetch_all_for_state(client: httpx.AsyncClient, state: str) -> list[dict]:
    """Fetch ALL chargers for a state using state query + dense ZIP queries.

    NREL's offset parameter is broken, so we combine:
    1. State query (gets 200 from API's default sort — catches dense-area chargers)
    2. Dense ZIP grid with 25-mile radius (geographic coverage)
    This hybrid approach maximizes unique charger discovery.
    """
    # Use dense ZIP grid for full coverage
    try:
        from scripts.dense_zips import DENSE_STATE_ZIPS
        zips = DENSE_STATE_ZIPS.get(state)
    except ImportError:
        zips = STATE_ZIPS.get(state)

    all_stations_by_id = {}

    # Step 1: State query to get 200 chargers (often from dense metros)
    params = {
        "api_key": NREL_API_KEY,
        "fuel_type": "ELEC",
        "status": "E",
        "access": "public",
        "state": state,
        "limit": 200,
    }
    response = None
    for attempt in range(4):
        try:
            response = await client.get(NREL_BASE_URL, params=params)
        except Exception as e:
            logger.warning(f"[NREL] {state}: request error: {e} (attempt {attempt+1})")
            await asyncio.sleep(15)
            continue
        if response.status_code == 429:
            wait = 60 * (attempt + 1)
            logger.warning(f"[NREL] {state}: rate limited on state query, waiting {wait}s")
            await asyncio.sleep(wait)
            continue
        break

    if response and response.status_code == 200:
        data = response.json()
        total = data.get("total_results", 0)
        initial_stations = data.get("fuel_stations", [])
        for s in initial_stations:
            sid = str(s.get("id", ""))
            if sid:
                all_stations_by_id[sid] = s
        logger.info(f"[NREL] {state}: state query returned {len(initial_stations)}/{total} total")

        # If all chargers fit in one page, done
        if total <= 200:
            return initial_stations

    await asyncio.sleep(2.0)

    # Step 2: Dense ZIP queries for geographic coverage
    if not zips:
        logger.warning(f"[NREL] {state}: no ZIP list, returning {len(all_stations_by_id)} from state query")
        return list(all_stations_by_id.values())

    logger.info(f"[NREL] {state}: using {len(zips)} dense ZIPs with 25-mile radius")

    for i, zip_code in enumerate(zips):
        stations = await _fetch_by_zip(client, zip_code, radius_miles=25.0)
        new_count = 0
        for s in stations:
            sid = str(s.get("id", ""))
            if sid and sid not in all_stations_by_id:
                if s.get("state", "").upper() == state.upper():
                    all_stations_by_id[sid] = s
                    new_count += 1
        if (i + 1) % 5 == 0 or i == len(zips) - 1:
            logger.info(f"[NREL] {state}: zip {zip_code} ({i+1}/{len(zips)}), total unique={len(all_stations_by_id)}")
        # Rate limit: 1.5s between requests
        await asyncio.sleep(1.5)

    logger.info(f"[NREL] {state}: fetched {len(all_stations_by_id)} unique chargers")
    return list(all_stations_by_id.values())


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
