import time
import uuid
import json
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log request
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "user_agent": request.headers.get("user-agent", ""),
                "remote_addr": request.client.host if request.client else None
            }
            
            logger.info(json.dumps(log_data))
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
        except Exception as e:
            # Log exceptions with full traceback
            duration_ms = (time.time() - start_time) * 1000
            logger.exception(
                "ERROR in LoggingMiddleware: %s %s failed after %sms: %s",
                request.method,
                request.url.path,
                round(duration_ms, 2),
                str(e)
            )
            raise
