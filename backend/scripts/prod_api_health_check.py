#!/usr/bin/env python3
"""Production API Health Check — validates credentials and connectivity for all external integrations.

Usage:
    python scripts/prod_api_health_check.py           # uses local env vars
    python scripts/prod_api_health_check.py --prod    # fetches secrets from AWS Secrets Manager
"""

import sys
import os
import json

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── AWS Secrets Manager loader ──────────────────────────────────────

# Mapping: AWS secret name → list of (env_var_name, json_key_or_None)
# json_key=None means the secret is a plain string, not JSON.
_SECRET_MAP = [
    ("nerava/backend/database",             [("DATABASE_URL", None)]),
    ("nerava/backend/stripe",               [
        ("STRIPE_SECRET_KEY", "secret_key"),
        ("STRIPE_WEBHOOK_SECRET", "webhook_secret"),
    ]),
    ("nerava/backend/twilio",               [
        ("TWILIO_ACCOUNT_SID", "account_sid"),
        ("TWILIO_AUTH_TOKEN", "auth_token"),
        ("TWILIO_VERIFY_SERVICE_SID", "verify_service_sid"),
    ]),
    ("nerava/backend/tesla",                [
        ("TESLA_CLIENT_ID", "client_id"),
        ("TESLA_CLIENT_SECRET", "client_secret"),
    ]),
    ("nerava/backend/smartcar",             [
        ("SMARTCAR_CLIENT_ID", "client_id"),
        ("SMARTCAR_CLIENT_SECRET", "client_secret"),
    ]),
    ("nerava/backend/google",               [
        ("GOOGLE_PLACES_API_KEY", "places_api_key"),
    ]),
    ("nerava/backend/posthog",              [("POSTHOG_KEY", None)]),
    ("nerava/backend/square",               [
        ("SQUARE_APPLICATION_ID_PRODUCTION", "application_id"),
        ("SQUARE_APPLICATION_SECRET_PRODUCTION", "application_secret"),
    ]),
]

# Plain env var overrides to simulate production config
_PROD_ENV_OVERRIDES = {
    "ENV": "prod",
    "SQUARE_ENV": "production",
    "SMARTCAR_ENABLED": "true",
}


def load_aws_secrets(region="us-east-1"):
    """Fetch production secrets from AWS Secrets Manager and inject into env vars."""
    try:
        import boto3
    except ImportError:
        print("  ERROR: boto3 is required for --prod. Install with: pip install boto3")
        sys.exit(1)

    client = boto3.client("secretsmanager", region_name=region)
    loaded = 0

    for secret_name, mappings in _SECRET_MAP:
        try:
            resp = client.get_secret_value(SecretId=secret_name)
            raw = resp["SecretString"]
        except client.exceptions.ResourceNotFoundException:
            print(f"  WARN: secret '{secret_name}' not found in Secrets Manager, skipping")
            continue
        except Exception as e:
            print(f"  WARN: could not read '{secret_name}': {e}")
            continue

        # Try to parse as JSON; fall back to plain string
        try:
            data = json.loads(raw)
            is_json = True
        except json.JSONDecodeError:
            # Some secrets have unescaped backslashes (e.g. \! in passwords).
            # Fix invalid JSON escape sequences by doubling lone backslashes.
            import re
            fixed = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw)
            try:
                data = json.loads(fixed)
                is_json = True
            except (json.JSONDecodeError, TypeError):
                data = raw
                is_json = False
        except TypeError:
            data = raw
            is_json = False

        for env_var, json_key in mappings:
            if json_key is None:
                # Plain string secret
                value = data if isinstance(data, str) else raw
            else:
                if not is_json:
                    print(f"  WARN: expected JSON for '{secret_name}' but got plain string")
                    continue
                value = data.get(json_key, "")
            if value:
                os.environ[env_var] = str(value)
                loaded += 1

    # Apply production env overrides
    for k, v in _PROD_ENV_OVERRIDES.items():
        os.environ[k] = v

    return loaded


# ── Load secrets before importing settings ──────────────────────────

_prod_mode = "--prod" in sys.argv

if _prod_mode:
    print()
    print("  Loading secrets from AWS Secrets Manager...")
    count = load_aws_secrets()
    print(f"  Loaded {count} secret values")
    print()

# Import settings AFTER env vars are set so Pydantic picks them up
from app.core.config import Settings
settings = Settings()


# ── Health check functions ──────────────────────────────────────────

