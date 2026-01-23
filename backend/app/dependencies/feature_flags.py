"""
Dependencies for feature flag checks
"""
from fastapi import HTTPException, status
from app.core.config import settings


def check_feature_enabled(feature_name: str, enabled: bool):
    """
    Check if a feature is enabled. Raises 410 Gone if disabled.
    
    Args:
        feature_name: Name of the feature (for error message)
        enabled: Whether the feature is enabled
    """
    if not enabled:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Disabled for pilot: {feature_name}"
        )


def require_google_oauth():
    """Require Google OAuth to be enabled"""
    check_feature_enabled("Google OAuth", settings.ENABLE_GOOGLE_OAUTH)


def require_square():
    """Require Square integration to be enabled"""
    check_feature_enabled("Square", settings.ENABLE_SQUARE)


def require_stripe():
    """Require Stripe integration to be enabled"""
    check_feature_enabled("Stripe", settings.ENABLE_STRIPE)


def require_smartcar():
    """Require Smartcar integration to be enabled"""
    check_feature_enabled("Smartcar", settings.ENABLE_SMARTCAR)


def require_apple_wallet_signing():
    """Require Apple Wallet signing to be enabled"""
    check_feature_enabled("Apple Wallet Signing", settings.ENABLE_APPLE_WALLET_SIGNING)



