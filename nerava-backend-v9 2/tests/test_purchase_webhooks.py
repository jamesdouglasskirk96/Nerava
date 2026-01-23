"""
Tests for purchase webhook endpoints
P0-1: Purchase webhook replay protection
P0-4: Square webhook signature verification
"""
import pytest
import os
import json
import hmac
import hashlib
import base64
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main_simple import app

client = TestClient(app)


class TestPurchaseWebhookReplayProtection:
    """Test P0-1: Purchase webhook replay protection"""
    
    def test_reject_old_webhook_event(self):
        """Test that events older than 5 minutes are rejected"""
        # Create a webhook payload with timestamp 10 minutes ago
        old_timestamp = datetime.now(timezone.utc) - timedelta(minutes=10)
        
        payload = {
            "provider": "clo",
            "transaction_id": "test-txn-123",
            "user_id": 1,
            "amount_cents": 1000,
            "ts": old_timestamp.isoformat(),
            "merchant_ext_id": "merchant-123"
        }
        
        response = client.post(
            "/v1/webhooks/purchase",
            json=payload,
            headers={"X-Webhook-Secret": "test-secret"} if True else {}
        )
        
        # Should be rejected with 400
        assert response.status_code == 400
        assert "replay protection" in response.json()["detail"].lower() or "too old" in response.json()["detail"].lower()
    
    def test_accept_recent_webhook_event(self):
        """Test that events within 5 minutes are accepted"""
        # Create a webhook payload with timestamp 2 minutes ago
        recent_timestamp = datetime.now(timezone.utc) - timedelta(minutes=2)
        
        payload = {
            "provider": "clo",
            "transaction_id": "test-txn-456",
            "user_id": 1,
            "amount_cents": 1000,
            "ts": recent_timestamp.isoformat(),
            "merchant_ext_id": "merchant-456"
        }
        
        # Note: This test may fail if the endpoint requires authentication or other setup
        # We're testing the replay protection logic, not the full endpoint
        response = client.post(
            "/v1/webhooks/purchase",
            json=payload,
            headers={"X-Webhook-Secret": "test-secret"} if True else {}
        )
        
        # Should not be rejected due to replay protection (may fail for other reasons)
        # If it's 400 with "replay protection", that's a failure
        if response.status_code == 400:
            assert "replay protection" not in response.json()["detail"].lower()
            assert "too old" not in response.json()["detail"].lower()
    
    def test_handle_missing_timestamp_gracefully(self):
        """Test that missing timestamp is handled gracefully (defaults to now)"""
        payload = {
            "provider": "clo",
            "transaction_id": "test-txn-789",
            "user_id": 1,
            "amount_cents": 1000,
            # No ts field
            "merchant_ext_id": "merchant-789"
        }
        
        # Should not fail due to missing timestamp (normalize_event sets default)
        response = client.post(
            "/v1/webhooks/purchase",
            json=payload,
            headers={"X-Webhook-Secret": "test-secret"} if True else {}
        )
        
        # Should not be rejected due to replay protection
        if response.status_code == 400:
            assert "replay protection" not in response.json()["detail"].lower()
            assert "too old" not in response.json()["detail"].lower()


