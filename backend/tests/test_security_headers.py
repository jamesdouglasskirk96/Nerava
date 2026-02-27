"""
Tests for security headers middleware and request size limit.
"""
import pytest


class TestSecurityHeaders:
    """Test SecurityHeadersMiddleware adds correct headers."""

    def test_healthz_has_security_headers(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "geolocation=(self)" in response.headers["Permissions-Policy"]

    def test_api_endpoint_has_security_headers(self, client):
        response = client.get("/readyz")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"


class TestRequestSizeLimit:
    """Test RequestSizeLimitMiddleware rejects oversized requests."""

    def test_oversized_request_rejected(self, client):
        response = client.post(
            "/v1/exclusive/activate",
            content=b"x" * (11 * 1024 * 1024),  # 11 MB
            headers={"Content-Length": str(11 * 1024 * 1024), "Content-Type": "application/json"},
        )
        assert response.status_code == 413

    def test_normal_request_passes(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
