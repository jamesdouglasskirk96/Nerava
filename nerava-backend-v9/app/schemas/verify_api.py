"""
Pydantic models for Verify API.
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

class Location(BaseModel):
    lat: float
    lng: float

class VerifyChargeRequest(BaseModel):
    charge_session_id: str
    kwh_charged: float
    location: Location
    timestamp: str
    station_location: Optional[Location] = None

class VerifyChargeResponse(BaseModel):
    request_id: str
    verified: bool
    reason: Optional[str] = None
    meta: Dict[str, Any]
