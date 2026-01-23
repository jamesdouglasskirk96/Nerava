"""
Tests for Wallet Service Core Functions

Tests get_wallet, credit_wallet, and debit_wallet functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.wallet import get_wallet, credit_wallet, debit_wallet


class TestGetWallet:
    """Test get_wallet function"""
    
    def test_get_wallet_creates_if_not_exists(self):
        """Test get_wallet creates wallet with zero balance if not exists"""
        user_id = "test_user_123"
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                mock_con = MagicMock()
                mock_con.execute.return_value.fetchone.return_value = None
                mock_conn.return_value.__enter__.return_value = mock_con
                mock_conn.return_value.__exit__.return_value = None
                
                result = get_wallet(user_id)
                
                assert result["user_id"] == user_id
                assert result["balance_cents"] == 0
                assert result["currency"] == "USD"
    
    def test_get_wallet_returns_existing(self):
        """Test get_wallet returns existing wallet"""
        user_id = "test_user_123"
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                mock_con = MagicMock()
                mock_row = MagicMock()
                mock_row.__getitem__.side_effect = lambda k: {
                    "user_id": user_id,
                    "balance_cents": 500,
                    "currency": "USD"
                }[k]
                mock_con.execute.return_value.fetchone.return_value = mock_row
                mock_conn.return_value.__enter__.return_value = mock_con
                mock_conn.return_value.__exit__.return_value = None
                
                result = get_wallet(user_id)
                
                assert result["user_id"] == user_id
                assert result["balance_cents"] == 500
                assert result["currency"] == "USD"
    
    def test_get_wallet_fallback_in_local(self):
        """Test get_wallet uses in-memory fallback in local env"""
        user_id = "test_user_123"
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                # Simulate connection failure
                mock_conn.return_value.__enter__.return_value = None
                mock_conn.return_value.__exit__.return_value = None
                
                result = get_wallet(user_id)
                
                assert result["user_id"] == user_id
                assert result["balance_cents"] == 0
                assert result["currency"] == "USD"


class TestCreditWallet:
    """Test credit_wallet function"""
    
    def test_credit_wallet_happy_path(self):
        """Test credit_wallet increments balance"""
        user_id = "test_user_123"
        amount = 100
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                mock_con = MagicMock()
                mock_row = MagicMock()
                mock_row.__getitem__.side_effect = lambda k: {
                    "balance_cents": 200,
                    "currency": "USD"
                }[k]
                mock_con.execute.return_value.fetchone.return_value = mock_row
                mock_conn.return_value.__enter__.return_value = mock_con
                mock_conn.return_value.__exit__.return_value = None
                
                result = credit_wallet(user_id, amount)
                
                assert result["user_id"] == user_id
                assert result["balance_cents"] == 300  # 200 + 100
                assert result["currency"] == "USD"
    
    def test_credit_wallet_creates_if_not_exists(self):
        """Test credit_wallet creates wallet if not exists"""
        user_id = "test_user_123"
        amount = 100
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                mock_con = MagicMock()
                mock_con.execute.return_value.fetchone.return_value = None
                mock_conn.return_value.__enter__.return_value = mock_con
                mock_conn.return_value.__exit__.return_value = None
                
                result = credit_wallet(user_id, amount)
                
                assert result["user_id"] == user_id
                assert result["balance_cents"] == amount
                assert result["currency"] == "USD"
    
    def test_credit_wallet_negative_amount_raises(self):
        """Test credit_wallet raises ValueError for negative amount"""
        user_id = "test_user_123"
        
        with pytest.raises(ValueError, match="amount_cents must be >= 0"):
            credit_wallet(user_id, -10)
    
    def test_credit_wallet_fallback_in_local(self):
        """Test credit_wallet uses in-memory fallback in local env"""
        user_id = "test_user_123"
        amount = 100
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                # Simulate connection failure
                mock_conn.return_value.__enter__.return_value = None
                mock_conn.return_value.__exit__.return_value = None
                
                result = credit_wallet(user_id, amount)
                
                assert result["user_id"] == user_id
                assert result["balance_cents"] == amount


class TestDebitWallet:
    """Test debit_wallet function"""
    
    def test_debit_wallet_happy_path(self):
        """Test debit_wallet decrements balance"""
        user_id = "test_user_123"
        amount = 50
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                mock_con = MagicMock()
                mock_row = MagicMock()
                mock_row.__getitem__.side_effect = lambda k: {
                    "balance_cents": 200,
                    "currency": "USD"
                }[k]
                mock_con.execute.return_value.fetchone.return_value = mock_row
                mock_conn.return_value.__enter__.return_value = mock_con
                mock_conn.return_value.__exit__.return_value = None
                
                result = debit_wallet(user_id, amount)
                
                assert result["user_id"] == user_id
                assert result["balance_cents"] == 150  # 200 - 50
                assert result["currency"] == "USD"
    
    def test_debit_wallet_prevents_negative_balance(self):
        """Test debit_wallet prevents negative balance"""
        user_id = "test_user_123"
        amount = 300  # More than balance
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                mock_con = MagicMock()
                mock_row = MagicMock()
                mock_row.__getitem__.side_effect = lambda k: {
                    "balance_cents": 200,
                    "currency": "USD"
                }[k]
                mock_con.execute.return_value.fetchone.return_value = mock_row
                mock_conn.return_value.__enter__.return_value = mock_con
                mock_conn.return_value.__exit__.return_value = None
                
                result = debit_wallet(user_id, amount)
                
                assert result["balance_cents"] == 0  # Should not go negative
    
    def test_debit_wallet_creates_if_not_exists(self):
        """Test debit_wallet creates empty wallet if not exists"""
        user_id = "test_user_123"
        amount = 50
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                mock_con = MagicMock()
                mock_con.execute.return_value.fetchone.return_value = None
                mock_conn.return_value.__enter__.return_value = mock_con
                mock_conn.return_value.__exit__.return_value = None
                
                result = debit_wallet(user_id, amount)
                
                assert result["user_id"] == user_id
                assert result["balance_cents"] == 0  # Empty wallet
    
    def test_debit_wallet_negative_amount_raises(self):
        """Test debit_wallet raises ValueError for negative amount"""
        user_id = "test_user_123"
        
        with pytest.raises(ValueError, match="amount_cents must be >= 0"):
            debit_wallet(user_id, -10)
    
    def test_debit_wallet_fallback_in_local(self):
        """Test debit_wallet uses in-memory fallback in local env"""
        user_id = "test_user_123"
        amount = 50
        
        with patch('app.services.wallet.is_local_env', return_value=True):
            with patch('app.services.wallet._conn') as mock_conn:
                # Simulate connection failure
                mock_conn.return_value.__enter__.return_value = None
                mock_conn.return_value.__exit__.return_value = None
                
                result = debit_wallet(user_id, amount)
                
                assert result["user_id"] == user_id
                assert result["balance_cents"] == 0  # Starts at 0, debits to 0







