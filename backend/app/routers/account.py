"""
Account management router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
import logging

from app.db import get_db
from app.models import (
    User,
    RefreshToken,
    UserConsent,
    ExclusiveSession,
    NovaTransaction,
    IntentSession,
)
from app.models.while_you_charge import FavoriteMerchant
from app.models.vehicle import VehicleAccount, VehicleToken
from app.models.domain import DriverWallet
from app.dependencies_domain import get_current_user
from app.dependencies.driver import get_current_driver
from app.services.audit import log_admin_action

router = APIRouter(prefix="/v1/account", tags=["account"])

logger = logging.getLogger(__name__)


class ExportResponse(BaseModel):
    ok: bool
    data: dict


class DeleteRequest(BaseModel):
    confirmation: str


class DeleteResponse(BaseModel):
    ok: bool


# ─── Vehicle Endpoint ──────────────────────────────────────────────

class VehicleRequest(BaseModel):
    color: str
    model: str


class VehicleResponse(BaseModel):
    color: str
    model: str
    set_at: str


@router.put("/vehicle", response_model=VehicleResponse)
def set_vehicle(
    req: VehicleRequest,
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """Set or update driver vehicle info (one-time, editable)."""
    now = datetime.now(timezone.utc)
    current_user.vehicle_color = req.color
    current_user.vehicle_model = req.model
    current_user.vehicle_set_at = now
    db.commit()

    return VehicleResponse(
        color=req.color,
        model=req.model,
        set_at=now.isoformat() + "Z",
    )


@router.get("/vehicle", response_model=VehicleResponse)
def get_vehicle(
    current_user: User = Depends(get_current_driver),
    db: Session = Depends(get_db),
):
    """Get driver's saved vehicle info."""
    color = getattr(current_user, "vehicle_color", None)
    model = getattr(current_user, "vehicle_model", None)
    set_at = getattr(current_user, "vehicle_set_at", None)

    if not color and not model:
        raise HTTPException(status_code=404, detail="No vehicle saved")

    return VehicleResponse(
        color=color or "",
        model=model or "",
        set_at=set_at.isoformat() + "Z" if set_at else "",
    )


# ─── Export / Delete ───────────────────────────────────────────────

