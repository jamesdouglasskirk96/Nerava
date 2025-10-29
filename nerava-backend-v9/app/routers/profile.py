from fastapi import APIRouter

router = APIRouter(prefix="/v1/profile", tags=["profile"])

@router.get("/me")
def get_my_profile(user_id: str = "demo-user-123"):
    """Get current user profile"""
    return {
        "id": user_id,
        "email": f"{user_id}@nerava.app",
        "name": "Demo User",
        "tier": "Silver",
        "followers": 12,
        "following": 8
    }