def check_database():
    """Check database connectivity with SELECT 1."""
    db_url = settings.DATABASE_URL
    if not db_url:
        return False, "MISSING: DATABASE_URL"
    try:
        from sqlalchemy import create_engine, text
        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        engine = create_engine(db_url, connect_args=connect_args)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_type = "PostgreSQL" if "postgresql" in db_url else "SQLite" if "sqlite" in db_url else "database"
        return True, f"{db_type} connected, SELECT 1 OK"
    except Exception as e:
        return False, f"connection failed: {e}"


def check_stripe():
    """Check Stripe API by retrieving own account."""
    key = settings.STRIPE_SECRET_KEY
    if not key:
        return False, "MISSING: STRIPE_SECRET_KEY"
    try:
        import stripe
        stripe.api_key = key
        acct = stripe.Account.retrieve()
        acct_id = acct.get("id", "unknown")
        livemode = acct.get("livemode", "unknown")
        return True, f"account {acct_id}, livemode={livemode}"
    except Exception as e:
        return False, f"API error: {e}"


def check_twilio():
    """Check Twilio API by fetching account info."""
    sid = settings.TWILIO_ACCOUNT_SID
    token = settings.TWILIO_AUTH_TOKEN
    verify_sid = settings.TWILIO_VERIFY_SERVICE_SID
    missing = []
    if not sid:
        missing.append("TWILIO_ACCOUNT_SID")
    if not token:
        missing.append("TWILIO_AUTH_TOKEN")
    if not verify_sid:
        missing.append("TWILIO_VERIFY_SERVICE_SID")
    if missing:
        return False, f"MISSING: {', '.join(missing)}"
    try:
        from twilio.rest import Client
        client = Client(sid, token)
        account = client.api.accounts(sid).fetch()
        return True, f"account {sid[:8]}..., status={account.status}"
    except Exception as e:
        return False, f"API error: {e}"


def check_tesla():
    """Presence-only check for Tesla Fleet API credentials."""
    client_id = settings.TESLA_CLIENT_ID
    client_secret = settings.TESLA_CLIENT_SECRET
    missing = []
    if not client_id:
        missing.append("TESLA_CLIENT_ID")
    if not client_secret:
        missing.append("TESLA_CLIENT_SECRET")
    if missing:
        return False, f"MISSING: {', '.join(missing)}"
    return True, "credentials configured"


def check_smartcar():
    """Presence-only check for Smartcar credentials (skipped if disabled)."""
    if not settings.SMARTCAR_ENABLED:
        return None, "SMARTCAR_ENABLED=false"
    client_id = settings.SMARTCAR_CLIENT_ID
    client_secret = settings.SMARTCAR_CLIENT_SECRET
    missing = []
    if not client_id:
        missing.append("SMARTCAR_CLIENT_ID")
    if not client_secret:
        missing.append("SMARTCAR_CLIENT_SECRET")
    if missing:
        return False, f"MISSING: {', '.join(missing)}"
    return True, "credentials configured"


def check_google_places():
    """Check Google Places API with a minimal nearby search."""
    key = settings.GOOGLE_PLACES_API_KEY
    if not key:
        return False, "MISSING: GOOGLE_PLACES_API_KEY"
    try:
        import urllib.request
        # Use Places API (New) nearbySearch with known Austin lat/lng
        url = "https://places.googleapis.com/v1/places:searchNearby"
        body = json.dumps({
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": 30.2672, "longitude": -97.7431},
                    "radius": 500.0,
                }
            },
            "maxResultCount": 1,
        }).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": "places.displayName",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        count = len(data.get("places", []))
        return True, f"API returned {count} result(s)"
    except Exception as e:
        return False, f"API error: {e}"


def check_posthog():
    """Check PostHog connectivity by fetching project info."""
    key = os.getenv("POSTHOG_KEY") or os.getenv("POSTHOG_API_KEY", "")
    host = os.getenv("POSTHOG_HOST", "https://app.posthog.com")
    if not key:
        return False, "MISSING: POSTHOG_KEY"
    try:
        import urllib.request
        url = f"{host.rstrip('/')}/api/projects/@current"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {key}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        name = data.get("name", "unknown")
        return True, f"project '{name}' connected"
    except Exception as e:
        return False, f"API error: {e}"


def check_hubspot():
    """Check HubSpot API by reading one contact (skipped if disabled)."""
    if not settings.HUBSPOT_ENABLED:
        return None, "HUBSPOT_ENABLED=false"
    token = settings.HUBSPOT_PRIVATE_APP_TOKEN
    if not token:
        return False, "MISSING: HUBSPOT_PRIVATE_APP_TOKEN"
    try:
        import urllib.request
        url = "https://api.hubapi.com/crm/v3/objects/contacts?limit=1"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        total = data.get("total", 0)
        return True, f"API connected, {total} total contacts"
    except Exception as e:
        return False, f"API error: {e}"


