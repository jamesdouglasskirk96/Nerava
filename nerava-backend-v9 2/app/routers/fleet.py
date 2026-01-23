from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.fleet import get_overview
from app.security.scopes import require_scopes
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/fleet", tags=["fleet-workplace"])

# Required scopes: fleet:read for fleet overview
@router.get("/overview")
async def get_fleet_overview(
    request: Request,
    org_id: str = Query(..., description="Organization ID"),
    current_user: Dict[str, Any] = Depends(require_scopes(["fleet:read"]))
) -> Dict[str, Any]:
    """
    Get fleet/workplace overview with vehicles and ESG report.
    
    Requires scope: fleet:read
    """
    
    # Check feature flag
    if not flag_enabled("feature_fleet_workplace"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "fleet_overview",
        "org_id": org_id,
        "actor_id": current_user.get("user_id")
    })
    
    try:
        result = get_overview(org_id)
        
        log_info({
            "trace_id": trace_id,
            "route": "fleet_overview",
            "org_id": org_id,
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "fleet_overview",
            "org_id": org_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
