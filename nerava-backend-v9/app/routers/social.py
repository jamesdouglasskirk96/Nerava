from __future__ import annotations
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/v1/social", tags=["social"])

# Demo in-memory store (replace with DB later)
class FeedItem(BaseModel):
    id: str
    user_id: str
    user_display: str
    avatar_url: Optional[str] = None
    kwh: float
    reward_usd: float
    hub_name: str
    city: str
    timestamp: datetime

# Seed some demo users/events
USERS = [
    {"id":"u_alex","name":"Alex Park","avatar":None},
    {"id":"u_maya","name":"Maya Chen","avatar":None},
    {"id":"u_rob","name":"Robert Kim","avatar":None},
    {"id":"u_alisha","name":"Alisha Hurston","avatar":None},
]

def _seed(n=18) -> List[FeedItem]:
    base = datetime.now(timezone.utc)
    hubs = [("Nerava Hub","Domain, Austin"), ("Lone Star Hub","South Congress"), ("Capital Hub","Downtown Austin")]
    out = []
    for i in range(n):
      u = USERS[i % len(USERS)]
      h, c = hubs[i % len(hubs)]
      ts = base - timedelta(minutes=5*i)
      out.append(FeedItem(
        id=f"e{i:03d}", user_id=u["id"], user_display=u["name"], avatar_url=u["avatar"],
        kwh=3.5 + (i % 5)*1.1, reward_usd=0.75 + (i%2)*2.98, hub_name=h, city=c, timestamp=ts
      ))
    return out

FEED: List[FeedItem] = _seed()

@router.get("/feed", response_model=List[FeedItem])
async def feed(limit: int = Query(25, ge=1, le=100), following: str = ""):
    ids = [x for x in following.split(",") if x]
    items = FEED
    if ids:
        items = [x for x in FEED if x.user_id in ids]
    return items[:limit]

class FollowReq(BaseModel):
    user_id: str
    target_id: str
    follow: bool

@router.post("/follow")
async def follow(_payload: FollowReq):
    # no-op demo endpoint (client keeps localStorage state)
    return {"ok": True}
