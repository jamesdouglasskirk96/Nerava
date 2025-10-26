from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import json
from typing import Dict, Any
from .db import get_db
from .deps import current_user_id
from .square_client import square
from .config import config

router = APIRouter(prefix="/v1/square")

@router.post("/checkout")
async def create_checkout(
    request_data: Dict[str, Any],
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db)
):
    """Create Square checkout link"""
    merchant_id = request_data.get('merchantId')
    amount_cents = request_data.get('amountCents')
    note = request_data.get('note', '')
    
    if not merchant_id or not amount_cents:
        raise HTTPException(status_code=400, detail="merchantId and amountCents required")
    
    payment_id = str(uuid.uuid4())
    
    # Insert payment record
    db.execute(text("""
        INSERT INTO payments (id, user_id, merchant_id, amount_cents, note)
        VALUES (:id, :user_id, :merchant_id, :amount_cents, :note)
    """), {
        'id': payment_id,
        'user_id': user_id,
        'merchant_id': merchant_id,
        'amount_cents': amount_cents,
        'note': note
    })
    db.commit()
    
    # Create checkout link
    redirect_url = f"{config.PUBLIC_BASE_URL}/?tab=wallet&paid={payment_id}"
    
    checkout_request = {
        'idempotencyKey': payment_id,
        'description': note or f"Nerava: {merchant_id}",
        'quickPay': {
            'name': f"Nerava • {merchant_id}",
            'priceMoney': {'amount': amount_cents, 'currency': 'USD'},
            'locationId': config.SQUARE_LOCATION_ID,
        },
        'checkoutOptions': {'redirectUrl': redirect_url},
        'metadata': {
            'nerava_payment_id': payment_id,
            'merchant_id': merchant_id,
            'user_id': user_id
        }
    }
    
    result = await square.checkoutApi.create_payment_link(checkout_request)
    
    return {
        'url': result['result']['paymentLink']['url'],
        'paymentId': payment_id
    }

@router.post("/webhook")
async def square_webhook(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Handle Square webhook events"""
    try:
        event_type = request_data.get('type')
        if event_type != 'payment.updated':
            return {'status': 'ignored'}
        
        payment_data = request_data.get('data', {}).get('object', {}).get('payment', {})
        if not payment_data:
            return {'status': 'ignored'}
        
        provider_payment_id = payment_data.get('id')
        amount_cents = int(payment_data.get('amountMoney', {}).get('amount', 0))
        status = payment_data.get('status')
        metadata = payment_data.get('metadata', {})
        
        nerava_id = metadata.get('nerava_payment_id')
        user_id = metadata.get('user_id')
        
        if not nerava_id:
            return {'status': 'ignored'}
        
        # Update payment status
        db.execute(text("""
            UPDATE payments
            SET status = :status, provider_payment_id = :provider_payment_id
            WHERE id = :id
        """), {
            'status': status,
            'provider_payment_id': provider_payment_id,
            'id': nerava_id
        })
        
        # If completed, add reward event
        if status == 'COMPLETED' and user_id:
            reward_amount = int(amount_cents * 0.2)  # 20% reward
            reward_id = str(uuid.uuid4())
            
            db.execute(text("""
                INSERT INTO reward_events (id, user_id, type, amount_cents)
                VALUES (:id, :user_id, :type, :amount_cents)
            """), {
                'id': reward_id,
                'user_id': user_id,
                'type': 'merchant',
                'amount_cents': reward_amount
            })
        
        db.commit()
        return {'status': 'success'}
        
    except Exception as e:
        print(f"Square webhook error: {e}")
        return {'status': 'error'}

@router.get("/payments/me")
async def get_my_payments(
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db)
):
    """Get user's payment history"""
    result = db.execute(text("""
        SELECT id, merchant_id, status, amount_cents, created_at
        FROM payments 
        WHERE user_id = :user_id 
        ORDER BY created_at DESC 
        LIMIT 50
    """), {'user_id': user_id})
    
    payments = []
    for row in result:
        payments.append({
            'id': row[0],
            'merchantId': row[1],
            'status': row[2],
            'amountCents': row[3],
            'createdAt': str(row[4]) if row[4] else None
        })
    
    return payments

@router.get("/payments/test")
async def test_payments(
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db)
):
    """Test payments query"""
    try:
        result = db.execute(text("SELECT COUNT(*) FROM payments WHERE user_id = :user_id"), {'user_id': user_id})
        count = result.fetchone()[0]
        return {"status": "success", "count": count}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/payments/test2")
async def test_payments2(
    user_id: str = Depends(current_user_id),
    db: Session = Depends(get_db)
):
    """Test payments query with data"""
    try:
        result = db.execute(text("""
            SELECT id, merchant_id, status, amount_cents, created_at
            FROM payments 
            WHERE user_id = :user_id 
            ORDER BY created_at DESC 
            LIMIT 5
        """), {'user_id': user_id})
        
        payments = []
        for row in result:
            payments.append({
                'id': row[0],
                'merchantId': row[1],
                'status': row[2],
                'amountCents': row[3],
                'createdAt': str(row[4]) if row[4] else None
            })
        
        return {"status": "success", "payments": payments}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.post("/mock-payment")
async def mock_payment_completion(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Mock endpoint to simulate payment completion for testing"""
    payment_id = request_data.get('paymentId')
    status = request_data.get('status', 'COMPLETED')
    
    if not payment_id:
        raise HTTPException(status_code=400, detail="paymentId required")
    
    # Update payment status
    db.execute(text("""
        UPDATE payments
        SET status = :status, provider_payment_id = :provider_payment_id
        WHERE id = :id
    """), {
        'status': status,
        'provider_payment_id': f"MOCK_{payment_id}",
        'id': payment_id
    })
    
    # If completed, add reward event
    if status == 'COMPLETED':
        # Get payment details
        result = db.execute(text("""
            SELECT user_id, amount_cents FROM payments WHERE id = :id
        """), {'id': payment_id})
        
        row = result.fetchone()
        if row:
            user_id, amount_cents = row
            reward_amount = int(amount_cents * 0.2)  # 20% reward
            reward_id = str(uuid.uuid4())
            
            db.execute(text("""
                INSERT INTO reward_events (id, user_id, type, amount_cents)
                VALUES (:id, :user_id, :type, :amount_cents)
            """), {
                'id': reward_id,
                'user_id': user_id,
                'type': 'merchant',
                'amount_cents': reward_amount
            })
    
    db.commit()
    return {'status': 'success', 'message': f'Payment {payment_id} marked as {status}'}
