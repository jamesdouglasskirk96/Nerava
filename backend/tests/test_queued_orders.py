"""
Tests for the Queued Orders feature (Phase 0).

Status flow:
  QUEUED → RELEASED (on arrival confirmation)
  QUEUED → CANCELED (if session canceled)
  QUEUED → EXPIRED (if session expires)
"""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db import get_db
from app.models import User, Merchant, Charger, ChargerMerchant
from app.models.arrival_session import ArrivalSession
from app.models.queued_order import QueuedOrder, QueuedOrderStatus


# ─── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def test_db(test_client):
    """Get test database session."""
    return next(get_db())


@pytest.fixture
def test_driver(test_db: Session):
    """Create a test driver user."""
    driver = User(
        phone="+15551234567",
        phone_verified=True,
        vehicle_color="Red",
        vehicle_model="Tesla Model 3",
    )
    test_db.add(driver)
    test_db.commit()
    test_db.refresh(driver)
    yield driver
    # Cleanup
    test_db.delete(driver)
    test_db.commit()


@pytest.fixture
def test_merchant(test_db: Session):
    """Create a test merchant with ordering URL."""
    merchant = Merchant(
        id=f"test-merchant-{uuid.uuid4().hex[:8]}",
        name="Test Grill",
        address="123 Test St",
        lat=29.4241,
        lng=-98.4936,
        ordering_url="https://testgrill.com/order",
    )
    test_db.add(merchant)
    test_db.commit()
    test_db.refresh(merchant)
    yield merchant
    # Cleanup
    test_db.delete(merchant)
    test_db.commit()


@pytest.fixture
def test_merchant_no_ordering(test_db: Session):
    """Create a test merchant without ordering URL."""
    merchant = Merchant(
        id=f"test-merchant-no-order-{uuid.uuid4().hex[:8]}",
        name="No Order Grill",
        address="456 Test St",
        lat=29.4242,
        lng=-98.4937,
        ordering_url=None,
    )
    test_db.add(merchant)
    test_db.commit()
    test_db.refresh(merchant)
    yield merchant
    # Cleanup
    test_db.delete(merchant)
    test_db.commit()


@pytest.fixture
def test_charger(test_db: Session, test_merchant: Merchant):
    """Create a test charger near the merchant."""
    charger = Charger(
        id=f"test-charger-{uuid.uuid4().hex[:8]}",
        name="Test Charger",
        lat=29.4241,
        lng=-98.4936,
        network="Tesla",
    )
    test_db.add(charger)
    test_db.commit()
    test_db.refresh(charger)
    yield charger
    # Cleanup
    test_db.delete(charger)
    test_db.commit()


@pytest.fixture
def test_session(test_db: Session, test_driver: User, test_merchant: Merchant):
    """Create a test arrival session."""
    session = ArrivalSession(
        id=uuid.uuid4(),
        driver_id=test_driver.id,
        merchant_id=test_merchant.id,
        arrival_type="ev_curbside",
        status="pending_order",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=2),
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    yield session
    # Cleanup
    test_db.query(QueuedOrder).filter(
        QueuedOrder.arrival_session_id == session.id
    ).delete()
    test_db.delete(session)
    test_db.commit()


@pytest.fixture
def auth_headers(test_driver: User):
    """Create auth headers for the test driver."""
    # In real tests, this would generate a JWT token
    # For now, mock the authentication
    return {"Authorization": f"Bearer test-token-{test_driver.id}"}


# ─── Unit Tests ───────────────────────────────────────────────────────


