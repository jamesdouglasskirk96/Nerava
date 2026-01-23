"""
API endpoints for sending custom SMS messages.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from ..services.sms_service import get_sms_service
from ..dependencies.domain import get_current_user
from ..models import User

router = APIRouter()


class SendSMSRequest(BaseModel):
    """Request to send a custom SMS"""
    to_phone: str = Field(..., description="Recipient phone number (any format)")
    message: str = Field(..., description="Message text (can include links)", min_length=1, max_length=1600)
    link_url: Optional[str] = Field(None, description="Optional URL to include in message")
    link_text: Optional[str] = Field(None, description="Optional text for the link")


class SendSMSResponse(BaseModel):
    """Response from sending SMS"""
    success: bool
    message_sid: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


@router.post("/send", response_model=SendSMSResponse)
async def send_sms(
    request: SendSMSRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a custom SMS message.
    
    Requires authentication. The message can include links.
    Links will be sent as plain URLs in the SMS (most phones will auto-link them).
    """
    try:
        sms_service = get_sms_service()
        
        # Build message
        if request.link_url:
            if request.link_text:
                message = f"{request.message}\n\n{request.link_text}: {request.link_url}"
            else:
                message = f"{request.message}\n\n{request.link_url}"
        else:
            message = request.message
        
        # Send SMS
        result = await sms_service.send_sms(
            to_phone=request.to_phone,
            message=message
        )
        
        if result["success"]:
            return SendSMSResponse(
                success=True,
                message_sid=result.get("message_sid"),
                status=result.get("status")
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to send SMS")
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send SMS: {str(e)}"
        )


