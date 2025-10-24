from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging
import uuid
from app.core.config import flag_enabled
from app.services.wallet_interop import interop_options

router = APIRouter(prefix="/v1/wallet", tags=["wallet-interop"])
logger = logging.getLogger(__name__)

@router.get("/interop/options")
async def get_wallet_interop_options(
    # TODO: Add auth dependency when available
    # current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get wallet interoperability options (Apple Pay, Visa, etc.)"""
    
    # Check feature flag
    if not flag_enabled("feature_energy_wallet_ext"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = str(uuid.uuid4())
    logger.info(f"wallet_interop_options_request", extra={
        "trace_id": trace_id,
        "route": "wallet_interop_options"
    })
    
    try:
        result = interop_options()
        
        logger.info(f"wallet_interop_options_success", extra={
            "trace_id": trace_id,
            "route": "wallet_interop_options"
        })
        
        return result
        
    except Exception as e:
        logger.error(f"wallet_interop_options_error", extra={
            "trace_id": trace_id,
            "route": "wallet_interop_options",
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
