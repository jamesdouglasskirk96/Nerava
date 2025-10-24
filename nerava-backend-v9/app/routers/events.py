from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.events import create_event
from app.security.ratelimit import rate_limit
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/events", tags=["energy-events"])

class EventCreationRequest(BaseModel):
    host_id: str
    schedule: Dict[str, Any]
    boost_rate: float

# Rate limited to 10/min per host
@router.post("/create")
async def create_energy_event(
    request: Request,
    event_request: EventCreationRequest,
    _: bool = Depends(rate_limit("energy_events", 10))
) -> Dict[str, Any]:
    """
    Create an energy event with boost rate.
    
    Rate limited to 10 requests per minute per host
    """
    
    # Check feature flag
    if not flag_enabled("feature_energy_events"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "energy_event_creation",
        "host_id": event_request.host_id,
        "boost_rate": event_request.boost_rate
    })
    
    try:
        result = create_event(event_request.dict())
        
        log_info({
            "trace_id": trace_id,
            "route": "energy_event_creation",
            "host_id": event_request.host_id,
            "event_id": result.get("event_id"),
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "energy_event_creation",
            "host_id": event_request.host_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
