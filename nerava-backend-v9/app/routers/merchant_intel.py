from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any, Optional
from app.core.config import flag_enabled
from app.services.merchant_intel import get_overview
from app.schemas.merchant_intel import MerchantIntelOverviewResponse
from app.security.scopes import require_scopes
from app.security.ratelimit import rate_limit
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/merchant", tags=["merchant-intel"])

# Required scopes: merchant:read for GET endpoints
@router.get("/intel/overview", response_model=MerchantIntelOverviewResponse)
async def get_merchant_intel_overview(
    request: Request,
    merchant_id: str = Query(..., description="Merchant ID"),
    grid_load_pct: Optional[float] = Query(75.0, description="Grid load percentage for dynamic promos"),
    current_user: Dict[str, Any] = Depends(require_scopes(["merchant:read"]))
) -> MerchantIntelOverviewResponse:
    """
    Get merchant intelligence overview with cohorts, forecasts, and promos.
    
    Requires scope: merchant:read
    """
    
    # Check feature flag
    if not flag_enabled("feature_merchant_intel"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "merchant_intel_overview",
        "merchant_id": merchant_id,
        "actor_id": current_user.get("user_id")
    })
    
    # clamp grid_load_pct to 0..100 before passing to service
    grid_load_pct = max(0.0, min(100.0, grid_load_pct))
    
    try:
        result = get_overview(merchant_id, grid_load_pct)
        
        log_info({
            "trace_id": trace_id,
            "route": "merchant_intel_overview",
            "merchant_id": merchant_id,
            "status": "success"
        })
        
        return MerchantIntelOverviewResponse(**result)
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "merchant_intel_overview",
            "merchant_id": merchant_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