class TestSquareWebhookSignatureVerification:
    """Test P0-4: Square webhook signature verification"""
    
    def _generate_square_signature(self, body: bytes, secret: str) -> str:
        """Generate Square webhook signature for testing"""
        computed_hmac = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).digest()
        return base64.b64encode(computed_hmac).decode('utf-8')
    
    def test_valid_signature_accepted(self):
        """Test that valid Square signature is accepted"""
        secret = "test-signature-key-123"
        payload = {
            "provider": "square",
            "transaction_id": "test-txn-sig-valid",
            "user_id": 1,
            "amount_cents": 1000,
            "ts": datetime.now(timezone.utc).isoformat(),
            "merchant_ext_id": "merchant-sig-valid"
        }
        body = bytes(json.dumps(payload), 'utf-8')
        signature = self._generate_square_signature(body, secret)
        
        with patch.dict(os.environ, {"SQUARE_WEBHOOK_SIGNATURE_KEY": secret}):
            # Reload app to pick up new env var
            from importlib import reload
            import app.config
            reload(app.config)
            
            response = client.post(
                "/v1/webhooks/purchase",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Square-Signature": signature
                }
            )
            
            # Should not be rejected due to signature (may fail for other reasons like DB)
            assert response.status_code != 401
            if response.status_code == 401:
                assert "signature" not in response.json().get("detail", "").lower()
    
    def test_invalid_signature_rejected(self):
        """Test that invalid Square signature is rejected"""
        secret = "test-signature-key-123"
        payload = {
            "provider": "square",
            "transaction_id": "test-txn-sig-invalid",
            "user_id": 1,
            "amount_cents": 1000,
            "ts": datetime.now(timezone.utc).isoformat(),
            "merchant_ext_id": "merchant-sig-invalid"
        }
        body = bytes(json.dumps(payload), 'utf-8')
        invalid_signature = "invalid-signature-123"
        
        with patch.dict(os.environ, {"SQUARE_WEBHOOK_SIGNATURE_KEY": secret}):
            from importlib import reload
            import app.config
            reload(app.config)
            
            response = client.post(
                "/v1/webhooks/purchase",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Square-Signature": invalid_signature
                }
            )
            
            # Should be rejected with 401
            assert response.status_code == 401
            assert "signature" in response.json()["detail"].lower()
    
    def test_missing_signature_header_with_configured_key_fails(self):
        """Test that missing signature header fails when key is configured"""
        secret = "test-signature-key-123"
        payload = {
            "provider": "square",
            "transaction_id": "test-txn-sig-missing",
            "user_id": 1,
            "amount_cents": 1000,
            "ts": datetime.now(timezone.utc).isoformat(),
            "merchant_ext_id": "merchant-sig-missing"
        }
        body = bytes(json.dumps(payload), 'utf-8')
        
        with patch.dict(os.environ, {"SQUARE_WEBHOOK_SIGNATURE_KEY": secret}):
            from importlib import reload
            import app.config
            reload(app.config)
            
            response = client.post(
                "/v1/webhooks/purchase",
                content=body,
                headers={
                    "Content-Type": "application/json"
                    # No X-Square-Signature header
                }
            )
            
            # Should be rejected with 401
            assert response.status_code == 401
            assert "signature" in response.json()["detail"].lower() or "missing" in response.json()["detail"].lower()
    
    def test_missing_key_falls_back_to_secret_check(self):
        """Test that missing signature key falls back to secret check (backward compat)"""
        payload = {
            "provider": "square",
            "transaction_id": "test-txn-secret-fallback",
            "user_id": 1,
            "amount_cents": 1000,
            "ts": datetime.now(timezone.utc).isoformat(),
            "merchant_ext_id": "merchant-secret-fallback"
        }
        body = bytes(json.dumps(payload), 'utf-8')
        secret = "test-webhook-secret"
        
        with patch.dict(os.environ, {
            "SQUARE_WEBHOOK_SIGNATURE_KEY": "",  # Empty = not configured
            "WEBHOOK_SHARED_SECRET": secret
        }):
            from importlib import reload
            import app.config
            reload(app.config)
            
            response = client.post(
                "/v1/webhooks/purchase",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Secret": secret
                }
            )
            
            # Should not be rejected due to signature (falls back to secret check)
            # May fail for other reasons like DB, but not signature
            if response.status_code == 401:
                assert "signature" not in response.json().get("detail", "").lower()
    
    def test_replay_attempt_blocked_with_timestamp_tolerance(self):
        """Test that replay attempts are blocked by timestamp tolerance (already tested in P0-1)"""
        # This is already covered by TestPurchaseWebhookReplayProtection
        # But verify it works with signature verification too
        secret = "test-signature-key-123"
        old_timestamp = datetime.now(timezone.utc) - timedelta(minutes=10)
        payload = {
            "provider": "square",
            "transaction_id": "test-txn-replay",
            "user_id": 1,
            "amount_cents": 1000,
            "ts": old_timestamp.isoformat(),
            "merchant_ext_id": "merchant-replay"
        }
        body = bytes(json.dumps(payload), 'utf-8')
        signature = self._generate_square_signature(body, secret)
        
        with patch.dict(os.environ, {"SQUARE_WEBHOOK_SIGNATURE_KEY": secret}):
            from importlib import reload
            import app.config
            reload(app.config)
            
            response = client.post(
                "/v1/webhooks/purchase",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Square-Signature": signature
                }
            )
            
            # Should be rejected due to replay protection (400), not signature (401)
            assert response.status_code == 400
            assert "replay" in response.json()["detail"].lower() or "too old" in response.json()["detail"].lower()

