"""
Tests for Vehicle Onboarding API
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.models import VehicleOnboarding, User, IntentSession
from app.services.vehicle_onboarding_service import (
    start_onboarding,
    complete_onboarding,
)


@pytest.fixture
def mock_user(db):
    """Create a test user"""
    user = User(
        id=1,
        public_id="test-user-123",
        email="test@example.com",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


class TestVehicleOnboardingService:
    """Test VehicleOnboardingService functions"""
    
    @patch('app.services.vehicle_onboarding_service.generate_upload_urls')
    def test_start_onboarding(self, mock_upload_urls, db, mock_user):
        """Test starting vehicle onboarding"""
        mock_upload_urls.return_value = [
            "https://s3.example.com/photo1.jpg",
            "https://s3.example.com/photo2.jpg",
        ]
        
        onboarding = start_onboarding(
            db=db,
            user_id=mock_user.id,
            intent_session_id="session-123",
        )
        
        assert onboarding.user_id == mock_user.id
        assert onboarding.status == "SUBMITTED"
        assert onboarding.intent_session_id == "session-123"
        assert onboarding.expires_at is not None
        
        # Verify photo URLs stored
        photo_urls = json.loads(onboarding.photo_urls)
        assert len(photo_urls) == 2
    
    def test_complete_onboarding(self, db, mock_user):
        """Test completing vehicle onboarding"""
        # Create onboarding record
        onboarding = VehicleOnboarding(
            id="onboarding-123",
            user_id=mock_user.id,
            status="SUBMITTED",
            photo_urls=json.dumps(["https://s3.example.com/photo1.jpg"]),
            expires_at=datetime.utcnow() + timedelta(days=90),
        )
        db.add(onboarding)
        db.commit()
        
        # Complete onboarding
        photo_urls = [
            "https://s3.example.com/photo1.jpg",
            "https://s3.example.com/photo2.jpg",
        ]
        
        updated = complete_onboarding(
            db=db,
            onboarding_id="onboarding-123",
            user_id=mock_user.id,
            photo_urls=photo_urls,
            license_plate="ABC123",
        )
        
        assert updated.status == "SUBMITTED"
        assert updated.license_plate == "ABC123"
        stored_urls = json.loads(updated.photo_urls)
        assert len(stored_urls) == 2
    
    def test_complete_onboarding_not_found(self, db, mock_user):
        """Test completing onboarding that doesn't exist"""
        with pytest.raises(ValueError):
            complete_onboarding(
                db=db,
                onboarding_id="nonexistent",
                user_id=mock_user.id,
                photo_urls=[],
            )


class TestVehicleOnboardingEndpoint:
    """Test vehicle onboarding endpoints"""
    
    @patch('app.services.vehicle_onboarding_service.start_onboarding')
    @patch('app.routers.vehicle_onboarding.get_current_user')
    def test_start_onboarding_endpoint(self, mock_get_user, mock_start, client, mock_user):
        """Test POST /v1/vehicle/onboarding/start"""
        mock_get_user.return_value = mock_user
        
        onboarding = VehicleOnboarding(
            id="onboarding-123",
            user_id=mock_user.id,
            status="SUBMITTED",
            photo_urls=json.dumps(["https://s3.example.com/photo1.jpg"]),
            expires_at=datetime.utcnow() + timedelta(days=90),
        )
        mock_start.return_value = onboarding
        
        response = client.post(
            "/v1/vehicle/onboarding/start",
            json={
                "intent_session_id": "session-123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_id"] == "onboarding-123"
        assert len(data["upload_urls"]) > 0
    
    @patch('app.services.vehicle_onboarding_service.complete_onboarding')
    @patch('app.routers.vehicle_onboarding.get_current_user')
    def test_complete_onboarding_endpoint(self, mock_get_user, mock_complete, client, mock_user):
        """Test POST /v1/vehicle/onboarding/complete"""
        mock_get_user.return_value = mock_user
        
        onboarding = VehicleOnboarding(
            id="onboarding-123",
            user_id=mock_user.id,
            status="SUBMITTED",
            photo_urls=json.dumps(["https://s3.example.com/photo1.jpg"]),
            expires_at=datetime.utcnow() + timedelta(days=90),
        )
        mock_complete.return_value = onboarding
        
        response = client.post(
            "/v1/vehicle/onboarding/complete",
            json={
                "onboarding_id": "onboarding-123",
                "photo_urls": ["https://s3.example.com/photo1.jpg"],
                "license_plate": "ABC123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_id"] == "onboarding-123"
        assert data["status"] == "SUBMITTED"

