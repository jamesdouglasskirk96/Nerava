from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.offsets import mint_offsets
from app.security.ratelimit import rate_limit
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/offsets", tags=["carbon-offsets"])

class OffsetMintRequest(BaseModel):
    tons_co2e: float
    source: str  # e.g., "charging_session", "renewable_energy"

# Rate limited to 5/min per tenant/api_key
@router.post("/mint")
async def mint_carbon_offsets(
    request: Request,
    offset_request: OffsetMintRequest,
    _: bool = Depends(rate_limit("carbon_offsets", 5))
) -> Dict[str, Any]:
    """
    Mint carbon micro-offsets.
    
    Rate limited to 5 requests per minute per tenant/api_key
    """
    
    # Check feature flag
    if not flag_enabled("feature_carbon_micro_offsets"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "carbon_offsets_mint",
        "tons_co2e": offset_request.tons_co2e,
        "source": offset_request.source
    })
    
    try:
        result = mint_offsets(offset_request.dict())
        
        log_info({
            "trace_id": trace_id,
            "route": "carbon_offsets_mint",
            "batch_id": result.get("batch_id"),
            "tons_co2e": offset_request.tons_co2e,
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "carbon_offsets_mint",
            "tons_co2e": offset_request.tons_co2e,
            "source": offset_request.source,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
