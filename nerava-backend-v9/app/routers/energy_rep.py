from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.energy_rep import compute
from app.schemas.energy_rep import EnergyRepResponse
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/profile", tags=["energy-rep"])

@router.get("/energy_rep", response_model=EnergyRepResponse)
async def get_energy_reputation(
    request: Request,
    user_id: str = Query(..., description="User ID")
) -> EnergyRepResponse:
    """
    Get user's energy reputation score and tier.
    
    No additional scopes required (user profile data)
    """
    
    # Check feature flag
    if not flag_enabled("feature_energy_rep"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "energy_rep",
        "user_id": user_id
    })
    
    try:
        result = compute(user_id)
        
        log_info({
            "trace_id": trace_id,
            "route": "energy_rep",
            "user_id": user_id,
            "score": result.get("score"),
            "tier": result.get("tier"),
            "status": "success"
        })
        
        return EnergyRepResponse(**result)
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "energy_rep",
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
