"""
Tests for primary merchant override functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.while_you_charge import Charger, Merchant, ChargerMerchant
from app.db import SessionLocal


@pytest.fixture
def test_charger(db: Session):
    """Create a test charger"""
    charger = Charger(
        id="test_charger_1",
        name="Test Charger",
        network_name="Tesla",
        lat=30.2680,
        lng=-97.7435,
        address="500 W Canyon Ridge Dr, Austin, TX 78753",
        city="Austin",
        state="TX",
        zip_code="78753",
        status="available",
        is_public=True,
    )
    db.add(charger)
    db.commit()
    db.refresh(charger)
    return charger


@pytest.fixture
def test_merchant(db: Session):
    """Create a test merchant"""
    merchant = Merchant(
        id="test_merchant_1",
        name="Test Merchant",
        lat=30.2680,
        lng=-97.7435,
        address="501 W Canyon Ridge Dr, Austin, TX 78753",
        city="Austin",
        state="TX",
        category="restaurant",
        primary_category="food",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@pytest.fixture
def test_primary_override(db: Session, test_charger, test_merchant):
    """Create a primary merchant override"""
    override = ChargerMerchant(
        charger_id=test_charger.id,
        merchant_id=test_merchant.id,
        distance_m=100.0,
        walk_duration_s=120,
        is_primary=True,
        override_mode="PRE_CHARGE_ONLY",
        suppress_others=True,
        exclusive_title="Free Margarita",
        exclusive_description="Free Margarita (Charging Exclusive)",
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


def test_primary_override_pre_charge(client: TestClient, test_user, test_charger, test_merchant, test_primary_override):
    """Test that pre-charge state returns only primary merchant"""
    response = client.get(
        f"/v1/drivers/merchants/open?charger_id={test_charger.id}&state=pre-charge",
        headers={"Authorization": f"Bearer {test_user.access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == test_merchant.id
    assert data[0]["is_primary"] is True
    assert data[0]["exclusive_title"] == "Free Margarita"
    assert data[0]["exclusive_description"] == "Free Margarita (Charging Exclusive)"


def test_primary_override_charging(client: TestClient, test_user, test_charger, test_merchant, test_primary_override, db: Session):
    """Test that charging state returns primary first, then secondary merchants"""
    # Create a secondary merchant
    secondary_merchant = Merchant(
        id="test_merchant_2",
        name="Secondary Merchant",
        lat=30.2690,
        lng=-97.7440,
        address="502 W Canyon Ridge Dr, Austin, TX 78753",
        city="Austin",
        state="TX",
        category="cafe",
        primary_category="coffee",
    )
    db.add(secondary_merchant)
    
    # Link secondary merchant to charger
    secondary_link = ChargerMerchant(
        charger_id=test_charger.id,
        merchant_id=secondary_merchant.id,
        distance_m=200.0,
        walk_duration_s=240,
        is_primary=False,
    )
    db.add(secondary_link)
    db.commit()
    
    response = client.get(
        f"/v1/drivers/merchants/open?charger_id={test_charger.id}&state=charging",
        headers={"Authorization": f"Bearer {test_user.access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Primary should be first
    assert data[0]["id"] == test_merchant.id
    assert data[0]["is_primary"] is True


def test_no_primary_override(client: TestClient, test_user, test_charger, test_merchant, db: Session):
    """Test that without primary override, normal merchant search applies"""
    # Create a non-primary link
    link = ChargerMerchant(
        charger_id=test_charger.id,
        merchant_id=test_merchant.id,
        distance_m=100.0,
        walk_duration_s=120,
        is_primary=False,
    )
    db.add(link)
    db.commit()
    
    response = client.get(
        f"/v1/drivers/merchants/open?charger_id={test_charger.id}&state=pre-charge",
        headers={"Authorization": f"Bearer {test_user.access_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should return merchants (may be empty if no matches)
    for merchant in data:
        assert merchant.get("is_primary") is False or merchant.get("is_primary") is None



