from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.behavior_cloud import get_cloud
from app.schemas.behavior_cloud import BehaviorCloudResponse
from app.security.scopes import require_scopes
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/utility", tags=["behavior-cloud"])

# Required scopes: utility:read for GET endpoints
@router.get("/behavior/cloud", response_model=BehaviorCloudResponse)
async def get_utility_behavior_cloud(
    request: Request,
    utility_id: str = Query(..., description="Utility ID"),
    window: str = Query("24h", description="Time window (e.g., 24h, 7d)"),
    current_user: Dict[str, Any] = Depends(require_scopes(["utility:read"]))
) -> BehaviorCloudResponse:
    """
    Get utility behavior cloud with segments, participation, and elasticity data.
    
    Requires scope: utility:read
    """
    
    # Check feature flag
    if not flag_enabled("feature_behavior_cloud"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "utility_behavior_cloud",
        "utility_id": utility_id,
        "window": window,
        "actor_id": current_user.get("user_id")
    })
    
    # window must be one of {"6h","24h","7d"}; default "24h"
    if window not in ["6h", "24h", "7d"]:
        window = "24h"
    
    try:
        result = get_cloud(utility_id, window)
        
        log_info({
            "trace_id": trace_id,
            "route": "utility_behavior_cloud",
            "utility_id": utility_id,
            "window": window,
            "status": "success"
        })
        
        return BehaviorCloudResponse(**result)
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "utility_behavior_cloud",
            "utility_id": utility_id,
            "window": window,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
