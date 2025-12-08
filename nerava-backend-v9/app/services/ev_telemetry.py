"""
EV Telemetry polling service
Polls Smartcar for vehicle telemetry and stores it
"""
import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
import uuid

from app.models_vehicle import VehicleAccount, VehicleTelemetry
from app.services.smartcar_client import (
    refresh_tokens,
    get_vehicle_charge,
    get_vehicle_location,
)

logger = logging.getLogger(__name__)


async def poll_vehicle_telemetry_for_account(
    db: Session, account: VehicleAccount
) -> VehicleTelemetry:
    """
    Poll Smartcar for vehicle telemetry and store it
    
    Args:
        db: Database session
        account: VehicleAccount to poll
        
    Returns:
        VehicleTelemetry record with fresh data
        
    Raises:
        Exception: If polling fails
    """
    # Get valid access token (refresh if needed)
    token = await refresh_tokens(db, account)
    
    # Poll charge and location
    charge_data = await get_vehicle_charge(token.access_token, account.provider_vehicle_id)
    location_data = await get_vehicle_location(token.access_token, account.provider_vehicle_id)
    
    # Map Smartcar fields to our schema
    # Smartcar charge API returns: stateOfCharge (0-100), isPluggedIn, state (CHARGING, FULLY_CHARGED, NOT_CHARGING)
    soc_pct = charge_data.get("stateOfCharge", {}).get("value")
    charging_state = charge_data.get("state", {}).get("value")
    
    # Smartcar location API returns: latitude, longitude
    latitude = location_data.get("latitude")
    longitude = location_data.get("longitude")
    
    # Create telemetry record
    telemetry = VehicleTelemetry(
        id=str(uuid.uuid4()),
        vehicle_account_id=account.id,
        recorded_at=datetime.utcnow(),
        soc_pct=soc_pct,
        charging_state=charging_state,
        latitude=latitude,
        longitude=longitude,
        raw_json={
            "charge": charge_data,
            "location": location_data,
        },
    )
    
    db.add(telemetry)
    db.commit()
    db.refresh(telemetry)
    
    logger.info(f"Polled telemetry for vehicle account {account.id}: SOC={soc_pct}%, state={charging_state}")
    
    return telemetry


async def poll_all_active_vehicles(db: Session) -> list[VehicleTelemetry]:
    """
    Poll all active vehicle accounts
    
    Args:
        db: Database session
        
    Returns:
        List of VehicleTelemetry records created
    """
    accounts = (
        db.query(VehicleAccount)
        .filter(VehicleAccount.is_active == True)
        .all()
    )
    
    results = []
    for account in accounts:
        try:
            telemetry = await poll_vehicle_telemetry_for_account(db, account)
            results.append(telemetry)
        except Exception as e:
            logger.error(f"Failed to poll vehicle {account.id}: {e}", exc_info=True)
            # Continue with other vehicles
    
    return results

