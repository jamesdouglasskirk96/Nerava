"""
FastAPI middleware for metrics collection.
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.obs.obs import get_trace_id, record_request

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics and set trace IDs."""
    
    async def dispatch(self, request: Request, call_next):
        # Set trace ID in request state
        trace_id = get_trace_id(request)
        request.state.trace_id = trace_id
        
        # Start timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Extract route from request
        route = f"{request.method} {request.url.path}"
        
        # Record metrics
        record_request(route, duration_ms)
        
        # Add trace ID to response headers
        response.headers["X-Trace-Id"] = trace_id
        
        return response