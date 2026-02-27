"""
Notification preferences and device token registration router
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Literal

from app.db import get_db
from app.models import User
from app.models.notification_prefs import UserNotificationPrefs
from app.models.device_token import DeviceToken
from app.dependencies_domain import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])


class NotificationPrefsResponse(BaseModel):
    earned_nova: bool
    nearby_nova: bool
    wallet_reminders: bool


class NotificationPrefsUpdate(BaseModel):
    earned_nova: bool = None
    nearby_nova: bool = None
    wallet_reminders: bool = None


@router.get("/prefs", response_model=NotificationPrefsResponse)
def get_notification_prefs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get notification preferences for current user
    """
    prefs = db.query(UserNotificationPrefs).filter(
        UserNotificationPrefs.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Return defaults if not set
        return NotificationPrefsResponse(
            earned_nova=True,
            nearby_nova=True,
            wallet_reminders=True
        )
    
    return NotificationPrefsResponse(
        earned_nova=prefs.earned_nova,
        nearby_nova=prefs.nearby_nova,
        wallet_reminders=prefs.wallet_reminders
    )


@router.put("/prefs", response_model=NotificationPrefsResponse)
def update_notification_prefs(
    update: NotificationPrefsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update notification preferences for current user
    """
    prefs = db.query(UserNotificationPrefs).filter(
        UserNotificationPrefs.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create new preferences
        prefs = UserNotificationPrefs(
            user_id=current_user.id,
            earned_nova=update.earned_nova if update.earned_nova is not None else True,
            nearby_nova=update.nearby_nova if update.nearby_nova is not None else True,
            wallet_reminders=update.wallet_reminders if update.wallet_reminders is not None else True,
        )
        db.add(prefs)
    else:
        # Update existing preferences
        if update.earned_nova is not None:
            prefs.earned_nova = update.earned_nova
        if update.nearby_nova is not None:
            prefs.nearby_nova = update.nearby_nova
        if update.wallet_reminders is not None:
            prefs.wallet_reminders = update.wallet_reminders
        prefs.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(prefs)

    return NotificationPrefsResponse(
        earned_nova=prefs.earned_nova,
        nearby_nova=prefs.nearby_nova,
        wallet_reminders=prefs.wallet_reminders
    )


# ---------------------------------------------------------------------------
# Device token registration (FCM / APNs)
# ---------------------------------------------------------------------------

class RegisterDeviceRequest(BaseModel):
    fcm_token: str
    platform: Literal["android", "ios"]


class RegisterDeviceResponse(BaseModel):
    ok: bool


@router.post("/register-device", response_model=RegisterDeviceResponse)
def register_device(
    payload: RegisterDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register (or refresh) a push-notification device token.

    The Android app calls this on every FCM token refresh.
    Upserts by token value — if the same token already exists for this user
    it just bumps updated_at; if it belongs to a different user the ownership
    is transferred (a device can only belong to one signed-in user).
    """
    existing = db.query(DeviceToken).filter(
        DeviceToken.token == payload.fcm_token,
    ).first()

    if existing:
        # Transfer ownership if user changed, reactivate if deactivated
        existing.user_id = current_user.id
        existing.platform = payload.platform
        existing.is_active = True
        existing.updated_at = datetime.utcnow()
    else:
        device = DeviceToken(
            user_id=current_user.id,
            token=payload.fcm_token,
            platform=payload.platform,
        )
        db.add(device)

    db.commit()
    logger.info("Device token registered for user %s (%s)", current_user.id, payload.platform)
    return RegisterDeviceResponse(ok=True)


# ---------------------------------------------------------------------------
# Test push notification endpoint (admin/debug)
# ---------------------------------------------------------------------------

class SendTestPushResponse(BaseModel):
    sent: int
    message: str


@router.post("/send-test", response_model=SendTestPushResponse)
def send_test_push(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a test push notification to the current user's registered devices.
    Useful for verifying push notification setup end-to-end.
    """
    from app.services.push_service import send_push_notification

    sent = send_push_notification(
        db,
        user_id=current_user.id,
        title="Test notification",
        body="Push notifications are working!",
        data={"type": "test"},
    )

    return SendTestPushResponse(
        sent=sent,
        message=f"Sent to {sent} device(s)" if sent > 0 else "No active devices found (or APNs not configured)",
    )

