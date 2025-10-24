"""
Tests for security features
"""
import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.security.jwt import jwt_manager
from app.security.rbac import Role, rbac_manager, Permission

client = TestClient(app)

class TestJWT:
    """Test JWT functionality"""
    
    def test_create_token(self):
        """Test token creation"""
        user_id = "test_user_123"
        token = jwt_manager.create_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token can be decoded
        payload = jwt_manager.verify_token(token)
        assert payload["user_id"] == user_id
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_expired_token(self):
        """Test verification of expired token"""
        user_id = "test_user_123"
        # Create token with very short expiry
        token = jwt_manager.create_token(user_id, expires_delta=timedelta(seconds=-1))
        
        with pytest.raises(Exception):  # Should raise HTTPException
            jwt_manager.verify_token(token)
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        invalid_token = "invalid.token.here"
        
        with pytest.raises(Exception):  # Should raise HTTPException
            jwt_manager.verify_token(invalid_token)
    
    def test_refresh_token(self):
        """Test token refresh"""
        user_id = "test_user_123"
        original_token = jwt_manager.create_token(user_id)
        
        new_token = jwt_manager.refresh_token(original_token)
        
        assert new_token != original_token
        
        # Verify new token
        payload = jwt_manager.verify_token(new_token)
        assert payload["user_id"] == user_id

class TestRBAC:
    """Test Role-Based Access Control"""
    
    def test_user_permissions(self):
        """Test user role permissions"""
        permissions = rbac_manager.get_user_permissions(Role.USER)
        
        assert Permission.START_CHARGE in permissions
        assert Permission.STOP_CHARGE in permissions
        assert Permission.VIEW_WALLET in permissions
        assert Permission.MANAGE_SYSTEM not in permissions
    
    def test_admin_permissions(self):
        """Test admin role permissions"""
        permissions = rbac_manager.get_user_permissions(Role.ADMIN)
        
        assert Permission.START_CHARGE in permissions
        assert Permission.MANAGE_SYSTEM in permissions
        assert Permission.VIEW_ALL_USERS in permissions
    
    def test_has_permission(self):
        """Test permission checking"""
        assert rbac_manager.has_permission(Role.USER, Permission.START_CHARGE)
        assert not rbac_manager.has_permission(Role.USER, Permission.MANAGE_SYSTEM)
        assert rbac_manager.has_permission(Role.ADMIN, Permission.MANAGE_SYSTEM)
    
    def test_require_permission_success(self):
        """Test successful permission requirement"""
        # Should not raise exception
        rbac_manager.require_permission(Role.USER, Permission.START_CHARGE)
    
    def test_require_permission_failure(self):
        """Test failed permission requirement"""
        with pytest.raises(Exception):  # Should raise HTTPException
            rbac_manager.require_permission(Role.USER, Permission.MANAGE_SYSTEM)

class TestAuthMiddleware:
    """Test authentication middleware"""
    
    def test_public_endpoints(self):
        """Test that public endpoints don't require authentication"""
        response = client.get("/healthz")
        assert response.status_code == 200
        
        response = client.get("/readyz")
        assert response.status_code == 200
        
        response = client.get("/metrics")
        assert response.status_code == 200
    
    def test_protected_endpoints_require_auth(self):
        """Test that protected endpoints require authentication"""
        response = client.get("/v1/flags")
        assert response.status_code == 401  # Unauthorized
    
    def test_invalid_token(self):
        """Test request with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/v1/flags", headers=headers)
        assert response.status_code == 401
    
    def test_missing_auth_header(self):
        """Test request without authorization header"""
        response = client.get("/v1/flags")
        assert response.status_code == 401

class TestFeatureFlags:
    """Test feature flags functionality"""
    
    def test_get_flags_unauthorized(self):
        """Test getting flags without authentication"""
        response = client.get("/v1/flags")
        assert response.status_code == 401
    
    def test_get_specific_flag_unauthorized(self):
        """Test getting specific flag without authentication"""
        response = client.get("/v1/flags/enable_sync_credit")
        assert response.status_code == 401
    
    def test_toggle_flag_unauthorized(self):
        """Test toggling flag without authentication"""
        response = client.post("/v1/flags/enable_sync_credit/toggle", json={"enabled": True})
        assert response.status_code == 401

class TestAuditLogging:
    """Test audit logging functionality"""
    
    def test_audit_middleware_logs_requests(self):
        """Test that audit middleware logs requests"""
        # This would require mocking the logger to verify log calls
        # For now, just test that the endpoint responds
        response = client.get("/healthz")
        assert response.status_code == 200
    
    def test_sensitive_endpoints_audit(self):
        """Test that sensitive endpoints are audited"""
        # This would require mocking the logger to verify audit log calls
        # For now, just test that the endpoint responds
        response = client.get("/v1/energyhub/windows")
        assert response.status_code == 200
