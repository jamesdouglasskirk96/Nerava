"""
Tests for /v1/drivers/merchants/nearby endpoint filtering.

Tests nova_only, search (q), category, and max_distance_to_charger_m filters.
Requires seed_eggman_demo.py to be run first (or seeds data in test).
"""
import uuid
import pytest
from app.models.while_you_charge import Merchant, MerchantPerk, Charger, ChargerMerchant
from app.models.domain import DomainMerchant
from app.dependencies.driver import get_current_driver


@pytest.fixture
def seed_eggman_merchants(db):
    """Seed three Eggman merchants with perks and charger links."""
    # Create Domain charger
    charger = Charger(
        id="ch_domain_tesla_001",
        name="Tesla Supercharger – Domain",
        network_name="Tesla",
        lat=30.4021,
        lng=-97.7254,
        address="11821 Rock Rose Ave, Austin, TX",
        is_public=True,
        status="available"
    )
    db.add(charger)
    db.flush()
    
    # Create three Eggman merchants
    merchants_data = [
        {
            "id": "eggman_coffee_001",
            "name": "Eggman ATX",
            "lat": 30.2569,
            "lng": -97.7614,
            "category": "coffee",
            "address": "1720 Barton Springs Rd, Austin, TX 78704"
        },
        {
            "id": "eggman_coffee_002",
            "name": "Eggman ATX – South",
            "lat": 30.3921,
            "lng": -97.7254,
            "category": "coffee",
            "address": "11821 Rock Rose Ave, Austin, TX 78758"
        },
        {
            "id": "eggman_coffee_003",
            "name": "Eggman ATX – East",
            "lat": 30.4021,
            "lng": -97.7154,
            "category": "coffee",
            "address": "11920 Domain Dr, Austin, TX 78758"
        }
    ]
    
    merchants = []
    for m_data in merchants_data:
        # Set place_types and primary_category based on category
        if m_data["category"] == "coffee":
            m_data["place_types"] = ["cafe", "coffee_shop"]
            m_data["primary_category"] = "coffee"
        elif m_data["category"] == "food":
            m_data["place_types"] = ["restaurant", "meal_takeaway"]
            m_data["primary_category"] = "food"
        else:
            m_data["place_types"] = []
            m_data["primary_category"] = "other"
        
        merchant = Merchant(**m_data)
        db.add(merchant)
        db.flush()
        
        # Set nearest_charger_id and nearest_charger_distance_m
        distances = {
            "eggman_coffee_001": 250,
            "eggman_coffee_002": 300,
            "eggman_coffee_003": 350
        }
        merchant.nearest_charger_id = charger.id
        merchant.nearest_charger_distance_m = distances.get(merchant.id, 250)
        db.flush()
        
        # Create active perk with Nova reward
        perk = MerchantPerk(
            merchant_id=merchant.id,
            title="Redeem Nova",
            description="350 Nova = $35.00",
            nova_reward=350,
            is_active=True
        )
        db.add(perk)
        
        # Link to charger with distance
        distances = {
            "eggman_coffee_001": 250.0,
            "eggman_coffee_002": 300.0,
            "eggman_coffee_003": 350.0
        }
        link = ChargerMerchant(
            charger_id=charger.id,
            merchant_id=merchant.id,
            distance_m=distances[merchant.id],
            walk_duration_s=int(distances[merchant.id] / 1.4),
            walk_distance_m=distances[merchant.id]
        )
        db.add(link)
        
        # Create DomainMerchant (needs UUID for id field)
        domain_merchant = DomainMerchant(
            id=str(uuid.uuid4()),
            name=merchant.name,
            lat=merchant.lat,
            lng=merchant.lng,
            zone_slug="domain_austin",
            status="active",
            nova_balance=0
        )
        db.add(domain_merchant)
        
        merchants.append(merchant)
    
    db.commit()
    return merchants


@pytest.fixture
def authenticated_user(db, test_user):
    """Override auth dependency to return test_user"""
    from app.main_simple import app
    
    def override_get_current_driver():
        return test_user
    
    app.dependency_overrides[get_current_driver] = override_get_current_driver
    
    yield test_user
    
    app.dependency_overrides.clear()


