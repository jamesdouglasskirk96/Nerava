import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm"""
    
    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.rate_limit_per_minute
        self.tokens_per_second = self.requests_per_minute / 60.0
        self.buckets: Dict[str, Dict] = {}
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting"""
        # Use IP address as primary identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # If user is authenticated, use user ID
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        return f"ip:{client_ip}"
    
    def _get_bucket(self, client_id: str) -> Dict:
        """Get or create token bucket for client"""
        if client_id not in self.buckets:
            self.buckets[client_id] = {
                'tokens': self.requests_per_minute,
                'last_refill': time.time()
            }
        return self.buckets[client_id]
    
    def _refill_tokens(self, bucket: Dict) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()
        time_passed = now - bucket['last_refill']
        tokens_to_add = time_passed * self.tokens_per_second
        
        bucket['tokens'] = min(
            self.requests_per_minute,
            bucket['tokens'] + tokens_to_add
        )
        bucket['last_refill'] = now
    
    def _consume_token(self, bucket: Dict) -> bool:
        """Consume a token from the bucket"""
        self._refill_tokens(bucket)
        
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return True
        return False
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        client_id = self._get_client_id(request)
        bucket = self._get_bucket(client_id)
        
        if not self._consume_token(bucket):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket['tokens']))
        response.headers["X-RateLimit-Reset"] = str(int(bucket['last_refill'] + 60))
        
        return response
