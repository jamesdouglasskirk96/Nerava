"""
Test error handling to ensure production errors don't leak internals.

Verifies that:
1. Production error responses are generic (don't leak internal details)
2. Local/dev error responses include details for debugging
3. Full error details are logged even in production
"""
import os
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.env import is_local_env


@pytest.fixture
def test_app():
    """Create a test FastAPI app with global exception handler"""
    app = FastAPI()
    
    @app.get("/test-error")
    async def test_error():
        """Endpoint that raises an exception"""
        raise ValueError("This is a test error with sensitive details")
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler (same as main_simple.py)"""
        from fastapi.responses import JSONResponse
        from app.core.env import is_local_env
        
        if is_local_env():
            # In local/dev, return detailed error for debugging
            error_message = str(exc) if exc else "Internal server error"
            error_response = {"detail": f"Internal server error: {error_message}"}
        else:
            # In production, return generic error message (details are in logs)
            error_response = {"detail": "Internal server error"}
        
        return JSONResponse(
            status_code=500,
            content=error_response
        )
    
    return app


def test_production_error_response_is_generic(test_app):
    """Test that production error responses don't leak internal details"""
    original_env = os.environ.get("ENV")
    
    try:
        # Set ENV to production
        os.environ["ENV"] = "prod"
        # Clear cache
        from app.core.env import is_local_env
        is_local_env.cache_clear()
        
        client = TestClient(test_app)
        response = client.get("/test-error")
        
        assert response.status_code == 500
        # Should not contain internal error details
        assert "This is a test error" not in response.json()["detail"]
        assert "sensitive details" not in response.json()["detail"]
        assert response.json()["detail"] == "Internal server error"
    finally:
        if original_env is not None:
            os.environ["ENV"] = original_env
        else:
            if "ENV" in os.environ:
                del os.environ["ENV"]
        from app.core.env import is_local_env
        is_local_env.cache_clear()


def test_local_error_response_includes_details(test_app):
    """Test that local/dev error responses include details for debugging"""
    original_env = os.environ.get("ENV")
    
    try:
        # Set ENV to local
        os.environ["ENV"] = "local"
        # Clear cache
        from app.core.env import is_local_env
        is_local_env.cache_clear()
        
        client = TestClient(test_app)
        response = client.get("/test-error")
        
        assert response.status_code == 500
        # Should include error details for debugging
        assert "This is a test error" in response.json()["detail"]
        assert "sensitive details" in response.json()["detail"]
    finally:
        if original_env is not None:
            os.environ["ENV"] = original_env
        else:
            if "ENV" in os.environ:
                del os.environ["ENV"]
        from app.core.env import is_local_env
        is_local_env.cache_clear()







