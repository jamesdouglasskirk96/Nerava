"""
Tests for token encryption service
"""
import pytest
import os
from app.services.token_encryption import (
    encrypt_token,
    decrypt_token,
    TokenDecryptionError
)


def test_encrypt_decrypt_roundtrip():
    """Test that encrypting and decrypting a token returns the original value"""
    # Set a test encryption key
    test_key = "test_key_32_bytes_long_for_fernet_encryption_test"
    # Fernet keys must be base64-encoded 32-byte keys (44 chars)
    import base64
    from cryptography.fernet import Fernet
    key_bytes = test_key[:32].encode()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    os.environ["TOKEN_ENCRYPTION_KEY"] = fernet_key.decode()
    
    original_token = "sq_test_token_12345"
    
    encrypted = encrypt_token(original_token)
    assert encrypted != original_token, "Encrypted token should be different from original"
    assert len(encrypted) > len(original_token), "Encrypted token should be longer"
    
    decrypted = decrypt_token(encrypted)
    assert decrypted == original_token, "Decrypted token should match original"


def test_encrypt_empty_token_raises_error():
    """Test that encrypting an empty token raises ValueError"""
    with pytest.raises(ValueError, match="Cannot encrypt empty token"):
        encrypt_token("")


def test_decrypt_invalid_cipher_raises_error():
    """Test that decrypting an invalid cipher raises TokenDecryptionError"""
    with pytest.raises(TokenDecryptionError):
        decrypt_token("invalid_cipher_text")


def test_decrypt_empty_cipher_raises_error():
    """Test that decrypting an empty cipher raises TokenDecryptionError"""
    with pytest.raises(TokenDecryptionError, match="Cannot decrypt empty cipher"):
        decrypt_token("")


def test_decrypt_wrong_key_raises_error():
    """Test that decrypting with a different key raises TokenDecryptionError"""
    # Set first key
    test_key1 = "test_key_32_bytes_long_for_fernet_encryption_test"
    import base64
    key_bytes1 = test_key1[:32].encode()
    fernet_key1 = base64.urlsafe_b64encode(key_bytes1)
    os.environ["TOKEN_ENCRYPTION_KEY"] = fernet_key1.decode()
    
    original_token = "sq_test_token_12345"
    encrypted = encrypt_token(original_token)
    
    # Change to different key
    test_key2 = "different_key_32_bytes_long_for_fernet_test"
    key_bytes2 = test_key2[:32].encode()
    fernet_key2 = base64.urlsafe_b64encode(key_bytes2)
    os.environ["TOKEN_ENCRYPTION_KEY"] = fernet_key2.decode()
    
    # Try to decrypt with different key - should fail
    with pytest.raises(TokenDecryptionError):
        decrypt_token(encrypted)

