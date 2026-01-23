#!/usr/bin/env python3
"""
Seed script for Activity with counts and demo intent
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

def main():
    # Get database session
    db = next(get_db())
    
    # Demo user ID
    me = os.getenv('DEMO_ME_ID', str(uuid.uuid4()))
    
    try:
        # Update reputation with counts
        db.execute(text("""
            UPDATE user_reputation 
            SET followers_count = 12, following_count = 8 
            WHERE user_id = :user_id
        """), {'user_id': me})
        
        # Insert demo intent
        db.execute(text("""
            INSERT INTO charge_intents
            (id, user_id, station_id, station_name, merchant_name, perk_title, address, eta_minutes,
             merchant_lat, merchant_lng, station_lat, station_lng)
            VALUES (:id, :user_id, 'TESLA_AUS_001', 'Tesla Supercharger – Domain',
                    'Starbucks', 'Free coffee 2–4pm', '310 E 5th St, Austin, TX', 15,
                    30.2653, -97.7393, 30.4021, -97.7266)
            ON CONFLICT DO NOTHING
        """), {'id': str(uuid.uuid4()), 'user_id': me})
        
        db.commit()
        print(f'✅ Seed complete: me={me}, added counts and demo intent')
        
    except Exception as e:
        db.rollback()
        print(f'❌ Seed failed: {e}')
        sys.exit(1)
    finally:
        db.close()

if __name__ == '__main__':
    main()
