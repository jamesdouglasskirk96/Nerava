"""
Tests for Nova Accrual Service

Tests the background service that accrues Nova for wallets with charging_detected=True.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from app.services.nova_accrual import NovaAccrualService
from app.models import DriverWallet, NovaTransaction


class TestNovaAccrualService:
    """Test NovaAccrualService class"""
    
    def test_is_enabled_with_demo_mode(self):
        """Test is_enabled returns True when DEMO_MODE is set"""
        service = NovaAccrualService()
        with patch.dict(os.environ, {"DEMO_MODE": "true"}):
            assert service.is_enabled() is True
    
    def test_is_enabled_with_demo_qr(self):
        """Test is_enabled returns True when DEMO_QR_ENABLED is set"""
        service = NovaAccrualService()
        with patch.dict(os.environ, {"DEMO_QR_ENABLED": "true"}):
            assert service.is_enabled() is True
    
    def test_is_enabled_false_when_disabled(self):
        """Test is_enabled returns False when demo mode is disabled"""
        service = NovaAccrualService()
        with patch.dict(os.environ, {"DEMO_MODE": "false", "DEMO_QR_ENABLED": "false"}, clear=False):
            assert service.is_enabled() is False
    
    @pytest.mark.asyncio
    async def test_start_when_disabled(self):
        """Test start() does nothing when service is disabled"""
        service = NovaAccrualService()
        with patch.dict(os.environ, {"DEMO_MODE": "false"}):
            await service.start()
            assert service.running is False
            assert service.task is None
    
    @pytest.mark.asyncio
    async def test_start_when_already_running(self):
        """Test start() warns when already running"""
        service = NovaAccrualService()
        service.running = True
        with patch.dict(os.environ, {"DEMO_MODE": "true"}):
            await service.start()
            # Should not create new task
            assert service.running is True
    
    @pytest.mark.asyncio
    async def test_stop_when_not_running(self):
        """Test stop() does nothing when not running"""
        service = NovaAccrualService()
        await service.stop()
        assert service.running is False
    
    @pytest.mark.asyncio
    async def test_stop_cancels_task(self):
        """Test stop() cancels running task"""
        service = NovaAccrualService()
        service.running = True
        mock_task = MagicMock()
        service.task = mock_task
        await service.stop()
        assert service.running is False
        mock_task.cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_accrue_nova_for_charging_wallets_no_wallets(self, db: Session):
        """Test _accrue_nova_for_charging_wallets() with no charging wallets"""
        service = NovaAccrualService()
        
        # Mock SessionLocal() call to return our test db
        with patch('app.db.SessionLocal', return_value=db):
            await service._accrue_nova_for_charging_wallets()
        
        # Should not create any transactions
        transactions = db.query(NovaTransaction).all()
        assert len(transactions) == 0
    
    @pytest.mark.asyncio
    async def test_accrue_nova_for_charging_wallets_happy_path(self, db: Session):
        """Test _accrue_nova_for_charging_wallets() accrues Nova for charging wallets"""
        service = NovaAccrualService()
        
        # Create a test user and wallet with charging detected
        from app.models import User
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.flush()
        
        wallet = DriverWallet(
            user_id=user.id,
            nova_balance=100,
            energy_reputation_score=50,
            charging_detected=True
        )
        db.add(wallet)
        db.commit()
        
        initial_balance = wallet.nova_balance
        initial_reputation = wallet.energy_reputation_score
        
        # Mock SessionLocal() call to return our test db
        with patch('app.db.SessionLocal', return_value=db):
            await service._accrue_nova_for_charging_wallets()
        
        # Refresh wallet from DB
        db.refresh(wallet)
        
        # Should have incremented Nova balance by 1
        assert wallet.nova_balance == initial_balance + 1
        
        # Should have incremented reputation by 1
        assert wallet.energy_reputation_score == initial_reputation + 1
        
        # Should have created a Nova transaction
        transactions = db.query(NovaTransaction).filter(
            NovaTransaction.driver_user_id == user.id
        ).all()
        assert len(transactions) == 1
        assert transactions[0].amount == 1
        assert transactions[0].type == "driver_earn"
        assert transactions[0].transaction_meta["source"] == "demo_charging_accrual"
    
    @pytest.mark.asyncio
    async def test_accrue_nova_for_charging_wallets_multiple_wallets(self, db: Session):
        """Test _accrue_nova_for_charging_wallets() handles multiple charging wallets"""
        service = NovaAccrualService()
        
        # Create multiple test users and wallets
        from app.models import User
        users = []
        wallets = []
        for i in range(3):
            user = User(
                email=f"test{i}@example.com",
                password_hash="hashed",
                is_active=True,
                role_flags="driver"
            )
            db.add(user)
            db.flush()
            users.append(user)
            
            wallet = DriverWallet(
                user_id=user.id,
                nova_balance=100,
                charging_detected=True
            )
            db.add(wallet)
            wallets.append(wallet)
        
        db.commit()
        
        # Mock SessionLocal() call to return our test db
        with patch('app.db.SessionLocal', return_value=db):
            await service._accrue_nova_for_charging_wallets()
        
        # All wallets should have been updated
        for wallet in wallets:
            db.refresh(wallet)
            assert wallet.nova_balance == 101
        
        # Should have created 3 transactions
        transactions = db.query(NovaTransaction).all()
        assert len(transactions) == 3
    
    @pytest.mark.asyncio
    async def test_accrue_nova_for_charging_wallets_skips_non_charging(self, db: Session):
        """Test _accrue_nova_for_charging_wallets() skips wallets without charging_detected"""
        service = NovaAccrualService()
        
        from app.models import User
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.flush()
        
        # Wallet without charging_detected
        wallet = DriverWallet(
            user_id=user.id,
            nova_balance=100,
            charging_detected=False
        )
        db.add(wallet)
        db.commit()
        
        initial_balance = wallet.nova_balance
        
        # Mock SessionLocal() call to return our test db
        with patch('app.db.SessionLocal', return_value=db):
            await service._accrue_nova_for_charging_wallets()
        
        # Wallet should not have been updated
        db.refresh(wallet)
        assert wallet.nova_balance == initial_balance
        
        # Should not have created any transactions
        transactions = db.query(NovaTransaction).all()
        assert len(transactions) == 0
    
    @pytest.mark.asyncio
    async def test_accrue_nova_for_charging_wallets_error_handling(self, db: Session):
        """Test _accrue_nova_for_charging_wallets() handles errors gracefully"""
        service = NovaAccrualService()
        
        # Mock SessionLocal to raise an error
        with patch('app.db.SessionLocal', side_effect=Exception("DB Error")):
            # Should not raise, should handle error gracefully
            await service._accrue_nova_for_charging_wallets()
    
    @pytest.mark.asyncio
    async def test_accrue_nova_for_charging_wallets_rollback_on_error(self, db: Session):
        """Test _accrue_nova_for_charging_wallets() rolls back on transaction error"""
        service = NovaAccrualService()
        
        from app.models import User
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.flush()
        
        wallet = DriverWallet(
            user_id=user.id,
            nova_balance=100,
            charging_detected=True
        )
        db.add(wallet)
        db.commit()
        
        initial_balance = wallet.nova_balance
        
        # Mock mark_wallet_activity to raise an error
        with patch('app.services.nova_accrual.mark_wallet_activity', side_effect=Exception("Activity error")):
            with patch('app.db.SessionLocal', return_value=db):
                await service._accrue_nova_for_charging_wallets()
        
        # Wallet should not have been updated (rolled back)
        db.refresh(wallet)
        assert wallet.nova_balance == initial_balance
        
        # Should not have created any transactions
        transactions = db.query(NovaTransaction).all()
        assert len(transactions) == 0
    
    def test_service_initialization(self):
        """Test service initializes with correct defaults"""
        service = NovaAccrualService()
        assert service.accrual_interval == 5
        assert service.running is False
        assert service.task is None
    
    def test_service_initialization_custom_interval(self):
        """Test service initializes with custom accrual interval"""
        service = NovaAccrualService(accrual_interval=10)
        assert service.accrual_interval == 10

