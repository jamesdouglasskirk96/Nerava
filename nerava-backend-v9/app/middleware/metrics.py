import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge

# Prometheus metrics
requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])
active_requests = Gauge('http_active_requests', 'Currently active requests')

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Increment active requests
        active_requests.inc()
        
        # Start timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Extract endpoint (remove path parameters)
        endpoint = request.url.path
        if '/v1/energyhub/events/charge-start' in endpoint:
            endpoint = '/v1/energyhub/events/charge-start'
        elif '/v1/energyhub/events/charge-stop' in endpoint:
            endpoint = '/v1/energyhub/events/charge-stop'
        elif '/v1/energyhub/windows' in endpoint:
            endpoint = '/v1/energyhub/windows'
        
        # Record metrics
        requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()
        
        request_duration.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)
        
        # Decrement active requests
        active_requests.dec()
        
        return response
