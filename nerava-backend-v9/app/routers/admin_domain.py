"""
Domain Charge Party MVP Admin Router
Admin endpoints for overview, merchant management, and manual Nova grants
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Literal

from app.db import get_db
from app.models import User
from app.models_domain import (
    DriverWallet,
    DomainMerchant,
    NovaTransaction,
    StripePayment
)
from app.services.nova_service import NovaService
from app.services.stripe_service import StripeService
from app.dependencies_domain import require_admin, get_current_user
from sqlalchemy import text
from app.utils.log import get_logger

router = APIRouter(prefix="/v1/admin", tags=["admin-v1"])

logger = get_logger(__name__)


class GrantNovaRequest(BaseModel):
    target: Literal["driver", "merchant"]
    driver_user_id: Optional[int] = None
    merchant_id: Optional[str] = None
    amount: int
    reason: str
    idempotency_key: Optional[str] = None  # Optional idempotency key for deduplication


class AdminOverviewResponse(BaseModel):
    total_drivers: int
    total_merchants: int
    total_driver_nova: int
    total_merchant_nova: int
    total_nova_outstanding: int
    total_stripe_usd: int


@router.get("/overview", response_model=AdminOverviewResponse)
def get_overview(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin overview statistics"""
    # Count drivers (users with driver role)
    total_drivers = db.query(User).filter(
        User.role_flags.contains("driver")
    ).count()
    
    # Count merchants
    total_merchants = db.query(DomainMerchant).count()
    
    # Sum driver Nova balances
    driver_nova_result = db.query(func.sum(DriverWallet.nova_balance)).scalar()
    total_driver_nova = int(driver_nova_result) if driver_nova_result else 0
    
    # Sum merchant Nova balances
    merchant_nova_result = db.query(func.sum(DomainMerchant.nova_balance)).scalar()
    total_merchant_nova = int(merchant_nova_result) if merchant_nova_result else 0
    
    # Total outstanding Nova
    total_nova_outstanding = total_driver_nova + total_merchant_nova
    
    # Sum Stripe payments (successful)
    stripe_usd_result = db.query(func.sum(StripePayment.amount_usd)).filter(
        StripePayment.status == "paid"
    ).scalar()
    total_stripe_usd = int(stripe_usd_result) if stripe_usd_result else 0
    
    return AdminOverviewResponse(
        total_drivers=total_drivers,
        total_merchants=total_merchants,
        total_driver_nova=total_driver_nova,
        total_merchant_nova=total_merchant_nova,
        total_nova_outstanding=total_nova_outstanding,
        total_stripe_usd=total_stripe_usd
    )


@router.get("/merchants")
def list_merchants(
    zone_slug: Optional[str] = Query(None, description="Filter by zone slug"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List merchants with filters"""
    query = db.query(DomainMerchant)
    
    if zone_slug:
        query = query.filter(DomainMerchant.zone_slug == zone_slug)
    
    if status_filter:
        query = query.filter(DomainMerchant.status == status_filter)
    
    merchants = query.order_by(DomainMerchant.created_at.desc()).all()
    
    # Get last transaction timestamp for each merchant
    merchant_list = []
    for merchant in merchants:
        last_txn = db.query(NovaTransaction).filter(
            NovaTransaction.merchant_id == merchant.id
        ).order_by(NovaTransaction.created_at.desc()).first()
        
        merchant_list.append({
            "id": merchant.id,
            "name": merchant.name,
            "zone_slug": merchant.zone_slug,
            "status": merchant.status,
            "nova_balance": merchant.nova_balance,
            "last_active_at": last_txn.created_at.isoformat() if last_txn else None,
            "created_at": merchant.created_at.isoformat()
        })
    
    return {"merchants": merchant_list}


@router.post("/nova/grant")
def grant_nova(
    request: GrantNovaRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Manually grant Nova to driver or merchant (admin only)"""
    try:
        if request.target == "driver":
            if not request.driver_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="driver_user_id required for driver target"
                )
            
            # Require idempotency key in non-local environments
            from app.utils.env import is_local_env
            
            idempotency_key = request.idempotency_key
            if not idempotency_key:
                if not is_local_env():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="idempotency_key is required in non-local environment"
                    )
                # In local, generate deterministic fallback for dev only
                idempotency_key = f"grant_driver_{request.driver_user_id}_{request.amount}"
            
            transaction = NovaService.grant_to_driver(
                db=db,
                driver_id=request.driver_user_id,
                amount=request.amount,
                type="admin_grant",
                idempotency_key=idempotency_key,
                metadata={"reason": request.reason, "granted_by": admin.id}
            )
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "target": "driver",
                "driver_user_id": request.driver_user_id,
                "amount": request.amount
            }
        
        elif request.target == "merchant":
            if not request.merchant_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="merchant_id required for merchant target"
                )
            
            # Require idempotency key in non-local environments
            from app.utils.env import is_local_env
            
            idempotency_key = request.idempotency_key
            if not idempotency_key:
                if not is_local_env():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="idempotency_key is required in non-local environment"
                    )
                # In local, generate deterministic fallback for dev only
                idempotency_key = f"grant_merchant_{request.merchant_id}_{request.amount}"
            
            transaction = NovaService.grant_to_merchant(
                db=db,
                merchant_id=request.merchant_id,
                amount=request.amount,
                type="admin_grant",
                idempotency_key=idempotency_key,
                metadata={"reason": request.reason, "granted_by": admin.id}
            )
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "target": "merchant",
                "merchant_id": request.merchant_id,
                "amount": request.amount
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="target must be 'driver' or 'merchant'"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/payments/{payment_id}/reconcile")
def reconcile_payment(
    payment_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to reconcile a payment with status 'unknown'.
    
    If payment status is not 'unknown', returns current payment summary (no-op).
    If payment is 'unknown', calls Stripe to check transfer status and updates accordingly.
    """
    try:
        # Call reconciliation logic
        result = StripeService.reconcile_payment(db, payment_id)
        
        # Fetch full payment details for response
        payment_row = db.execute(text("""
            SELECT id, status, stripe_transfer_id, stripe_status, 
                   error_code, error_message, reconciled_at, no_transfer_confirmed
            FROM payments
            WHERE id = :payment_id
        """), {"payment_id": payment_id}).first()
        
        if not payment_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment {payment_id} not found"
            )
        
        # Audit log
        logger.info(f"Admin reconciliation triggered: payment_id={payment_id}, admin_id={admin.id}, result_status={result.get('status')}")
        
        # Build response with all required fields
        response = {
            "payment_id": payment_row[0] or payment_id,
            "status": payment_row[1] or result.get("status"),
            "stripe_transfer_id": payment_row[2],
            "stripe_status": payment_row[3],
            "error_code": payment_row[4],
            "error_message": payment_row[5],
            "reconciled_at": payment_row[6].isoformat() if payment_row[6] else None,
            "no_transfer_confirmed": bool(payment_row[7]) if payment_row[7] is not None else None
        }
        
        # Add message from reconciliation result if present
        if "message" in result:
            response["message"] = result["message"]
        
        return response
        
    except ValueError as e:
        # Payment not found
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in admin reconcile endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reconciliation failed: {str(e)}"
        )

