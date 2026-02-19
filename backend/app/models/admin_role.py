"""
Admin Role enum and permissions for RBAC
"""
from enum import Enum


class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"      # Full access
    ZONE_MANAGER = "zone_manager"    # Manage merchants in assigned zones
    SUPPORT = "support"              # Read-only + handle support tickets
    ANALYST = "analyst"              # Read-only analytics access


ROLE_PERMISSIONS = {
    AdminRole.SUPER_ADMIN: {
        "merchants": ["read", "write", "delete"],
        "users": ["read", "write", "delete"],
        "analytics": ["read"],
        "settings": ["read", "write"],
        "kill_switch": ["read", "write"],
    },
    AdminRole.ZONE_MANAGER: {
        "merchants": ["read", "write"],
        "users": ["read"],
        "analytics": ["read"],
        "settings": ["read"],
    },
    AdminRole.SUPPORT: {
        "merchants": ["read"],
        "users": ["read"],
        "analytics": ["read"],
    },
    AdminRole.ANALYST: {
        "analytics": ["read"],
        "merchants": ["read"],
    },
}


def has_permission(role: AdminRole, resource: str, action: str) -> bool:
    """Check if a role has permission for a resource/action"""
    perms = ROLE_PERMISSIONS.get(role, {})
    return action in perms.get(resource, [])
