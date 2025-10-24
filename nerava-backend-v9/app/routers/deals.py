from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.deals import green_hour_deals
from app.schemas.deals import GreenHourDealsResponse
from app.security.scopes import require_scopes
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/deals", tags=["contextual-commerce"])

# Required scopes: merchant:read for contextual commerce
@router.get("/green_hours", response_model=GreenHourDealsResponse)
async def get_green_hour_deals(
    request: Request,
    lat: float = Query(..., description="Latitude"),
    lng: float = Query(..., description="Longitude"),
    current_user: Dict[str, Any] = Depends(require_scopes(["merchant:read"]))
) -> GreenHourDealsResponse:
    """
    Get contextual commerce deals for green hours.
    
    Requires scope: merchant:read
    """
    
    # Check feature flag
    if not flag_enabled("feature_contextual_commerce"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "green_hour_deals",
        "lat": lat,
        "lng": lng,
        "actor_id": current_user.get("user_id")
    })
    
    try:
        result = green_hour_deals(lat, lng)
        
        log_info({
            "trace_id": trace_id,
            "route": "green_hour_deals",
            "lat": lat,
            "lng": lng,
            "deals_count": len(result.get("deals", [])),
            "status": "success"
        })
        
        return GreenHourDealsResponse(**result)
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "green_hour_deals",
            "lat": lat,
            "lng": lng,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
