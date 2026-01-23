from typing import Dict, Any
from datetime import datetime

def purchase_credits(merchant_id: str, amount: int) -> Dict[str, Any]:
    """
    Purchase merchant credits.
    
    TODO: Implement real credit purchase logic
    - Validate merchant and payment
    - Update credit ledger
    - Process payment
    - Target p95 < 250ms
    """
    
    # Stub implementation
    credits_before = 150  # Would query from database
    credits_after = credits_before + amount
    price_cents = amount * 10  # 10 cents per credit
    
    return {
        "merchant_id": merchant_id,
        "credits_before": credits_before,
        "credits_after": credits_after,
        "price_cents": price_cents,
        "transaction_id": f"tx_{merchant_id}_{int(datetime.utcnow().timestamp())}"
    }
