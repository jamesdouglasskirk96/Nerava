# server/src/routes_dev.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
from .deps import current_user_id

router = APIRouter(prefix="/v1/dev")

@router.post("/location")
def set_location(payload: dict, user_id: str = Depends(current_user_id), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        u = User(id=user_id, handle="you")
        db.add(u)
    u.last_lat = float(payload.get("lat"))
    u.last_lng = float(payload.get("lng"))
    db.commit()
    return {"ok":True, "lat": u.last_lat, "lng": u.last_lng}
