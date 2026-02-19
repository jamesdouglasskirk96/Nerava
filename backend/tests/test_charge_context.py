import pytest

from app.models import User
from app.models.arrival_session import ArrivalSession
from app.models.verified_visit import VerifiedVisit
from app.models.while_you_charge import Charger, Merchant, ChargerMerchant
from tests.helpers.ev_arrival_test_utils import ensure_ev_arrival_routers


@pytest.fixture(scope="session", autouse=True)
def _ensure_charge_context_routes():
    ensure_ev_arrival_routers()


@pytest.fixture
def charger(db):
    charger = Charger(
        id="ch_ctx_1",
        name="Context Charger",
        lat=30.2672,
        lng=-97.7431,
        is_public=True,
        network_name="Test Network",
    )
    db.add(charger)
    db.commit()
    db.refresh(charger)
    return charger


@pytest.fixture
def merchants(db, charger):
    merchant_close = Merchant(
        id="m_ctx_close",
        name="Close Coffee",
        lat=30.2676,
        lng=-97.7431,
        category="coffee",
        primary_category="coffee",
    )
    merchant_far = Merchant(
        id="m_ctx_far",
        name="Far Diner",
        lat=30.2702,
        lng=-97.7431,
        category="restaurant",
        primary_category="restaurant",
    )
    db.add_all([merchant_close, merchant_far])
    db.commit()

    db.add_all([
        ChargerMerchant(
            charger_id=charger.id,
            merchant_id=merchant_close.id,
            distance_m=50,
            walk_duration_s=240,
        ),
        ChargerMerchant(
            charger_id=charger.id,
            merchant_id=merchant_far.id,
            distance_m=350,
            walk_duration_s=600,
        ),
    ])
    db.commit()
    return merchant_close, merchant_far


def test_charge_context_returns_merchants(client, charger, merchants):
    response = client.get(
        "/v1/charge-context/nearby",
        params={"lat": charger.lat, "lng": charger.lng},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["merchants"]


def test_charge_context_includes_charger_info(client, charger, merchants):
    response = client.get(
        "/v1/charge-context/nearby",
        params={"lat": charger.lat, "lng": charger.lng},
    )
    data = response.json()
    assert data["charger"]["charger_id"] == charger.id


def test_charge_context_includes_merchant_fields(client, charger, merchants):
    response = client.get(
        "/v1/charge-context/nearby",
        params={"lat": charger.lat, "lng": charger.lng},
    )
    merchant = response.json()["merchants"][0]
    assert "merchant_id" in merchant
    assert "name" in merchant
    assert "walk_minutes" in merchant
    assert "distance_m" in merchant


def test_charge_context_category_filter(client, charger, merchants):
    response = client.get(
        "/v1/charge-context/nearby",
        params={"lat": charger.lat, "lng": charger.lng, "category": "coffee"},
    )
    data = response.json()
    assert len(data["merchants"]) == 1
    assert data["merchants"][0]["merchant_id"] == "m_ctx_close"


def test_charge_context_merchants_sorted_by_distance(client, charger, merchants):
    response = client.get(
        "/v1/charge-context/nearby",
        params={"lat": charger.lat, "lng": charger.lng},
    )
    data = response.json()
    assert data["merchants"][0]["merchant_id"] == "m_ctx_close"
    assert data["merchants"][1]["merchant_id"] == "m_ctx_far"


def test_charge_context_includes_active_arrival_count(client, db, charger, merchants):
    merchant_close, _ = merchants
    driver = User(email="driver@ctx.test", is_active=True, role_flags="driver")
    db.add(driver)
    db.commit()
    db.refresh(driver)
    session = ArrivalSession(
        driver_id=driver.id,
        merchant_id=merchant_close.id,
        arrival_type="ev_curbside",
        status="pending_order",
        created_at=charger.created_at,
        expires_at=charger.created_at,
    )
    db.add(session)
    db.commit()
    response = client.get(
        "/v1/charge-context/nearby",
        params={"lat": charger.lat, "lng": charger.lng},
    )
    merchant = response.json()["merchants"][0]
    assert merchant["active_arrival_count"] == 1


def test_charge_context_includes_verified_visit_count(client, db, charger, merchants):
    merchant_close, _ = merchants
    visit = VerifiedVisit(
        verification_code="ATX-CLOSE-001",
        region_code="ATX",
        merchant_code="CLOSE",
        visit_number=1,
        merchant_id=merchant_close.id,
        driver_id=1,
    )
    db.add(visit)
    db.commit()
    response = client.get(
        "/v1/charge-context/nearby",
        params={"lat": charger.lat, "lng": charger.lng},
    )
    merchant = response.json()["merchants"][0]
    assert merchant["verified_visit_count"] == 1
