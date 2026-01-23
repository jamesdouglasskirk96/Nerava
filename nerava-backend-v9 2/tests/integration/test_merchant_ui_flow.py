"""
Smoke tests for merchant UI pages
"""
import pytest
from fastapi.testclient import TestClient
from app.main_simple import app


client = TestClient(app)


def test_merchant_onboard_page_served():
    """Test that merchant onboarding page is accessible"""
    response = client.get("/app/merchant/onboard.html")
    
    # Should return 200 and contain "Connect Square"
    assert response.status_code == 200
    assert "Connect Square" in response.text or "connect" in response.text.lower()


def test_merchant_dashboard_page_served():
    """Test that merchant dashboard page is accessible"""
    response = client.get("/app/merchant/dashboard.html")
    
    # Should return 200
    assert response.status_code == 200


def test_checkout_page_served():
    """Test that checkout page is accessible"""
    response = client.get("/app/checkout.html")
    
    # Should return 200
    assert response.status_code == 200

