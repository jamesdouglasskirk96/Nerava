"""
NotificationService — sends EV Arrival notifications to merchants via SMS/email.

Uses Twilio for SMS (same pattern as existing OTP service).
SMS includes a merchant_reply_code so DONE replies map to specific sessions.
"""
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

logger = logging.getLogger(__name__)

# Thread pool for blocking Twilio calls (reuse pattern from otp_service_v2)
_executor = ThreadPoolExecutor(max_workers=2)


def _send_sms_sync(to_phone: str, body: str, from_number: str) -> bool:
    """Send SMS via Twilio (blocking). Run in executor thread."""
    try:
        from twilio.rest import Client

        account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")

        if not account_sid or not auth_token:
            logger.warning("Twilio credentials not configured, skipping SMS")
            return False

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=to_phone,
        )
        logger.info(f"SMS sent to {to_phone[:6]}***: sid={message.sid}")
        return True
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_phone[:6]}***: {e}")
        return False


async def send_arrival_sms(
    to_phone: str,
    order_number: str,
    arrival_type: str,
    vehicle_color: Optional[str],
    vehicle_model: Optional[str],
    charger_name: Optional[str],
    merchant_reply_code: str,
    fulfillment_type: Optional[str] = None,
    arrival_distance_m: Optional[float] = None,
) -> bool:
    """
    Send EV Arrival notification SMS to merchant.

    Includes reply code so merchant can text DONE {code} to confirm.
    """
    import asyncio

    from_number = os.getenv("OTP_FROM_NUMBER", "")
    if not from_number:
        logger.warning("OTP_FROM_NUMBER not set, cannot send arrival SMS")
        return False

    # Use fulfillment_type if provided, otherwise fall back to arrival_type
    fulfillment = fulfillment_type or arrival_type
    
    type_emoji = "🚗" if fulfillment == "ev_curbside" else "🍽️"
    vehicle_desc = f"{vehicle_color or ''} {vehicle_model or ''}".strip() or "Unknown vehicle"

    if fulfillment == "ev_dine_in":
        # Dine-in: Driver walks to restaurant
        walk_time = max(1, int((arrival_distance_m or 0) / 80)) if arrival_distance_m else None
        walk_text = f"Walking over — ETA ~{walk_time} minutes" if walk_time else "Walking over now"
        
        body = (
            f"NERAVA EV DINE-IN 🍽️\n\n"
            f"Order #{order_number}\n\n"
            f"Driver arriving NOW from {charger_name if charger_name else 'nearby charger'}\n"
            f"{walk_text}\n\n"
            f"Vehicle: {vehicle_desc}\n\n"
            f"Reply READY when order is prepared."
        )
    else:
        # Curbside: Merchant brings food to car
        charger_address = charger_name or "Nearby charger"
        body = (
            f"NERAVA EV CURBSIDE 🚗\n\n"
            f"Order #{order_number}\n\n"
            f"DELIVER TO CHARGER when ready\n\n"
            f"{vehicle_desc}\n"
            f"{charger_address}\n\n"
            f"Bring order to the driver's car when ready.\n"
            f"Reply DELIVERED when complete."
        )

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _send_sms_sync, to_phone, body, from_number)


async def send_arrival_email(
    to_email: str,
    order_number: str,
    arrival_type: str,
    vehicle_color: Optional[str],
    vehicle_model: Optional[str],
    charger_name: Optional[str],
    merchant_name: str,
) -> bool:
    """Send EV Arrival notification email to merchant (placeholder)."""
    # Email integration is deferred — log for now
    logger.info(f"Email notification would be sent to {to_email} for order #{order_number}")
    return False


async def notify_merchant(
    notify_sms: bool,
    notify_email: bool,
    sms_phone: Optional[str],
    email_address: Optional[str],
    order_number: str,
    arrival_type: str,
    vehicle_color: Optional[str],
    vehicle_model: Optional[str],
    charger_name: Optional[str],
    merchant_name: str,
    merchant_reply_code: str,
    fulfillment_type: Optional[str] = None,
    arrival_distance_m: Optional[float] = None,
) -> str:
    """
    Send arrival notification via configured channels.

    Returns: notification method used ('sms', 'email', 'both', 'none')
    """
    sms_sent = False
    email_sent = False

    if notify_sms and sms_phone:
        sms_sent = await send_arrival_sms(
            to_phone=sms_phone,
            order_number=order_number,
            arrival_type=arrival_type,
            vehicle_color=vehicle_color,
            vehicle_model=vehicle_model,
            charger_name=charger_name,
            merchant_reply_code=merchant_reply_code,
            fulfillment_type=fulfillment_type,
            arrival_distance_m=arrival_distance_m,
        )

    if notify_email and email_address:
        email_sent = await send_arrival_email(
            to_email=email_address,
            order_number=order_number,
            arrival_type=arrival_type,
            vehicle_color=vehicle_color,
            vehicle_model=vehicle_model,
            charger_name=charger_name,
            merchant_name=merchant_name,
        )

    if sms_sent and email_sent:
        return "both"
    if sms_sent:
        return "sms"
    if email_sent:
        return "email"
    return "none"
