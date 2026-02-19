"""
Tests for merchant acquisition funnel endpoints.

Covers:
- HMAC signature sign/verify round-trip
- Expired signature rejection
- Tampered merchant_id rejection
- Resolve idempotency (same place_id -> same merchant_id)
"""
import time
import pytest

from app.routers.merchant_funnel import sign_preview, verify_signature


# ---------------------------------------------------------------------------
# Signature tests
# ---------------------------------------------------------------------------

class TestSignature:
    def test_sign_verify_round_trip(self):
        merchant_id = "m_test123"
        expires_at = int(time.time()) + 3600  # 1 hour from now
        sig = sign_preview(merchant_id, expires_at)
        assert verify_signature(merchant_id, expires_at, sig) is True

    def test_expired_signature_rejected(self):
        merchant_id = "m_test123"
        expires_at = int(time.time()) - 1  # Already expired
        sig = sign_preview(merchant_id, expires_at)
        assert verify_signature(merchant_id, expires_at, sig) is False

    def test_tampered_merchant_id_rejected(self):
        merchant_id = "m_test123"
        expires_at = int(time.time()) + 3600
        sig = sign_preview(merchant_id, expires_at)
        assert verify_signature("m_tampered", expires_at, sig) is False

    def test_tampered_expires_at_rejected(self):
        merchant_id = "m_test123"
        expires_at = int(time.time()) + 3600
        sig = sign_preview(merchant_id, expires_at)
        assert verify_signature(merchant_id, expires_at + 1000, sig) is False

    def test_wrong_signature_rejected(self):
        merchant_id = "m_test123"
        expires_at = int(time.time()) + 3600
        assert verify_signature(merchant_id, expires_at, "deadbeef") is False


# ---------------------------------------------------------------------------
# Resolve idempotency test (requires DB fixtures via conftest)
# ---------------------------------------------------------------------------

@pytest.fixture
def resolve_payload():
    return {
        "place_id": "ChIJ_test_funnel_123",
        "name": "Test Funnel Business",
        "lat": 30.2672,
        "lng": -97.7431,
    }


def test_resolve_idempotent(client, db, resolve_payload):
    """Same place_id called twice -> same merchant_id, one DB row."""
    resp1 = client.post("/v1/merchant/funnel/resolve", json=resolve_payload)
    assert resp1.status_code == 200
    data1 = resp1.json()
    merchant_id_1 = data1["merchant_id"]

    resp2 = client.post("/v1/merchant/funnel/resolve", json=resolve_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    merchant_id_2 = data2["merchant_id"]

    assert merchant_id_1 == merchant_id_2

    # Verify only one row in DB
    from app.models.while_you_charge import Merchant
    count = db.query(Merchant).filter(Merchant.place_id == resolve_payload["place_id"]).count()
    assert count == 1


def test_preview_invalid_sig(client):
    """Tampered sig returns 403."""
    resp = client.get("/v1/merchant/funnel/preview", params={
        "merchant_id": "m_doesnotexist",
        "exp": int(time.time()) + 3600,
        "sig": "invalidsig",
    })
    assert resp.status_code == 403


def test_preview_expired(client):
    """Expired link returns 403."""
    merchant_id = "m_expired_test"
    expires_at = int(time.time()) - 10
    sig = sign_preview(merchant_id, expires_at)
    resp = client.get("/v1/merchant/funnel/preview", params={
        "merchant_id": merchant_id,
        "exp": expires_at,
        "sig": sig,
    })
    assert resp.status_code == 403


def test_search_returns_results(client):
    """Search endpoint returns 200 (results depend on API key)."""
    resp = client.get("/v1/merchant/funnel/search", params={"q": "coffee"})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert isinstance(data["results"], list)
