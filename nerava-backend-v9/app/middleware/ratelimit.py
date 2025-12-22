import time
from typing import Dict, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using token bucket algorithm with endpoint-specific limits"""
    
    # Endpoint-specific rate limits (P1 security fix)
    # Format: path_prefix -> requests_per_minute
    ENDPOINT_LIMITS = {
        "/v1/auth/": 10,  # Stricter for auth endpoints
        "/v1/otp/": 5,  # Very strict for OTP
        "/v1/nova/": 30,  # Moderate for Nova operations
        "/v1/redeem/": 20,  # Moderate for redemption
        "/v1/stripe/": 30,  # Moderate for Stripe
        "/v1/smartcar/": 20,  # Moderate for Smartcar
        "/v1/square/": 20,  # Moderate for Square
    }
    
    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.default_requests_per_minute = requests_per_minute or settings.rate_limit_per_minute
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
    
    def _get_limit_for_path(self, path: str) -> int:
        """Get rate limit for a specific path"""
        for prefix, limit in self.ENDPOINT_LIMITS.items():
            if path.startswith(prefix):
                return limit
        return self.default_requests_per_minute
    
    def _get_bucket(self, client_id: str, path: str) -> Dict:
        """Get or create token bucket for client and path"""
        # Use path-specific bucket key
        bucket_key = f"{client_id}:{path}"
        limit = self._get_limit_for_path(path)
        
        if bucket_key not in self.buckets:
            self.buckets[bucket_key] = {
                'tokens': limit,
                'last_refill': time.time(),
                'limit': limit
            }
        return self.buckets[bucket_key]
    
    def _refill_tokens(self, bucket: Dict) -> None:
        """Refill tokens based on time elapsed"""
        now = time.time()
        time_passed = now - bucket['last_refill']
        limit = bucket.get('limit', self.default_requests_per_minute)
        tokens_per_second = limit / 60.0
        tokens_to_add = time_passed * tokens_per_second
        
        bucket['tokens'] = min(
            limit,
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
        path = request.url.path
        bucket = self._get_bucket(client_id, path)
        limit = bucket.get('limit', self.default_requests_per_minute)
        
        if not self._consume_token(bucket):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for {path}. Limit: {limit} requests/minute. Please try again later."
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(int(bucket['tokens']))
        response.headers["X-RateLimit-Reset"] = str(int(bucket['last_refill'] + 60))
        
        return response
