"""
Admin Service
Service layer for admin operations
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.while_you_charge import Merchant, MerchantPerk
from app.models.exclusive_session import ExclusiveSession, ExclusiveSessionStatus
from app.models import User


def get_exclusives_with_counts(
    db: Session,
    merchant_id: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict]:
    """
    Get exclusives with activation counts (today and this month).
    
    Args:
        db: Database session
        merchant_id: Optional merchant ID filter
        status: Optional status filter ("active", "paused", None for all)
    
    Returns:
        List of exclusive dicts with counts
    """
    # Base query
    query = db.query(MerchantPerk).join(Merchant)
    
    # Filter by merchant_id if provided
    if merchant_id:
        query = query.filter(MerchantPerk.merchant_id == merchant_id)
    
    # Filter by status
    if status == "active":
        query = query.filter(MerchantPerk.is_active == True)
    elif status == "paused":
        query = query.filter(MerchantPerk.is_active == False)
    
    # Get all matching perks (exclusives are perks with is_exclusive flag in metadata)
    perks = query.all()
    
    # Calculate today and this month start
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = today_start.replace(day=1)
    
    result = []
    for perk in perks:
        # Check if this is an exclusive (has is_exclusive in description metadata)
        import json
        try:
            metadata = json.loads(perk.description or "{}")
            if not metadata.get("is_exclusive"):
                continue
        except:
            # Skip if not valid JSON or not an exclusive
            continue
        
        # Count activations today
        activations_today = db.query(func.count(ExclusiveSession.id)).filter(
            ExclusiveSession.merchant_id == perk.merchant_id,
            ExclusiveSession.created_at >= today_start
        ).scalar() or 0
        
        # Count activations this month
        activations_this_month = db.query(func.count(ExclusiveSession.id)).filter(
            ExclusiveSession.merchant_id == perk.merchant_id,
            ExclusiveSession.created_at >= month_start
        ).scalar() or 0
        
        merchant = db.query(Merchant).filter(Merchant.id == perk.merchant_id).first()
        
        result.append({
            "id": str(perk.id),
            "merchant_id": perk.merchant_id,
            "merchant_name": merchant.name if merchant else "Unknown",
            "title": perk.title,
            "description": metadata.get("description") or perk.description,
            "nova_reward": perk.nova_reward,
            "is_active": perk.is_active,
            "daily_cap": metadata.get("daily_cap") or perk.daily_cap,
            "activations_today": activations_today,
            "activations_this_month": activations_this_month,
            "created_at": perk.created_at,
            "updated_at": perk.updated_at
        })
    
    return result


from typing import Tuple

def toggle_exclusive(
    db: Session,
    exclusive_id: str,
    admin_id: int
) -> Tuple[bool, bool]:
    """
    Toggle exclusive on/off.
    
    Args:
        db: Database session
        exclusive_id: Exclusive ID (perk ID)
        admin_id: Admin user ID
    
    Returns:
        Tuple of (previous_state, new_state)
    """
    perk = db.query(MerchantPerk).filter(MerchantPerk.id == int(exclusive_id)).first()
    if not perk:
        raise ValueError(f"Exclusive {exclusive_id} not found")
    
    previous_state = perk.is_active
    perk.is_active = not perk.is_active
    perk.updated_at = datetime.utcnow()
    
    db.commit()
    
    return previous_state, perk.is_active


def pause_merchant(
    db: Session,
    merchant_id: str,
    admin_id: int
) -> Tuple[str, str]:
    """
    Pause a merchant - disables all their exclusives.
    
    Args:
        db: Database session
        merchant_id: Merchant ID
        admin_id: Admin user ID
    
    Returns:
        Tuple of (previous_status, new_status)
    """
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise ValueError(f"Merchant {merchant_id} not found")
    
    if merchant.status == "paused":
        raise ValueError("Merchant already paused")
    
    previous_status = merchant.status or "active"
    merchant.status = "paused"
    merchant.updated_at = datetime.utcnow()
    
    # Disable all active exclusives
    db.query(MerchantPerk).filter(
        MerchantPerk.merchant_id == merchant_id,
        MerchantPerk.is_active == True
    ).update({"is_active": False, "updated_at": datetime.utcnow()})
    
    db.commit()
    
    return previous_status, "paused"


def resume_merchant(
    db: Session,
    merchant_id: str,
    admin_id: int
) -> Tuple[str, str]:
    """
    Resume a paused merchant.
    
    Args:
        db: Database session
        merchant_id: Merchant ID
        admin_id: Admin user ID
    
    Returns:
        Tuple of (previous_status, new_status)
    """
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        raise ValueError(f"Merchant {merchant_id} not found")
    
    if merchant.status != "paused":
        raise ValueError("Merchant is not paused")
    
    merchant.status = "active"
    merchant.updated_at = datetime.utcnow()
    
    db.commit()
    
    return "paused", "active"

