from datetime import datetime

import pytest

from app.main_simple import app
from app.dependencies.driver import get_current_driver
from app.models import User
from tests.helpers.ev_arrival_test_utils import ensure_ev_arrival_routers


@pytest.fixture(scope="session", autouse=True)
def _ensure_vehicle_routes():
    ensure_ev_arrival_routers()


@pytest.fixture
def driver_user(db):
    user = User(
        email="vehicle@test.com",
        is_active=True,
        role_flags="driver",
        auth_provider="local",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def driver_override(driver_user):
    app.dependency_overrides[get_current_driver] = lambda: driver_user
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_current_driver, None)


def test_put_vehicle_sets_fields(client, db, driver_user, driver_override):
    response = client.put(
        "/v1/account/vehicle",
        json={"color": "Blue", "model": "Tesla Model 3"},
    )
    assert response.status_code == 200
    db.refresh(driver_user)
    assert driver_user.vehicle_color == "Blue"
    assert driver_user.vehicle_model == "Tesla Model 3"
    assert isinstance(driver_user.vehicle_set_at, datetime)


def test_get_vehicle_returns_saved_vehicle(client, driver_user, driver_override):
    client.put(
        "/v1/account/vehicle",
        json={"color": "Red", "model": "Rivian R1S"},
    )
    response = client.get("/v1/account/vehicle")
    assert response.status_code == 200
    data = response.json()
    assert data["color"] == "Red"
    assert data["model"] == "Rivian R1S"


def test_get_vehicle_with_no_vehicle_returns_404(client, driver_user, driver_override):
    response = client.get("/v1/account/vehicle")
    assert response.status_code == 404


def test_put_vehicle_updates_existing(client, db, driver_user, driver_override):
    client.put(
        "/v1/account/vehicle",
        json={"color": "White", "model": "Model Y"},
    )
    response = client.put(
        "/v1/account/vehicle",
        json={"color": "Black", "model": "Model X"},
    )
    assert response.status_code == 200
    db.refresh(driver_user)
    assert driver_user.vehicle_color == "Black"
    assert driver_user.vehicle_model == "Model X"
