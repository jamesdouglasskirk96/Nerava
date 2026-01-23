from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
import uuid
from app.core.config import flag_enabled
from app.services.ai_rewards import suggest

router = APIRouter(prefix="/v1/ai", tags=["ai-reward-optimization"])
logger = logging.getLogger(__name__)

@router.post("/rewards/suggest")
async def suggest_ai_rewards(
    # TODO: Add auth dependency when available
    # current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get AI-powered reward optimization suggestions"""
    
    # Check feature flag
    if not flag_enabled("feature_ai_reward_opt"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = str(uuid.uuid4())
    logger.info(f"ai_rewards_suggest_request", extra={
        "trace_id": trace_id,
        "route": "ai_rewards_suggest"
    })
    
    try:
        result = suggest()
        
        logger.info(f"ai_rewards_suggest_success", extra={
            "trace_id": trace_id,
            "route": "ai_rewards_suggest",
            "suggestion_count": len(result.get("suggestions", []))
        })
        
        return result
        
    except Exception as e:
        logger.error(f"ai_rewards_suggest_error", extra={
            "trace_id": trace_id,
            "route": "ai_rewards_suggest",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
