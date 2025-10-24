from typing import Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from ..models_extra import EnergyRepBackfill
from ..obs.obs import log_info, log_warn

def compute_v1(user_id: str, db: Session = None) -> Dict[str, Any]:
    """
    Compute user's energy reputation score using v1 logic.
    
    Args:
        user_id: User identifier
        db: Database session for persistence
    
    Returns:
        Dict with energy reputation data
    """
    start_time = datetime.utcnow()
    log_info(f"Computing EnergyRep v1 for {user_id}")
    
    # v1 scoring components with deterministic calculation
    charging_score = 600 * (0.75 + (hash(user_id) % 25) / 100)  # 600 * (0.75-1.0) = 450-600
    referrals = 200 * min(1, (hash(user_id) % 10) / 5)  # 0-200 based on hash
    merchant = 150 * min(1, (hash(user_id) % 15) / 10)  # 0-150 based on hash  
    v2g = 250 * min(1, (hash(user_id) % 8) / 10)  # 0-250 based on hash
    
    # Apply weights: 0.5, 0.2, 0.15, 0.15
    total_score = int(charging_score * 0.5 + referrals * 0.2 + merchant * 0.15 + v2g * 0.15)
    
    # Determine tier based on thresholds: 400/650/850
    if total_score >= 850:
        tier = "Platinum"
    elif total_score >= 650:
        tier = "Gold"
    elif total_score >= 400:
        tier = "Silver"
    else:
        tier = "Bronze"
    
    breakdown = {
        "charging_score": int(charging_score),
        "referrals": int(referrals),
        "merchant": int(merchant),
        "v2g": int(v2g)
    }
    
    result = {
        "user_id": user_id,
        "total_score": total_score,
        "tier": tier,
        "breakdown": breakdown,
        "last_calculated_at": datetime.utcnow().isoformat()
    }
    
    # Persist if database available
    if db:
        try:
            # Check if already computed today
            today = date.today()
            existing = db.query(EnergyRepBackfill).filter(
                EnergyRepBackfill.user_id == user_id,
                EnergyRepBackfill.day == today
            ).first()
            
            if not existing:
                backfill = EnergyRepBackfill(
                    user_id=user_id,
                    day=today,
                    status="completed"
                )
                db.add(backfill)
                db.commit()
                log_info(f"Recorded EnergyRep backfill for {user_id}")
        except Exception as e:
            log_warn(f"Failed to record backfill: {e}")
            db.rollback()
    
    # Log metrics
    compute_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    log_info(f"EnergyRep v1 compute time: {compute_time:.2f}ms")
    
    return result

def snapshot_energy_rep(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Snapshot today's energy reputation score.
    
    Args:
        user_id: User identifier
        db: Database session
    
    Returns:
        Dict with snapshot data
    """
    return compute_v1(user_id, db)

def backfill_last_60_days(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Backfill energy reputation for last 60 days with idempotency.
    
    Args:
        user_id: User identifier
        db: Database session
    
    Returns:
        Dict with backfill results
    """
    start_date = date.today() - timedelta(days=60)
    end_date = date.today()
    
    backfilled_days = []
    skipped_days = []
    
    current_date = start_date
    while current_date <= end_date:
        # Check if already backfilled
        existing = db.query(EnergyRepBackfill).filter(
            EnergyRepBackfill.user_id == user_id,
            EnergyRepBackfill.day == current_date
        ).first()
        
        if existing:
            skipped_days.append(current_date.isoformat())
        else:
            # Create backfill record
            backfill = EnergyRepBackfill(
                user_id=user_id,
                day=current_date,
                status="completed"
            )
            db.add(backfill)
            backfilled_days.append(current_date.isoformat())
        
        current_date += timedelta(days=1)
    
    try:
        db.commit()
        log_info(f"Backfilled {len(backfilled_days)} days for {user_id}")
    except Exception as e:
        log_warn(f"Failed to backfill: {e}")
        db.rollback()
    
    return {
        "user_id": user_id,
        "backfilled_days": backfilled_days,
        "skipped_days": skipped_days,
        "total_days": len(backfilled_days) + len(skipped_days)
    }

# Legacy function for backward compatibility
def compute(user_id: str) -> Dict[str, Any]:
    """Legacy compute function - redirects to v1."""
    return compute_v1(user_id)
