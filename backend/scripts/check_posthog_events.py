#!/usr/bin/env python3
"""
Check PostHog events vs database visits for Saturday Jan 24, 2026
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

# Database connection
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def check_saturday_visits():
    """Check intent_sessions created on Saturday Jan 24, 2026"""
    db = SessionLocal()
    
    # Saturday Jan 24, 2026 00:00:00 UTC to 23:59:59 UTC
    saturday_start = datetime(2026, 1, 24, 0, 0, 0, tzinfo=timezone.utc)
    saturday_end = datetime(2026, 1, 25, 0, 0, 0, tzinfo=timezone.utc)
    
    print(f"\n=== Checking Intent Sessions for Saturday Jan 24, 2026 ===")
    print(f"Time range: {saturday_start} to {saturday_end}\n")
    
    # Query intent_sessions
    query = text("""
        SELECT 
            id,
            user_id,
            lat,
            lng,
            confidence_tier,
            charger_id,
            source,
            created_at
        FROM intent_sessions
        WHERE created_at >= :start_time 
          AND created_at < :end_time
        ORDER BY created_at ASC
    """)
    
    result = db.execute(query, {
        'start_time': saturday_start,
        'end_time': saturday_end
    })
    
    sessions = result.fetchall()
    
    print(f"Total intent_sessions on Saturday: {len(sessions)}\n")
    
    if sessions:
        print("Sessions:")
        for i, session in enumerate(sessions, 1):
            print(f"  {i}. ID: {session[0]}, User: {session[1]}, Tier: {session[4]}, Created: {session[7]}")
    else:
        print("No intent_sessions found for Saturday")
    
    # Check verified visits
    visit_query = text("""
        SELECT 
            id,
            driver_id,
            merchant_id,
            verification_code,
            verified_at
        FROM verified_visits
        WHERE verified_at >= :start_time 
          AND verified_at < :end_time
        ORDER BY verified_at ASC
    """)
    
    visit_result = db.execute(visit_query, {
        'start_time': saturday_start,
        'end_time': saturday_end
    })
    
    visits = visit_result.fetchall()
    
    print(f"\nTotal verified_visits on Saturday: {len(visits)}\n")
    
    if visits:
        print("Visits:")
        for i, visit in enumerate(visits, 1):
            print(f"  {i}. Code: {visit[3]}, Driver: {visit[1]}, Merchant: {visit[2]}, Verified: {visit[4]}")
    
    db.close()
    
    return len(sessions), len(visits)

if __name__ == "__main__":
    sessions_count, visits_count = check_saturday_visits()
    print(f"\n=== Summary ===")
    print(f"Intent Sessions: {sessions_count}")
    print(f"Verified Visits: {visits_count}")
    print(f"\nNote: PostHog events should match intent_sessions count")
    print(f"If PostHog shows fewer events, check:")
    print(f"  1. POSTHOG_KEY environment variable")
    print(f"  2. ANALYTICS_ENABLED setting")
    print(f"  3. Frontend VITE_POSTHOG_KEY")
    print(f"  4. Analytics consent banner")
    print(f"  5. PostHog API errors in logs")
