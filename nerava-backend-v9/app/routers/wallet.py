# app/routers/wallet.py
from fastapi import APIRouter, Query
from pydantic import BaseModel, EmailStr, conint
from typing import Union
from app.services.wallet import get_wallet, credit_wallet, debit_wallet

router = APIRouter(prefix="/v1/wallet", tags=["wallet"])

class WalletOp(BaseModel):
    user_id: Union[EmailStr, str]
    amount_cents: conint(ge=1, le=50000)

@router.get("")
def wallet_get(user_id: str = Query(..., description="User email or ID")):
    return get_wallet(user_id)

@router.post("/credit")
def wallet_credit(op: WalletOp):
    return credit_wallet(op.user_id, op.amount_cents)

@router.post("/debit")
def wallet_debit(op: WalletOp):
    return debit_wallet(op.user_id, op.amount_cents)

# QS convenience for quick demos:
@router.post("/credit_qs")
def wallet_credit_qs(user_id: str = Query(...), cents: int = Query(..., ge=1, le=50000)):
    return credit_wallet(user_id, cents)

@router.post("/debit_qs")
def wallet_debit_qs(user_id: str = Query(...), cents: int = Query(..., ge=1, le=50000)):
    return debit_wallet(user_id, cents)
