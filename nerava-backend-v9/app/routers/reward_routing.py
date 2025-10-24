from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from app.core.config import flag_enabled
from app.services.reward_routing import schedule_rebalance
from app.security.ratelimit import rate_limit
from app.obs.obs import get_trace_id, log_info, log_error

router = APIRouter(prefix="/v1/rewards", tags=["reward-routing"])

# Rate limited to 10/min per user
@router.post("/routing/rebalance")
async def rebalance_reward_routing(
    request: Request,
    _: bool = Depends(rate_limit("reward_rebalance", 10))
) -> Dict[str, Any]:
    """
    Schedule autonomous reward routing rebalance.
    
    Rate limited to 10 requests per minute per user
    """
    
    # Check feature flag
    if not flag_enabled("feature_autonomous_reward_routing"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = get_trace_id(request)
    log_info({
        "trace_id": trace_id,
        "route": "reward_routing_rebalance"
    })
    
    try:
        result = schedule_rebalance()
        
        log_info({
            "trace_id": trace_id,
            "route": "reward_routing_rebalance",
            "run_id": result.get("run_id"),
            "status": "success"
        })
        
        return result
        
    except Exception as e:
        log_error({
            "trace_id": trace_id,
            "route": "reward_routing_rebalance",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
