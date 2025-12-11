"""
Token Encryption Service
Encrypts and decrypts sensitive tokens (e.g., Square access tokens) at rest.
Uses Fernet symmetric encryption from the cryptography library.
"""
import os
import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

from ..config import settings

logger = logging.getLogger(__name__)


class TokenDecryptionError(Exception):
    """Raised when token decryption fails"""
    pass


# Global Fernet instance (lazy-loaded)
_fernet_instance: Optional[Fernet] = None


def _get_encryption_key() -> bytes:
    """
    Get or generate encryption key from environment.
    
    In production, TOKEN_ENCRYPTION_KEY must be set.
    In dev, if missing, generates a key and logs a warning.
    
    Returns:
        bytes: Encryption key (32 bytes for Fernet)
        
    Raises:
        ValueError: In production if key is missing
    """
    key_str = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    
    if not key_str:
        # In production, this is a hard error
        is_prod = os.getenv("ENVIRONMENT", "").lower() in ("production", "prod")
        if is_prod:
            raise ValueError(
                "TOKEN_ENCRYPTION_KEY is required in production. "
                "Generate a key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            )
        
        # In dev, generate a key and warn
        logger.warning(
            "TOKEN_ENCRYPTION_KEY not set. Generating a temporary key for local development only. "
            "This key will change on restart. For persistent encryption, set TOKEN_ENCRYPTION_KEY in .env"
        )
        # Generate a key from a fixed salt for dev (not secure, but consistent for testing)
        # In production, use Fernet.generate_key() and store securely
        dev_key = Fernet.generate_key()
        logger.warning(f"Generated dev key (first 8 chars): {dev_key[:8].decode()}...")
        logger.warning("Set TOKEN_ENCRYPTION_KEY in .env to use a persistent key")
        return dev_key
    
    # Key should be base64-encoded Fernet key (44 chars)
    try:
        # Validate it's a valid Fernet key
        key_bytes = key_str.encode() if isinstance(key_str, str) else key_str
        # Fernet keys are 32 bytes base64-encoded (44 chars)
        if len(key_bytes) != 44:
            raise ValueError(f"TOKEN_ENCRYPTION_KEY must be 44 characters (base64-encoded 32-byte key), got {len(key_bytes)}")
        
        # Try to create a Fernet instance to validate the key
        Fernet(key_bytes)
        return key_bytes
    except Exception as e:
        raise ValueError(f"Invalid TOKEN_ENCRYPTION_KEY: {e}")


def get_fernet() -> Fernet:
    """
    Get or create Fernet instance for encryption/decryption.
    
    Returns:
        Fernet: Configured Fernet instance
    """
    global _fernet_instance
    
    if _fernet_instance is None:
        key = _get_encryption_key()
        _fernet_instance = Fernet(key)
    
    return _fernet_instance


def encrypt_token(raw: str) -> str:
    """
    Encrypt a token for storage at rest.
    
    Args:
        raw: Plain text token to encrypt
        
    Returns:
        str: Encrypted token (base64-encoded)
        
    Raises:
        ValueError: If encryption fails
    """
    if not raw:
        raise ValueError("Cannot encrypt empty token")
    
    try:
        fernet = get_fernet()
        encrypted_bytes = fernet.encrypt(raw.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Token encryption failed: {e}", exc_info=True)
        raise ValueError(f"Token encryption failed: {e}")


def decrypt_token(cipher: str) -> str:
    """
    Decrypt a token from storage.
    
    Args:
        cipher: Encrypted token (base64-encoded)
        
    Returns:
        str: Decrypted plain text token
        
    Raises:
        TokenDecryptionError: If decryption fails (invalid cipher, wrong key, etc.)
    """
    if not cipher:
        raise TokenDecryptionError("Cannot decrypt empty cipher")
    
    try:
        fernet = get_fernet()
        decrypted_bytes = fernet.decrypt(cipher.encode('utf-8'))
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"Token decryption failed: {e}", exc_info=True)
        raise TokenDecryptionError(f"Token decryption failed: {e}")

