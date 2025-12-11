# LEGACY: This file has been moved to app/dependencies/domain.py
# Import from new location for backward compatibility
from .dependencies.domain import (
    oauth2_scheme,
    get_current_user_id,
    get_current_user,
    require_role,
    require_driver,
    require_merchant_admin,
    require_admin,
)

__all__ = [
    "oauth2_scheme",
    "get_current_user_id",
    "get_current_user",
    "require_role",
    "require_driver",
    "require_merchant_admin",
    "require_admin",
]

