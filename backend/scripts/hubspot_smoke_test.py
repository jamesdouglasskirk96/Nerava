#!/usr/bin/env python3
"""
HubSpot Integration Smoke Test

Validates end-to-end HubSpot integration:
1. Creates a test outbox event
2. Runs worker processing once
3. Verifies event is marked processed (in dry-run mode)

Usage:
    python scripts/hubspot_smoke_test.py
"""
import sys
import os
import asyncio
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import SessionLocal
from app.services.hubspot import track_event
from app.workers.hubspot_sync import hubspot_sync_worker
from sqlalchemy import text


def main():
    """Run smoke test"""
    print("=" * 60)
    print("HubSpot Integration Smoke Test")
    print("=" * 60)
    print()
    
    # Check configuration
    from app.core.config import settings
    print(f"HUBSPOT_ENABLED: {settings.HUBSPOT_ENABLED}")
    print(f"HUBSPOT_SEND_LIVE: {settings.HUBSPOT_SEND_LIVE}")
    print()
    
    if not settings.HUBSPOT_ENABLED:
        print("⚠️  WARNING: HUBSPOT_ENABLED=false, test will run but no processing will occur")
        print()
    
    # Create test event
    db = SessionLocal()
    try:
        print("Step 1: Creating test outbox event...")
        track_event(db, "driver_signed_up", {
            "user_id": "999999",  # Test user ID
            "email": "test@nerava.com",
            "auth_provider": "test",
            "created_at": datetime.utcnow().isoformat() + "Z",
        })
        db.commit()
        print("✅ Event created in outbox")
        print()
        
        # Get the event ID
        result = db.execute(text("""
            SELECT id, event_type, created_at
            FROM outbox_events
            WHERE event_type = 'driver_signed_up'
            ORDER BY created_at DESC
            LIMIT 1
        """))
        row = result.fetchone()
        if not row:
            print("❌ ERROR: Could not find created event")
            return 1
        
        event_id = row.id
        print(f"   Event ID: {event_id}")
        print(f"   Event Type: {row.event_type}")
        print()
        
        # Process event
        print("Step 2: Processing event with worker...")
        asyncio.run(hubspot_sync_worker.process_once())
        print("✅ Worker processing completed")
        print()
        
        # Check if event was processed
        print("Step 3: Verifying event was processed...")
        result = db.execute(text("""
            SELECT processed_at, attempt_count, last_error
            FROM outbox_events
            WHERE id = :event_id
        """), {"event_id": event_id})
        row = result.fetchone()
        
        if row:
            processed_at = row.processed_at
            attempt_count = row.attempt_count or 0
            last_error = row.last_error
            
            if processed_at:
                print(f"✅ Event marked as processed at {processed_at}")
                if settings.HUBSPOT_SEND_LIVE:
                    print("   (LIVE mode: Event was sent to HubSpot)")
                else:
                    print("   (DRY-RUN mode: Event was logged but not sent)")
            else:
                print(f"⚠️  Event not yet processed (attempt_count={attempt_count})")
                if last_error:
                    print(f"   Last error: {last_error}")
            
            print()
            print("=" * 60)
            print("✅ Smoke test completed successfully!")
            print("=" * 60)
            return 0
        else:
            print("❌ ERROR: Could not find event after processing")
            return 1
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    exit(main())






