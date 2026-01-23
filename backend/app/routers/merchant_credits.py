from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.merchant_credits import purchase_credits
from app.security.ratelimit import rate_limit
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/merchant", tags=["merchant-credits"])

class CreditPurchaseRequest(BaseModel):
    merchant_id: str
    amount: int  # credits to purchase

# Rate limited to 10/min per merchant
@router.post("/credits/purchase")
async def purchase_merchant_credits(
    request: Request,
    credit_request: CreditPurchaseRequest,
    _: bool = Depends(rate_limit("merchant_credits", 10))
) -> Dict[str, Any]:
    """
    Purchase merchant credits.
    
    Rate limited to 10 requests per minute per merchant
    """
    
    # Check feature flag
    if not flag_enabled("feature_merchant_credits"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "merchant_credits_purchase",
        "merchant_id": credit_request.merchant_id,
        "amount": credit_request.amount
    })
    
    try:
        result = purchase_credits(credit_request.merchant_id, credit_request.amount)
        
        log_info({
            "trace_id": trace_id,
            "route": "merchant_credits_purchase",
            "merchant_id": credit_request.merchant_id,
            "amount": credit_request.amount,
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "merchant_credits_purchase",
            "merchant_id": credit_request.merchant_id,
            "amount": credit_request.amount,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
