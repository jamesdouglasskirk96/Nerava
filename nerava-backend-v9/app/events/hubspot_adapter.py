"""
HubSpot Event Adapter

P3: Converts domain events to HubSpot event format.
"""
from typing import Dict, Any
from app.utils.log import get_logger

logger = get_logger(__name__)


def adapt_user_signup_event(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert user signup event to HubSpot format.
    
    Args:
        user_data: User data from signup event
    
    Returns:
        HubSpot-formatted payload
    """
    return {
        "eventName": "nerava_user_signup",
        "properties": {
            "user_id": user_data.get("user_id"),
            "email": user_data.get("email"),
            "signup_date": user_data.get("created_at"),
            "role_flags": user_data.get("role_flags", ""),
        }
    }


def adapt_redemption_event(redemption_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert redemption event to HubSpot format.
    
    Args:
        redemption_data: Redemption data from event
    
    Returns:
        HubSpot-formatted payload
    """
    return {
        "eventName": "nerava_redemption",
        "properties": {
            "user_id": redemption_data.get("user_id"),
            "merchant_id": redemption_data.get("merchant_id"),
            "amount_cents": redemption_data.get("amount_cents"),
            "redemption_id": redemption_data.get("redemption_id"),
            "redeemed_at": redemption_data.get("redeemed_at"),
        }
    }


def adapt_wallet_pass_install_event(install_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert wallet pass install event to HubSpot format.
    
    Args:
        install_data: Wallet pass install data
    
    Returns:
        HubSpot-formatted payload
    """
    return {
        "eventName": "nerava_wallet_pass_install",
        "properties": {
            "user_id": install_data.get("user_id"),
            "pass_type": install_data.get("pass_type", "apple"),  # apple or google
            "installed_at": install_data.get("installed_at"),
        }
    }
