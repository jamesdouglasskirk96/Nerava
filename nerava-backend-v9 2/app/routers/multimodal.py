from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Literal
import logging
import uuid
from app.core.config import flag_enabled
from app.services.multimodal import register_device

router = APIRouter(prefix="/v1/mobility", tags=["multimodal"])
logger = logging.getLogger(__name__)

class DeviceRegistrationRequest(BaseModel):
    user_id: str
    mode: Literal["scooter", "ebike", "av"]

@router.post("/register_device")
async def register_mobility_device(
    request: DeviceRegistrationRequest,
    # TODO: Add auth dependency when available
    # current_user: str = Depends(get_current_user)
) -> Dict[str, Any]:
    """Register a multi-modal mobility device"""
    
    # Check feature flag
    if not flag_enabled("feature_multimodal"):
        raise HTTPException(status_code=404, detail="Feature not enabled")
    
    trace_id = str(uuid.uuid4())
    logger.info(f"mobility_device_registration_request", extra={
        "trace_id": trace_id,
        "route": "mobility_device_registration",
        "user_id": request.user_id,
        "mode": request.mode
    })
    
    try:
        result = register_device(request.user_id, request.mode)
        
        logger.info(f"mobility_device_registration_success", extra={
            "trace_id": trace_id,
            "route": "mobility_device_registration",
            "user_id": request.user_id,
            "mode": request.mode,
            "device_id": result.get("device_id")
        })
        
        return result
        
    except Exception as e:
        logger.error(f"mobility_device_registration_error", extra={
            "trace_id": trace_id,
            "route": "mobility_device_registration",
            "user_id": request.user_id,
            "mode": request.mode,
            "error": str(e)
        })
        raise HTTPException(status_code=500, detail="Internal server error")
