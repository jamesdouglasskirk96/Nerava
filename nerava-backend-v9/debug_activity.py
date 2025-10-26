#!/usr/bin/env python3
import os
import sys
import traceback

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.db import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

def test_activity_query():
    try:
        # Get database session
        db = next(get_db())
        
        # Demo user ID
        me = "demo-user-123"
        
        # Get current month
        from datetime import datetime
        month = int(datetime.now().strftime("%Y%m"))
        print(f"Testing with user_id: {me}, month: {month}")
        
        # Test reputation query
        rep_query = text("SELECT score, tier, COALESCE(streak_days, 0), COALESCE(followers_count, 0), COALESCE(following_count, 0) FROM user_reputation WHERE user_id = :user_id")
        rep_result = db.execute(rep_query, {'user_id': me})
        rep_row = rep_result.fetchone()
        print(f"Reputation query result: {rep_row}")
        
        if rep_row:
            reputation = {
                'score': rep_row[0],
                'tier': rep_row[1],
                'streakDays': rep_row[2],
                'followers_count': rep_row[3],
                'following_count': rep_row[4]
            }
            print(f"Reputation object: {reputation}")
        
        # Test earnings query
        earn_query = text("""
            SELECT fem.payer_user_id AS user_id,
                   COALESCE(u.handle,'member') AS handle,
                   u.avatar_url,
                   COALESCE(ur.tier,'Bronze') AS tier,
                   fem.amount_cents,
                   fem.context
            FROM follow_earnings_monthly fem
            LEFT JOIN users u ON u.id = fem.payer_user_id
            LEFT JOIN user_reputation ur ON ur.user_id = fem.payer_user_id
            WHERE fem.month_yyyymm = :month AND fem.receiver_user_id = :user_id
            ORDER BY fem.amount_cents DESC
        """)
        
        earn_result = db.execute(earn_query, {'month': month, 'user_id': me})
        earnings = []
        total_cents = 0
        
        for row in earn_result:
            earnings.append({
                'userId': row[0],
                'handle': row[1],
                'avatarUrl': row[2],
                'tier': row[3],
                'amountCents': int(row[4]),
                'context': row[5]
            })
            total_cents += int(row[4])
        
        print(f"Earnings query result: {len(earnings)} rows, total_cents: {total_cents}")
        
        # Test final response
        response = {
            'month': month,
            'reputation': reputation if rep_row else {
                'score': 180,
                'tier': 'Silver',
                'streakDays': 7,
                'followers_count': 12,
                'following_count': 8
            },
            'followEarnings': earnings,
            'totals': {
                'followCents': total_cents
            }
        }
        
        print(f"Final response: {response}")
        print("✅ Activity query test successful!")
        
    except Exception as e:
        print(f"❌ Activity query test failed: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    test_activity_query()
