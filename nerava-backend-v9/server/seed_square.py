#!/usr/bin/env python3
"""
Square Demo Seed Script
Creates demo data and provides test commands for Square integration
"""

import os
import sys
import uuid
from sqlalchemy import text

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from db import SessionLocal

def main():
    db = SessionLocal()
    demo_user_id = os.getenv('DEMO_USER_ID', 'user-demo-1')
    
    print("🌱 Seeding Square demo data...")
    
    try:
        # Ensure demo user exists
        db.execute(text("""
            INSERT INTO users (id, handle, followers, following)
            VALUES (:id, 'you', 12, 8)
            ON CONFLICT (id) DO NOTHING
        """), {'id': demo_user_id})
        
        # Ensure reputation exists
        db.execute(text("""
            INSERT INTO user_reputation (user_id, score, tier)
            VALUES (:user_id, 180, 'Silver')
            ON CONFLICT (user_id) DO NOTHING
        """), {'user_id': demo_user_id})
        
        db.commit()
        
        print(f"✅ Demo user created: {demo_user_id}")
        
        # Generate test commands
        print("\n🧪 Test Commands:")
        print("=" * 50)
        
        print("\n1. Create Square checkout (via API):")
        print(f"""curl -X POST http://127.0.0.1:8001/v1/square/checkout \\
  -H 'Content-Type: application/json' \\
  -H 'X-User-Id: {demo_user_id}' \\
  -d '{{"merchantId": "starbucks", "amountCents": 500, "note": "Perk @ Starbucks"}}'""")
        
        print("\n2. Mock payment completion:")
        payment_id = str(uuid.uuid4())
        print(f"""curl -X POST http://127.0.0.1:8001/v1/square/mock-payment \\
  -H 'Content-Type: application/json' \\
  -d '{{"paymentId": "{payment_id}", "status": "COMPLETED"}}'""")
        
        print("\n3. Check payment history:")
        print(f"""curl -H 'X-User-Id: {demo_user_id}' http://127.0.0.1:8001/v1/square/payments/me""")
        
        print("\n4. Check wallet summary:")
        print(f"""curl -H 'X-User-Id: {demo_user_id}' http://127.0.0.1:8001/v1/wallet/summary""")
        
        print("\n🎯 UI Testing:")
        print("1. Open http://127.0.0.1:5173")
        print("2. Go to Explore tab")
        print("3. Click 'Pay & Claim' button")
        print("4. Complete mock payment")
        print("5. Check Wallet tab for new payment and reward")
        
        print(f"\n✅ Square demo setup complete!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
