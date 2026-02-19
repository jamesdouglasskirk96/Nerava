from datetime import datetime, timedelta

import pytest

from app.models.arrival_session import ArrivalSession
from app.models.merchant_notification_config import MerchantNotificationConfig
from app.models.while_you_charge import Merchant
from tests.helpers.ev_arrival_test_utils import ensure_ev_arrival_routers


@pytest.fixture(scope="session", autouse=True)
def _ensure_merchant_arrivals_routes():
    ensure_ev_arrival_routers()


@pytest.fixture
def merchant(db):
    merchant = Merchant(
        id="m_arrivals_1",
        name="Arrivals Merchant",
        lat=30.2672,
        lng=-97.7431,
        category="coffee",
    )
    db.add(merchant)
    db.commit()
    db.refresh(merchant)
    return merchant


def test_list_arrivals_returns_sessions(client, db, merchant):
    session = ArrivalSession(
        driver_id=1,
        merchant_id=merchant.id,
        arrival_type="ev_curbside",
        status="pending_order",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(session)
    db.commit()
    response = client.get(f"/v1/merchants/{merchant.id}/arrivals")
    assert response.status_code == 200
    data = response.json()
    assert data["sessions"]
    assert data["sessions"][0]["session_id"] == str(session.id)


def test_get_notification_config_defaults(client, merchant):
    response = client.get(f"/v1/merchants/{merchant.id}/notification-config")
    assert response.status_code == 200
    data = response.json()
    assert data["notify_sms"] is True
    assert data["notify_email"] is False


def test_put_notification_config_creates_config(client, db, merchant):
    response = client.put(
        f"/v1/merchants/{merchant.id}/notification-config",
        json={"sms_phone": "+15125551234", "notify_sms": True, "notify_email": False},
    )
    assert response.status_code == 200
    config = db.query(MerchantNotificationConfig).filter(
        MerchantNotificationConfig.merchant_id == merchant.id
    ).first()
    assert config is not None
    assert config.sms_phone == "+15125551234"


def test_put_notification_config_updates_existing(client, db, merchant):
    client.put(
        f"/v1/merchants/{merchant.id}/notification-config",
        json={"sms_phone": "+15125551234", "notify_sms": True, "notify_email": False},
    )
    response = client.put(
        f"/v1/merchants/{merchant.id}/notification-config",
        json={"sms_phone": "+15125559876", "notify_sms": False, "notify_email": True},
    )
    assert response.status_code == 200
    config = db.query(MerchantNotificationConfig).filter(
        MerchantNotificationConfig.merchant_id == merchant.id
    ).first()
    assert config.sms_phone == "+15125559876"
    assert config.notify_sms is False
    assert config.notify_email is True


def test_notification_config_persists_across_requests(client, merchant):
    client.put(
        f"/v1/merchants/{merchant.id}/notification-config",
        json={"sms_phone": "+15125551234", "notify_sms": True, "notify_email": False},
    )
    response = client.get(f"/v1/merchants/{merchant.id}/notification-config")
    assert response.status_code == 200
    data = response.json()
    assert data["sms_phone"] == "+15125551234"
