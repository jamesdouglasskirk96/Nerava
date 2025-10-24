from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging
import uuid
from app.core.config import flag_enabled
from app.services.iot import link_device

router = APIRouter(prefix="/v1/iot", tags=["smart-home-iot"])
logger = logging.getLogger(__name__)

class IotLinkRequest(BaseModel):
    provider: str  # e.g., "nest", "ecobee", "tesla"
    device_id: str
    user_id: str

@router.post("/link_device")
async def link_iot_device(
    request: IotLinkRequest,
    # TODO: Add auth dependency when available
    # current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Link a smart home/IoT device"""
    
    # Check feature flag
    if not flag_enabled("feature_smart_home_iot"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = str(uuid.uuid4())
    logger.info(f"iot_device_link_request", extra={
        "trace_id": trace_id,
        "route": "iot_device_link",
        "provider": request.provider,
        "device_id": request.device_id,
        "user_id": request.user_id
    })
    
    try:
        result = link_device(request.provider, request.device_id, request.user_id)
        
        logger.info(f"iot_device_link_success", extra={
            "trace_id": trace_id,
            "route": "iot_device_link",
            "provider": request.provider,
            "device_id": request.device_id,
            "user_id": request.user_id,
            "status": result.get("status")
        })
        
        return result
        
    except Exception as e:
        logger.error(f"iot_device_link_error", extra={
            "trace_id": trace_id,
            "route": "iot_device_link",
            "provider": request.provider,
            "device_id": request.device_id,
            "user_id": request.user_id,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
