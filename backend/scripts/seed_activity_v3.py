#!/usr/bin/env python3
"""
Seed script for Activity v3 with context and scrolling list
Creates 10 users with varied tiers and context-rich earnings
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
    ids = [str(uuid.uuid4()) for _ in range(10)]
    handles = ['alex','sam','riley','jordan','morgan','taylor','casey','kai','remy','avery']
    
    try:
        # Create users
        user_values = [f"('{me}','you','')"]
        user_values.extend([f"('{ids[i]}','{handles[i]}','')" for i in range(10)])
        
        db.execute(text(f"""
            INSERT INTO users (id, handle, avatar_url) VALUES 
            {','.join(user_values)}
            ON CONFLICT (id) DO NOTHING
        """))
        
        # My reputation
        db.execute(text("""
            INSERT INTO user_reputation (user_id, score, tier, streak_days)
            VALUES ($1, 180, 'Silver', 7)
            ON CONFLICT (user_id) DO UPDATE
            SET score = EXCLUDED.score, tier = EXCLUDED.tier, 
                streak_days = EXCLUDED.streak_days, updated_at = now()
        """), [me])
        
        # Payers' tiers with variety
        tier_map = ['Gold','Bronze','Silver','Gold','Bronze','Silver','Gold','Bronze','Silver','Gold']
        for i, (user_id, tier) in enumerate(zip(ids, tier_map)):
            score = 80 + i * 35
            streak = 1 + (i % 5)
            db.execute(text("""
                INSERT INTO user_reputation (user_id, score, tier, streak_days)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE 
                SET score = EXCLUDED.score, tier = EXCLUDED.tier, 
                    streak_days = EXCLUDED.streak_days, updated_at = now()
            """), [user_id, score, tier, streak])
        
        # 10 earnings rows with context + varied amounts
        m = month_now()
        places = [
            'Starbucks','Target','Whole Foods','H-E-B','Costco',
            'Trader Joe\'s','REI','IKEA','Best Buy','Kroger'
        ]
        verbs = [
            'charged and chilled at','topped up at','smart-charged at',
            'queued and earned at','plugged in at'
        ]
        
        for i, (user_id, place, verb) in enumerate(zip(ids, places, [verbs[i % len(verbs)] for i in range(10)])):
            amount = 60 + i * 15  # cents
            context = f"{verb} {place}"
            
            db.execute(text("""
                INSERT INTO follow_earnings_monthly
                (month_yyyymm, receiver_user_id, payer_user_id, amount_cents, created_at, context)
                VALUES ($1, $2, $3, $4, now(), $5)
                ON CONFLICT DO NOTHING
            """), [m, me, user_id, amount, context])
        
        db.commit()
        print(f'✅ Seed v3 complete: me={me}, month={m}, 10 users with context')
        
    except Exception as e:
        db.rollback()
        print(f'❌ Seed failed: {e}')
        sys.exit(1)
    finally:
        db.close()

if __name__ == '__main__':
    main()
