# server/tests/test_square_route.py
import pytest
import json
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.main_simple import app
from src.config import config

# Test database setup
TEST_DB_URL = "sqlite:///./test_nerava.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)

def test_square_checkout_flow():
    """Test end-to-end: create checkout → simulate webhook → wallet balance increases"""
    
    # Setup: Create a payment in the database
    db = SessionLocal()
    demo_user_id = config.DEMO_USER_ID
    payment_id = str(uuid.uuid4())
    
    # Insert test payment
    db.execute(text("""
        INSERT INTO payments (id, user_id, merchant_id, amount_cents, note, status)
        VALUES (:id, :user_id, :merchant_id, :amount_cents, :note, :status)
    """), {
        'id': payment_id,
        'user_id': demo_user_id,
        'merchant_id': 'test-merchant',
        'amount_cents': 1000,  # $10.00
        'note': 'Test payment',
        'status': 'PENDING'
    })
    db.commit()
    
    try:
        # Get initial wallet balance
        initial_result = client.get(
            "/v1/wallet/summary",
            headers={"X-User-Id": demo_user_id}
        )
        initial_balance = initial_result.json()["availableCreditCents"]
        
        # Simulate payment completion via mock endpoint
        response = client.post(
            "/v1/square/mock-payment",
            json={
                "paymentId": payment_id,
                "status": "COMPLETED"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "success"
        
        # Get updated wallet balance
        updated_result = client.get(
            "/v1/wallet/summary",
            headers={"X-User-Id": demo_user_id}
        )
        updated_balance = updated_result.json()["availableCreditCents"]
        
        # Verify balance increased by 20% (200 cents from $10 payment)
        expected_increase = 200
        assert updated_balance == initial_balance + expected_increase, \
            f"Balance should increase by {expected_increase}. Initial: {initial_balance}, Updated: {updated_balance}"
        
        # Test idempotency: call mock-payment again
        idempotent_response = client.post(
            "/v1/square/mock-payment",
            json={
                "paymentId": payment_id,
                "status": "COMPLETED"
            }
        )
        idempotent_result = idempotent_response.json()
        assert idempotent_result["status"] == "success"
        assert "already_processed" in idempotent_result.get("message", "")
        
        # Verify balance did NOT increase again
        final_result = client.get(
            "/v1/wallet/summary",
            headers={"X-User-Id": demo_user_id}
        )
        final_balance = final_result.json()["availableCreditCents"]
        assert final_balance == updated_balance, \
            f"Balance should not change on second call. Updated: {updated_balance}, Final: {final_balance}"
        
        print("✅ Square payment flow test passed!")
        print(f"  Initial balance: {initial_balance} cents")
        print(f"  After payment: {updated_balance} cents")
        print(f"  Increase: {updated_balance - initial_balance} cents")
        
    finally:
        # Cleanup
        db.execute(text("DELETE FROM payments WHERE id = :id"), {'id': payment_id})
        db.execute(text("DELETE FROM wallet_events WHERE json_extract(meta, '$.payment_id') = :payment_id"), 
                   {'payment_id': payment_id})
        db.commit()
        db.close()

if __name__ == "__main__":
    test_square_checkout_flow()

