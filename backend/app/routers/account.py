"""
Account management router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db import get_db
from app.models import User
from app.dependencies_domain import get_current_user

router = APIRouter(prefix="/v1/account", tags=["account"])

logger = logging.getLogger(__name__)


class ExportResponse(BaseModel):
    ok: bool
    message: str


class DeleteRequest(BaseModel):
    confirmation: str


class DeleteResponse(BaseModel):
    ok: bool


@router.post("/export", response_model=ExportResponse)
def export_account_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Request account data export.
    
    TODO: Implement actual export functionality:
    - Export user profile data
    - Export transaction history
    - Export vehicle connection data
    - Generate downloadable archive
    - Send email with download link
    """
    logger.info(f"Account export requested for user {current_user.id} (public_id: {current_user.public_id})")
    
    # TODO: Queue export job
    # TODO: Generate export archive
    # TODO: Send email notification
    
    return ExportResponse(
        ok=True,
        message="Export request queued. You will receive an email when your data is ready."
    )


@router.delete("", response_model=DeleteResponse)
def delete_account(
    request: DeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete user account.
    
    Requires explicit confirmation by typing "DELETE" in the request body.
    
    TODO: Implement full data deletion workflow:
    - Soft delete: set is_active=False, deleted_at=now()
    - Schedule hard delete job (after retention period)
    - Delete all related data (tokens, preferences, transactions, etc.)
    - Send confirmation email
    """
    if request.confirmation != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "CONFIRMATION_REQUIRED",
                "message": "Account deletion requires typing 'DELETE' as confirmation"
            }
        )
    
    # Soft delete: set is_active=False
    current_user.is_active = False
    # TODO: Add deleted_at column to users table if not exists
    # current_user.deleted_at = datetime.utcnow()
    
    db.commit()
    
    logger.info(f"Account soft-deleted for user {current_user.id} (public_id: {current_user.public_id})")
    
    # TODO: Queue hard delete job
    # TODO: Send confirmation email
    
    return DeleteResponse(ok=True)







