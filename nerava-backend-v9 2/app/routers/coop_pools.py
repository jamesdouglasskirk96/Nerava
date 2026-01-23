from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import logging
import uuid
from app.core.config import flag_enabled
from app.services.coop_pools import create_pool

router = APIRouter(prefix="/v1/coop", tags=["coop-pools"])
logger = logging.getLogger(__name__)

class CoopPoolRequest(BaseModel):
    utility_id: str
    merchants: List[str]

@router.post("/pools")
async def create_coop_pool(
    request: CoopPoolRequest,
    # TODO: Add auth dependency when available
    # current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Create a merchant-utility cooperation pool"""
    
    # Check feature flag
    if not flag_enabled("feature_merchant_utility_coops"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = str(uuid.uuid4())
    logger.info(f"coop_pool_creation_request", extra={
        "trace_id": trace_id,
        "route": "coop_pool_creation",
        "utility_id": request.utility_id,
        "merchant_count": len(request.merchants)
    })
    
    try:
        result = create_pool(request.dict())
        
        logger.info(f"coop_pool_creation_success", extra={
            "trace_id": trace_id,
            "route": "coop_pool_creation",
            "utility_id": request.utility_id,
            "pool_id": result.get("pool_id")
        })
        
        return result
        
    except Exception as e:
        logger.error(f"coop_pool_creation_error", extra={
            "trace_id": trace_id,
            "route": "coop_pool_creation",
            "utility_id": request.utility_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
