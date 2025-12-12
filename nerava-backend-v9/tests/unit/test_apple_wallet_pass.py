"""
Unit tests for Apple Wallet pass generator
"""
import pytest
import json
import zipfile
from io import BytesIO
from sqlalchemy.orm import Session

from app.models.domain import DriverWallet
from app.services.apple_wallet_pass import create_pkpass_bundle, _ensure_wallet_pass_token
import uuid


def test_pkpass_bundle_non_empty(db: Session, test_user):
    """Test that pkpass bundle returns non-empty bytes"""
    wallet = DriverWallet(user_id=test_user.id, nova_balance=1000, energy_reputation_score=0)
    db.add(wallet)
    db.commit()
    
    bundle_bytes, is_signed = create_pkpass_bundle(db, test_user.id)
    
    assert len(bundle_bytes) > 0
    # Bundle should be a ZIP file
    assert bundle_bytes.startswith(b'PK')  # ZIP file signature


def test_pkpass_contains_pass_json(db: Session, test_user):
    """Test that pkpass bundle contains pass.json"""
    wallet = DriverWallet(user_id=test_user.id, nova_balance=1000, energy_reputation_score=0)
    db.add(wallet)
    db.commit()
    
    bundle_bytes, is_signed = create_pkpass_bundle(db, test_user.id)
    
    # Extract ZIP
    with zipfile.ZipFile(BytesIO(bundle_bytes), 'r') as zf:
        assert 'pass.json' in zf.namelist()
        
        # Read pass.json
        pass_json = json.loads(zf.read('pass.json'))
        
        # Verify structure
        assert 'barcode' in pass_json
        assert 'message' in pass_json['barcode']
        
        # Verify barcode message is opaque token (not driver_id)
        barcode_message = pass_json['barcode']['message']
        assert str(test_user.id) not in barcode_message
        assert len(barcode_message) > 20  # Should be a long token


def test_pkpass_no_driver_id_in_pass_json(db: Session, test_user):
    """Test that pass.json does not contain raw driver_id"""
    wallet = DriverWallet(user_id=test_user.id, nova_balance=1000, energy_reputation_score=0)
    db.add(wallet)
    db.commit()
    
    bundle_bytes, is_signed = create_pkpass_bundle(db, test_user.id)
    
    # Extract and check pass.json
    with zipfile.ZipFile(BytesIO(bundle_bytes), 'r') as zf:
        pass_json_str = zf.read('pass.json').decode('utf-8')
        
        # Verify driver_id is not in the JSON
        assert str(test_user.id) not in pass_json_str


def test_pkpass_signing_disabled_returns_unsigned(db: Session, test_user, monkeypatch):
    """Test that when signing is disabled, is_signed=False"""
    wallet = DriverWallet(user_id=test_user.id, nova_balance=1000, energy_reputation_score=0)
    db.add(wallet)
    db.commit()
    
    # Disable signing
    monkeypatch.setenv("APPLE_WALLET_SIGNING_ENABLED", "false")
    
    bundle_bytes, is_signed = create_pkpass_bundle(db, test_user.id)
    
    # Should still return bundle, but unsigned
    assert len(bundle_bytes) > 0
    assert is_signed == False
    
    # Bundle should still be valid ZIP
    with zipfile.ZipFile(BytesIO(bundle_bytes), 'r') as zf:
        assert 'pass.json' in zf.namelist()
        assert 'manifest.json' in zf.namelist()
        # signature should not be present when unsigned
        assert 'signature' not in zf.namelist()


def test_ensure_wallet_pass_token_creates_token(db: Session, test_user):
    """Test that _ensure_wallet_pass_token creates token if missing"""
    wallet = DriverWallet(user_id=test_user.id, nova_balance=1000, energy_reputation_score=0)
    db.add(wallet)
    db.commit()
    
    token = _ensure_wallet_pass_token(db, test_user.id)
    
    assert token is not None
    assert len(token) > 20  # Should be a long opaque token
    assert str(test_user.id) not in token  # Should not contain driver_id
    
    # Token should be saved
    db.refresh(wallet)
    assert wallet.wallet_pass_token == token
