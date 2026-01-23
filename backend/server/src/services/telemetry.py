from datetime import datetime
from typing import Optional
from ..config import Config

def mark_verified_charge(db, session, kwh: float, start_at: Optional[datetime] = None, end_at: Optional[datetime] = None, confidence: str = "HIGH"):
    """Mark a session as verified with charge data"""
    session.verified_charge = True
    session.kwh = kwh
    if start_at:
        session.start_at = start_at
    if end_at:
        session.end_at = end_at
    session.confidence = confidence
    db.commit()

def maybe_mark_medium_confidence(db, session):
    """Mark session as medium confidence if not already verified"""
    if not session.verified_charge and not session.confidence:
        session.confidence = "MEDIUM"
        db.commit()
