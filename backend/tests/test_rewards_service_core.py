"""
Tests for Rewards Service Core Functions

Tests award_verify_bonus and award_purchase_reward functions.
"""
import pytest
from unittest.mock import patch
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.rewards import award_verify_bonus, award_purchase_reward
from app.models import User


class TestAwardVerifyBonus:
    """Test award_verify_bonus function"""
    
    def test_award_verify_bonus_happy_path(self, db: Session):
        """Test successful verify bonus award"""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        session_id = "test_session_123"
        amount = 200  # cents
        now = datetime.utcnow()
        
        # Award bonus
        result = award_verify_bonus(
            db=db,
            user_id=user.id,
            session_id=session_id,
            amount=amount,
            now=now
        )
        
        # Should have awarded
        assert result["awarded"] is True
        assert result["user_delta"] == 180  # 90% of 200
        assert result["pool_delta"] == 20   # 10% of 200
        
        # Check reward_events was created
        reward = db.execute(text("""
            SELECT * FROM reward_events
            WHERE user_id = :user_id AND source = 'verify_bonus'
        """), {"user_id": str(user.id)}).first()
        assert reward is not None
        
        # Check wallet_ledger was updated
        ledger = db.execute(text("""
            SELECT * FROM wallet_ledger
            WHERE user_id = :user_id
        """), {"user_id": user.id}).first()
        assert ledger is not None
        assert ledger[1] == 180  # amount_cents
    
    def test_award_verify_bonus_idempotent(self, db: Session):
        """Test verify bonus is idempotent - duplicate call returns already_rewarded"""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        session_id = "test_session_123"
        amount = 200
        now = datetime.utcnow()
        
        # First award
        result1 = award_verify_bonus(
            db=db,
            user_id=user.id,
            session_id=session_id,
            amount=amount,
            now=now
        )
        assert result1["awarded"] is True
        
        # Second award - should be idempotent
        result2 = award_verify_bonus(
            db=db,
            user_id=user.id,
            session_id=session_id,
            amount=amount,
            now=now
        )
        assert result2["awarded"] is False
        assert result2["reason"] == "already_rewarded"
        assert result2["user_delta"] == 0
        assert result2["pool_delta"] == 0
    
    def test_award_verify_bonus_error_handling(self, db: Session):
        """Test error handling in verify bonus"""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        session_id = "test_session_123"
        amount = 200
        now = datetime.utcnow()
        
        # Mock get_table_columns to raise error
        with pytest.raises(Exception):
            with patch('app.services.rewards.get_table_columns', side_effect=Exception("DB Error")):
                award_verify_bonus(
                    db=db,
                    user_id=user.id,
                    session_id=session_id,
                    amount=amount,
                    now=now
                )
        
        # Should have rolled back
        reward = db.execute(text("""
            SELECT * FROM reward_events
            WHERE user_id = :user_id
        """), {"user_id": str(user.id)}).first()
        assert reward is None


class TestAwardPurchaseReward:
    """Test award_purchase_reward function"""
    
    def test_award_purchase_reward_happy_path(self, db: Session):
        """Test successful purchase reward award"""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        session_id = "test_session_123"
        payment_id = "payment_456"
        amount = 300  # cents
        now = datetime.utcnow()
        
        # Award reward
        result = award_purchase_reward(
            db=db,
            user_id=user.id,
            session_id=session_id,
            payment_id=payment_id,
            amount=amount,
            now=now
        )
        
        # Should have awarded
        assert result["awarded"] is True
        assert result["user_delta"] == 270  # 90% of 300
        assert result["pool_delta"] == 30   # 10% of 300
        
        # Check reward_events was created
        reward = db.execute(text("""
            SELECT * FROM reward_events
            WHERE user_id = :user_id AND source = 'purchase'
        """), {"user_id": str(user.id)}).first()
        assert reward is not None
    
    def test_award_purchase_reward_idempotent(self, db: Session):
        """Test purchase reward is idempotent"""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        session_id = "test_session_123"
        payment_id = "payment_456"
        amount = 300
        now = datetime.utcnow()
        
        # First award
        result1 = award_purchase_reward(
            db=db,
            user_id=user.id,
            session_id=session_id,
            payment_id=payment_id,
            amount=amount,
            now=now
        )
        assert result1["awarded"] is True
        
        # Second award - should be idempotent
        result2 = award_purchase_reward(
            db=db,
            user_id=user.id,
            session_id=session_id,
            payment_id=payment_id,
            amount=amount,
            now=now
        )
        assert result2["awarded"] is False
        assert result2["reason"] == "already_rewarded"
    
    def test_award_purchase_reward_error_handling(self, db: Session):
        """Test error handling in purchase reward"""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed",
            is_active=True,
            role_flags="driver"
        )
        db.add(user)
        db.commit()
        
        session_id = "test_session_123"
        payment_id = "payment_456"
        amount = 300
        now = datetime.utcnow()
        
        # Mock get_table_columns to raise error
        with pytest.raises(Exception):
            with patch('app.services.rewards.get_table_columns', side_effect=Exception("DB Error")):
                award_purchase_reward(
                    db=db,
                    user_id=user.id,
                    session_id=session_id,
                    payment_id=payment_id,
                    amount=amount,
                    now=now
                )

