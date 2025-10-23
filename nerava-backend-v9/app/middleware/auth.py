"""
Authentication middleware for FastAPI
"""
import logging
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.security.jwt import jwt_manager
from app.security.rbac import get_user_role, Role

logger = logging.getLogger(__name__)

security = HTTPBearer()

class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.excluded_paths = {
            "/healthz",
            "/readyz", 
            "/metrics",
            "/docs",
            "/openapi.json",
            "/v1/energyhub/windows",  # Public endpoint
            "/v1/energyhub/events/charge-start",  # Public endpoint
            "/v1/energyhub/events/charge-stop",  # Public endpoint
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid authorization header"
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Verify token and extract user info
            payload = jwt_manager.verify_token(token)
            user_id = payload.get("user_id")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Set user context in request state
            request.state.user_id = user_id
            request.state.user_role = get_user_role(user_id)
            
            logger.debug(f"Authenticated user: {user_id} with role: {request.state.user_role.value}")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
        
        response = await call_next(request)
        return response

def get_current_user(request: Request) -> str:
    """Get current user from request state"""
    if not hasattr(request.state, 'user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.user_id

def get_current_user_role(request: Request) -> Role:
    """Get current user role from request state"""
    if not hasattr(request.state, 'user_role'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return request.state.user_role

def require_role(required_role: Role):
    """Decorator to require a specific role"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get request from kwargs (FastAPI dependency injection)
            request = kwargs.get('request')
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request context not available"
                )
            
            user_role = get_current_user_role(request)
            if user_role != required_role and user_role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {required_role.value} required"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
