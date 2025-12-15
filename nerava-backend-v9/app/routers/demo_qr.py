"""
Demo QR Router

Sandbox-only redirect for printed demo QR codes.

Does NOT affect real QR token logic or production flows.
"""
import os

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["demo-qr"])


@router.get("/qr/eggman-demo-checkout")
async def eggman_demo_qr_redirect():
    """
    Sandbox-only redirect for the printed Eggman demo QR.

    Behavior:
    - If DEMO_QR_ENABLED != "true" -> 404
    - If DEMO_EGGMAN_QR_TOKEN missing -> 404
    - Else 302 redirect to /app/checkout.html?token=<DEMO_EGGMAN_QR_TOKEN>
    """
    if os.getenv("DEMO_QR_ENABLED", "false").lower() != "true":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "DEMO_QR_DISABLED",
                "message": "Demo QR redirect is disabled in this environment.",
            },
        )

    demo_token = os.getenv("DEMO_EGGMAN_QR_TOKEN", "").strip()
    if not demo_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "DEMO_QR_TOKEN_MISSING",
                "message": "Demo QR token is not configured.",
            },
        )

    # Preserve opaque token – this is just a redirect helper
    location = f"/app/checkout.html?token={demo_token}"
    return RedirectResponse(url=location, status_code=status.HTTP_302_FOUND)


