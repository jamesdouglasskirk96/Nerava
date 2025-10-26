#!/usr/bin/env python3
"""Debug wallet summary"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from db import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    user_id = 'user-demo-1'
    
    try:
        print("Testing wallet summary components...")
        
        # Test wallet events query
        print("1. Testing wallet events...")
        result = db.execute(text("SELECT * FROM wallet_events WHERE user_id = :user_id"), {'user_id': user_id})
        wallet_rows = result.fetchall()
        print(f"   Found {len(wallet_rows)} wallet events")
        
        # Test Square payments query
        print("2. Testing Square payments...")
        result = db.execute(text("""
            SELECT merchant_id, amount_cents, created_at, status
            FROM payments 
            WHERE user_id = :user_id AND status = 'COMPLETED'
            ORDER BY created_at DESC
            LIMIT 10
        """), {'user_id': user_id})
        payments = result.fetchall()
        print(f"   Found {len(payments)} completed payments")
        
        # Test reward events query
        print("3. Testing reward events...")
        result = db.execute(text("""
            SELECT type, amount_cents, created_at
            FROM reward_events 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 10
        """), {'user_id': user_id})
        rewards = result.fetchall()
        print(f"   Found {len(rewards)} reward events")
        
        print("All queries successful!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
