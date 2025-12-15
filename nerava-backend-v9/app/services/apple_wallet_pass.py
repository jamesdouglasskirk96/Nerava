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
from app.services.token_encryption import encrypt_token, decrypt_token, TokenDecryptionError

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


def _ensure_apple_auth_token(db: Session, wallet: DriverWallet) -> str:
    """
    Ensure the driver wallet has an Apple authentication token for PassKit web service.
    
    The token is:
    - Random, opaque (no PII)
    - Stored encrypted-at-rest via token_encryption
    - Used as the PassKit authenticationToken (header + pass.json)
    """
    # If already present, decrypt and return
    if wallet.apple_authentication_token:
        try:
            return decrypt_token(wallet.apple_authentication_token)
        except TokenDecryptionError:
            # If decryption fails (e.g., key rotation), generate a new token
            pass

    # Generate a new opaque token
    auth_token = secrets.token_urlsafe(24)
    wallet.apple_authentication_token = encrypt_token(auth_token)
    db.commit()
    db.refresh(wallet)
    return auth_token


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
    # Get recent timeline events for auxiliary fields / back fields
    timeline = get_wallet_timeline(db, driver_user_id, limit=5)
    
    # Format balance
    balance_dollars = wallet.nova_balance / 100.0
    balance_str = f"${balance_dollars:.2f}"
    
    # Build auxiliary fields from balance + quick summary amounts (up to 3)
    auxiliary_fields = []
    
    # Add charging status as first auxiliary field if charging detected
    if wallet.charging_detected:
        auxiliary_fields.append(
            {
                "key": "charging_status",
                "label": "Status",
                "value": "Charging detected",
            }
        )
    
    for i, event in enumerate(timeline[:3]):
        sign = "+" if event["type"] == "EARNED" else "-"
        label = f"{sign}${event['amount_cents'] / 100:.2f}"
        auxiliary_fields.append(
            {
                "key": f"event_{i+1}",
                "label": label,
                "value": event["title"][:30],  # Truncate if needed
            }
        )

    # Build back fields for deeper history (last 5 items) with short timestamps
    back_fields = [
        {
            "key": "about",
            "label": "About",
            "value": "Nerava rewards you for off-peak EV charging. Use Nova at participating merchants.",
        },
        {
            "key": "open_wallet",
            "label": "Open Wallet",
            "value": "/app/wallet/",
        },
        {
            "key": "scan_merchant_qr",
            "label": "Scan Merchant QR",
            "value": "/app/scan.html",
        },
        {
            "key": "where_to_spend",
            "label": "Where to Spend Nova",
            "value": "/app/spend.html",
        },
    ]
    
    # Add charging status to back fields (always visible, even if not charging)
    if wallet.charging_detected:
        back_fields.append(
            {
                "key": "charging_status",
                "label": "Status",
                "value": "Charging detected",
            }
        )
    else:
        back_fields.append(
            {
                "key": "charging_status",
                "label": "Status",
                "value": "Not charging",
            }
        )

    for i, event in enumerate(timeline[:5]):
        try:
            # created_at is ISO string from timeline service
            ts = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
            short_ts = ts.strftime("%m/%d %H:%M")
        except Exception:
            short_ts = event.get("created_at", "")[:16]

        label = short_ts
        sign = "+" if event["type"] == "EARNED" else "-"
        amount_str = f"{sign}${event['amount_cents'] / 100:.2f}"
        back_fields.append(
            {
                "key": f"timeline_{i+1}",
                "label": label,
                "value": f"{amount_str} • {event['title'][:40]}",
            }
        )
    
    # Get webServiceURL and app launch URL from settings
    base_url = getattr(settings, 'public_base_url', 'https://my.nerava.network').rstrip('/')
    web_service_url = f"{base_url}/v1/wallet/pass/apple"
    
    # Get pass token (opaque, for serial/barcode) and Apple auth token (for web service)
    pass_token = _ensure_wallet_pass_token(db, driver_user_id)
    auth_token = _ensure_apple_auth_token(db, wallet)
    
    pass_data = {
        "formatVersion": 1,
        "passTypeIdentifier": os.getenv("APPLE_WALLET_PASS_TYPE_ID", "pass.com.nerava.wallet"),
        # Serial must not contain PII; use opaque wallet_pass_token with stable prefix
        "serialNumber": f"nerava-{pass_token}",
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
            "backFields": back_fields,
        },
        "barcode": {
            "format": "PKBarcodeFormatQR",
            "message": pass_token,  # OPAQUE TOKEN - never driver_id or PII
            "messageEncoding": "iso-8859-1"
        },
        "webServiceURL": web_service_url,
        "authenticationToken": auth_token,  # For web service updates (separate from barcode token)
        "appLaunchURL": f"{base_url}/app/wallet/",
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
