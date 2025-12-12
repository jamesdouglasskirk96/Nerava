"""
Apple Wallet Pass Generator

Generates .pkpass bundles for Apple Wallet with optional signing.
"""
import os
import json
import hashlib
import zipfile
import secrets
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime
from io import BytesIO
import logging

from sqlalchemy.orm import Session

from app.models.domain import DriverWallet
from app.config import settings
from app.services.wallet_timeline import get_wallet_timeline

logger = logging.getLogger(__name__)


def _ensure_wallet_pass_token(db: Session, driver_user_id: int) -> str:
    """
    Ensure driver has a wallet_pass_token, creating one if missing.
    
    Returns the token (opaque, random).
    """
    wallet = db.query(DriverWallet).filter(DriverWallet.user_id == driver_user_id).first()
    
    if not wallet:
        wallet = DriverWallet(
            user_id=driver_user_id,
            nova_balance=0,
            energy_reputation_score=0
        )
        db.add(wallet)
        db.flush()
    
    if not wallet.wallet_pass_token:
        # Generate random opaque token (24 bytes = 32 chars in base64)
        token = secrets.token_urlsafe(24)
        # Ensure uniqueness (very unlikely collision, but check anyway)
        existing = db.query(DriverWallet).filter(DriverWallet.wallet_pass_token == token).first()
        if existing:
            token = secrets.token_urlsafe(24)  # Regenerate if collision
        
        wallet.wallet_pass_token = token
        db.commit()
        db.refresh(wallet)
    
    return wallet.wallet_pass_token


def _get_pass_images_dir() -> Path:
    """Get directory for pass images"""
    # Try ui-mobile/assets first, fallback to a default location
    ui_mobile_path = Path(__file__).parent.parent.parent.parent / "ui-mobile" / "assets"
    if ui_mobile_path.exists():
        return ui_mobile_path
    
    # Fallback: create a pass directory in static
    static_path = Path(__file__).parent.parent / "static" / "pass"
    static_path.mkdir(parents=True, exist_ok=True)
    return static_path


def _create_pass_json(db: Session, driver_user_id: int, wallet: DriverWallet) -> dict:
    """
    Create pass.json structure for Apple Wallet.
    
    Uses wallet_pass_token (opaque) in barcode, never driver_id or PII.
    """
    # Get recent timeline events for auxiliary fields
    timeline = get_wallet_timeline(db, driver_user_id, limit=3)
    
    # Format balance
    balance_dollars = wallet.nova_balance / 100.0
    balance_str = f"${balance_dollars:.2f}"
    
    # Build auxiliary fields from timeline
    auxiliary_fields = []
    for i, event in enumerate(timeline[:3]):
        if event["type"] == "EARNED":
            label = f"+${event['amount_cents'] / 100:.2f}"
        else:
            label = f"-${event['amount_cents'] / 100:.2f}"
        auxiliary_fields.append({
            "key": f"event_{i+1}",
            "label": label,
            "value": event["title"][:30]  # Truncate if needed
        })
    
    # Get webServiceURL from settings
    base_url = getattr(settings, 'public_base_url', 'https://my.nerava.network').rstrip('/')
    web_service_url = f"{base_url}/v1/wallet/pass/apple"
    
    # Get pass token (opaque)
    pass_token = _ensure_wallet_pass_token(db, driver_user_id)
    
    pass_data = {
        "formatVersion": 1,
        "passTypeIdentifier": os.getenv("APPLE_WALLET_PASS_TYPE_ID", "pass.com.nerava.wallet"),
        "serialNumber": f"nerava-{driver_user_id}",
        "teamIdentifier": os.getenv("APPLE_WALLET_TEAM_ID", ""),
        "organizationName": "Nerava",
        "description": "Nerava Wallet - Off-Peak Charging Rewards",
        "logoText": "Nerava",
        "foregroundColor": "rgb(255, 255, 255)",
        "backgroundColor": "rgb(30, 64, 175)",
        "storeCard": {
            "primaryFields": [
                {
                    "key": "balance",
                    "label": "Balance",
                    "value": balance_str
                }
            ],
            "auxiliaryFields": auxiliary_fields,
            "backFields": [
                {
                    "key": "description",
                    "label": "About",
                    "value": "Nerava rewards you for off-peak EV charging. Use Nova at participating merchants."
                }
            ]
        },
        "barcode": {
            "format": "PKBarcodeFormatQR",
            "message": pass_token,  # OPAQUE TOKEN - never driver_id or PII
            "messageEncoding": "iso-8859-1"
        },
        "webServiceURL": web_service_url,
        "authenticationToken": pass_token,  # For web service updates
        "relevantDate": datetime.utcnow().isoformat() + "Z"
    }
    
    return pass_data


