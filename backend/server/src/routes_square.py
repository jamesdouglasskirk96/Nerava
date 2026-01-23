"""
LEGACY CODE - DO NOT DEPLOY

This module is legacy code and contains dangerous bypass logic.
It should NOT be deployed in production.

If you see this error, it means legacy code from server/src/ is being imported.
Use app/routers/ instead.
"""
import os

# DEPLOYMENT GUARD: Fail if accidentally imported in non-local environment
# This prevents dangerous bypass logic from being used in production
env = os.getenv("ENV", "dev").lower()
if env not in {"local", "dev"}:
    raise RuntimeError(
        "CRITICAL SECURITY ERROR: Legacy code from server/src/routes_square.py "
        "is being imported in a non-local environment. This code contains "
        "dangerous bypass logic (DEV_WEBHOOK_BYPASS) and must not be deployed. "
        f"ENV={env}. Use app/routers/ instead of server/src/."
    )

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import json
import hashlib
import base64
import hmac
import logging
from typing import Dict, Any
from .db import get_db
from .deps import current_user_id
from .square_client import square
from .config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/square")

def verify_square_signature(body: bytes, signature: str) -> bool:
    """Verify Square webhook signature per Square docs"""
    if config.DEV_WEBHOOK_BYPASS or config.SQUARE_WEBHOOK_SIGNATURE_KEY == 'REPLACE_ME':
        return True  # Bypass in dev mode
    
    try:
        # Decode signature from base64
        expected_signature = base64.b64decode(signature)
        
        # Create HMAC signature from body
        signature_key_bytes = config.SQUARE_WEBHOOK_SIGNATURE_KEY.encode('utf-8')
        calculated_signature = hmac.new(
            signature_key_bytes,
            body,
            hashlib.sha256
        ).digest()
        
        # Compare signatures using constant-time comparison
        return hmac.compare_digest(expected_signature, calculated_signature)
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False

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
async def square_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Square webhook events with signature verification and idempotency"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature (bypassed in dev mode)
        signature = request.headers.get('X-Square-Signature', '')
        if not verify_square_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse webhook event
        event = json.loads(body.decode('utf-8'))
        event_type = event.get('type')
        
        if event_type != 'payment.updated':
            return {'status': 'ignored'}
        
        payment_data = event.get('data', {}).get('object', {}).get('payment', {})
        if not payment_data:
            return {'status': 'ignored'}
        
        # Extract payment details
        provider_payment_id = payment_data.get('id')
        amount_cents = int(payment_data.get('amountMoney', {}).get('amount', 0))
        status = payment_data.get('status')
        metadata = payment_data.get('metadata', {})
        
        nerava_id = metadata.get('nerava_payment_id')
        user_id = metadata.get('user_id')
        
        if not nerava_id or not user_id:
            logger.warning(f"Missing metadata: nerava_id={nerava_id}, user_id={user_id}")
            return {'status': 'ignored'}
        
        # Upsert payment status
        db.execute(text("""
            UPDATE payments
            SET status = :status, provider_payment_id = :provider_payment_id
            WHERE id = :id
        """), {
            'status': status,
            'provider_payment_id': provider_payment_id,
            'id': nerava_id
        })
        db.flush()  # Ensure payment update is committed before reward check
        
        # If completed, add reward event with idempotency
        if status == 'COMPLETED':
            # Check if reward already exists for this payment
            existing_reward = db.execute(text("""
                SELECT id FROM wallet_events 
                WHERE user_id = :user_id 
                AND source = 'merchant_reward'
                AND json_extract(meta, '$.payment_id') = :payment_id
                LIMIT 1
            """), {
                'user_id': user_id,
                'payment_id': nerava_id
            }).fetchone()
            
            if existing_reward:
                logger.info(f"Reward already exists for payment {nerava_id}")
                db.commit()
                return {'status': 'success', 'message': 'already_processed'}
            
            # Insert reward event
            reward_amount = int(amount_cents * 0.2)  # 20% reward
            reward_id = str(uuid.uuid4())
            
            reward_meta = json.dumps({
                'payment_id': nerava_id,
                'provider_payment_id': provider_payment_id,
                'amount_paid_cents': amount_cents
            })
            
            db.execute(text("""
                INSERT INTO wallet_events (id, user_id, kind, source, amount_cents, meta)
                VALUES (:id, :user_id, :kind, :source, :amount_cents, :meta)
            """), {
                'id': reward_id,
                'user_id': user_id,
                'kind': 'credit',
                'source': 'merchant_reward',
                'amount_cents': reward_amount,
                'meta': reward_meta
            })
        
        db.commit()
        return {'status': 'success'}
        
    except Exception as e:
        logger.exception(f"Square webhook error: {e}")
        return {'status': 'error', 'message': str(e)}

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
    """Mock endpoint to simulate payment completion for testing (idempotent)"""
    payment_id = request_data.get('paymentId')
    status = request_data.get('status', 'COMPLETED')
    
    if not payment_id:
        raise HTTPException(status_code=400, detail="paymentId required")
    
    # Get payment details first
    payment_result = db.execute(text("""
        SELECT user_id, amount_cents FROM payments WHERE id = :id
    """), {'id': payment_id})
    
    row = payment_result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    user_id, amount_cents = row
    
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
    db.flush()
    
    # If completed, add reward event with idempotency check
    if status == 'COMPLETED':
        # Check if reward already exists for this payment
        existing_reward = db.execute(text("""
            SELECT id FROM wallet_events 
            WHERE user_id = :user_id 
            AND source = 'merchant_reward'
            AND json_extract(meta, '$.payment_id') = :payment_id
            LIMIT 1
        """), {
            'user_id': user_id,
            'payment_id': payment_id
        }).fetchone()
        
        if existing_reward:
            logger.info(f"Reward already exists for payment {payment_id}")
            db.commit()
            return {'status': 'success', 'message': 'already_processed'}
        
        # Insert reward event
        reward_amount = int(amount_cents * 0.2)  # 20% reward
        reward_id = str(uuid.uuid4())
        
        reward_meta = json.dumps({
            'payment_id': payment_id,
            'provider_payment_id': f"MOCK_{payment_id}",
            'amount_paid_cents': amount_cents
        })
        
        db.execute(text("""
            INSERT INTO wallet_events (id, user_id, kind, source, amount_cents, meta)
            VALUES (:id, :user_id, :kind, :source, :amount_cents, :meta)
        """), {
            'id': reward_id,
            'user_id': user_id,
            'kind': 'credit',
            'source': 'merchant_reward',
            'amount_cents': reward_amount,
            'meta': reward_meta
        })
    
    db.commit()
    return {'status': 'success', 'message': f'Payment {payment_id} marked as {status}'}

@router.post("/dev/square/mock-payment")
async def dev_mock_payment_completion(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Dev-only endpoint to simulate payment completion for testing"""
    # This is the same as mock-payment but under /dev path
    return await mock_payment_completion(request_data, db)
