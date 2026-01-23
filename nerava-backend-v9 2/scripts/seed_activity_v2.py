#!/usr/bin/env python3
"""
Seed script for Activity v2 demo data
Creates users, reputation scores, and follow earnings
"""

import os
import sys
import uuid
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

def month_now():
    return int(datetime.now().strftime("%Y%m"))

def main():
    # Get database session
    db = next(get_db())
    
    # Demo user IDs
    me = os.getenv('DEMO_ME_ID', str(uuid.uuid4()))
    u1 = os.getenv('DEMO_U1_ID', str(uuid.uuid4()))
    u2 = os.getenv('DEMO_U2_ID', str(uuid.uuid4()))
    
    try:
        # Create users
        db.execute(text("""
            INSERT INTO users (id, handle, avatar_url) VALUES
            ($1, 'you', ''),
            ($2, 'alex', ''),
            ($3, 'sam', '')
            ON CONFLICT (id) DO NOTHING
        """), [me, u1, u2])
        
        # Me: Silver 180, 7-day streak
        db.execute(text("""
            INSERT INTO user_reputation (user_id, score, tier, streak_days)
            VALUES ($1, 180, 'Silver', 7)
            ON CONFLICT (user_id) DO UPDATE
            SET score = EXCLUDED.score, tier = EXCLUDED.tier, 
                streak_days = EXCLUDED.streak_days, updated_at = now()
        """), [me])
        
        # Payers with visible tiers
        db.execute(text("""
            INSERT INTO user_reputation (user_id, score, tier, streak_days)
            VALUES
            ($1, 520, 'Gold', 3),
            ($2, 80, 'Bronze', 1)
            ON CONFLICT (user_id) DO UPDATE 
            SET score = EXCLUDED.score, tier = EXCLUDED.tier, 
                streak_days = EXCLUDED.streak_days, updated_at = now()
        """), [u1, u2])
        
        # Follow earnings for current month
        m = month_now()
        db.execute(text("""
            INSERT INTO follow_earnings_monthly (month_yyyymm, receiver_user_id, payer_user_id, amount_cents)
            VALUES
            ($1, $2, $3, 185),
            ($1, $2, $4, 90)
            ON CONFLICT DO NOTHING
        """), [m, me, u1, u2])
        
        db.commit()
        print(f'✅ Seed complete: me={me}, u1={u1}, u2={u2}, month={m}')
        
    except Exception as e:
        db.rollback()
        print(f'❌ Seed failed: {e}')
        sys.exit(1)
    finally:
        db.close()

if __name__ == '__main__':
    main()