def check_sentry():
    """Presence-only check for Sentry DSN."""
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        return False, "MISSING: SENTRY_DSN"
    return True, "DSN configured"


def check_redis():
    """Check Redis connectivity with PING (skipped if disabled)."""
    if not settings.REDIS_ENABLED:
        return None, "REDIS_ENABLED=false"
    url = settings.REDIS_URL
    if not url:
        return False, "MISSING: REDIS_URL"
    try:
        import redis
        r = redis.from_url(url, socket_timeout=5)
        result = r.ping()
        if result:
            return True, "PONG received"
        return False, "PING returned False"
    except Exception as e:
        return False, f"connection error: {e}"


def check_square():
    """Presence-only check for Square credentials (checks env-appropriate pair)."""
    square_env = os.getenv("SQUARE_ENV", "sandbox")
    if square_env == "production":
        app_id = os.getenv("SQUARE_APPLICATION_ID_PRODUCTION", "")
        app_secret = os.getenv("SQUARE_APPLICATION_SECRET_PRODUCTION", "")
        label = "PRODUCTION"
    else:
        app_id = os.getenv("SQUARE_APPLICATION_ID_SANDBOX", "")
        app_secret = os.getenv("SQUARE_APPLICATION_SECRET_SANDBOX", "")
        label = "SANDBOX"
    # Fall back to legacy env vars
    if not app_id:
        app_id = os.getenv("SQUARE_APPLICATION_ID", "")
    if not app_secret:
        app_secret = os.getenv("SQUARE_APPLICATION_SECRET", "")
    missing = []
    if not app_id or app_id == "REPLACE_ME":
        missing.append(f"SQUARE_APPLICATION_ID_{label}")
    if not app_secret or app_secret == "REPLACE_ME":
        missing.append(f"SQUARE_APPLICATION_SECRET_{label}")
    if missing:
        return False, f"MISSING: {', '.join(missing)}"
    return True, f"credentials configured (env={square_env})"


def check_apple_auth():
    """Check Apple Auth by fetching the public JWKS endpoint."""
    client_id = settings.APPLE_CLIENT_ID
    team_id = settings.APPLE_TEAM_ID
    missing = []
    if not client_id:
        missing.append("APPLE_CLIENT_ID")
    if not team_id:
        missing.append("APPLE_TEAM_ID")
    if missing:
        return False, f"MISSING: {', '.join(missing)}"
    try:
        import urllib.request
        url = "https://appleid.apple.com/auth/keys"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        keys = data.get("keys", [])
        return True, f"JWKS fetched, {len(keys)} keys"
    except Exception as e:
        return False, f"JWKS fetch failed: {e}"


# ── Main ────────────────────────────────────────────────────────────

def main():
    checks = [
        ("Database",       check_database),
        ("Stripe",         check_stripe),
        ("Twilio",         check_twilio),
        ("Tesla",          check_tesla),
        ("Smartcar",       check_smartcar),
        ("Google Places",  check_google_places),
        ("PostHog",        check_posthog),
        ("HubSpot",        check_hubspot),
        ("Sentry",         check_sentry),
        ("Redis",          check_redis),
        ("Square",         check_square),
        ("Apple Auth",     check_apple_auth),
    ]

    env = settings.ENV
    source = "AWS Secrets Manager" if _prod_mode else "local env"

    print()
    print("=" * 58)
    print("  Nerava Production API Health Check")
    print("=" * 58)
    print(f"  ENV: {env}  (source: {source})")
    print()

    results = []
    for name, fn in checks:
        try:
            passed, detail = fn()
        except Exception as e:
            passed, detail = False, f"unexpected error: {e}"
        results.append((name, passed, detail))

    passed_count = 0
    failed_count = 0
    skipped_count = 0

    for name, passed, detail in results:
        dots = "." * max(3, 22 - len(name))
        if passed is None:
            status = "SKIP   "
            skipped_count += 1
        elif passed:
            status = "SUCCESS"
            passed_count += 1
        else:
            status = "FAIL   "
            failed_count += 1
        print(f"  {name} {dots} {status}  ({detail})")

    print()
    print("=" * 58)
    parts = [f"{passed_count} passed"]
    if failed_count:
        parts.append(f"{failed_count} failed")
    if skipped_count:
        parts.append(f"{skipped_count} skipped")
    print(f"  Result: {', '.join(parts)}")
    print("=" * 58)
    print()

    sys.exit(1 if failed_count else 0)


if __name__ == "__main__":
    main()
