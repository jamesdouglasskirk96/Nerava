"""
Unit tests for Square Orders service
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.services.square_orders import (
    search_recent_orders,
    get_order_total_cents,
    create_order,
    create_payment_for_order,
    get_square_token_for_merchant,
    SquareNotConnectedError,
    SquareOrderTotalUnavailableError,
    SquareError
)
from app.models.domain import DomainMerchant
from app.services.token_encryption import TokenDecryptionError


@pytest.fixture
def mock_merchant():
    """Create a mock merchant with Square credentials"""
    merchant = Mock(spec=DomainMerchant)
    merchant.id = "test-merchant-id"
    merchant.square_access_token = "encrypted-token"
    merchant.square_location_id = "test-location-id"
    merchant.square_merchant_id = "test-square-merchant-id"
    return merchant


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    return Mock()


class TestGetSquareTokenForMerchant:
    """Tests for get_square_token_for_merchant"""
    
    def test_success(self, mock_merchant):
        """Test successful token decryption"""
        with patch('app.services.square_orders.decrypt_token', return_value='decrypted-token'):
            token = get_square_token_for_merchant(mock_merchant)
            assert token == 'decrypted-token'
    
    def test_missing_token(self, mock_merchant):
        """Test error when token is missing"""
        mock_merchant.square_access_token = None
        with pytest.raises(SquareNotConnectedError):
            get_square_token_for_merchant(mock_merchant)
    
    def test_missing_location_id(self, mock_merchant):
        """Test error when location_id is missing"""
        mock_merchant.square_location_id = None
        with pytest.raises(SquareNotConnectedError):
            get_square_token_for_merchant(mock_merchant)
    
    def test_decryption_failure(self, mock_merchant):
        """Test error when decryption fails"""
        with patch('app.services.square_orders.decrypt_token', side_effect=TokenDecryptionError("Decryption failed")):
            with pytest.raises(SquareNotConnectedError):
                get_square_token_for_merchant(mock_merchant)


class TestSearchRecentOrders:
    """Tests for search_recent_orders"""
    
    @patch('app.services.square_orders.httpx.Client')
    @patch('app.services.square_orders.get_square_token_for_merchant')
    @patch('app.services.square_orders._get_square_base_url')
    def test_success(self, mock_base_url, mock_get_token, mock_client_class, mock_db, mock_merchant):
        """Test successful order search"""
        mock_base_url.return_value = "https://connect.squareupsandbox.com"
        mock_get_token.return_value = "decrypted-token"
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "orders": [
                {
                    "id": "order-1",
                    "created_at": "2025-01-24T10:41:00Z",
                    "total_money": {
                        "amount": 850,
                        "currency": "USD"
                    }
                }
            ]
        }
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        orders = search_recent_orders(mock_db, mock_merchant, minutes=10, limit=20)
        
        assert len(orders) == 1
        assert orders[0]["order_id"] == "order-1"
        assert orders[0]["total_cents"] == 850
        assert orders[0]["currency"] == "USD"
    
    @patch('app.services.square_orders.get_square_token_for_merchant')
    def test_not_connected(self, mock_get_token, mock_db, mock_merchant):
        """Test error when merchant not connected"""
        mock_get_token.side_effect = SquareNotConnectedError("Not connected")
        
        with pytest.raises(SquareNotConnectedError):
            search_recent_orders(mock_db, mock_merchant)


class TestGetOrderTotalCents:
    """Tests for get_order_total_cents"""
    
    @patch('app.services.square_orders.httpx.Client')
    @patch('app.services.square_orders.get_square_token_for_merchant')
    @patch('app.services.square_orders._get_square_base_url')
    def test_success(self, mock_base_url, mock_get_token, mock_client_class, mock_db, mock_merchant):
        """Test successful order total retrieval"""
        mock_base_url.return_value = "https://connect.squareupsandbox.com"
        mock_get_token.return_value = "decrypted-token"
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "order": {
                "id": "order-1",
                "location_id": "test-location-id",
                "total_money": {
                    "amount": 850
                }
            }
        }
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        total = get_order_total_cents(mock_db, mock_merchant, "order-1")
        
        assert total == 850
    
    @patch('app.services.square_orders.httpx.Client')
    @patch('app.services.square_orders.get_square_token_for_merchant')
    @patch('app.services.square_orders._get_square_base_url')
    def test_location_mismatch(self, mock_base_url, mock_get_token, mock_client_class, mock_db, mock_merchant):
        """Test error when order location doesn't match merchant location"""
        mock_base_url.return_value = "https://connect.squareupsandbox.com"
        mock_get_token.return_value = "decrypted-token"
        
        # Mock HTTP response with wrong location
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "order": {
                "id": "order-1",
                "location_id": "wrong-location-id",
                "total_money": {
                    "amount": 850
                }
            }
        }
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        with pytest.raises(SquareOrderTotalUnavailableError):
            get_order_total_cents(mock_db, mock_merchant, "order-1")


class TestCreateOrder:
    """Tests for create_order"""
    
    @patch('app.services.square_orders.httpx.Client')
    @patch('app.services.square_orders.get_square_token_for_merchant')
    @patch('app.services.square_orders._get_square_base_url')
    @patch('app.services.square_orders.uuid.uuid4')
    def test_success(self, mock_uuid, mock_base_url, mock_get_token, mock_client_class, mock_db, mock_merchant):
        """Test successful order creation"""
        mock_base_url.return_value = "https://connect.squareupsandbox.com"
        mock_get_token.return_value = "decrypted-token"
        mock_uuid.return_value.hex = "test-uuid"
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "order": {
                "id": "order-1",
                "created_at": "2025-01-24T10:41:00Z",
                "total_money": {
                    "amount": 850
                }
            }
        }
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        result = create_order(mock_db, mock_merchant, 850, "Coffee")
        
        assert result["order_id"] == "order-1"
        assert result["total_cents"] == 850


class TestCreatePaymentForOrder:
    """Tests for create_payment_for_order"""
    
    @patch('app.services.square_orders.httpx.Client')
    @patch('app.services.square_orders.get_square_token_for_merchant')
    @patch('app.services.square_orders._get_square_base_url')
    @patch('app.services.square_orders.uuid.uuid4')
    @patch('app.services.square_orders.os.getenv')
    def test_success(self, mock_getenv, mock_uuid, mock_base_url, mock_get_token, mock_client_class, mock_db, mock_merchant):
        """Test successful payment creation"""
        mock_getenv.return_value = "sandbox"
        mock_base_url.return_value = "https://connect.squareupsandbox.com"
        mock_get_token.return_value = "decrypted-token"
        mock_uuid.return_value.hex = "test-uuid"
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "payment": {
                "id": "payment-1",
                "status": "COMPLETED"
            }
        }
        
        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        result = create_payment_for_order(mock_db, mock_merchant, "order-1", 850)
        
        assert result["payment_id"] == "payment-1"
        assert result["status"] == "COMPLETED"

