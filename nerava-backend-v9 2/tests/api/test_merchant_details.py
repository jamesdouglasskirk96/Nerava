"""
Tests for Merchant Details API
"""
import pytest
from fastapi.testclient import TestClient
from app.main_simple import app
from app.models.while_you_charge import Merchant, MerchantPerk
from app.models.intent import IntentSession
from app.models import User


@pytest.fixture
def client():
    return TestClient(app)


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


@pytest.fixture
def mock_merchant(db):
    """Create a test merchant"""
    merchant = Merchant(
        id="m_test_1",
        external_id="mock_asadas_grill",
        name="Asadas Grill",
        category="Restaurant",
        primary_category="food",
        lat=30.2680,
        lng=-97.7435,
        address="123 Main St, Austin, TX",
        rating=4.5,
        price_level=2,
        photo_url="https://example.com/photo.jpg",
    )
    db.add(merchant)
    
    # Add a perk
    perk = MerchantPerk(
        merchant_id=merchant.id,
        title="Happy Hour",
        description="Show your pass to access Happy Hour.",
        nova_reward=100,
        is_active=True,
    )
    db.add(perk)
    db.commit()
    return merchant


@pytest.fixture
def mock_intent_session(db, mock_user):
    """Create a test intent session"""
    session = IntentSession(
        id="session-123",
        user_id=mock_user.id,
        lat=30.2672,
        lng=-97.7431,
        accuracy_m=50.0,
        confidence_tier="A",
        source="web",
    )
    db.add(session)
    db.commit()
    return session


class TestMerchantDetailsEndpoint:
    """Test GET /v1/merchants/{merchant_id} endpoint"""
    
    def test_get_merchant_details_by_id(self, client, mock_merchant):
        """Test getting merchant details by internal ID"""
        response = client.get(f"/v1/merchants/{mock_merchant.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["merchant"]["id"] == mock_merchant.id
        assert data["merchant"]["name"] == "Asadas Grill"
        assert data["merchant"]["category"] == "Restaurant"
        assert data["perk"]["title"] == "Happy Hour"
        assert data["perk"]["badge"] == "Happy Hour ⭐️"
        assert data["wallet"]["can_add"] is True
        assert data["actions"]["add_to_wallet"] is True
    
    def test_get_merchant_details_by_external_id(self, client, mock_merchant):
        """Test getting merchant details by Google Places external_id"""
        response = client.get(f"/v1/merchants/{mock_merchant.external_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["merchant"]["name"] == "Asadas Grill"
    
    def test_get_merchant_details_with_session_id(self, client, mock_merchant, mock_intent_session):
        """Test getting merchant details with session_id for distance calculation"""
        response = client.get(
            f"/v1/merchants/{mock_merchant.id}",
            params={"session_id": str(mock_intent_session.id)}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["merchant"]["name"] == "Asadas Grill"
        assert "distance_miles" in data["moment"]
        assert data["moment"]["distance_miles"] > 0
        assert "min walk" in data["moment"]["label"] or "On your way out" in data["moment"]["label"]
    
    def test_get_merchant_details_not_found(self, client):
        """Test 404 when merchant not found"""
        response = client.get("/v1/merchants/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_merchant_details_response_schema(self, client, mock_merchant):
        """Test that response matches expected schema"""
        response = client.get(f"/v1/merchants/{mock_merchant.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all required fields
        assert "merchant" in data
        assert "moment" in data
        assert "perk" in data
        assert "wallet" in data
        assert "actions" in data
        
        # Check merchant fields
        assert "id" in data["merchant"]
        assert "name" in data["merchant"]
        assert "category" in data["merchant"]
        
        # Check moment fields
        assert "label" in data["moment"]
        assert "distance_miles" in data["moment"]
        assert "moment_copy" in data["moment"]
        
        # Check perk fields
        assert "title" in data["perk"]
        assert "badge" in data["perk"]
        assert "description" in data["perk"]
        
        # Check wallet fields
        assert "can_add" in data["wallet"]
        assert "state" in data["wallet"]
        
        # Check actions fields
        assert "add_to_wallet" in data["actions"]