class TestQueuedOrderModel:
    """Unit tests for the QueuedOrder model."""

    def test_status_enum_values(self):
        """Verify status enum has expected values."""
        assert QueuedOrderStatus.QUEUED.value == "QUEUED"
        assert QueuedOrderStatus.RELEASED.value == "RELEASED"
        assert QueuedOrderStatus.CANCELED.value == "CANCELED"
        assert QueuedOrderStatus.EXPIRED.value == "EXPIRED"

    def test_release_method(self, test_db: Session, test_session: ArrivalSession, test_merchant: Merchant):
        """Test the release() method sets correct fields."""
        queued_order = QueuedOrder(
            arrival_session_id=test_session.id,
            merchant_id=test_merchant.id,
            ordering_url="https://test.com/order",
        )
        test_db.add(queued_order)
        test_db.commit()

        # Release the order
        queued_order.release("https://test.com/order?released=true")
        test_db.commit()
        test_db.refresh(queued_order)

        assert queued_order.status == QueuedOrderStatus.RELEASED.value
        assert queued_order.release_url == "https://test.com/order?released=true"
        assert queued_order.released_at is not None

    def test_cancel_method(self, test_db: Session, test_session: ArrivalSession, test_merchant: Merchant):
        """Test the cancel() method sets correct fields."""
        queued_order = QueuedOrder(
            arrival_session_id=test_session.id,
            merchant_id=test_merchant.id,
            ordering_url="https://test.com/order",
        )
        test_db.add(queued_order)
        test_db.commit()

        queued_order.cancel()
        test_db.commit()
        test_db.refresh(queued_order)

        assert queued_order.status == QueuedOrderStatus.CANCELED.value
        assert queued_order.canceled_at is not None

    def test_expire_method(self, test_db: Session, test_session: ArrivalSession, test_merchant: Merchant):
        """Test the expire() method sets correct fields."""
        queued_order = QueuedOrder(
            arrival_session_id=test_session.id,
            merchant_id=test_merchant.id,
            ordering_url="https://test.com/order",
        )
        test_db.add(queued_order)
        test_db.commit()

        queued_order.expire()
        test_db.commit()
        test_db.refresh(queued_order)

        assert queued_order.status == QueuedOrderStatus.EXPIRED.value
        assert queued_order.expired_at is not None

    def test_is_active_property(self, test_db: Session, test_session: ArrivalSession, test_merchant: Merchant):
        """Test the is_active property."""
        queued_order = QueuedOrder(
            arrival_session_id=test_session.id,
            merchant_id=test_merchant.id,
            ordering_url="https://test.com/order",
        )
        test_db.add(queued_order)
        test_db.commit()

        assert queued_order.is_active is True

        queued_order.release("https://test.com/order?released=true")
        test_db.commit()

        assert queued_order.is_active is False


# ─── API Tests ────────────────────────────────────────────────────────


class TestQueueOrderEndpoint:
    """Tests for POST /v1/arrival/{session_id}/queue-order."""

    @patch("app.dependencies.driver.get_current_driver")
    def test_queue_order_creates_record(
        self,
        mock_get_driver,
        test_client: TestClient,
        test_db: Session,
        test_driver: User,
        test_session: ArrivalSession,
        test_merchant: Merchant,
    ):
        """Test that queueing an order creates a QueuedOrder record."""
        mock_get_driver.return_value = test_driver

        response = test_client.post(
            f"/v1/arrival/{test_session.id}/queue-order",
            json={"order_number": "ORD-123"},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "QUEUED"
        assert data["ordering_url"] == test_merchant.ordering_url
        assert data["order_number"] == "ORD-123"
        assert data["release_url"] is None

        # Verify in database
        queued_order = test_db.query(QueuedOrder).filter(
            QueuedOrder.arrival_session_id == test_session.id
        ).first()
        assert queued_order is not None
        assert queued_order.status == QueuedOrderStatus.QUEUED.value

    @patch("app.dependencies.driver.get_current_driver")
    def test_queue_order_idempotent(
        self,
        mock_get_driver,
        test_client: TestClient,
        test_db: Session,
        test_driver: User,
        test_session: ArrivalSession,
        test_merchant: Merchant,
    ):
        """Test that queueing the same order twice returns the same record."""
        mock_get_driver.return_value = test_driver

        # First request
        response1 = test_client.post(
            f"/v1/arrival/{test_session.id}/queue-order",
            json={"order_number": "ORD-123"},
            headers={"Authorization": "Bearer test-token"},
        )
        assert response1.status_code == 201
        id1 = response1.json()["id"]

        # Second request (should return same record)
        response2 = test_client.post(
            f"/v1/arrival/{test_session.id}/queue-order",
            json={"order_number": "ORD-456"},  # Different order number
            headers={"Authorization": "Bearer test-token"},
        )
        assert response2.status_code == 201
        id2 = response2.json()["id"]

        assert id1 == id2

        # Verify only one record in database
        count = test_db.query(QueuedOrder).filter(
            QueuedOrder.arrival_session_id == test_session.id
        ).count()
        assert count == 1

    @patch("app.dependencies.driver.get_current_driver")
    def test_queue_order_requires_ordering_url(
        self,
        mock_get_driver,
        test_client: TestClient,
        test_db: Session,
        test_driver: User,
        test_merchant_no_ordering: Merchant,
    ):
        """Test that queueing fails if merchant has no ordering URL."""
        mock_get_driver.return_value = test_driver

        # Create session with merchant that has no ordering URL
        session = ArrivalSession(
            id=uuid.uuid4(),
            driver_id=test_driver.id,
            merchant_id=test_merchant_no_ordering.id,
            arrival_type="ev_curbside",
            status="pending_order",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=2),
        )
        test_db.add(session)
        test_db.commit()

        try:
            response = test_client.post(
                f"/v1/arrival/{session.id}/queue-order",
                json={},
                headers={"Authorization": "Bearer test-token"},
            )

            assert response.status_code == 400
            assert "does not support online ordering" in response.json()["detail"]
        finally:
            test_db.delete(session)
            test_db.commit()


