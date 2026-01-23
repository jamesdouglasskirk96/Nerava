from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.ai_growth import generate_campaigns
from app.security.ratelimit import rate_limit
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/ai", tags=["ai-growth-automation"])

# Rate limited to 5/min per user
@router.post("/growth/campaigns/generate")
async def generate_ai_growth_campaigns(
    request: Request,
    _: bool = Depends(rate_limit("ai_growth", 5))
) -> Dict[str, Any]:
    """
    Generate AI-powered growth campaigns.
    
    Rate limited to 5 requests per minute per user
    """
    
    # Check feature flag
    if not flag_enabled("feature_ai_growth_automation"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "ai_growth_campaigns_generate"
    })
    
    try:
        result = generate_campaigns()
        
        log_info({
            "trace_id": trace_id,
            "route": "ai_growth_campaigns_generate",
            "campaign_id": result.get("campaign_id"),
            "variant_count": len(result.get("variants", [])),
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "ai_growth_campaigns_generate",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
