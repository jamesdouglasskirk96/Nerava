"""
Integration tests for Checkout API with Square integration
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main_simple import app
from app.models.domain import DomainMerchant, DriverWallet, MerchantRedemption
from app.db import get_db
from sqlalchemy.orm import Session


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_merchant(db: Session):
    """Create a test merchant with Square credentials"""
    merchant = DomainMerchant(
        id="test-merchant-id",
        name="Test Merchant",
        lat=30.4021,
        lng=-97.7266,
        zone_slug="domain_austin",
        status="active",
        qr_token="test-qr-token",
        square_access_token="encrypted-token",
        square_location_id="test-location-id",
        square_merchant_id="test-square-merchant-id",
        recommended_perk_cents=300
    )
    db.add(merchant)
    db.commit()
    return merchant


@pytest.fixture
def mock_driver_wallet(db: Session):
    """Create a test driver wallet"""
    from app.models import User
    user = User(id=1, email="test@example.com")
    db.add(user)
    
    wallet = DriverWallet(
        user_id=1,
        nova_balance=1000,
        energy_reputation_score=0
    )
    db.add(wallet)
    db.commit()
    return wallet


class TestCheckoutOrdersEndpoint:
    """Tests for GET /v1/checkout/orders"""
    
    @patch('app.routers.checkout.search_recent_orders')
    def test_list_orders_success(self, mock_search, client, mock_merchant):
        """Test successful order listing"""
        mock_search.return_value = [
            {
                "order_id": "order-1",
                "created_at": "2025-01-24T10:41:00Z",
                "total_cents": 850,
                "currency": "USD",
                "display": "$8.50 • 10:41 AM"
            }
        ]
        
        response = client.get("/v1/checkout/orders?token=test-qr-token&minutes=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["merchant_id"] == "test-merchant-id"
        assert len(data["orders"]) == 1
        assert data["orders"][0]["order_id"] == "order-1"
    
    def test_list_orders_invalid_token(self, client):
        """Test error with invalid QR token"""
        response = client.get("/v1/checkout/orders?token=invalid-token&minutes=10")
        
        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["error"] == "INVALID_QR_TOKEN"
    
    @patch('app.routers.checkout.search_recent_orders')
    def test_list_orders_not_connected(self, mock_search, client, mock_merchant):
        """Test handling when merchant not connected to Square"""
        from app.services.square_orders import SquareNotConnectedError
        mock_search.side_effect = SquareNotConnectedError("Not connected")
        
        response = client.get("/v1/checkout/orders?token=test-qr-token&minutes=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["orders"]) == 0  # Empty orders list


class TestCheckoutRedeemWithSquareOrder:
    """Tests for POST /v1/checkout/redeem with square_order_id"""
    
    @patch('app.routers.checkout.get_order_total_cents')
    @patch('app.routers.checkout.NovaService.redeem_from_driver')
    @patch('app.routers.checkout.record_merchant_fee')
    @patch('app.routers.checkout.mark_wallet_activity')
    def test_redeem_with_square_order_success(
        self, mock_mark_activity, mock_record_fee, mock_redeem, mock_get_total,
        client, mock_merchant, mock_driver_wallet, db: Session
    ):
        """Test successful redemption with Square order ID"""
        mock_get_total.return_value = 850
        mock_redeem.return_value = {"driver_balance": 700}
        mock_record_fee.return_value = 45
        
        response = client.post(
            "/v1/checkout/redeem",
            json={
                "qr_token": "test-qr-token",
                "order_total_cents": 850,
                "square_order_id": "order-1"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["square_order_id"] == "order-1"
        assert data["merchant_fee_cents"] == 45
        
        # Verify redemption was created
        redemption = db.query(MerchantRedemption).filter(
            MerchantRedemption.square_order_id == "order-1"
        ).first()
        assert redemption is not None
        assert redemption.order_total_cents == 850
    
    @patch('app.routers.checkout.get_order_total_cents')
    def test_redeem_duplicate_order(self, mock_get_total, client, mock_merchant, mock_driver_wallet, db: Session):
        """Test error when trying to redeem same order twice"""
        mock_get_total.return_value = 850
        
        # Create existing redemption
        existing = MerchantRedemption(
            id="redemption-1",
            merchant_id="test-merchant-id",
            driver_user_id=1,
            square_order_id="order-1",
            order_total_cents=850,
            discount_cents=300,
            nova_spent_cents=300
        )
        db.add(existing)
        db.commit()
        
        response = client.post(
            "/v1/checkout/redeem",
            json={
                "qr_token": "test-qr-token",
                "order_total_cents": 850,
                "square_order_id": "order-1"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"] == "ORDER_ALREADY_REDEEMED"
    
    @patch('app.routers.checkout.get_order_total_cents')
    def test_redeem_square_not_connected(self, mock_get_total, client, mock_merchant, mock_driver_wallet):
        """Test error when merchant not connected to Square"""
        from app.services.square_orders import SquareNotConnectedError
        mock_get_total.side_effect = SquareNotConnectedError("Not connected")
        
        response = client.post(
            "/v1/checkout/redeem",
            json={
                "qr_token": "test-qr-token",
                "order_total_cents": 850,
                "square_order_id": "order-1"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "SQUARE_NOT_CONNECTED"

