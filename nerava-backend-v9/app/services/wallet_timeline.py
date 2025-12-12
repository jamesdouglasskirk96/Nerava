"""
Wallet Timeline Service

Provides a unified timeline of wallet activity (earned/spent events)
with explicit duplicate prevention rules.
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.models.domain import NovaTransaction, MerchantRedemption, DriverWallet


def get_wallet_timeline(
    db: Session,
    driver_user_id: int,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get unified wallet timeline for a driver.
    
    Rules:
    - EARNED events = NovaTransaction rows where type == "driver_earn"
    - SPENT events = MerchantRedemption rows ONLY
    - Explicitly EXCLUDE NovaTransaction rows where type == "driver_redeem" to avoid duplicates
    - Ordering: newest first across both sources
    - Tie-breaker: when timestamps equal, order by type (SPENT before EARNED) then id
    
    Args:
        db: Database session
        driver_user_id: Driver user ID
        limit: Maximum number of events to return
        
    Returns:
        List of normalized event dicts with fields:
        - id: str
        - type: "EARNED" | "SPENT"
        - amount_cents: int
        - title: str
        - subtitle: str
        - created_at: ISO string
        - merchant_id: optional str
        - redemption_id: optional str
    """
    events: List[Dict[str, Any]] = []
    
    # 1. Get EARNED events from NovaTransaction (driver_earn only)
    earned_txns = db.query(NovaTransaction).filter(
        and_(
            NovaTransaction.driver_user_id == driver_user_id,
            NovaTransaction.type == "driver_earn"
        )
    ).order_by(NovaTransaction.created_at.desc()).limit(limit * 2).all()
    
    for txn in earned_txns:
        # Get merchant name if available
        merchant_name = None
        if txn.merchant:
            merchant_name = txn.merchant.name
        elif txn.merchant_id:
            # Fallback: just use merchant_id if relationship not loaded
            merchant_name = f"Merchant {txn.merchant_id[:8]}"
        
        # Determine title/subtitle
        title = "Off-Peak Charging"
        subtitle = "Nova issued"
        
        # Check metadata for better labels
        if txn.transaction_meta:
            if txn.transaction_meta.get("source") == "charging_session":
                title = "Charging Reward"
            elif txn.transaction_meta.get("event_id"):
                title = "Event Reward"
        
        events.append({
            "id": f"earn_{txn.id}",
            "type": "EARNED",
            "amount_cents": txn.amount,
            "title": title,
            "subtitle": subtitle,
            "created_at": txn.created_at.isoformat(),
            "merchant_id": txn.merchant_id,
            "redemption_id": None
        })
    
    # 2. Get SPENT events from MerchantRedemption (ONLY source for spent)
    spent_redemptions = db.query(MerchantRedemption).filter(
        MerchantRedemption.driver_user_id == driver_user_id
    ).order_by(MerchantRedemption.created_at.desc()).limit(limit * 2).all()
    
    for redemption in spent_redemptions:
        merchant_name = "Merchant"
        if redemption.merchant:
            merchant_name = redemption.merchant.name
        elif redemption.merchant_id:
            merchant_name = f"Merchant {redemption.merchant_id[:8]}"
        
        events.append({
            "id": f"spent_{redemption.id}",
            "type": "SPENT",
            "amount_cents": redemption.nova_spent_cents,
            "title": merchant_name,
            "subtitle": "Nova applied",
            "created_at": redemption.created_at.isoformat(),
            "merchant_id": redemption.merchant_id,
            "redemption_id": redemption.id
        })
    
    # 3. Sort by created_at descending, with tie-breaker
    # Tie-breaker: SPENT before EARNED when timestamps equal, then by id
    def sort_key(event: Dict[str, Any]) -> tuple:
        created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
        type_order = 0 if event["type"] == "SPENT" else 1  # SPENT first
        return (-created_at.timestamp(), type_order, event["id"])
    
    events.sort(key=sort_key)
    
    # 4. Limit and return
    return events[:limit]
