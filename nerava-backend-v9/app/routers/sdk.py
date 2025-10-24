from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Dict, Any
import logging
import uuid
from app.core.config import flag_enabled
from app.services.sdk import get_config

router = APIRouter(prefix="/v1/sdk", tags=["sdk"])
logger = logging.getLogger(__name__)

@router.get("/config")
async def get_sdk_config(
    tenant_id: str = Path(..., description="Tenant ID"),
    # TODO: Add auth dependency when available
    # current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get white-label SDK configuration for tenant"""
    
    # Check feature flag
    if not flag_enabled("feature_whitelabel_sdk"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = str(uuid.uuid4())
    logger.info(f"sdk_config_request", extra={
        "trace_id": trace_id,
        "route": "sdk_config",
        "tenant_id": tenant_id
    })
    
    try:
        result = get_config(tenant_id)
        
        logger.info(f"sdk_config_success", extra={
            "trace_id": trace_id,
            "route": "sdk_config",
            "tenant_id": tenant_id
        })
        
        return result
        
    except Exception as e:
        logger.error(f"sdk_config_error", extra={
            "trace_id": trace_id,
            "route": "sdk_config",
            "tenant_id": tenant_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