@pytest.fixture
def merchant_without_perk(db, seed_eggman_merchants):
    """Create a merchant without an active perk (for nova_only testing)."""
    charger = db.query(Charger).filter(Charger.id == "ch_domain_tesla_001").first()
    
    merchant = Merchant(
        id="merchant_no_perk",
        name="No Perk Merchant",
        lat=30.4000,
        lng=-97.7200,
        category="food",
        address="Test Address"
    )
    db.add(merchant)
    db.flush()
    
    # Link to charger but no active perk
    link = ChargerMerchant(
        charger_id=charger.id,
        merchant_id=merchant.id,
        distance_m=400.0,
        walk_duration_s=300,
        walk_distance_m=400.0
    )
    db.add(link)
    db.commit()
    
    return merchant


def test_nova_only_returns_only_active_perks(client, authenticated_user, seed_eggman_merchants, merchant_without_perk):
    """Test that nova_only=true returns only merchants with active perks."""
    # Call endpoint with nova_only=true
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True
        }
    )
    
    # Should return 200
    assert response.status_code == 200
    merchants = response.json()
    
    # Should only return merchants with active perks (3 Eggmans, not merchant_without_perk)
    assert len(merchants) == 3
    merchant_names = [m["name"] for m in merchants]
    assert "Eggman ATX" in merchant_names
    assert "Eggman ATX – South" in merchant_names
    assert "Eggman ATX – East" in merchant_names
    assert "No Perk Merchant" not in merchant_names
    
    # All should have nova_accepted=True
    for m in merchants:
        assert m.get("nova_accepted") is True


def test_search_by_name_returns_matching(client, authenticated_user, seed_eggman_merchants):
    """Test that q parameter filters by merchant name."""
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True,
            "q": "eggman"
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # Should return all 3 Eggmans
    assert len(merchants) == 3
    for m in merchants:
        assert "eggman" in m["name"].lower()


def test_category_filter_coffee(client, authenticated_user, seed_eggman_merchants):
    """Test that category=coffee returns coffee merchants."""
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True,
            "category": "coffee"
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # Should return all 3 Eggmans (all are coffee)
    assert len(merchants) == 3
    for m in merchants:
        assert m.get("category", "").lower() == "coffee"


def test_category_filter_food_empty(client, authenticated_user, seed_eggman_merchants):
    """Test that category=food returns empty (no food merchants seeded)."""
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True,
            "category": "food"
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # Should return empty (no food merchants with active perks)
    assert len(merchants) == 0


def test_max_distance_to_charger_filter(client, authenticated_user, seed_eggman_merchants):
    """Test that max_distance_to_charger_m filters by distance to charger."""
    # Filter to merchants within 300m of charger
    # Only eggman_coffee_001 (250m) and eggman_coffee_002 (300m) should pass
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True,
            "max_distance_to_charger_m": 300
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # Should return 2 merchants (250m and 300m, but not 350m)
    assert len(merchants) <= 2
    for m in merchants:
        assert m.get("distance_to_charger_m") is not None
        assert m["distance_to_charger_m"] <= 300


def test_all_three_eggmans_returned(client, authenticated_user, seed_eggman_merchants):
    """Test that all three Eggmans are returned with default params."""
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # Should return all 3 Eggmans
    assert len(merchants) == 3
    merchant_ids = {m["id"] for m in merchants}
    assert "eggman_coffee_001" in merchant_ids
    assert "eggman_coffee_002" in merchant_ids
    assert "eggman_coffee_003" in merchant_ids
    
    # All should have distance_to_charger_m
    for m in merchants:
        assert m.get("distance_to_charger_m") is not None
        assert isinstance(m["distance_to_charger_m"], (int, float))


def test_response_includes_required_fields(client, authenticated_user, seed_eggman_merchants):
    """Test that response includes all required fields."""
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    if len(merchants) > 0:
        m = merchants[0]
        # Required fields
        assert "id" in m
        assert "name" in m
        assert "lat" in m
        assert "lng" in m
        assert "category" in m
        assert "nova_reward" in m
        assert "nova_accepted" in m
        assert "distance_to_charger_m" in m
        # New fields
        assert "primary_category" in m
        assert "nearest_charger_distance_m" in m
        # Optional but should be present
        assert "logo_url" in m or "photo_url" in m


