"""
Merchant Reconciliation Router

Provides claim-based billing summaries and CSV exports for merchants.
Claims (completed exclusive sessions) are the billing events.
Merchants reconcile against their own POS exports (e.g., Toast) for disputes.
"""
import csv
import io
import logging
from datetime import datetime, timedelta, timezone, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.models.exclusive_session import ExclusiveSession, ExclusiveSessionStatus
from app.models.verified_visit import VerifiedVisit
from app.dependencies.domain import require_merchant_admin
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/merchant/reconciliation", tags=["merchant_reconciliation"])


# --- Schemas ---

class DailyClaims(BaseModel):
    date: str
    claims: int
    redeemed: int


class ReconciliationSummary(BaseModel):
    merchant_id: str
    merchant_name: str
    period_start: str
    period_end: str
    total_claims: int
    total_redeemed: int
    total_expired: int
    daily_breakdown: list[DailyClaims]


# --- Helpers ---

def _get_period_range(period: str) -> tuple[datetime, datetime]:
    """Convert period string to start/end datetimes."""
    now = datetime.now(timezone.utc)
    end = now
    if period == "week":
        start = now - timedelta(days=7)
    elif period == "month":
        start = now - timedelta(days=30)
    elif period == "quarter":
        start = now - timedelta(days=90)
    else:
        # Default to last 30 days
        start = now - timedelta(days=30)
    return start, end


def _get_custom_range(start_date: Optional[str], end_date: Optional[str]) -> tuple[datetime, datetime]:
    """Parse custom date range strings."""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        end = datetime.strptime(end_date, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59, tzinfo=timezone.utc
        )
        return start, end
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD."
        )


# --- Endpoints ---

@router.get("/summary", response_model=ReconciliationSummary)
async def get_reconciliation_summary(
    period: str = Query("month", description="week, month, or quarter"),
    start_date: Optional[str] = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end date (YYYY-MM-DD)"),
    current_user: User = Depends(require_merchant_admin),
    db: Session = Depends(get_db),
):
    """
    Get claims summary for billing reconciliation.

    Claims = completed exclusive sessions. This is what Nerava bills on.
    Merchants compare this against their Toast/POS export for disputes.
    """
    merchant = AuthService.get_user_merchant(db, current_user.id)
    if not merchant:
        raise HTTPException(status_code=403, detail="No merchant linked to this account")

    # Determine date range
    if start_date and end_date:
        period_start, period_end = _get_custom_range(start_date, end_date)
    else:
        period_start, period_end = _get_period_range(period)

    merchant_id = str(merchant.id)

    # Total completed claims in period
    total_claims = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == merchant_id,
        ExclusiveSession.status == ExclusiveSessionStatus.COMPLETED,
        ExclusiveSession.activated_at >= period_start,
        ExclusiveSession.activated_at <= period_end,
    ).count()

    # Total expired (activated but not completed)
    total_expired = db.query(ExclusiveSession).filter(
        ExclusiveSession.merchant_id == merchant_id,
        ExclusiveSession.status == ExclusiveSessionStatus.EXPIRED,
        ExclusiveSession.activated_at >= period_start,
        ExclusiveSession.activated_at <= period_end,
    ).count()

    # Total redeemed visits (subset of claims that have a verified visit with redemption)
    total_redeemed = db.query(VerifiedVisit).filter(
        VerifiedVisit.merchant_id == merchant_id,
        VerifiedVisit.verified_at >= period_start,
        VerifiedVisit.verified_at <= period_end,
        VerifiedVisit.redeemed_at.isnot(None),
    ).count()

    # Daily breakdown — group completed sessions by date
    # Use func.date for SQLite compatibility, cast for PostgreSQL
    daily_claims_q = (
        db.query(
            func.date(ExclusiveSession.activated_at).label("day"),
            func.count().label("count"),
        )
        .filter(
            ExclusiveSession.merchant_id == merchant_id,
            ExclusiveSession.status == ExclusiveSessionStatus.COMPLETED,
            ExclusiveSession.activated_at >= period_start,
            ExclusiveSession.activated_at <= period_end,
        )
        .group_by(func.date(ExclusiveSession.activated_at))
        .order_by(func.date(ExclusiveSession.activated_at))
        .all()
    )

    # Daily redeemed visits
    daily_redeemed_q = (
        db.query(
            func.date(VerifiedVisit.verified_at).label("day"),
            func.count().label("count"),
        )
        .filter(
            VerifiedVisit.merchant_id == merchant_id,
            VerifiedVisit.verified_at >= period_start,
            VerifiedVisit.verified_at <= period_end,
            VerifiedVisit.redeemed_at.isnot(None),
        )
        .group_by(func.date(VerifiedVisit.verified_at))
        .all()
    )
    redeemed_by_day = {str(r.day): r.count for r in daily_redeemed_q}

    daily_breakdown = [
        DailyClaims(
            date=str(row.day),
            claims=row.count,
            redeemed=redeemed_by_day.get(str(row.day), 0),
        )
        for row in daily_claims_q
    ]

    return ReconciliationSummary(
        merchant_id=merchant_id,
        merchant_name=merchant.name or "",
        period_start=period_start.strftime("%Y-%m-%d"),
        period_end=period_end.strftime("%Y-%m-%d"),
        total_claims=total_claims,
        total_redeemed=total_redeemed,
        total_expired=total_expired,
        daily_breakdown=daily_breakdown,
    )


