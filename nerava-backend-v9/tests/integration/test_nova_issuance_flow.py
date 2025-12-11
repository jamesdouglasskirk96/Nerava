"""
Integration tests for Nova issuance flow
Tests that telemetry/sessions can be converted to Nova rewards
"""
import pytest
from datetime import datetime, timedelta
from app.models import User
from app.models.domain import DomainChargingSession, DriverWallet, NovaTransaction
from app.models.vehicle import VehicleAccount
from app.models.domain import EnergyEvent


@pytest.fixture
def test_user_with_wallet(db):
    """Create test user with driver wallet"""
    user = User(
        id=2,
        email="driver@example.com",
        password_hash="hashed",
        is_active=True,
        role_flags="driver"
    )
    db.add(user)
    
    wallet = DriverWallet(
        user_id=user.id,
        nova_balance=0,
        energy_reputation_score=0
    )
    db.add(wallet)
    db.commit()
    db.refresh(user)
    db.refresh(wallet)
    return user, wallet


@pytest.fixture
def test_vehicle_account(db, test_user_with_wallet):
    """Create vehicle account linked to test user"""
    user, _ = test_user_with_wallet
    account = VehicleAccount(
        id="va_test",
        user_id=user.id,
        provider="smartcar",
        provider_vehicle_id="vehicle_123",
        is_active=True
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@pytest.fixture
def test_charging_session(db, test_user_with_wallet):
    """Create test charging session (off-peak)"""
    user, _ = test_user_with_wallet
    session = DomainChargingSession(
        id="session_test",
        driver_user_id=user.id,
        charger_provider="smartcar",
        start_time=datetime.utcnow() - timedelta(hours=1),
        end_time=datetime.utcnow(),
        kwh_estimate=15.5,
        verified=False
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


class TestNovaIssuanceFlow:
    """Test Nova issuance from charging sessions"""
    
    def test_grant_nova_creates_transaction_and_updates_wallet(
        self, client, db, test_user_with_wallet, test_charging_session
    ):
        """Granting Nova should create NovaTransaction and update DriverWallet"""
        user, wallet = test_user_with_wallet
        session = test_charging_session
        
        # Create admin user for the grant endpoint
        admin_user = User(
            id=999,
            email="admin@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="admin"
        )
        db.add(admin_user)
        db.commit()
        
        # Grant Nova via the endpoint
        # Note: This requires admin auth, so we might need to mock the auth dependency
        # For now, test the service directly
        from app.services.nova_service import NovaService
        
        initial_balance = wallet.nova_balance
        
        transaction = NovaService.grant_to_driver(
            db=db,
            driver_id=user.id,
            amount=100,  # Grant 100 Nova
            type="driver_earn",
            session_id=session.id,
            metadata={"test": "integration_test"}
        )
        
        # Refresh wallet from DB
        db.refresh(wallet)
        
        # Verify NovaTransaction was created
        assert transaction is not None
        assert transaction.amount == 100
        assert transaction.type == "driver_earn"
        assert transaction.driver_user_id == user.id
        assert transaction.session_id == session.id
        
        # Verify wallet balance increased
        assert wallet.nova_balance == initial_balance + 100
        
        # Verify transaction exists in DB
        txn_in_db = db.query(NovaTransaction).filter(
            NovaTransaction.id == transaction.id
        ).first()
        assert txn_in_db is not None
    
    def test_off_peak_session_eligible_for_nova(self, db, test_user_with_wallet, test_charging_session):
        """Off-peak session should be eligible for Nova (test the calculation logic)"""
        user, wallet = test_user_with_wallet
        session = test_charging_session
        
        # Set session to off-peak time (23:00)
        session.start_time = datetime(2025, 1, 15, 23, 0, 0)
        session.end_time = datetime(2025, 1, 16, 1, 0, 0)  # 2 hour session
        db.commit()
        
        # Calculate expected Nova using nova_engine
        from app.services.nova_engine import calculate_nova_for_session
        
        rules = [
            {
                "code": "OFF_PEAK_BASE",
                "active": True,
                "params": {"cents": 25, "window": ["22:00", "06:00"]}
            }
        ]
        
        duration_minutes = int((session.end_time - session.start_time).total_seconds() / 60)
        expected_nova = calculate_nova_for_session(
            kwh=session.kwh_estimate,
            duration_minutes=duration_minutes,
            session_time=session.start_time,
            rules=rules
        )
        
        # Should grant Nova for off-peak session
        assert expected_nova > 0

