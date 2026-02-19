"""
Helpers for EV Arrival-related API tests.

Ensures required routers are registered on the test app used by fixtures.
"""
from app.main_simple import app


def ensure_ev_arrival_routers() -> None:
    """Register EV Arrival routers on the test app if missing."""
    from app.routers import arrival, charge_context, twilio_sms_webhook, merchant_arrivals, account

    existing_paths = {getattr(route, "path", "") for route in app.routes}

    if "/v1/arrival/create" not in existing_paths:
        app.include_router(arrival.router)
    if "/v1/charge-context/nearby" not in existing_paths:
        app.include_router(charge_context.router)
    if "/v1/webhooks/twilio-arrival-sms" not in existing_paths:
        app.include_router(twilio_sms_webhook.router)
    if "/v1/merchants/{merchant_id}/arrivals" not in existing_paths:
        app.include_router(merchant_arrivals.router)
    if "/v1/account/vehicle" not in existing_paths:
        app.include_router(account.router)