@router.post("/export", response_model=ExportResponse)
def export_account_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export user account data in JSON format.
    
    Returns:
    - User profile (anonymized if deleted)
    - Wallet balance and transactions
    - Exclusive sessions (anonymized if deleted)
    - Intent sessions
    - Nova transactions
    - Consents
    """
    user_id = current_user.id
    
    logger.info(f"Account export requested for user {user_id} (public_id: {current_user.public_id})")
    
    # 1. User profile
    user_data = {
        "id": user_id,
        "public_id": str(current_user.public_id),
        "email": current_user.email,
        "phone": current_user.phone,
        "display_name": current_user.display_name,
        "is_active": current_user.is_active,
        "role_flags": current_user.role_flags,
        "auth_provider": current_user.auth_provider,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
    }
    
    # 2. Wallet balance
    wallet = db.query(DriverWallet).filter(DriverWallet.user_id == user_id).first()
    wallet_data = None
    if wallet:
        wallet_data = {
            "nova_balance": wallet.nova_balance,
            "energy_reputation_score": wallet.energy_reputation_score,
            "created_at": wallet.created_at.isoformat() if wallet.created_at else None,
            "updated_at": wallet.updated_at.isoformat() if wallet.updated_at else None,
        }
    
    # 3. Nova transactions
    transactions = db.query(NovaTransaction).filter(
        NovaTransaction.driver_user_id == user_id
    ).order_by(NovaTransaction.created_at.desc()).all()
    transactions_data = [
        {
            "id": str(tx.id),
            "type": tx.type,
            "amount": tx.amount,
            "merchant_id": tx.merchant_id,
            "created_at": tx.created_at.isoformat() if tx.created_at else None,
            "metadata": tx.metadata,
        }
        for tx in transactions
    ]
    
    # 4. Exclusive sessions
    exclusive_sessions = db.query(ExclusiveSession).filter(
        ExclusiveSession.driver_id == user_id
    ).order_by(ExclusiveSession.created_at.desc()).all()
    exclusive_sessions_data = [
        {
            "id": str(session.id),
            "merchant_id": session.merchant_id,
            "charger_id": session.charger_id,
            "status": session.status.value if hasattr(session.status, 'value') else str(session.status),
            "activated_at": session.activated_at.isoformat() if session.activated_at else None,
            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        }
        for session in exclusive_sessions
    ]
    
    # 5. Intent sessions
    intent_sessions = db.query(IntentSession).filter(
        IntentSession.user_id == user_id
    ).order_by(IntentSession.created_at.desc()).all()
    intent_sessions_data = [
        {
            "id": str(session.id),
            "lat": session.lat,
            "lng": session.lng,
            "accuracy_m": session.accuracy_m,
            "charger_id": session.charger_id,
            "charger_distance_m": session.charger_distance_m,
            "confidence_tier": session.confidence_tier,
            "source": session.source,
            "created_at": session.created_at.isoformat() if session.created_at else None,
        }
        for session in intent_sessions
    ]
    
    # 6. Consents
    consents = db.query(UserConsent).filter(
        UserConsent.user_id == user_id
    ).all()
    consents_data = [
        {
            "consent_type": consent.consent_type,
            "granted": consent.is_granted(),
            "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
            "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None,
            "created_at": consent.created_at.isoformat() if consent.created_at else None,
        }
        for consent in consents
    ]
    
    export_data = {
        "user": user_data,
        "wallet": wallet_data,
        "transactions": transactions_data,
        "exclusive_sessions": exclusive_sessions_data,
        "intent_sessions": intent_sessions_data,
        "consents": consents_data,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    
    return ExportResponse(
        ok=True,
        data=export_data
    )


@router.delete("", response_model=DeleteResponse)
def delete_account(
    request: DeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete user account with anonymization.
    
    Requires explicit confirmation by typing "DELETE" in the request body.
    
    Performs:
    - Anonymizes user data (email, phone, display_name)
    - Deletes related records (refresh_tokens, vehicle_tokens, favorite_merchants, user_consents)
    - Anonymizes references in exclusive_sessions (driver_id → -1)
    - Anonymizes references in nova_transactions (driver_user_id → -1, keep transactions immutable)
    - Logs deletion via audit service
    """
    if request.confirmation != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "CONFIRMATION_REQUIRED",
                "message": "Account deletion requires typing 'DELETE' as confirmation"
            }
        )
    
    user_id = current_user.id
    public_id = current_user.public_id
    
    try:
        # 1. Anonymize user data
        current_user.email = f"deleted_user_{user_id}@deleted.local"
        current_user.phone = "+00000000000"
        current_user.display_name = "Deleted User"
        current_user.is_active = False
        
        # 2. Cascade deletes: refresh_tokens, favorite_merchants, user_consents
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
        db.query(FavoriteMerchant).filter(FavoriteMerchant.user_id == user_id).delete()
        db.query(UserConsent).filter(UserConsent.user_id == user_id).delete()
        
        # 3. Delete vehicle accounts and tokens (cascade via relationship)
        vehicle_accounts = db.query(VehicleAccount).filter(VehicleAccount.user_id == user_id).all()
        for vehicle_account in vehicle_accounts:
            # Delete tokens first (they reference vehicle_account)
            db.query(VehicleToken).filter(VehicleToken.vehicle_account_id == vehicle_account.id).delete()
            db.delete(vehicle_account)
        
        # 4. Anonymize exclusive_sessions (set driver_id to -1 for deleted user marker)
        db.query(ExclusiveSession).filter(ExclusiveSession.driver_id == user_id).update(
            {"driver_id": -1},
            synchronize_session=False
        )
        
        # 5. Anonymize nova_transactions (keep immutable, but anonymize driver_user_id references)
        db.query(NovaTransaction).filter(NovaTransaction.driver_user_id == user_id).update(
            {"driver_user_id": -1},
            synchronize_session=False
        )
        
        # 6. Anonymize verified_visits if they exist
        try:
            from app.models.verified_visit import VerifiedVisit
            db.query(VerifiedVisit).filter(VerifiedVisit.driver_id == user_id).update(
                {"driver_id": -1},
                synchronize_session=False
            )
        except Exception:
            pass  # Table might not exist in all environments
        
        # 7. Log deletion via audit service
        log_admin_action(
            db=db,
            actor_id=user_id,  # User is deleting their own account
            action="account_deleted",
            target_type="user",
            target_id=str(user_id),
            before_json={"public_id": str(public_id), "email": "anonymized"},
            after_json={"status": "deleted", "anonymized": True},
            metadata={"deleted_at": datetime.now(timezone.utc).isoformat()}
        )
        
        db.commit()
        
        logger.info(f"Account deleted and anonymized for user {user_id} (public_id: {public_id})")
        
        return DeleteResponse(ok=True)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete account for user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account. Please contact support."
        )







