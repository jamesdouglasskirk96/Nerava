#!/usr/bin/env python3
"""Test payments table queries"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from db import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    try:
        # Test simple query
        result = db.execute(text("SELECT COUNT(*) FROM payments"))
        count = result.fetchone()[0]
        print(f"Payments count: {count}")
        
        # Test query with user filter
        result = db.execute(text("SELECT * FROM payments WHERE user_id = :user_id"), {'user_id': 'user-demo-1'})
        payments = result.fetchall()
        print(f"Payments for user-demo-1: {len(payments)}")
        for payment in payments:
            print(f"  {payment}")
        
        # Test reward_events query
        result = db.execute(text("SELECT COUNT(*) FROM reward_events"))
        count = result.fetchone()[0]
        print(f"Reward events count: {count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()