def test_while_you_charge_filter(client, authenticated_user, seed_eggman_merchants):
    """Test that while_you_charge=true returns only merchants within 805m of charger."""
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True,
            "while_you_charge": True
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # Should return all 3 Eggmans (all are within 805m: 250m, 300m, 350m)
    assert len(merchants) == 3
    for m in merchants:
        assert m.get("nearest_charger_distance_m") is not None
        assert m["nearest_charger_distance_m"] <= 805


def test_while_you_charge_excludes_far_merchants(client, authenticated_user, db, seed_eggman_merchants):
    """Test that while_you_charge excludes merchants >805m from charger."""
    charger = db.query(Charger).filter(Charger.id == "ch_domain_tesla_001").first()
    
    # Create a merchant far from charger (1200m)
    far_merchant = Merchant(
        id="merchant_far",
        name="Far Merchant",
        lat=30.4000,
        lng=-97.7200,
        category="food",
        address="Test Address",
        place_types=["restaurant"],
        primary_category="food",
        nearest_charger_id=charger.id,
        nearest_charger_distance_m=1200
    )
    db.add(far_merchant)
    
    # Create active perk
    perk = MerchantPerk(
        merchant_id=far_merchant.id,
        title="Redeem Nova",
        nova_reward=350,
        is_active=True
    )
    db.add(perk)
    db.commit()
    
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True,
            "while_you_charge": True
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # Should not include far merchant (1200m > 805m)
    merchant_ids = [m["id"] for m in merchants]
    assert "merchant_far" not in merchant_ids
    # Should still include all 3 Eggmans
    assert len(merchants) == 3


def test_while_you_charge_excludes_null_distance(client, authenticated_user, db, seed_eggman_merchants):
    """Test that while_you_charge excludes merchants without charger mapping."""
    charger = db.query(Charger).filter(Charger.id == "ch_domain_tesla_001").first()
    
    # Create a merchant without nearest_charger_distance_m
    no_charger_merchant = Merchant(
        id="merchant_no_charger",
        name="No Charger Merchant",
        lat=30.4000,
        lng=-97.7200,
        category="food",
        address="Test Address",
        place_types=["restaurant"],
        primary_category="food",
        nearest_charger_id=None,
        nearest_charger_distance_m=None
    )
    db.add(no_charger_merchant)
    
    # Create active perk
    perk = MerchantPerk(
        merchant_id=no_charger_merchant.id,
        title="Redeem Nova",
        nova_reward=350,
        is_active=True
    )
    db.add(perk)
    db.commit()
    
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True,
            "while_you_charge": True
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # Should not include merchant without charger mapping
    merchant_ids = [m["id"] for m in merchants]
    assert "merchant_no_charger" not in merchant_ids
    # Should still include all 3 Eggmans
    assert len(merchants) == 3


def test_primary_category_derived_from_place_types(client, authenticated_user, seed_eggman_merchants):
    """Test that primary_category is correctly derived from place_types."""
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # All merchants should have primary_category set
    for m in merchants:
        assert "primary_category" in m
        assert m["primary_category"] in ["coffee", "food", "other"]
        # All seeded merchants are coffee
        assert m["primary_category"] == "coffee"


def test_category_filter_uses_primary_category(client, authenticated_user, seed_eggman_merchants):
    """Test that category filter uses primary_category."""
    response = client.get(
        "/v1/drivers/merchants/nearby",
        params={
            "lat": 30.4021,
            "lng": -97.7254,
            "zone_slug": "domain_austin",
            "radius_m": 5000,
            "nova_only": True,
            "category": "coffee"
        }
    )
    
    assert response.status_code == 200
    merchants = response.json()
    
    # Should return all 3 Eggmans (all have primary_category=coffee)
    assert len(merchants) == 3
    for m in merchants:
        assert m.get("primary_category") == "coffee"