@router.get("/export")
async def export_claims_csv(
    period: str = Query("month", description="week, month, or quarter"),
    start_date: Optional[str] = Query(None, description="Custom start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Custom end date (YYYY-MM-DD)"),
    current_user: User = Depends(require_merchant_admin),
    db: Session = Depends(get_db),
):
    """
    Export claims as CSV for reconciliation against POS exports.

    Each row is a completed exclusive session (claim).
    Merchants can compare this against their Toast export by date/time.
    """
    merchant = AuthService.get_user_merchant(db, current_user.id)
    if not merchant:
        raise HTTPException(status_code=403, detail="No merchant linked to this account")

    # Determine date range
    if start_date and end_date:
        period_start, period_end = _get_custom_range(start_date, end_date)
    else:
        period_start, period_end = _get_period_range(period)

    merchant_id = str(merchant.id)

    # Get all completed sessions in period
    sessions = (
        db.query(ExclusiveSession)
        .filter(
            ExclusiveSession.merchant_id == merchant_id,
            ExclusiveSession.status == ExclusiveSessionStatus.COMPLETED,
            ExclusiveSession.activated_at >= period_start,
            ExclusiveSession.activated_at <= period_end,
        )
        .order_by(ExclusiveSession.activated_at)
        .all()
    )

    # Get verified visits for these sessions for enrichment
    session_ids = [str(s.id) for s in sessions]
    visits = {}
    if session_ids:
        visit_rows = db.query(VerifiedVisit).filter(
            VerifiedVisit.exclusive_session_id.in_(session_ids)
        ).all()
        visits = {v.exclusive_session_id: v for v in visit_rows}

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Claim Date",
        "Claim Time (UTC)",
        "Session ID",
        "Status",
        "Duration (min)",
        "Verification Code",
        "Redeemed",
        "Order Reference",
    ])

    for s in sessions:
        activated = s.activated_at
        duration_min = ""
        if s.completed_at and s.activated_at:
            duration_min = round((s.completed_at - s.activated_at).total_seconds() / 60, 1)

        visit = visits.get(str(s.id))
        verification_code = visit.verification_code if visit else ""
        redeemed = "Yes" if visit and visit.redeemed_at else "No"
        order_ref = visit.order_reference if visit else ""

        writer.writerow([
            activated.strftime("%Y-%m-%d") if activated else "",
            activated.strftime("%H:%M:%S") if activated else "",
            str(s.id),
            s.status.value,
            duration_min,
            verification_code,
            redeemed,
            order_ref,
        ])

    output.seek(0)
    filename = f"nerava-claims-{merchant_id[:8]}-{period_start.strftime('%Y%m%d')}-{period_end.strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
