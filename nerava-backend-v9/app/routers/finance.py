from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.finance import offers
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/finance", tags=["esg-finance-gateway"])

@router.get("/offers")
async def get_finance_offers(
    request: Request,
    user_id: str = Query(..., description="User ID")
) -> Dict[str, Any]:
    """
    Get ESG finance gateway offers.
    
    No additional scopes required (user auth only)
    """
    
    # Check feature flag
    if not flag_enabled("feature_esg_finance_gateway"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "finance_offers",
        "user_id": user_id
    })
    
    try:
        result = offers(user_id)
        
        log_info({
            "trace_id": trace_id,
            "route": "finance_offers",
            "user_id": user_id,
            "offer_count": len(result.get("offers", [])),
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "finance_offers",
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
