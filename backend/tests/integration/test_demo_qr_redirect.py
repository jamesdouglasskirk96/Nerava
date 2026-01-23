"""
Integration tests for demo QR redirect.
"""
import os


def test_demo_qr_redirect_enabled(client, monkeypatch):
    """When DEMO_QR_ENABLED=true and token set, /qr/eggman-demo-checkout redirects to checkout UI."""
    monkeypatch.setenv("DEMO_QR_ENABLED", "true")
    monkeypatch.setenv("DEMO_EGGMAN_QR_TOKEN", "demo-token-123")

    resp = client.get("/qr/eggman-demo-checkout", allow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["location"].endswith("/app/checkout.html?token=demo-token-123")


def test_demo_qr_redirect_disabled(client, monkeypatch):
    """When DEMO_QR_ENABLED!=true, endpoint returns 404."""
    monkeypatch.setenv("DEMO_QR_ENABLED", "false")
    monkeypatch.delenv("DEMO_EGGMAN_QR_TOKEN", raising=False)

    resp = client.get("/qr/eggman-demo-checkout")

    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "DEMO_QR_DISABLED"


def test_demo_qr_redirect_missing_token(client, monkeypatch):
    """When token missing, endpoint returns 404 with structured error."""
    monkeypatch.setenv("DEMO_QR_ENABLED", "true")
    monkeypatch.delenv("DEMO_EGGMAN_QR_TOKEN", raising=False)

    resp = client.get("/qr/eggman-demo-checkout")

    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "DEMO_QR_TOKEN_MISSING"