class TestGetQueuedOrderEndpoint:
    """Tests for GET /v1/arrival/{session_id}/queued-order."""

    @patch("app.dependencies.driver.get_current_driver")
    def test_get_queued_order_returns_null_when_none(
        self,
        mock_get_driver,
        test_client: TestClient,
        test_driver: User,
        test_session: ArrivalSession,
    ):
        """Test that GET returns null when no queued order exists."""
        mock_get_driver.return_value = test_driver

        response = test_client.get(
            f"/v1/arrival/{test_session.id}/queued-order",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        assert response.json()["queued_order"] is None

    @patch("app.dependencies.driver.get_current_driver")
    def test_get_queued_order_returns_data(
        self,
        mock_get_driver,
        test_client: TestClient,
        test_db: Session,
        test_driver: User,
        test_session: ArrivalSession,
        test_merchant: Merchant,
    ):
        """Test that GET returns queued order data."""
        mock_get_driver.return_value = test_driver

        # Create queued order
        queued_order = QueuedOrder(
            arrival_session_id=test_session.id,
            merchant_id=test_merchant.id,
            ordering_url="https://test.com/order",
            order_number="ORD-123",
        )
        test_db.add(queued_order)
        test_db.commit()

        response = test_client.get(
            f"/v1/arrival/{test_session.id}/queued-order",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200
        data = response.json()["queued_order"]
        assert data["status"] == "QUEUED"
        assert data["order_number"] == "ORD-123"


class TestReleaseOnArrival:
    """Tests for queued order release on arrival confirmation."""

    @patch("app.dependencies.driver.get_current_driver")
    @patch("app.services.notification_service.notify_merchant")
    def test_release_on_confirmed_arrival(
        self,
        mock_notify,
        mock_get_driver,
        test_client: TestClient,
        test_db: Session,
        test_driver: User,
        test_session: ArrivalSession,
        test_merchant: Merchant,
        test_charger: Charger,
    ):
        """Test that queued order is released when arrival is confirmed."""
        mock_get_driver.return_value = test_driver
        mock_notify.return_value = "sms"

        # Create queued order
        queued_order = QueuedOrder(
            arrival_session_id=test_session.id,
            merchant_id=test_merchant.id,
            ordering_url="https://test.com/order",
        )
        test_db.add(queued_order)

        # Update session status to awaiting_arrival
        test_session.status = "awaiting_arrival"
        test_db.commit()

        # Confirm arrival (at charger location)
        response = test_client.post(
            f"/v1/arrival/{test_session.id}/confirm-arrival",
            json={
                "charger_id": test_charger.id,
                "lat": test_charger.lat,
                "lng": test_charger.lng,
            },
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200

        # Verify queued order was released
        test_db.refresh(queued_order)
        assert queued_order.status == QueuedOrderStatus.RELEASED.value
        assert queued_order.release_url is not None
        assert queued_order.released_at is not None
        assert "nerava_session=" in queued_order.release_url
        assert "nerava_released=true" in queued_order.release_url


class TestCancelQueuedOrder:
    """Tests for queued order cancellation on session cancel."""

    @patch("app.dependencies.driver.get_current_driver")
    def test_cancel_session_cancels_queued_order(
        self,
        mock_get_driver,
        test_client: TestClient,
        test_db: Session,
        test_driver: User,
        test_session: ArrivalSession,
        test_merchant: Merchant,
    ):
        """Test that canceling session cancels the queued order."""
        mock_get_driver.return_value = test_driver

        # Create queued order
        queued_order = QueuedOrder(
            arrival_session_id=test_session.id,
            merchant_id=test_merchant.id,
            ordering_url="https://test.com/order",
        )
        test_db.add(queued_order)
        test_db.commit()

        # Cancel the session
        response = test_client.post(
            f"/v1/arrival/{test_session.id}/cancel",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 200

        # Verify queued order was canceled
        test_db.refresh(queued_order)
        assert queued_order.status == QueuedOrderStatus.CANCELED.value
        assert queued_order.canceled_at is not None
