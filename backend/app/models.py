# LEGACY: This file has been moved to app/models/user.py
# Import from new location for backward compatibility
from .models.user import User, UserPreferences

__all__ = ["User", "UserPreferences"]
