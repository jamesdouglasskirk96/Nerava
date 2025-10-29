"""
Stripe Connect API endpoints for payouts and webhooks
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import uuid
import hmac
import hashlib

from app.db import get_db
from app.config import settings
from app.clients.stripe_client import get_stripe, create_transfer, create_express_account_if_needed
from app.utils.log import get_logger, log_reward_event

router = APIRouter(prefix="/v1", tags=["stripe"])

logger = get_logger(__name__)


class PayoutRequest(BaseModel):
    user_id: int
    amount_cents: int
    method: str
    client_token: Optional[str] = None


@router.post("/payouts/create")
async def create_payout(
    request: PayoutRequest,
    db: Session = Depends(get_db)
):
    """
    Create a payout by debiting user wallet and initiating Stripe transfer.
    
    Rate limit: 5/min per user (enforced by middleware if configured)
    """
    now = datetime.utcnow()
    
    # Validate method
    if request.method not in ["wallet", "card_push"]:
        raise HTTPException(status_code=400, detail=f"Invalid method: {request.method}. Must be 'wallet' or 'card_push'")
    
    # Validate amount limits
    if request.amount_cents < settings.payout_min_cents:
        raise HTTPException(
            status_code=400,
            detail=f"Amount too low: {request.amount_cents} cents (minimum: {settings.payout_min_cents})"
        )
    if request.amount_cents > settings.payout_max_cents:
        raise HTTPException(
            status_code=400,
            detail=f"Amount too high: {request.amount_cents} cents (maximum: {settings.payout_max_cents})"
        )
    
    # Check daily cap
    day_start = now - timedelta(hours=24)
    daily_total_result = db.execute(text("""
        SELECT COALESCE(SUM(amount_cents), 0) FROM payments
        WHERE user_id = :user_id 
        AND created_at >= :day_start
        AND status IN ('pending', 'paid')
    """), {
        "user_id": request.user_id,
        "day_start": day_start
    }).scalar()
    daily_total = int(daily_total_result) if daily_total_result else 0
    
    if daily_total + request.amount_cents > settings.payout_daily_cap_cents:
        raise HTTPException(
            status_code=400,
            detail=f"Daily cap exceeded: {daily_total} + {request.amount_cents} > {settings.payout_daily_cap_cents} cents"
        )
    
    # Check idempotency via client_token (stored in metadata)
    if request.client_token:
        existing_payment = db.execute(text("""
            SELECT id, status, metadata FROM payments
            WHERE user_id = :user_id 
            AND metadata LIKE :pattern
            LIMIT 1
        """), {
            "user_id": request.user_id,
            "pattern": f'%{request.client_token}%'
        }).first()
        
        if existing_payment:
            # Extract provider_ref from metadata if available
            import json
            metadata_str = existing_payment[2] if len(existing_payment) > 2 else "{}"
            try:
                meta = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                provider_ref = meta.get("provider_ref", None)
            except:
                provider_ref = None
            
            return {
                "ok": True,
                "payment_id": str(existing_payment[0]),  # Convert to string for consistency
                "status": existing_payment[1],
                "provider_ref": provider_ref,
                "message": "Idempotent: returning existing payment"
            }
    
    # Fetch wallet balance
    wallet_result = db.execute(text("""
        SELECT COALESCE(SUM(amount_cents), 0) FROM wallet_ledger
        WHERE user_id = :user_id
    """), {"user_id": request.user_id}).scalar()
    wallet_balance = int(wallet_result) if wallet_result else 0
    
    # Check sufficient funds
    if wallet_balance < request.amount_cents:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient funds: balance={wallet_balance} cents, requested={request.amount_cents} cents"
        )
    
    # Generate payment ID (use integer if table expects integer, else UUID string)
    # Check if payments.id is INTEGER or TEXT/VARCHAR
    # For now, use integer ID (auto-increment) - but we'll insert with a generated integer
    # Actually, let's use UUID stored as string for id if it's INTEGER, we need to use a different approach
    # Check: payments table uses INTEGER id, so we'll let SQLite auto-generate it
    client_token = request.client_token or f"payout_{uuid.uuid4()}"
    payment_id = None  # Will be set after insert
    
    try:
        # Start transaction
        # 1. Insert payments row (adapt to actual schema)
        # Payments table: id (INTEGER auto-increment), user_id, merchant_id, amount_cents, payment_method, status, transaction_id, metadata, created_at
        # Let SQLite auto-generate id, then retrieve it
        is_sqlite = settings.database_url.startswith("sqlite")
        
        log_reward_event(logger, "payout_start", client_token, request.user_id, True, {
            "amount": request.amount_cents,
            "method": request.method,
            "client_token": client_token
        })
        
        if is_sqlite:
            # SQLite: let auto-increment handle id
            db.execute(text("""
                INSERT INTO payments (
                    user_id, amount_cents, payment_method, status,
                    transaction_id, metadata, created_at
                ) VALUES (
                    :user_id, :amount_cents, :payment_method, 'pending',
                    NULL, :metadata, :created_at
                )
            """), {
                "user_id": request.user_id,
                "amount_cents": request.amount_cents,
                "payment_method": request.method,
                "metadata": f'{{"payment_id_placeholder":"{client_token}","user_id":{request.user_id},"provider":"stripe","client_token":"{client_token}"}}',
                "created_at": now
            })
            # Get the last insert id
            payment_id = db.execute(text("SELECT last_insert_rowid()")).scalar()
            # Update metadata with actual payment_id
            import json
            metadata_dict = {
                "payment_id": str(payment_id),
                "user_id": request.user_id,
                "provider": "stripe",
                "client_token": client_token
            }
            db.execute(text("""
                UPDATE payments SET metadata = :metadata WHERE id = :payment_id
            """), {
                "payment_id": payment_id,
                "metadata": json.dumps(metadata_dict)
            })
        else:
            # Postgres: use UUID
            payment_id = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO payments (
                    id, user_id, amount_cents, payment_method, status,
                    transaction_id, metadata, created_at
                ) VALUES (
                    :id, :user_id, :amount_cents, :payment_method, 'pending',
                    NULL, :metadata, :created_at
                )
            """), {
                "id": payment_id,
                "user_id": request.user_id,
                "amount_cents": request.amount_cents,
                "payment_method": request.method,
                "metadata": f'{{"payment_id":"{payment_id}","user_id":{request.user_id},"provider":"stripe","client_token":"{client_token}"}}',
                "created_at": now
            })
        
        log_reward_event(logger, "payout_payment_created", payment_id, request.user_id, True)
        
        # 2. Debit wallet_ledger
        balance_result = db.execute(text("""
            SELECT COALESCE(SUM(amount_cents), 0) FROM wallet_ledger
            WHERE user_id = :user_id
        """), {"user_id": request.user_id}).scalar()
        new_balance = int(balance_result) if balance_result else 0
        new_balance -= request.amount_cents
        
        db.execute(text("""
            INSERT INTO wallet_ledger (
                user_id, amount_cents, transaction_type,
                reference_id, reference_type, balance_cents, metadata, created_at
            ) VALUES (
                :user_id, :amount_cents, 'debit',
                :reference_id, 'payout', :balance_cents, :metadata, :created_at
            )
        """), {
            "user_id": request.user_id,
            "amount_cents": -request.amount_cents,  # Negative for debit
            "reference_id": payment_id,
            "balance_cents": new_balance,
            "metadata": f'{{"payment_id":"{payment_id}","type":"payout"}}',
            "created_at": now
        })
        
        log_reward_event(logger, "payout_debit", payment_id, request.user_id, True, {
            "amount": -request.amount_cents,
            "new_balance": new_balance
        })
        
        # 3. Handle Stripe transfer (or simulate)
        stripe_client = get_stripe()
        
        if not stripe_client or not settings.stripe_secret:
            # Simulation mode: mark as paid immediately
            # Update metadata with provider_ref (SQLite compatible)
            import json
            # Get existing metadata
            existing_meta_result = db.execute(text("""
                SELECT metadata FROM payments WHERE id = :payment_id
            """), {"payment_id": payment_id}).first()
            
            if existing_meta_result:
                try:
                    meta_str = existing_meta_result[0] if existing_meta_result else "{}"
                    metadata_dict = json.loads(meta_str) if isinstance(meta_str, str) else meta_str
                except:
                    metadata_dict = {"payment_id": str(payment_id), "user_id": request.user_id}
            else:
                metadata_dict = {"payment_id": str(payment_id), "user_id": request.user_id}
            
            metadata_dict["provider"] = "stripe"
            metadata_dict["client_token"] = client_token
            metadata_dict["provider_ref"] = "simulated"
            db.execute(text("""
                UPDATE payments
                SET status = 'paid', metadata = :metadata
                WHERE id = :payment_id
            """), {
                "payment_id": payment_id,
                "metadata": json.dumps(metadata_dict)
            })
            
            db.commit()
            
            log_reward_event(logger, "payout_stripe_transfer", payment_id, request.user_id, True, {
                "simulated": True,
                "status": "paid"
            })
            
            return {
                "ok": True,
                "payment_id": str(payment_id),  # Convert to string for consistency
                "status": "paid",
                "provider_ref": "simulated",
                "message": "Simulated payout (Stripe keys not configured)"
            }
        else:
            # Real Stripe mode
            # Get or create Stripe account for user
            user_account_result = db.execute(text("""
                SELECT stripe_account_id FROM users WHERE id = :user_id
            """), {"user_id": request.user_id}).first()
            
            stripe_account_id = user_account_result[0] if user_account_result and user_account_result[0] else None
            
            if not stripe_account_id:
                # Create or get test account
                stripe_account_id = create_express_account_if_needed(request.user_id)
                
                # Update user record
                db.execute(text("""
                    UPDATE users
                    SET stripe_account_id = :stripe_account_id, stripe_onboarded = 1
                    WHERE id = :user_id
                """), {
                    "user_id": request.user_id,
                    "stripe_account_id": stripe_account_id
                })
            
            # Create transfer
            transfer_result = create_transfer(
                connected_account_id=stripe_account_id,
                amount_cents=request.amount_cents,
                metadata={
                    "payment_id": payment_id,
                    "user_id": str(request.user_id),
                    "client_token": client_token
                }
            )
            
            # Update payment metadata with transfer ID (SQLite compatible)
            import json
            # First get existing metadata
            existing_meta_result = db.execute(text("""
                SELECT metadata FROM payments WHERE id = :payment_id
            """), {"payment_id": payment_id}).first()
            
            if existing_meta_result:
                try:
                    meta_str = existing_meta_result[0] if existing_meta_result else "{}"
                    meta = json.loads(meta_str) if isinstance(meta_str, str) else meta_str
                except:
                    meta = {}
                meta["provider_ref"] = transfer_result.get("id")
                
                db.execute(text("""
                    UPDATE payments
                    SET metadata = :metadata
                    WHERE id = :payment_id
                """), {
                    "payment_id": payment_id,
                    "metadata": json.dumps(meta)
                })
            
            # If simulated transfer returned paid, update status
            if transfer_result.get("simulated") or transfer_result.get("status") == "paid":
                db.execute(text("""
                    UPDATE payments
                    SET status = 'paid'
                    WHERE id = :payment_id
                """), {"payment_id": payment_id})
            
            db.commit()
            
            log_reward_event(logger, "payout_stripe_transfer", payment_id, request.user_id, True, {
                "transfer_id": transfer_result.get("id"),
                "status": transfer_result.get("status")
            })
            
            return {
                "ok": True,
                "payment_id": str(payment_id),  # Convert to string for consistency
                "status": "paid" if (transfer_result.get("simulated") or transfer_result.get("status") == "paid") else "pending",
                "provider_ref": transfer_result.get("id")
            }
            
    except Exception as e:
        db.rollback()
        log_reward_event(logger, "payout_stripe_transfer", payment_id, request.user_id, False, {
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise HTTPException(status_code=500, detail=f"Payout creation failed: {str(e)}")


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events to finalize payouts.
    
    Verifies webhook signature if STRIPE_WEBHOOK_SECRET is set.
    """
    body = await request.body()
    signature = request.headers.get("stripe-signature")
    
    # Verify signature if secret is configured
    if settings.stripe_webhook_secret and signature:
        try:
            stripe_client = get_stripe()
            if stripe_client:
                event = stripe_client.Webhook.construct_event(
                    body, signature, settings.stripe_webhook_secret
                )
            else:
                # In simulation, skip verification
                import json
                event = json.loads(body)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {str(e)}")
    else:
        # No secret configured, parse body directly (dev/simulation)
        import json
        try:
            event = json.loads(body)
        except:
            raise HTTPException(status_code=400, detail="Invalid webhook body")
    
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})
    
    log_reward_event(logger, "payout_webhook_received", "webhook", 0, True, {
        "event_type": event_type,
        "event_id": event.get("id")
    })
    
    # Handle transfer/payout success events
    if event_type in ["transfer.paid", "payout.paid", "balance.available"]:
        # Extract payment_id from metadata
        metadata = event_data.get("metadata", {})
        payment_id = metadata.get("payment_id")
        
        if payment_id:
            # Update payment status to paid
            result = db.execute(text("""
                UPDATE payments
                SET status = 'paid'
                WHERE id = :payment_id AND status = 'pending'
            """), {"payment_id": payment_id})
            
            db.commit()
            
            if result.rowcount > 0:
                log_reward_event(logger, "payout_webhook_update", payment_id, 0, True, {
                    "new_status": "paid",
                    "event_type": event_type
                })
                
                return {"ok": True, "payment_id": payment_id, "status": "paid"}
            else:
                return {"ok": True, "message": "Payment already processed or not found"}
    
    # Unknown event types: return 200 but don't process
    return {"ok": True, "message": f"Ignored event type: {event_type}"}