def _create_manifest(pass_files: dict) -> dict:
    """
    Create manifest.json with SHA1 hashes of all files.
    
    Args:
        pass_files: Dict of filename -> bytes content
    """
    manifest = {}
    for filename, content in pass_files.items():
        sha1 = hashlib.sha1(content).hexdigest()
        manifest[filename] = sha1
    return manifest


def _sign_pkpass(pass_files: dict, manifest: dict) -> Optional[bytes]:
    """
    Sign the pkpass bundle using Apple certificates.
    
    Returns signature bytes if signing succeeds, None if signing disabled/failed.
    """
    signing_enabled = os.getenv("APPLE_WALLET_SIGNING_ENABLED", "false").lower() == "true"
    
    if not signing_enabled:
        logger.debug("Apple Wallet signing disabled (APPLE_WALLET_SIGNING_ENABLED=false)")
        return None
    
    cert_path = os.getenv("APPLE_WALLET_CERT_PATH")
    key_path = os.getenv("APPLE_WALLET_KEY_PATH")
    key_password = os.getenv("APPLE_WALLET_KEY_PASSWORD", "")
    
    if not cert_path or not key_path:
        logger.debug("Apple Wallet signing certificates not configured")
        return None
    
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logger.warning(f"Apple Wallet certificate/key files not found: cert={cert_path}, key={key_path}")
        return None
    
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography import x509
        
        # Load certificate and key
        with open(cert_path, 'rb') as f:
            cert = x509.load_pem_x509_certificate(f.read())
        
        with open(key_path, 'rb') as f:
            key_data = f.read()
            if key_password:
                private_key = serialization.load_pem_private_key(
                    key_data,
                    password=key_password.encode() if isinstance(key_password, str) else key_password,
                )
            else:
                private_key = serialization.load_pem_private_key(key_data, password=None)
        
        # Create manifest JSON string
        manifest_json = json.dumps(manifest, sort_keys=True).encode('utf-8')
        
        # Sign manifest
        signature = private_key.sign(
            manifest_json,
            padding.PKCS1v15(),
            hashes.SHA1()
        )
        
        logger.info("Apple Wallet pass signed successfully")
        return signature
        
    except Exception as e:
        logger.error(f"Failed to sign Apple Wallet pass: {e}", exc_info=True)
        return None


def create_pkpass_bundle(db: Session, driver_user_id: int) -> Tuple[bytes, bool]:
    """
    Create a .pkpass bundle for Apple Wallet.
    
    Args:
        db: Database session
        driver_user_id: Driver user ID
        
    Returns:
        Tuple of (bundle_bytes, is_signed)
        - bundle_bytes: The .pkpass file as bytes
        - is_signed: True if bundle is signed, False if unsigned (preview)
    """
    wallet = db.query(DriverWallet).filter(DriverWallet.user_id == driver_user_id).first()
    if not wallet:
        wallet = DriverWallet(
            user_id=driver_user_id,
            nova_balance=0,
            energy_reputation_score=0
        )
        db.add(wallet)
        db.flush()
    
    # Create pass.json
    pass_data = _create_pass_json(db, driver_user_id, wallet)
    pass_json = json.dumps(pass_data, indent=2).encode('utf-8')
    
    # Get images directory
    images_dir = _get_pass_images_dir()
    
    # Collect pass files
    pass_files = {
        "pass.json": pass_json
    }
    
    # Add images if available (Apple Wallet requires specific sizes)
    # Logo: 160x50 (or up to 320x100 for @2x)
    logo_path = images_dir / "icon-192.png"
    if logo_path.exists():
        pass_files["logo.png"] = logo_path.read_bytes()
    
    # Icon: 29x29 (or up to 58x58 for @2x)
    icon_path = images_dir / "icon-192.png"
    if icon_path.exists():
        pass_files["icon.png"] = icon_path.read_bytes()
    
    # Create manifest
    manifest = _create_manifest(pass_files)
    manifest_json = json.dumps(manifest, sort_keys=True).encode('utf-8')
    pass_files["manifest.json"] = manifest_json
    
    # Sign the pass
    signature = _sign_pkpass(pass_files, manifest)
    is_signed = signature is not None
    
    if signature:
        pass_files["signature"] = signature
    
    # Create .pkpass bundle (ZIP file)
    bundle = BytesIO()
    with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename, content in pass_files.items():
            zf.writestr(filename, content)
    
    bundle.seek(0)
    bundle_bytes = bundle.read()
    
    logger.info(f"Created Apple Wallet pass bundle for driver {driver_user_id} (signed={is_signed}, size={len(bundle_bytes)} bytes)")
    
    return bundle_bytes, is_signed


def refresh_pkpass_bundle(db: Session, driver_user_id: int) -> Tuple[bytes, bool]:
    """
    Refresh an existing .pkpass bundle (same as create, but updates timestamp).
    
    This is an alias for create_pkpass_bundle for now.
    """
    return create_pkpass_bundle(db, driver_user_id)
