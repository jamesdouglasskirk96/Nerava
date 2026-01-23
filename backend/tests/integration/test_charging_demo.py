"""
Integration tests for charging demo endpoints
"""
import pytest
import os
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.domain import DriverWallet
from app.dependencies.driver import get_current_driver
from app.main_simple import app


@pytest.fixture
def enable_demo_mode(monkeypatch):
    """Enable demo mode for tests"""
    monkeypatch.setenv("DEMO_MODE", "true")
    yield
    monkeypatch.delenv("DEMO_MODE", raising=False)


@pytest.fixture
def disable_demo_mode(monkeypatch):
    """Disable demo mode for tests"""
    monkeypatch.setenv("DEMO_MODE", "false")
    yield
    monkeypatch.delenv("DEMO_MODE", raising=False)


def test_charging_start_bumps_wallet_activity(db: Session, test_user, enable_demo_mode, client):
    """Test that charging start bumps wallet_activity_updated_at"""
    # Override get_current_driver dependency
    def mock_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = mock_get_current_driver
    
    try:
        # Create wallet
        wallet = DriverWallet(
            user_id=test_user.id,
            nova_balance=0,
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
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "OK"
        assert data["charging_detected"] is True
        assert "charging_detected_at" in data
        
        # Check wallet was updated
        db.refresh(wallet)
        assert wallet.charging_detected is True
        assert wallet.charging_detected_at is not None
        # wallet_activity_updated_at should be bumped
        assert wallet.wallet_activity_updated_at is not None
        if initial_activity:
            assert wallet.wallet_activity_updated_at > initial_activity
    finally:
        app.dependency_overrides.pop(get_current_driver, None)


def test_charging_start_disabled_returns_404(db: Session, test_user, disable_demo_mode, client):
    """Test that charging start returns 404 when demo is disabled"""
    # Override get_current_driver dependency
    def mock_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = mock_get_current_driver
    
    try:
        response = client.post("/v1/demo/charging/start")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "DEMO_DISABLED"
    finally:
        app.dependency_overrides.pop(get_current_driver, None)


def test_charging_stop_sets_false(db: Session, test_user, enable_demo_mode, client):
    """Test that charging stop sets charging_detected=false"""
    # Override get_current_driver dependency
    def mock_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = mock_get_current_driver
    
    try:
        # Create wallet with charging detected
        wallet = DriverWallet(
            user_id=test_user.id,
            nova_balance=0,
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
        app.dependency_overrides.pop(get_current_driver, None)


def test_wallet_status_returns_charging_state(db: Session, test_user, client):
    """Test that wallet status endpoint returns charging state"""
    # Override get_current_driver dependency
    def mock_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = mock_get_current_driver
    
    try:
        # Create wallet with charging detected
        now = datetime.utcnow()
        wallet = DriverWallet(
            user_id=test_user.id,
            nova_balance=0,
            energy_reputation_score=0,
            charging_detected=True,
            charging_detected_at=now
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
        app.dependency_overrides.pop(get_current_driver, None)


def test_wallet_status_returns_not_charging(db: Session, test_user, client):
    """Test that wallet status returns not charging when false"""
    # Override get_current_driver dependency
    def mock_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = mock_get_current_driver
    
    try:
        # Create wallet without charging
        wallet = DriverWallet(
            user_id=test_user.id,
            nova_balance=0,
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
        app.dependency_overrides.pop(get_current_driver, None)

