"""
HubSpot Integration Service

P3: HubSpot integration scaffolding (dry run only).
When HUBSPOT_ENABLED=true and HUBSPOT_SEND_LIVE=false:
- Logs JSON payloads that WOULD be sent
- Stores them in outbox table for replay
- No outbound network calls unless HUBSPOT_SEND_LIVE=true
"""
import os
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.hubspot import HubSpotOutbox
from app.utils.log import get_logger

logger = get_logger(__name__)

# Feature flags
HUBSPOT_ENABLED = os.getenv("HUBSPOT_ENABLED", "false").lower() == "true"
HUBSPOT_SEND_LIVE = os.getenv("HUBSPOT_SEND_LIVE", "false").lower() == "true"
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY", "")


def track_event(
    db: Session,
    event_type: str,
    payload: Dict[str, Any]
) -> Optional[str]:
    """
    Track an event to HubSpot (dry run mode by default).
    
    Args:
        db: Database session
        event_type: Event type ("user_signup", "redemption", "wallet_pass_install")
        payload: Event payload (will be stored in outbox)
    
    Returns:
        Outbox record ID if stored, None otherwise
    """
    if not HUBSPOT_ENABLED:
        # HubSpot not enabled - skip
        return None
    
    # Store in outbox
    outbox_id = str(uuid.uuid4())
    outbox_record = HubSpotOutbox(
        id=outbox_id,
        event_type=event_type,
        payload_json=payload,
        created_at=datetime.utcnow()
    )
    db.add(outbox_record)
    # Don't commit here - let caller commit
    
    if HUBSPOT_SEND_LIVE:
        # P3: Live sending is commented out for now
        # When ready to enable, uncomment and implement actual HubSpot API call
        # try:
        #     hubspot_client.send_event(event_type, payload)
        #     outbox_record.sent_at = datetime.utcnow()
        #     logger.info(f"[HUBSPOT] Event sent: {event_type}, outbox_id={outbox_id}")
        # except Exception as e:
        #     outbox_record.error_message = str(e)
        #     outbox_record.retry_count += 1
        #     logger.error(f"[HUBSPOT] Failed to send event: {event_type}, error={e}")
        logger.warning(
            f"[HUBSPOT] HUBSPOT_SEND_LIVE=true but sending is not yet implemented. "
            f"Event stored in outbox: {outbox_id}"
        )
    else:
        # Dry run mode - just log
        logger.info(
            f"[HUBSPOT_DRY_RUN] Event type={event_type}, payload={json.dumps(payload, default=str)}"
        )
    
    return outbox_id


def send_outbox_events(db: Session, limit: int = 100) -> Dict[str, Any]:
    """
    Manually send pending events from outbox (for testing/replay).
    
    Args:
        db: Database session
        limit: Maximum number of events to send
    
    Returns:
        Dict with send results
    """
    if not HUBSPOT_ENABLED:
        return {"error": "HUBSPOT_ENABLED is false"}
    
    if not HUBSPOT_SEND_LIVE:
        return {"error": "HUBSPOT_SEND_LIVE is false - cannot send live events"}
    
    # Get pending events (not yet sent)
    pending = db.query(HubSpotOutbox).filter(
        HubSpotOutbox.sent_at.is_(None)
    ).order_by(HubSpotOutbox.created_at.asc()).limit(limit).all()
    
    sent_count = 0
    error_count = 0
    
    for event in pending:
        try:
            # P3: Actual sending is commented out
            # hubspot_client.send_event(event.event_type, event.payload_json)
            # event.sent_at = datetime.utcnow()
            # sent_count += 1
            logger.warning(
                f"[HUBSPOT] Sending not yet implemented. Event {event.id} would be sent."
            )
            # For now, mark as sent (simulated)
            event.sent_at = datetime.utcnow()
            sent_count += 1
        except Exception as e:
            event.error_message = str(e)
            event.retry_count += 1
            error_count += 1
            logger.error(f"[HUBSPOT] Failed to send event {event.id}: {e}")
    
    db.commit()
    
    return {
        "sent": sent_count,
        "errors": error_count,
        "total": len(pending)
    }
