#!/usr/bin/env python3
"""
Seed script for Activity demo data
"""
import os
import sys
import uuid
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db import get_db
from sqlalchemy import text

def days_ago(n: int):
    return datetime.now() - timedelta(days=n)

async def seed_activity():
    db = next(get_db())
    
    # Demo users
    me = os.getenv('DEMO_ME_ID', str(uuid.uuid4()))
    alex = os.getenv('DEMO_U1_ID', str(uuid.uuid4()))
    sam = os.getenv('DEMO_U2_ID', str(uuid.uuid4()))
    
    print(f"Seeding Activity demo with users: {me}, {alex}, {sam}")
    
    # Insert users
    users_query = text("""
        INSERT INTO users (id, handle, avatar_url) VALUES
        (:me, 'you', ''),
        (:alex, 'alex', ''),
        (:sam, 'sam', '')
        ON CONFLICT (id) DO NOTHING
    """)
    db.execute(users_query, {'me': me, 'alex': alex, 'sam': sam})
    
    # Insert reputation
    rep_query = text("""
        INSERT INTO user_reputation (user_id, score, tier)
        VALUES (:me, 180, 'Silver'), (:alex, 420, 'Gold'), (:sam, 95, 'Bronze')
        ON CONFLICT (user_id) DO UPDATE SET 
            score = EXCLUDED.score, 
            tier = EXCLUDED.tier, 
            updated_at = NOW()
    """)
    db.execute(rep_query, {'me': me, 'alex': alex, 'sam': sam})
    
    # Insert sessions
    s1 = str(uuid.uuid4())
    s2 = str(uuid.uuid4())
    s3 = str(uuid.uuid4())
    
    sessions_query = text("""
        INSERT INTO sessions(id, user_id, station_id, start_at, end_at, energy_kwh) VALUES
        (:s1, :me, 'STATION_A', :day2, :day2, 18.2),
        (:s2, :alex, 'STATION_A', :day5, :day5, 12.0),
        (:s3, :me, 'STATION_B', :day1, :day1, 9.5)
        ON CONFLICT DO NOTHING
    """)
    db.execute(sessions_query, {
        's1': s1, 's2': s2, 's3': s3,
        'me': me, 'alex': alex,
        'day1': days_ago(1),
        'day2': days_ago(2),
        'day5': days_ago(5)
    })
    
    # Insert follows: me follows alex (auto)
    follows_query = text("""
        INSERT INTO follows(follower_id, followee_id, is_auto) 
        VALUES (:me, :alex, true)
        ON CONFLICT DO NOTHING
    """)
    db.execute(follows_query, {'me': me, 'alex': alex})
    
    # Insert earnings: alex charged → me earns
    earnings_query = text("""
        INSERT INTO follow_earnings_events(id, payer_user_id, receiver_user_id, station_id, session_id, energy_kwh, amount_cents)
        VALUES (:event_id, :alex, :me, 'STATION_A', :s2, 12.0, 64)
        ON CONFLICT DO NOTHING
    """)
    db.execute(earnings_query, {
        'event_id': str(uuid.uuid4()),
        'alex': alex,
        'me': me,
        's2': s2
    })
    
    db.commit()
    print("Seeded Activity demo successfully!")
    print(f"Users: {me}, {alex}, {sam}")
    print("Run the backend and visit /v1/activity to see the data")

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_activity())
