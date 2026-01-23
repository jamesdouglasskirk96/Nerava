"""
Unit tests for Apple Wallet pass charging status field
"""
import pytest
import json
import zipfile
from io import BytesIO
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.domain import DriverWallet
from app.services.apple_wallet_pass import create_pkpass_bundle


def test_pass_includes_charging_status_when_detected(db: Session, test_user):
    """Test that pass.json includes charging status when charging_detected=true"""
    wallet = DriverWallet(
        user_id=test_user.id,
        nova_balance=1000,
        energy_reputation_score=0,
        charging_detected=True,
        charging_detected_at=datetime.utcnow()
    )
    db.add(wallet)
    db.commit()
    
    bundle_bytes, is_signed = create_pkpass_bundle(db, test_user.id)
    
    # Extract pass.json
    with zipfile.ZipFile(BytesIO(bundle_bytes), 'r') as zf:
        pass_json = json.loads(zf.read('pass.json'))
    
    # Check auxiliary fields for charging status
    store_card = pass_json.get("storeCard", {})
    auxiliary_fields = store_card.get("auxiliaryFields", [])
    
    # Should have charging status as first auxiliary field
    assert len(auxiliary_fields) > 0
    charging_field = auxiliary_fields[0]
    assert charging_field["key"] == "charging_status"
    assert charging_field["label"] == "Status"
    assert charging_field["value"] == "Charging detected"
    
    # Check back fields for charging status
    back_fields = store_card.get("backFields", [])
    charging_back_field = None
    for field in back_fields:
        if field.get("key") == "charging_status":
            charging_back_field = field
            break
    
    assert charging_back_field is not None
    assert charging_back_field["label"] == "Status"
    assert charging_back_field["value"] == "Charging detected"


def test_pass_includes_not_charging_status_when_false(db: Session, test_user):
    """Test that pass.json includes 'Not charging' when charging_detected=false"""
    wallet = DriverWallet(
        user_id=test_user.id,
        nova_balance=1000,
        energy_reputation_score=0,
        charging_detected=False
    )
    db.add(wallet)
    db.commit()
    
    bundle_bytes, is_signed = create_pkpass_bundle(db, test_user.id)
    
    # Extract pass.json
    with zipfile.ZipFile(BytesIO(bundle_bytes), 'r') as zf:
        pass_json = json.loads(zf.read('pass.json'))
    
    # Check back fields for 'Not charging' status
    store_card = pass_json.get("storeCard", {})
    back_fields = store_card.get("backFields", [])
    
    charging_back_field = None
    for field in back_fields:
        if field.get("key") == "charging_status":
            charging_back_field = field
            break
    
    assert charging_back_field is not None
    assert charging_back_field["label"] == "Status"
    assert charging_back_field["value"] == "Not charging"
    
    # Auxiliary fields should NOT have charging status (only when detected)
    auxiliary_fields = store_card.get("auxiliaryFields", [])
    has_charging_in_aux = any(f.get("key") == "charging_status" for f in auxiliary_fields)
    assert not has_charging_in_aux
