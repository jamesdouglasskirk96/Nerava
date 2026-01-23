from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db import get_db
from app.models import User
from app.dependencies.domain import get_current_user

router = APIRouter(prefix="/v1/support", tags=["support"])


class FAQItem(BaseModel):
    q: str
    a: str


class SupportTicketRequest(BaseModel):
    subject: str
    description: str


class SupportTicketResponse(BaseModel):
    ticket_id: int
    message: str


@router.get("/faq", response_model=List[FAQItem])
async def get_faq():
    """Get FAQ items"""
    return [
        {"q": "How do I activate an exclusive?", "a": "Navigate to a charger and select a merchant with an exclusive offer. Tap 'Activate Exclusive' to start your session."},
        {"q": "What is Nova?", "a": "Nova is our rewards currency. Earn Nova by charging at partner locations and redeem them at nearby merchants."},
        {"q": "How do I find chargers?", "a": "Use the discovery screen to see nearby chargers. The app shows chargers within 400m of your location."},
        {"q": "Can I favorite merchants?", "a": "Yes! Tap the heart icon on any merchant to add them to your favorites. Access favorites from your Account page."},
    ]


@router.post("/ticket", response_model=SupportTicketResponse)
async def create_ticket(
    data: SupportTicketRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create support ticket"""
    # TODO: Implement actual ticket creation with database model
    # For now, return a mock ticket ID
    ticket_id = hash(f"{current_user.id}{data.subject}{datetime.utcnow()}") % 1000000
    return SupportTicketResponse(
        ticket_id=ticket_id,
        message="Support ticket created. We'll get back to you soon."
    )


