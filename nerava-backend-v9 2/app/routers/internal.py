"""Internal test endpoints for integrations"""
import os
from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/_internal", tags=["internal"])

INTERNAL_TEST_SECRET = os.getenv("INTERNAL_TEST_SECRET", "test-secret-change-me")


@router.get("/sentry-test")
async def sentry_test(x_internal_test: str = Header(...)):
    """Test endpoint to verify Sentry error tracking is working."""
    if x_internal_test != INTERNAL_TEST_SECRET:
        raise HTTPException(status_code=403, detail="Invalid test secret")

    # Trigger a controlled error
    try:
        raise ValueError("Sentry test error - this is intentional")
    except Exception as e:
        from app.core.sentry import capture_exception
        capture_exception(e, extra={"test": True})
        return {"ok": True, "message": "Error captured to Sentry"}


