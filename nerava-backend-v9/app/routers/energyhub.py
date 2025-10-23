from __future__ import annotations
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import httpx

from app.services.energyhub_sim import sim

router = APIRouter(prefix="/v1/energyhub", tags=["energyhub"])

def parse_at(at: Optional[str]) -> Optional[datetime]:
    if not at:
        return None
    try:
        dt = datetime.fromisoformat(at.replace("Z", "+00:00"))
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_at_param")

class ChargeStartReq(BaseModel):
    user_id: str = Field(..., description="User email or id")
    hub_id: str = Field(..., description="Hub identifier")

class ChargeStartResp(BaseModel):
    session_id: str
    active_window: Optional[dict]

class ChargeStopReq(BaseModel):
    session_id: str
    kwh_consumed: float = Field(..., gt=0)

class ChargeStopResp(BaseModel):
    session_id: str
    user_id: str
    hub_id: str
    kwh: float
    window_applied: Optional[str]
    grid_reward_usd: float
    merchant_reward_usd: float
    total_reward_usd: float
    wallet_balance_cents: Optional[int] = None
    message: str

@router.get("/windows")
async def list_windows(at: Optional[str] = Query(None, description="ISO datetime override")):
    override_dt = parse_at(at)
    return sim.list_windows(override_dt)

@router.post("/events/charge-start", response_model=ChargeStartResp)
async def charge_start(payload: ChargeStartReq, at: Optional[str] = Query(None)):
    override_dt = parse_at(at)
    return sim.start_session(payload.user_id, payload.hub_id, override_dt)

@router.post("/events/charge-stop", response_model=ChargeStopResp)
async def charge_stop(payload: ChargeStopReq, at: Optional[str] = Query(None)):
    override_dt = parse_at(at)
    try:
        result = sim.stop_session(payload.session_id, payload.kwh_consumed, override_dt)
    except KeyError:
        raise HTTPException(status_code=404, detail="session_not_found")

    cents = int(round(result["total_reward_usd"] * 100))
    new_balance: Optional[int] = None
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.post(
                "http://127.0.0.1:8000/v1/wallet/credit_qs",
                params={"user_id": result["user_id"], "cents": cents}
            )
            if r.status_code == 200:
                jd = r.json()
                new_balance = jd.get("new_balance_cents") or jd.get("balance_cents")
    except Exception:
        pass

    result["wallet_balance_cents"] = new_balance
    return result

@router.delete("/dev/reset")
async def dev_reset():
    sim.reset()
    return {"ok": True}