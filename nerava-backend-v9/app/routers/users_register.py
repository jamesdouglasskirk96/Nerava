from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.db_user_ext import register_user, get_user

router = APIRouter(prefix="/v1/users", tags=["users"])

class RegisterIn(BaseModel):
    email: EmailStr
    name: str = ""

@router.post("/register")
def register(payload: RegisterIn):
    try:
        return register_user(payload.email, payload.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"register_failed: {e}")

@router.get("/{email}")
def user_get(email: str):
    u = get_user(email)
    if not u:
        raise HTTPException(status_code=404, detail="not_found")
    return u
