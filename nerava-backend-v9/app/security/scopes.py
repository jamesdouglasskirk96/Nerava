"""
Security scopes and authorization utilities.
"""
from fastapi import HTTPException, Depends
from typing import List, Dict, Any

# Mock current user for now - in production this would come from JWT/auth
def get_current_user() -> Dict[str, Any]:
    """Get current user with scopes."""
    # TODO: Implement real JWT validation
    return {
        "user_id": "current_user",
        "scopes": ["merchant:read", "utility:read", "fleet:read"]
    }

def require_scopes(required: List[str]):
    """Dependency to require specific scopes."""
    def scope_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_scopes = current_user.get("scopes", [])
        
        # Check if user has any of the required scopes
        if not any(scope in user_scopes for scope in required):
            raise HTTPException(
                status_code=403,
                detail=f"Missing required scopes: {required}. User has: {user_scopes}"
            )
        
        return current_user
    
    return scope_checker
