from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
import math
from app.core.config import flag_enabled
from app.services.verify_api import verify_charge
from app.schemas.verify_api import VerifyChargeRequest, VerifyChargeResponse
from app.security.apikey import require_api_key
from app.security.ratelimit import rate_limit
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/verify", tags=["verify-api"])

# Required API key with verify:charge scope, rate limited to 30/min
@router.post("/charge", response_model=VerifyChargeResponse)
async def verify_charge_session(
    request: Request,
    charge_request: VerifyChargeRequest,
    api_key_data: Dict[str, Any] = Depends(require_api_key("verify:charge")),
    _: bool = Depends(rate_limit("verify_charge", 30))
) -> VerifyChargeResponse:
    """
    Verify a charge session (3rd-party API).
    
    Requires API key with scope: verify:charge
    Rate limited to 30 requests per minute
    """
    
    # Check feature flag
    if not flag_enabled("feature_charge_verify_api"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "charge_verification",
        "charge_session_id": charge_request.charge_session_id,
        "api_key": api_key_data.get("api_key", "unknown")
    })
    
    try:
        # Basic fraud checks
        verified = True
        reason = None
        
        # Check minimum kWh
        if charge_request.kwh_charged < 1.0:
            verified = False
            reason = "below_min_kwh"
        
        # Geo radius check (if station location provided)
        if (charge_request.station_location and 
            charge_request.kwh_charged >= 1.0):
            
            # Calculate distance between charge location and station
            lat1, lng1 = charge_request.location.lat, charge_request.location.lng
            lat2, lng2 = charge_request.station_location.lat, charge_request.station_location.lng
            
            # Haversine formula for distance calculation
            R = 6371  # Earth's radius in km
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = (math.sin(dlat/2) * math.sin(dlat/2) + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlng/2) * math.sin(dlng/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance_km = R * c
            
            if distance_km > 5.0:  # 5km radius
                verified = False
                reason = "geo_mismatch"
        
        # Call service with fraud check results
        result = verify_charge({
            **charge_request.dict(),
            "verified": verified,
            "fraud_reason": reason
        })
        
        log_info({
            "trace_id": trace_id,
            "route": "charge_verification",
            "charge_session_id": charge_request.charge_session_id,
            "verified": result.get("verified"),
            "fraud_check": reason
        })
        
        return VerifyChargeResponse(**result)
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "charge_verification",
            "charge_session_id": charge_request.charge_session_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
