"""
Integration tests for demo charging flow
"""
import pytest
import os
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.domain import DriverWallet
from app.models import User
from app.dependencies.driver import get_current_driver


@pytest.fixture
def demo_enabled(monkeypatch):
    """Enable demo mode for tests"""
    monkeypatch.setenv("DEMO_MODE", "true")
    yield
    monkeypatch.delenv("DEMO_MODE", raising=False)


@pytest.fixture
def demo_disabled(monkeypatch):
    """Disable demo mode for tests"""
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.delenv("DEMO_QR_ENABLED", raising=False)
    yield


def test_charging_start_bumps_wallet_activity(db: Session, test_user, demo_enabled, client):
    """Test that charging start bumps wallet_activity_updated_at"""
    from app.main_simple import app
    
    # Override auth dependency
    def override_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = override_get_current_driver
    
    try:
        # Create wallet
        wallet = DriverWallet(
            user_id=test_user.id,
            nova_balance=1000,
            energy_reputation_score=0,
            charging_detected=False
        )
        db.add(wallet)
        db.commit()
        
        # Get initial activity timestamp (should be None)
        db.refresh(wallet)
        initial_activity = wallet.wallet_activity_updated_at
        
        # Start charging
        response = client.post("/v1/demo/charging/start")
        
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert data["charging_detected"] is True
        
        # Check wallet was updated
        db.refresh(wallet)
        assert wallet.charging_detected is True
        assert wallet.charging_detected_at is not None
        
        # wallet_activity_updated_at should be bumped
        assert wallet.wallet_activity_updated_at is not None
        if initial_activity:
            assert wallet.wallet_activity_updated_at >= initial_activity
    finally:
        app.dependency_overrides.clear()


def test_wallet_status_returns_charging_detected(db: Session, test_user, client):
    """Test that GET /v1/wallet/status returns charging state"""
    from app.main_simple import app
    
    # Override auth dependency
    def override_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = override_get_current_driver
    
    try:
        # Create wallet with charging detected
        wallet = DriverWallet(
            user_id=test_user.id,
            nova_balance=1000,
            energy_reputation_score=0,
            charging_detected=True,
            charging_detected_at=datetime.utcnow()
        )
        db.add(wallet)
        db.commit()
        
        # Get status
        response = client.get("/v1/wallet/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["charging_detected"] is True
        assert data["charging_detected_at"] is not None
        assert data["message"] == "Charging detected. Nova is accruing."
    finally:
        app.dependency_overrides.clear()


def test_wallet_status_returns_not_charging(db: Session, test_user, client):
    """Test that GET /v1/wallet/status returns not charging when false"""
    from app.main_simple import app
    
    # Override auth dependency
    def override_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = override_get_current_driver
    
    try:
        # Create wallet without charging
        wallet = DriverWallet(
            user_id=test_user.id,
            nova_balance=1000,
            energy_reputation_score=0,
            charging_detected=False
        )
        db.add(wallet)
        db.commit()
        
        # Get status
        response = client.get("/v1/wallet/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["charging_detected"] is False
        assert data["charging_detected_at"] is None
        assert data["message"] == ""
    finally:
        app.dependency_overrides.clear()


def test_charging_start_disabled_returns_404(db: Session, test_user, demo_disabled, client):
    """Test that charging start returns 404 when demo is disabled"""
    from app.main_simple import app
    
    # Override auth dependency
    def override_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = override_get_current_driver
    
    try:
        response = client.post("/v1/demo/charging/start")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "DEMO_DISABLED"
    finally:
        app.dependency_overrides.clear()


def test_charging_stop_sets_false(db: Session, test_user, demo_enabled, client):
    """Test that charging stop sets charging_detected=false"""
    from app.main_simple import app
    
    # Override auth dependency
    def override_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = override_get_current_driver
    
    try:
        # Create wallet with charging detected
        wallet = DriverWallet(
            user_id=test_user.id,
            nova_balance=1000,
            energy_reputation_score=0,
            charging_detected=True,
            charging_detected_at=datetime.utcnow()
        )
        db.add(wallet)
        db.commit()
        
        # Stop charging
        response = client.post("/v1/demo/charging/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        
        # Check wallet was updated
        db.refresh(wallet)
        assert wallet.charging_detected is False
    finally:
        app.dependency_overrides.clear()

