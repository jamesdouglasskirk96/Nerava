"""
Notification preferences router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.db import get_db
from app.models import User
from app.models.notification_prefs import UserNotificationPrefs
from app.dependencies_domain import get_current_user

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

