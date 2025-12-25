"""
HubSpot sync worker

Reads events from the outbox and sends them to HubSpot (in log-only mode by default).
"""
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import text
from contextlib import contextmanager
from app.db import SessionLocal
from app.events.domain import DomainEvent, EVENT_TYPES
from app.services.hubspot import hubspot_client
from app.events.hubspot_adapter import adapt_event_to_hubspot, to_hubspot_external_id
from app.models import User

logger = logging.getLogger(__name__)


@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class HubSpotSyncWorker:
    """Worker that processes outbox events and sends them to HubSpot"""
    
    def __init__(self, poll_interval: int = 10):
        self.poll_interval = poll_interval
        self.running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the HubSpot sync worker"""
        if self.running:
            logger.warning("HubSpot sync worker is already running")
            return
        
        if not hubspot_client.enabled:
            logger.info("HubSpot sync worker not started (HUBSPOT_ENABLED=false)")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._run())
        logger.info("HubSpot sync worker started")
    
    async def stop(self):
        """Stop the HubSpot sync worker"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("HubSpot sync worker stopped")
    
    async def _run(self):
        """Main worker loop"""
        while self.running:
            try:
                await self._process_outbox_events()
                await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in HubSpot sync worker: {e}", exc_info=True)
                await asyncio.sleep(self.poll_interval)
    
    async def _process_outbox_events(self):
        """Process pending outbox events for HubSpot"""
        try:
            # Get unprocessed events for HubSpot-relevant event types
            events = await self._get_relevant_unprocessed_events()
            
            for event in events:
                try:
                    # Process the event
                    await self._process_event(event)
                    
                    # Mark as processed
                    await self._mark_event_processed(event["id"])
                    
                    logger.info(f"Processed HubSpot event: {event['id']} ({event['event_type']})")
                    
                except Exception as e:
                    logger.error(f"Error processing HubSpot event {event['id']}: {e}", exc_info=True)
                    # Don't mark as processed if there was an error (will retry)
                    
        except Exception as e:
            logger.error(f"Error processing HubSpot outbox events: {e}", exc_info=True)
    
    async def _get_relevant_unprocessed_events(self) -> List[Dict[str, Any]]:
        """
        Get unprocessed events that are relevant for HubSpot.
        
        Only fetches events of types that HubSpot cares about.
        """
        relevant_types = [
            "driver_signed_up",
            "wallet_pass_installed",
            "nova_earned",
            "nova_redeemed",
            "first_redemption_completed"
        ]
        
        try:
            with get_db_session() as db:
                # Build query with IN clause for relevant event types
                placeholders = ",".join([f"'{t}'" for t in relevant_types])
                result = db.execute(text(f"""
                    SELECT id, event_type, payload_json, created_at
                    FROM outbox_events
                    WHERE processed_at IS NULL
                    AND event_type IN ({placeholders})
                    ORDER BY created_at ASC
                    LIMIT 50
                """))
                
                events = []
                for row in result:
                    events.append({
                        "id": row.id,
                        "event_type": row.event_type,
                        "payload_json": row.payload_json,
                        "created_at": row.created_at
                    })
                
                return events
                
        except Exception as e:
            logger.error(f"Error getting HubSpot relevant events: {e}", exc_info=True)
            return []
    
    async def _process_event(self, event: Dict[str, Any]):
        """Process a single event and send to HubSpot"""
        try:
            # Deserialize the event
            event_data = json.loads(event["payload_json"])
            event_type = event["event_type"]
            
            if event_type not in EVENT_TYPES:
                logger.warning(f"Unknown event type for HubSpot: {event_type}")
                return
            
            event_class = EVENT_TYPES[event_type]
            domain_event = event_class(**event_data)
            
            # Get user email if user_id is available
            email = None
            user_id = getattr(domain_event, "user_id", None)
            if user_id:
                try:
                    with get_db_session() as db:
                        # Try to get user email
                        user = db.query(User).filter(User.id == int(user_id)).first()
                        if user:
                            email = user.email
                except Exception as e:
                    logger.debug(f"Could not fetch email for user {user_id}: {e}")
            
            # Adapt event to HubSpot format
            hubspot_payload = adapt_event_to_hubspot(domain_event, email)
            
            if not hubspot_payload:
                logger.debug(f"Event type {event_type} not supported by HubSpot adapter")
                return
            
            # Get external ID
            external_id = to_hubspot_external_id(int(user_id)) if user_id else None
            
            if not external_id:
                logger.warning(f"No external_id available for HubSpot event {event_type}")
                return
            
            if not email:
                logger.warning(f"No email available for HubSpot event {event_type}, skipping")
                return
            
            # Upsert contact if contact_properties are provided
            if "contact_properties" in hubspot_payload:
                hubspot_client.upsert_contact(
                    email=email,
                    properties=hubspot_payload["contact_properties"],
                    external_id=external_id
                )
            
            # Send event
            hubspot_client.send_event(
                event_name=hubspot_payload["event_name"],
                properties=hubspot_payload["event_properties"],
                email=email,
                external_id=external_id
            )
            
        except Exception as e:
            logger.error(f"Error processing HubSpot event: {e}", exc_info=True)
            raise
    
    async def _mark_event_processed(self, event_id: int):
        """Mark an event as processed"""
        try:
            with get_db_session() as db:
                db.execute(text("""
                    UPDATE outbox_events
                    SET processed_at = :processed_at
                    WHERE id = :event_id
                """), {
                    "processed_at": datetime.utcnow(),
                    "event_id": event_id
                })
                
        except Exception as e:
            logger.error(f"Error marking HubSpot event as processed: {e}", exc_info=True)
            raise


# Global worker instance
hubspot_sync_worker = HubSpotSyncWorker()

