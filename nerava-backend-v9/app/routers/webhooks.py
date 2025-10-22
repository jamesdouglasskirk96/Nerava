# app/routers/webhooks.py
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ..services.cache import clicks
from ..services.wallet import credit_wallet  # you already have wallet endpoints

router = APIRouter(prefix="/v1/webhooks", tags=["webhooks"])

class OrderEvent(BaseModel):
    user_id: str
    hub_id: str
    merchant: str
    order_id: str
    subtotal_cents: int
    source: str  # "doordash" | "opentable"

@router.post("/doordash")
def dd_credit(evt: OrderEvent):
    # find last click to same merchant by same user (optional)
    _ = clicks.last_for(evt.user_id, evt.merchant, hours=6)
    # demo: 5% cashback
    bonus = int(round(evt.subtotal_cents * 0.05))
    new_bal = credit_wallet(evt.user_id, bonus)
    return {"ok": True, "added_cents": bonus, "new_balance_cents": new_bal}

@router.post("/opentable")
def ot_credit(evt: OrderEvent):
    _ = clicks.last_for(evt.user_id, evt.merchant, hours=6)
    # demo: flat $1.00
    bonus = 100
    new_bal = credit_wallet(evt.user_id, bonus)
    return {"ok": True, "added_cents": bonus, "new_balance_cents": new_bal}
