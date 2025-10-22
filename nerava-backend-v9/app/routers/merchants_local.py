from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.services.db_merchant import create_merchant, list_merchants_near, add_perk, list_perks, claim_perk
from app.services.wallet import credit_wallet

router = APIRouter(prefix="/v1/local", tags=["local_merchants"])

class MerchantIn(BaseModel):
    name: str
    lat: float
    lng: float
    category: str = "other"
    logo_url: str = ""

@router.post("/merchant")
def register_merchant(m: MerchantIn):
    try:
        return create_merchant(m.name, m.lat, m.lng, m.category, m.logo_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"merchant_create_failed: {e}")

@router.get("/merchants_near", response_model=List[Dict[str, Any]])
def merchants_near(lat: float = Query(...), lng: float = Query(...), radius_m: float = Query(800)):
    return list_merchants_near(lat, lng, radius_m)

class PerkIn(BaseModel):
    merchant_id: int
    title: str = Field(..., min_length=2)
    description: str = ""
    reward_cents: int = Field(ge=0, default=0)

@router.post("/perk")
def create_perk(p: PerkIn):
    try:
        return add_perk(p.merchant_id, p.title, p.description, p.reward_cents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"perk_create_failed: {e}")

@router.get("/perks")
def perks(merchant_id: int):
    return list_perks(merchant_id)

class ClaimIn(BaseModel):
    perk_id: int
    user_id: str

@router.post("/perk/claim")
def claim(p: ClaimIn):
    try:
        record = claim_perk(p.perk_id, p.user_id)
        # optional: auto-credit wallet with reward (read reward_cents)
        # fetch reward cents quickly:
        # (simple join-less look-up to keep the demo clean)
        from app.services.db_merchant import _conn
        with _conn() as con:
            row = con.execute("SELECT reward_cents FROM merchant_perks WHERE id=?", (p.perk_id,)).fetchone()
            reward = int(row["reward_cents"]) if row else 0
        if reward > 0:
            out = credit_wallet(p.user_id, reward)
            record["wallet_balance_cents"] = out.get("balance_cents", 0)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"claim_failed: {e}")
