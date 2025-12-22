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


def _get_tier_from_score(score: int) -> str:
    """
    Compute tier from energy reputation score.
    
    Thresholds:
    - >= 850: Platinum
    - >= 650: Gold
    - >= 400: Silver
    - < 400: Bronze
    """
    if score >= 850:
        return "Platinum"
    elif score >= 650:
        return "Gold"
    elif score >= 400:
        return "Silver"
    else:
        return "Bronze"


def _get_pass_images_dir() -> Path:
    """Get directory for pass images"""
    # Try ui-mobile/assets/pass first, then ui-mobile/assets
    ui_mobile_pass_path = Path(__file__).parent.parent.parent.parent / "ui-mobile" / "assets" / "pass"
    if ui_mobile_pass_path.exists():
        return ui_mobile_pass_path
    
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
    
    Pass design spec:
    - Primary: NOVA BALANCE → $xx.xx
    - Secondary: NOVA → integer balance, TIER → tier name
    - Auxiliary: STATUS → "⚡ Charging" or "Not charging"
    - Colors: background #1e40af, foreground #ffffff, label rgba(255,255,255,0.7)
    - Back fields: Last 5 wallet events, deep links, support email
    """
    # Get recent timeline events for back fields
    timeline = get_wallet_timeline(db, driver_user_id, limit=5)
    
    # Format balance for primary field (dollars with 2 decimals)
    balance_dollars = wallet.nova_balance / 100.0
    balance_str = f"${balance_dollars:.2f}"
    
    # Get tier from energy reputation score
    tier = _get_tier_from_score(wallet.energy_reputation_score)
    
    # Nova integer balance (no division, already in smallest unit)
    nova_integer = wallet.nova_balance
    
    # Charging status
    charging_status = "⚡ Charging" if wallet.charging_detected else "Not charging"
    
    # Build secondary fields
    secondary_fields = [
        {
            "key": "nova",
            "label": "NOVA",
            "value": str(nova_integer)
        },
        {
            "key": "tier",
            "label": "TIER",
            "value": tier
        }
    ]
    
    # Build auxiliary field (status)
    auxiliary_fields = [
        {
            "key": "status",
            "label": "STATUS",
            "value": charging_status
        }
    ]

    # Build back fields
    base_url = getattr(settings, 'public_base_url', 'https://my.nerava.network').rstrip('/')
    support_email = os.getenv("NERAVA_SUPPORT_EMAIL", "support@nerava.network")
    
    back_fields = []
    
    # Add last 5 wallet events
    for i, event in enumerate(timeline[:5]):
        try:
            # created_at is ISO string from timeline service
            ts = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
            short_ts = ts.strftime("%m/%d %H:%M")
        except Exception:
            short_ts = event.get("created_at", "")[:16]

        sign = "+" if event["type"] == "EARNED" else "-"
        amount_str = f"{sign}${event['amount_cents'] / 100:.2f}"
        back_fields.append(
            {
                "key": f"event_{i+1}",
                "label": short_ts,
                "value": f"{amount_str} • {event['title'][:40]}",
            }
        )
    
    # Add deep links and support
    back_fields.extend([
        {
            "key": "open_app",
            "label": "Open Nerava App",
            "value": f"{base_url}/app/wallet/",
            "attributedValue": f"{base_url}/app/wallet/"
        },
        {
            "key": "find_merchants",
            "label": "Find Merchants",
            "value": f"{base_url}/app/explore/",
            "attributedValue": f"{base_url}/app/explore/"
        },
        {
            "key": "support",
            "label": "Support",
            "value": support_email,
            "attributedValue": f"mailto:{support_email}"
        }
    ])
    
    # Get webServiceURL and app launch URL from settings
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
        "foregroundColor": "#ffffff",
        "backgroundColor": "#1e40af",
        "labelColor": "rgba(255,255,255,0.7)",
        "storeCard": {
            "primaryFields": [
                {
                    "key": "balance",
                    "label": "NOVA BALANCE",
                    "value": balance_str
                }
            ],
            "secondaryFields": secondary_fields,
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
    
    Supports both P12 (preferred) and PEM cert/key formats.
    
    Returns signature bytes if signing succeeds, None if signing disabled/failed.
    """
    signing_enabled = os.getenv("APPLE_WALLET_SIGNING_ENABLED", "false").lower() == "true"
    
    if not signing_enabled:
        logger.debug("Apple Wallet signing disabled (APPLE_WALLET_SIGNING_ENABLED=false)")
        return None
    
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography import x509
        
        private_key = None
        
        # Try P12 first (preferred)
        p12_path = os.getenv("APPLE_WALLET_CERT_P12_PATH")
        p12_password = os.getenv("APPLE_WALLET_CERT_P12_PASSWORD", "")
        
        if p12_path and os.path.exists(p12_path):
            try:
                # Try cryptography's pkcs12 support (available in cryptography 2.5+)
                try:
                    from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
                    with open(p12_path, 'rb') as f:
                        p12_data = f.read()
                    password_bytes = p12_password.encode() if p12_password else None
                    private_key, cert, additional_certs = load_key_and_certificates(
                        p12_data,
                        password_bytes
                    )
                    logger.debug("Loaded P12 certificate for Apple Wallet signing")
                except ImportError:
                    # Fallback: try pyOpenSSL if available
                    try:
                        from OpenSSL import crypto
                        with open(p12_path, 'rb') as f:
                            p12_data = f.read()
                        p12 = crypto.load_pkcs12(p12_data, p12_password.encode() if p12_password else b'')
                        # Convert pyOpenSSL key to cryptography key
                        private_key_pem = crypto.dump_privatekey(crypto.FILETYPE_PEM, p12.get_privatekey())
                        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
                        cert_pem = crypto.dump_certificate(crypto.FILETYPE_PEM, p12.get_certificate())
                        cert = x509.load_pem_x509_certificate(cert_pem)
                        logger.debug("Loaded P12 certificate for Apple Wallet signing (via pyOpenSSL)")
                    except ImportError:
                        logger.warning("P12 support requires cryptography>=2.5 or pyOpenSSL, falling back to PEM")
                        private_key = None
            except Exception as e:
                logger.warning(f"Failed to load P12 certificate: {e}, falling back to PEM")
                private_key = None
        
        # Fallback to PEM cert/key
        if private_key is None:
            cert_path = os.getenv("APPLE_WALLET_CERT_PATH")
            key_path = os.getenv("APPLE_WALLET_KEY_PATH")
            key_password = os.getenv("APPLE_WALLET_KEY_PASSWORD", "")
            
            if not cert_path or not key_path:
                logger.debug("Apple Wallet signing certificates not configured")
                return None
            
            if not os.path.exists(cert_path) or not os.path.exists(key_path):
                logger.warning(f"Apple Wallet certificate/key files not found: cert={cert_path}, key={key_path}")
                return None
            
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
            
            logger.debug("Loaded PEM certificate/key for Apple Wallet signing")
        
        if private_key is None:
            logger.error("Failed to load private key for Apple Wallet signing")
            return None
        
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
        
    except ImportError:
        # pkcs12 might not be available, try without it
        logger.warning("pkcs12 module not available, P12 support disabled. Install with: pip install pyopenssl")
        # Fall back to PEM only
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
            
            manifest_json = json.dumps(manifest, sort_keys=True).encode('utf-8')
            signature = private_key.sign(
                manifest_json,
                padding.PKCS1v15(),
                hashes.SHA1()
            )
            
            logger.info("Apple Wallet pass signed successfully (PEM)")
            return signature
        except Exception as e:
            logger.error(f"Failed to sign Apple Wallet pass with PEM: {e}", exc_info=True)
            return None
        
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
    
    Raises:
        ValueError: If required assets are missing (with list of missing files)
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
    
    # Check for required images
    missing_assets = []
    
    # Try to find icon (29x29 or 58x58)
    icon_path = images_dir / "icon.png"
    icon_2x_path = images_dir / "icon@2x.png"
    if icon_path.exists():
        pass_files["icon.png"] = icon_path.read_bytes()
    elif icon_2x_path.exists():
        # Use @2x as fallback (Apple Wallet will scale)
        pass_files["icon.png"] = icon_2x_path.read_bytes()
    else:
        missing_assets.append("icon.png or icon@2x.png")
    
    # Try to find logo (160x50 or 320x100)
    logo_path = images_dir / "logo.png"
    logo_2x_path = images_dir / "logo@2x.png"
    if logo_path.exists():
        pass_files["logo.png"] = logo_path.read_bytes()
    elif logo_2x_path.exists():
        # Use @2x as fallback (Apple Wallet will scale)
        pass_files["logo.png"] = logo_2x_path.read_bytes()
    else:
        missing_assets.append("logo.png or logo@2x.png")
    
    # If assets are missing, raise error with list
    if missing_assets:
        raise ValueError(f"Missing required pass assets: {', '.join(missing_assets)}")
    
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
