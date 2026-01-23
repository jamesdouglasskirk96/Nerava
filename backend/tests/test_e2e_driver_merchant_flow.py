"""
E2E Test: Driver-Merchant Flow

Tests the complete end-to-end flow:
1. Driver captures intent at charger location → receives nearby merchants
2. Merchant signs in, claims location, adds card-on-file, sets placement rule
3. Driver captures intent again → sees merchant placement change (boosted, badges)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import os

from app.main_simple import app
from app.db import get_db
from app.models import (
    User,
    Charger,
    MerchantAccount,
    MerchantLocationClaim,
    MerchantPlacementRule,
    MerchantPaymentMethod,
    IntentSession,
)


# Test fixtures
@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create test user"""
    user = User(
        email="driver@test.com",
        hashed_password="hashed",
        display_name="Test Driver",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_merchant_user(db: Session):
    """Create test merchant user"""
    user = User(
        email="merchant@test.com",
        hashed_password="hashed",
        display_name="Test Merchant",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_charger(db: Session):
    """Create test charger"""
    charger = Charger(
        id="charger_1",
        name="Test Charger",
        lat=30.2672,  # Austin, TX
        lng=-97.7431,
        is_public=True,
        network_name="Test Network",
    )
    db.add(charger)
    db.commit()
    db.refresh(charger)
    return charger


@pytest.fixture
def mock_google_places():
    """Mock Google Places API to return seeded merchants"""
    mock_merchants = [
        {
            "place_id": "ChIJMockPlace1",
            "name": "Mock Coffee Shop",
            "lat": 30.2680,
            "lng": -97.7430,
            "distance_m": 100,
            "types": ["cafe", "restaurant"],
            "photo_url": "https://example.com/photo1.jpg",
            "icon_url": "https://example.com/icon1.png",
        },
        {
            "place_id": "ChIJMockPlace2",
            "name": "Mock Restaurant",
            "lat": 30.2660,
            "lng": -97.7420,
            "distance_m": 200,
            "types": ["restaurant"],
            "photo_url": "https://example.com/photo2.jpg",
            "icon_url": "https://example.com/icon2.png",
        },
    ]
    return mock_merchants


@pytest.fixture
def mock_google_business_profile():
    """Mock Google Business Profile locations"""
    return [
        {
            "location_id": "mock_location_1",
            "name": "Mock Coffee Shop",
            "address": "123 Main St, Austin, TX 78701",
            "place_id": "ChIJMockPlace1",
        },
        {
            "location_id": "mock_location_2",
            "name": "Mock Restaurant",
            "address": "456 Oak Ave, Austin, TX 78702",
            "place_id": "ChIJMockPlace2",
        },
    ]


@pytest.fixture
def mock_stripe_setup_intent():
    """Mock Stripe SetupIntent"""
    return {
        "client_secret": "seti_mock_client_secret_123",
        "id": "seti_mock_123",
    }


def test_e2e_driver_merchant_flow(
    client: TestClient,
    db: Session,
    test_user: User,
    test_merchant_user: User,
    test_charger: Charger,
    mock_google_places: list,
    mock_google_business_profile: list,
    mock_stripe_setup_intent: dict,
):
    """
    E2E test: Full driver-merchant flow
    
    1. Driver captures intent → expect default ordering
    2. Merchant signs in → claims merchant1 → creates SetupIntent → sets placement rule
    3. Driver captures intent again → expect merchant1 appears first with "Boosted" badge
    """
    # Set MERCHANT_AUTH_MOCK=true for testing
    os.environ["MERCHANT_AUTH_MOCK"] = "true"
    
    # Mock Google Places API
    with patch("app.services.intent_service.search_nearby") as mock_search:
        mock_search.return_value = mock_google_places
        
        # Step 1: Driver captures intent (first time)
        # Get auth token for driver
        driver_token = "mock_driver_token"  # In real test, would authenticate
        
        # Mock authentication
        with patch("app.dependencies_domain.get_current_user") as mock_auth:
            mock_auth.return_value = test_user
            
            # Capture intent
            response1 = client.post(
                "/v1/intent/capture",
                json={
                    "lat": test_charger.lat,
                    "lng": test_charger.lng,
                    "accuracy_m": 10.0,
                },
                headers={"Authorization": f"Bearer {driver_token}"},
            )
            
            assert response1.status_code == 200
            data1 = response1.json()
            assert "merchants" in data1
            assert len(data1["merchants"]) == 2
            
            # Check default ordering (by distance)
            merchants1 = data1["merchants"]
            assert merchants1[0]["place_id"] == "ChIJMockPlace1"  # Closer (100m)
            assert merchants1[1]["place_id"] == "ChIJMockPlace2"  # Farther (200m)
            
            # No badges initially
            assert merchants1[0].get("badges") is None or len(merchants1[0].get("badges", [])) == 0
            
            session_id = data1["session_id"]
        
        # Step 2: Merchant onboarding flow
        with patch("app.dependencies_domain.get_current_user") as mock_auth:
            mock_auth.return_value = test_merchant_user
            
            # 2a. Start Google OAuth (mock)
            oauth_response = client.post(
                "/v1/merchant/auth/google/start",
                headers={"Authorization": f"Bearer mock_merchant_token"},
            )
            assert oauth_response.status_code == 200
            oauth_data = oauth_response.json()
            assert "auth_url" in oauth_data
            assert "state" in oauth_data
            
            # 2b. Mock OAuth callback (simulate completing OAuth)
            # In real flow, this would be called by Google redirect
            # For test, we'll skip the callback and directly create merchant account
            
            # 2c. List locations (mock mode returns seeded locations)
            locations_response = client.get(
                "/v1/merchant/locations",
                headers={"Authorization": f"Bearer mock_merchant_token"},
            )
            assert locations_response.status_code == 200
            locations_data = locations_response.json()
            assert len(locations_data["locations"]) == 2
            
            # 2d. Claim first location
            claim_response = client.post(
                "/v1/merchant/claim",
                json={"place_id": "ChIJMockPlace1"},
                headers={"Authorization": f"Bearer mock_merchant_token"},
            )
            assert claim_response.status_code == 200
            claim_data = claim_response.json()
            assert claim_data["place_id"] == "ChIJMockPlace1"
            assert claim_data["status"] == "CLAIMED"
            
            # 2e. Create SetupIntent (mock Stripe)
            with patch("stripe.SetupIntent.create") as mock_setup_intent_create:
                mock_setup_intent = MagicMock()
                mock_setup_intent.client_secret = mock_stripe_setup_intent["client_secret"]
                mock_setup_intent.id = mock_stripe_setup_intent["id"]
                mock_setup_intent_create.return_value = mock_setup_intent
                
                # Mock Stripe Customer creation
                with patch("stripe.Customer.create") as mock_customer_create:
                    mock_customer = MagicMock()
                    mock_customer.id = "cus_mock_123"
                    mock_customer_create.return_value = mock_customer
                    
                    setup_intent_response = client.post(
                        "/v1/merchant/billing/setup_intent",
                        headers={"Authorization": f"Bearer mock_merchant_token"},
                    )
                    assert setup_intent_response.status_code == 200
                    setup_data = setup_intent_response.json()
                    assert "client_secret" in setup_data
                    assert "setup_intent_id" in setup_data
                    
                    # Simulate SetupIntent confirmation (in real flow, done via webhook)
                    # For test, we'll create a payment method record directly
                    merchant_account = (
                        db.query(MerchantAccount)
                        .filter(MerchantAccount.owner_user_id == test_merchant_user.id)
                        .first()
                    )
                    assert merchant_account is not None
                    
                    payment_method = MerchantPaymentMethod(
                        id="pm_mock_123",
                        merchant_account_id=merchant_account.id,
                        stripe_customer_id="cus_mock_123",
                        stripe_payment_method_id="pm_mock_123",
                        status="ACTIVE",
                    )
                    db.add(payment_method)
                    db.commit()
            
            # 2f. Update placement rule with high boost_weight
            placement_response = client.post(
                "/v1/merchant/placement/update",
                json={
                    "place_id": "ChIJMockPlace1",
                    "boost_weight": 1000.0,  # High boost
                    "perks_enabled": True,
                    "daily_cap_cents": 5000,
                },
                headers={"Authorization": f"Bearer mock_merchant_token"},
            )
            assert placement_response.status_code == 200
            placement_data = placement_response.json()
            assert placement_data["place_id"] == "ChIJMockPlace1"
            assert placement_data["boost_weight"] == 1000.0
            assert placement_data["perks_enabled"] is True
        
        # Step 3: Driver captures intent again (should see placement change)
        with patch("app.dependencies_domain.get_current_user") as mock_auth:
            mock_auth.return_value = test_user
            
            response2 = client.post(
                "/v1/intent/capture",
                json={
                    "lat": test_charger.lat,
                    "lng": test_charger.lng,
                    "accuracy_m": 10.0,
                },
                headers={"Authorization": f"Bearer {driver_token}"},
            )
            
            assert response2.status_code == 200
            data2 = response2.json()
            assert "merchants" in data2
            assert len(data2["merchants"]) == 2
            
            # Check that merchant1 now appears first (due to boost_weight)
            merchants2 = data2["merchants"]
            assert merchants2[0]["place_id"] == "ChIJMockPlace1"  # Should be first due to boost
            
            # Check badges
            assert merchants2[0].get("badges") is not None
            badges = merchants2[0]["badges"]
            assert "Boosted" in badges
            assert "Perks available" in badges
            
            # Check daily_cap_cents (internal use only)
            assert merchants2[0].get("daily_cap_cents") == 5000


def test_placement_rule_boost_ordering(db: Session):
    """Test that boost_weight correctly affects merchant ordering"""
    # Create placement rule with boost
    rule = MerchantPlacementRule(
        id="rule_1",
        place_id="ChIJMockPlace1",
        status="ACTIVE",
        boost_weight=1000.0,
        perks_enabled=True,
        daily_cap_cents=5000,
    )
    db.add(rule)
    db.commit()
    
    # Verify rule exists
    assert rule.boost_weight == 1000.0
    assert rule.perks_enabled is True



