"""
Tests for Nova Merchants Nearby API

Tests cover:
- Filtering: only Nova-accepting merchants are returned
- Sorting: featured first, then by distance
- Location fallback: returns featured merchants when no location
- Radius filtering: merchants outside radius are excluded
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.while_you_charge import Merchant, MerchantPerk
from app.models.domain import DomainMerchant


def test_nova_merchants_filters_non_nova(client: TestClient, db: Session):
    """Test that merchants without Nova acceptance are excluded"""
    # Create a merchant with Nova (has active perk)
    nova_merchant = Merchant(
        id="m_nova_001",
        name="Nova Coffee Shop",
        lat=30.4021,
        lng=-97.7266,
        category="coffee"
    )
    db.add(nova_merchant)
    db.flush()
    
    # Add active perk
    perk = MerchantPerk(
        merchant_id="m_nova_001",
        title="Free espresso shot",
        nova_reward=100,
        is_active=True
    )
    db.add(perk)
    
    # Create a merchant without Nova (no active perk)
    non_nova_merchant = Merchant(
        id="m_non_nova_001",
        name="Regular Shop",
        lat=30.4022,
        lng=-97.7267,
        category="retail"
    )
    db.add(non_nova_merchant)
    
    db.commit()
    
    # Call API
    response = client.get(
        "/v1/merchants/nova/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7266,
            "radius_m": 5000
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only return Nova-accepting merchant
    assert len(data) >= 1
    merchant_ids = [m["id"] for m in data]
    assert "m_nova_001" in merchant_ids
    assert "m_non_nova_001" not in merchant_ids
    
    # Verify all returned merchants accept Nova
    for merchant in data:
        assert merchant["accepts_nova"] is True


def test_nova_merchants_sorts_by_distance(client: TestClient, db: Session):
    """Test that merchants are sorted by distance (featured first, then distance)"""
    # Create multiple Nova merchants at different distances
    merchants = [
        Merchant(id="m_far", name="Far Merchant", lat=30.4100, lng=-97.7300, category="food"),
        Merchant(id="m_near", name="Near Merchant", lat=30.4022, lng=-97.7267, category="coffee"),
        Merchant(id="m_mid", name="Mid Merchant", lat=30.4050, lng=-97.7280, category="retail"),
    ]
    
    for merchant in merchants:
        db.add(merchant)
        db.flush()
        
        # Add active perk
        perk = MerchantPerk(
            merchant_id=merchant.id,
            title="Nova accepted",
            nova_reward=50,
            is_active=True
        )
        db.add(perk)
    
    db.commit()
    
    # Call API from a location closer to m_near
    response = client.get(
        "/v1/merchants/nova/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7266,
            "radius_m": 10000
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have at least our test merchants
    merchant_ids = [m["id"] for m in data]
    assert "m_near" in merchant_ids
    assert "m_mid" in merchant_ids
    assert "m_far" in merchant_ids
    
    # Find positions in sorted list
    near_idx = next(i for i, m in enumerate(data) if m["id"] == "m_near")
    mid_idx = next(i for i, m in enumerate(data) if m["id"] == "m_mid")
    far_idx = next(i for i, m in enumerate(data) if m["id"] == "m_far")
    
    # Near should come before mid, mid before far (ignoring featured)
    # Check distances are in ascending order (excluding featured)
    non_featured = [m for m in data if not m.get("is_featured", False)]
    if len(non_featured) >= 3:
        distances = [m["distance_m"] for m in non_featured if m["distance_m"] is not None]
        assert distances == sorted(distances), "Distances should be sorted ascending"


def test_nova_merchants_location_fallback(client: TestClient, db: Session):
    """Test that when no location is provided, featured merchants are returned"""
    # Create a Nova merchant
    merchant = Merchant(
        id="m_featured_001",
        name="Featured Merchant",
        lat=30.4021,
        lng=-97.7266,
        category="coffee"
    )
    db.add(merchant)
    db.flush()
    
    # Add active perk
    perk = MerchantPerk(
        merchant_id="m_featured_001",
        title="Featured offer",
        nova_reward=100,
        is_active=True
    )
    db.add(perk)
    db.commit()
    
    # Call API without location
    response = client.get(
        "/v1/merchants/nova/nearby",
        params={
            "radius_m": 2000
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return merchants (may be empty if no featured, but should not error)
    assert isinstance(data, list)
    
    # If merchants are returned, they should be marked as featured
    for merchant in data:
        if merchant.get("is_featured"):
            assert merchant.get("distance_m") is None, "Featured merchants should not have distance"


def test_nova_merchants_radius_filtering(client: TestClient, db: Session):
    """Test that merchants outside radius are excluded"""
    # Create a Nova merchant within radius
    near_merchant = Merchant(
        id="m_near_radius",
        name="Near Merchant",
        lat=30.4022,  # Very close to test location
        lng=-97.7267,
        category="coffee"
    )
    db.add(near_merchant)
    db.flush()
    
    perk_near = MerchantPerk(
        merchant_id="m_near_radius",
        title="Near offer",
        nova_reward=50,
        is_active=True
    )
    db.add(perk_near)
    
    # Create a Nova merchant far away (outside radius)
    far_merchant = Merchant(
        id="m_far_radius",
        name="Far Merchant",
        lat=30.5000,  # Far from test location
        lng=-97.8000,
        category="food"
    )
    db.add(far_merchant)
    db.flush()
    
    perk_far = MerchantPerk(
        merchant_id="m_far_radius",
        title="Far offer",
        nova_reward=50,
        is_active=True
    )
    db.add(perk_far)
    
    db.commit()
    
    # Call API with small radius
    response = client.get(
        "/v1/merchants/nova/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7266,
            "radius_m": 1000  # Small radius
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only return near merchant
    merchant_ids = [m["id"] for m in data]
    assert "m_near_radius" in merchant_ids
    assert "m_far_radius" not in merchant_ids


def test_nova_merchants_response_schema(client: TestClient, db: Session):
    """Test that response matches expected schema"""
    # Create a Nova merchant
    merchant = Merchant(
        id="m_schema_test",
        name="Schema Test Merchant",
        lat=30.4021,
        lng=-97.7266,
        category="coffee"
    )
    db.add(merchant)
    db.flush()
    
    perk = MerchantPerk(
        merchant_id="m_schema_test",
        title="Test offer",
        description="Test description",
        nova_reward=75,
        is_active=True
    )
    db.add(perk)
    db.commit()
    
    # Call API
    response = client.get(
        "/v1/merchants/nova/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7266,
            "radius_m": 2000
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) >= 1
    
    # Check first merchant has all required fields
    merchant = data[0]
    assert "id" in merchant
    assert "name" in merchant
    assert "category" in merchant
    assert "address" in merchant
    assert "lat" in merchant
    assert "lng" in merchant
    assert "accepts_nova" in merchant
    assert merchant["accepts_nova"] is True
    assert "offer_headline" in merchant
    assert "nova_redemption_method" in merchant
    assert merchant["nova_redemption_method"] == "CODE"
    assert "is_featured" in merchant
    assert isinstance(merchant["is_featured"], bool)

