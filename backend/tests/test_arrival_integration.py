from datetime import datetime, timedelta

import pytest

from app.main_simple import app
from app.dependencies.driver import get_current_driver
from app.models.arrival_session import ArrivalSession
from app.models.billing_event import BillingEvent
from app.models.merchant_notification_config import MerchantNotificationConfig
from app.models.while_you_charge import Charger, Merchant
from tests.helpers.ev_arrival_test_utils import ensure_ev_arrival_routers


@pytest.fixture(scope="session", autouse=True)
def _ensure_ev_arrival_routes():
    ensure_ev_arrival_routers()


@pytest.fixture
def driver_user(db):
    user = User(
        email="driver@test.com",
        is_active=True,
        role_flags="driver",
        auth_provider="local",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def merchant(db):
    merchant = Merchant(
        id="m_test_1",
        name="Test Merchant",
        lat=30.2672,
        lng=-97.7431,
        category="coffee",
        ordering_url="https://order.example.com",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


@pytest.fixture
def charger(db):
    charger = Charger(
        id="ch_test_1",
        name="Test Charger",
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
def notif_config(db, merchant):
    config = MerchantNotificationConfig(
        merchant_id=merchant.id,
        notify_sms=False,
        notify_email=False,
        pos_integration="none",
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@pytest.fixture
def driver_override(driver_user):
    app.dependency_overrides[get_current_driver] = lambda: driver_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_driver, None)


def _create_arrival(client, merchant_id, charger_id=None, idempotency_key=None):
    payload = {
        "merchant_id": merchant_id,
        "arrival_type": "ev_curbside",
        "lat": 30.2672,
        "lng": -97.7431,
    }
    if charger_id:
        payload["charger_id"] = charger_id
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key
    return client.post("/v1/arrival/create", json=payload)


def test_create_arrival_valid_returns_session(client, db, merchant, charger, driver_override):
    response = _create_arrival(client, merchant.id, charger.id)
    assert response.status_code == 201
    data = response.json()
    assert data["session_id"]
    assert data["status"] == "pending_order"


def test_create_arrival_idempotent(client, db, merchant, charger, driver_override):
    response1 = _create_arrival(client, merchant.id, charger.id, idempotency_key="idem-1")
    response2 = _create_arrival(client, merchant.id, charger.id, idempotency_key="idem-1")
    assert response1.status_code == 201
    assert response2.status_code == 201
    assert response1.json()["session_id"] == response2.json()["session_id"]


def test_create_arrival_when_active_exists_returns_409(client, db, merchant, charger, driver_override):
    response1 = _create_arrival(client, merchant.id, charger.id)
    assert response1.status_code == 201
    response2 = _create_arrival(client, merchant.id, charger.id)
    assert response2.status_code == 409
    assert response2.json()["detail"]["error"] == "ACTIVE_SESSION_EXISTS"


def test_create_arrival_invalid_type_returns_422(client, db, merchant, charger, driver_override):
    response = client.post(
        "/v1/arrival/create",
        json={
            "merchant_id": merchant.id,
            "charger_id": charger.id,
            "arrival_type": "ev_drive_thru",
            "lat": 30.2672,
            "lng": -97.7431,
        },
    )
    assert response.status_code == 422


def test_bind_order_transitions_to_awaiting_arrival(
    client, db, merchant, charger, notif_config, driver_override
):
    create = _create_arrival(client, merchant.id, charger.id)
    session_id = create.json()["session_id"]
    response = client.put(
        f"/v1/arrival/{session_id}/order",
        json={"order_number": "1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "awaiting_arrival"
    assert data["order_number"] == "1234"
    assert data["order_source"] == "manual"
    assert data["order_status"] == "unknown"


def test_bind_order_with_estimated_total_stores_driver_estimate(
    client, db, merchant, charger, notif_config, driver_override
):
    create = _create_arrival(client, merchant.id, charger.id)
    session_id = create.json()["session_id"]
    response = client.put(
        f"/v1/arrival/{session_id}/order",
        json={"order_number": "1234", "estimated_total_cents": 2500},
    )
    assert response.status_code == 200
    session = db.query(ArrivalSession).filter(ArrivalSession.id == session_id).first()
    assert session.driver_estimate_cents == 2500


def test_confirm_arrival_requires_charger_id(client, db, merchant, charger, driver_override):
    create = _create_arrival(client, merchant.id)
    session_id = create.json()["session_id"]
    response = client.post(
        f"/v1/arrival/{session_id}/confirm-arrival",
        json={"lat": 30.2672, "lng": -97.7431},
    )
    assert response.status_code == 422


def test_confirm_arrival_too_far_returns_400(client, db, merchant, charger, driver_override):
    create = _create_arrival(client, merchant.id)
    session_id = create.json()["session_id"]
    response = client.post(
        f"/v1/arrival/{session_id}/confirm-arrival",
        json={
            "charger_id": charger.id,
            "lat": 30.2772,
            "lng": -97.7431,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "TOO_FAR_FROM_CHARGER"


def test_confirm_arrival_success_returns_status(client, db, merchant, charger, driver_override):
    create = _create_arrival(client, merchant.id)
    session_id = create.json()["session_id"]
    response = client.post(
        f"/v1/arrival/{session_id}/confirm-arrival",
        json={
            "charger_id": charger.id,
            "lat": charger.lat,
            "lng": charger.lng,
            "accuracy_m": 10.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("arrived", "merchant_notified")


def test_merchant_confirm_creates_billing_event_when_total_available(
    client, db, merchant, charger, driver_override
):
    create = _create_arrival(client, merchant.id)
    session_id = create.json()["session_id"]
    client.put(
        f"/v1/arrival/{session_id}/order",
        json={"order_number": "1234", "estimated_total_cents": 3000},
    )
    client.post(
        f"/v1/arrival/{session_id}/confirm-arrival",
        json={"charger_id": charger.id, "lat": charger.lat, "lng": charger.lng},
    )
    response = client.post(f"/v1/arrival/{session_id}/merchant-confirm", json={})
    assert response.status_code == 200
    session = db.query(ArrivalSession).filter(ArrivalSession.id == session_id).first()
    assert session.status == "completed"
    billing = db.query(BillingEvent).filter(BillingEvent.arrival_session_id == session.id).first()
    assert billing is not None


def test_merchant_confirm_without_total_marks_unbillable(
    client, db, merchant, charger, driver_override
):
    create = _create_arrival(client, merchant.id)
    session_id = create.json()["session_id"]
    client.post(
        f"/v1/arrival/{session_id}/confirm-arrival",
        json={"charger_id": charger.id, "lat": charger.lat, "lng": charger.lng},
    )
    response = client.post(f"/v1/arrival/{session_id}/merchant-confirm", json={})
    assert response.status_code == 200
    session = db.query(ArrivalSession).filter(ArrivalSession.id == session_id).first()
    assert session.status == "completed_unbillable"
    billing = db.query(BillingEvent).filter(BillingEvent.arrival_session_id == session.id).first()
    assert billing is None


def test_merchant_confirm_with_reported_total_uses_that_total(
    client, db, merchant, charger, driver_override
):
    create = _create_arrival(client, merchant.id)
    session_id = create.json()["session_id"]
    client.post(
        f"/v1/arrival/{session_id}/confirm-arrival",
        json={"charger_id": charger.id, "lat": charger.lat, "lng": charger.lng},
    )
    response = client.post(
        f"/v1/arrival/{session_id}/merchant-confirm",
        json={"merchant_reported_total_cents": 4200},
    )
    assert response.status_code == 200
    session = db.query(ArrivalSession).filter(ArrivalSession.id == session_id).first()
    assert session.order_total_cents == 4200
    billing = db.query(BillingEvent).filter(BillingEvent.arrival_session_id == session.id).first()
    assert billing.order_total_cents == 4200


def test_feedback_up_is_stored(client, db, merchant, charger, driver_override):
    create = _create_arrival(client, merchant.id)
    session_id = create.json()["session_id"]
    client.post(
        f"/v1/arrival/{session_id}/confirm-arrival",
        json={"charger_id": charger.id, "lat": charger.lat, "lng": charger.lng},
    )
    client.post(f"/v1/arrival/{session_id}/merchant-confirm", json={})
    response = client.post(
        f"/v1/arrival/{session_id}/feedback",
        json={"rating": "up", "comment": "Great"},
    )
    assert response.status_code == 200
    session = db.query(ArrivalSession).filter(ArrivalSession.id == session_id).first()
    assert session.feedback_rating == "up"
    assert session.feedback_comment == "Great"


def test_feedback_down_with_reason_is_stored(client, db, merchant, charger, driver_override):
    create = _create_arrival(client, merchant.id)
    session_id = create.json()["session_id"]
    client.post(
        f"/v1/arrival/{session_id}/confirm-arrival",
        json={"charger_id": charger.id, "lat": charger.lat, "lng": charger.lng},
    )
    client.post(f"/v1/arrival/{session_id}/merchant-confirm", json={})
    response = client.post(
        f"/v1/arrival/{session_id}/feedback",
        json={"rating": "down", "reason": "slow_service"},
    )
    assert response.status_code == 200
    session = db.query(ArrivalSession).filter(ArrivalSession.id == session_id).first()
    assert session.feedback_rating == "down"
    assert session.feedback_reason == "slow_service"


def test_feedback_invalid_rating_returns_422(client, db, merchant, charger, driver_override):
    create = _create_arrival(client, merchant.id)
    session_id = create.json()["session_id"]
    client.post(
        f"/v1/arrival/{session_id}/confirm-arrival",
        json={"charger_id": charger.id, "lat": charger.lat, "lng": charger.lng},
    )
    client.post(f"/v1/arrival/{session_id}/merchant-confirm", json={})
    response = client.post(
        f"/v1/arrival/{session_id}/feedback",
        json={"rating": "sideways"},
    )
    assert response.status_code == 422


def test_get_active_returns_current_session(client, db, merchant, charger, driver_override):
    create = _create_arrival(client, merchant.id, charger.id)
    session_id = create.json()["session_id"]
    response = client.get("/v1/arrival/active")
    assert response.status_code == 200
    data = response.json()
    assert data["session"]["session_id"] == session_id


def test_get_active_expires_session_and_returns_null(
    client, db, merchant, driver_user, driver_override
):
    expired_session = ArrivalSession(
        driver_id=driver_user.id,
        merchant_id=merchant.id,
        arrival_type="ev_curbside",
        status="pending_order",
        created_at=datetime.utcnow() - timedelta(hours=3),
        expires_at=datetime.utcnow() - timedelta(minutes=1),
    )
    db.add(expired_session)
    db.commit()
    response = client.get("/v1/arrival/active")
    assert response.status_code == 200
    assert response.json()["session"] is None
    session = db.query(ArrivalSession).filter(ArrivalSession.id == expired_session.id).first()
    assert session.status == "expired"


def test_cancel_sets_status_canceled(client, db, merchant, charger, driver_override):
    create = _create_arrival(client, merchant.id, charger.id)
    session_id = create.json()["session_id"]
    response = client.post(f"/v1/arrival/{session_id}/cancel")
    assert response.status_code == 200
    session = db.query(ArrivalSession).filter(ArrivalSession.id == session_id).first()
    assert session.status == "canceled"


def test_cancel_on_already_canceled_returns_400(
    client, db, merchant, driver_user, driver_override
):
    session = ArrivalSession(
        driver_id=driver_user.id,
        merchant_id=merchant.id,
        arrival_type="ev_curbside",
        status="canceled",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(session)
    db.commit()
    response = client.post(f"/v1/arrival/{session.id}/cancel")
    assert response.status_code == 400
