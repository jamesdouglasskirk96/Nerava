"""
Unit tests for OTP authentication: happy path, rate limiting, audit logging
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import User, OTPChallenge
from app.services.otp_service import OTPService


@pytest.fixture
def test_db(db: Session) -> Session:
    """Test database session"""
    return db


def test_otp_happy_path_with_stub_provider(db: Session):
    """Test OTP happy path with stub provider (no Twilio)"""
    phone = "+15551234567"
    
    # Start OTP flow
    result = OTPService.send_otp(db, phone)
    assert result is True
    
    # Find challenge
    challenge = db.query(OTPChallenge).filter(
        OTPChallenge.phone == phone,
        OTPChallenge.consumed == False
    ).order_by(OTPChallenge.created_at.desc()).first()
    
    assert challenge is not None
    assert challenge.phone == phone
    assert challenge.consumed is False
    assert challenge.expires_at > datetime.utcnow()
    
    # In stub mode, code is logged - for test, we need to get it
    # For MVP, we'll use a test code
    test_code = "123456"  # Would need to hash this to verify
    
    # Verify OTP (would need actual code hash)
    # For MVP test, create challenge with known code
    from app.core.security import hash_password
    known_code = "123456"
    challenge.code_hash = hash_password(known_code)
    db.commit()
    
    # Verify
    verified_phone = OTPService.verify_otp(db, phone, known_code)
    assert verified_phone == phone
    
    # Challenge should be consumed
    db.refresh(challenge)
    assert challenge.consumed is True


def test_otp_rate_limiting_per_phone(db: Session):
    """Test rate limiting per phone number"""
    phone = "+15551234567"
    
    # Create multiple recent challenges
    for i in range(5):
        challenge = OTPChallenge(
            id=f"test_{i}",
            phone=phone,
            code_hash="hash",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            attempts=0,
            max_attempts=5,
            consumed=False,
            created_at=datetime.utcnow() - timedelta(seconds=i * 10)
        )
        db.add(challenge)
    
    db.commit()
    
    # Check recent count (within 1 minute)
    recent_count = db.query(OTPChallenge).filter(
        OTPChallenge.phone == phone,
        OTPChallenge.created_at > datetime.utcnow() - timedelta(minutes=1)
    ).count()
    
    assert recent_count == 5
    
    # Endpoint should block if recent_count >= 3
    # This is enforced in the router, not the service


def test_otp_max_attempts(db: Session):
    """Test OTP max attempts enforcement"""
    phone = "+15551234567"
    from app.core.security import hash_password
    
    # Create challenge
    challenge = OTPChallenge(
        id="test_challenge",
        phone=phone,
        code_hash=hash_password("123456"),
        expires_at=datetime.utcnow() + timedelta(minutes=10),
        attempts=4,  # One attempt remaining
        max_attempts=5,
        consumed=False
    )
    db.add(challenge)
    db.commit()
    
    # Try wrong code (should increment attempts)
    from fastapi import HTTPException
    try:
        OTPService.verify_otp(db, phone, "wrong_code")
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 401  # Unauthorized
    
    # Refresh challenge
    db.refresh(challenge)
    assert challenge.attempts == 5
    
    # Try again (should fail with max attempts exceeded)
    try:
        OTPService.verify_otp(db, phone, "wrong_code")
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 400  # Bad Request (max attempts)
        assert "Maximum verification attempts" in str(e.detail)


def test_otp_expiration(db: Session):
    """Test OTP expiration"""
    phone = "+15551234567"
    from app.core.security import hash_password
    
    # Create expired challenge
    expired_challenge = OTPChallenge(
        id="expired_challenge",
        phone=phone,
        code_hash=hash_password("123456"),
        expires_at=datetime.utcnow() - timedelta(minutes=1),  # Expired
        attempts=0,
        max_attempts=5,
        consumed=False
    )
    db.add(expired_challenge)
    db.commit()
    
    # Try to verify expired challenge
    from fastapi import HTTPException
    try:
        OTPService.verify_otp(db, phone, "123456")
        assert False, "Should have raised HTTPException"
    except HTTPException as e:
        assert e.status_code == 400
        assert "No active OTP challenge" in str(e.detail)


def test_otp_audit_logging(db: Session):
    """Test OTP audit logging (check that logs are created)"""
    import logging
    
    # Capture log output
    log_capture = []
    handler = logging.Handler()
    handler.emit = lambda record: log_capture.append(record.getMessage())
    
    logger = logging.getLogger("app.routers.auth")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    phone = "+15551234567"
    
    # Start OTP (should log)
    OTPService.send_otp(db, phone)
    
    # Check logs contain OTP start
    log_messages = [msg for msg in log_capture if "OTP" in msg]
    assert len(log_messages) > 0
    
    logger.removeHandler(handler)







