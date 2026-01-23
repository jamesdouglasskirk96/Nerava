#!/usr/bin/env python3
"""Test database schema"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from db import SessionLocal
from sqlalchemy import text

def main():
    db = SessionLocal()
    try:
        # Check if payments table exists
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='payments'"))
        payments_exists = result.fetchone() is not None
        print(f"Payments table exists: {payments_exists}")
        
        # Check if reward_events table exists
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='reward_events'"))
        rewards_exists = result.fetchone() is not None
        print(f"Reward events table exists: {rewards_exists}")
        
        # List all tables
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        print(f"All tables: {tables}")
        
        # If payments table exists, check its structure
        if payments_exists:
            result = db.execute(text("PRAGMA table_info(payments)"))
            columns = result.fetchall()
            print(f"Payments table columns: {[col[1] for col in columns]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
