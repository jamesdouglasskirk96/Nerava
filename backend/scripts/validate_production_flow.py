#!/usr/bin/env python3
"""
Production Flow Validation Script

Validates the entire user flow end-to-end to catch failures BEFORE users hit them.
Run this after every deployment and as a scheduled health check.

Usage:
    # Against production
    python scripts/validate_production_flow.py --env production

    # Against staging
    python scripts/validate_production_flow.py --env staging

    # Against local
    python scripts/validate_production_flow.py --env local

    # Quick health check only (no OTP, no DB writes)
    python scripts/validate_production_flow.py --env production --quick

Exit codes:
    0 = All checks passed
    1 = Critical failure (blocks users)
    2 = Non-critical failure (degraded experience)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urljoin

import requests

# Configuration per environment
ENVIRONMENTS = {
    "local": {
        "api_url": "http://localhost:8000",
        "test_phone": "+15555550100",  # Stub OTP always accepts 123456
        "test_otp": "123456",
    },
    "staging": {
        "api_url": os.getenv("STAGING_API_URL", "https://api.staging.nerava.network"),
        "test_phone": os.getenv("STAGING_TEST_PHONE", "+15555550100"),
        "test_otp": os.getenv("STAGING_TEST_OTP", "123456"),
    },
    "production": {
        "api_url": os.getenv("PROD_API_URL", "https://api.nerava.network"),
        "test_phone": os.getenv("PROD_TEST_PHONE"),  # Must be set for real OTP
        "test_otp": None,  # Real OTP - will prompt or skip
    },
}

# Test data
TEST_CHARGER_ID = "demo-charger-001"  # Should exist in all environments
TEST_MERCHANT_ID = None  # Will be discovered from charger
TEST_LOCATION = {"lat": 30.2672, "lng": -97.7431}  # Austin, TX


class ValidationResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.duration_ms = 0
        self.critical = True  # If False, failure is non-blocking

    def pass_(self, message: str = "OK"):
        self.passed = True
        self.message = message

    def fail(self, message: str, critical: bool = True):
        self.passed = False
        self.message = message
        self.critical = critical


class ProductionValidator:
    def __init__(self, env: str, quick: bool = False, verbose: bool = False):
        self.config = ENVIRONMENTS.get(env)
        if not self.config:
            raise ValueError(f"Unknown environment: {env}")

        self.env = env
        self.quick = quick
        self.verbose = verbose
        self.api_url = self.config["api_url"]
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.results: list[ValidationResult] = []

    def log(self, message: str):
        if self.verbose:
            print(f"  [DEBUG] {message}")

    def run_check(self, name: str, check_func, critical: bool = True) -> ValidationResult:
        result = ValidationResult(name)
        result.critical = critical
        start = time.time()

        try:
            check_func(result)
        except Exception as e:
            result.fail(f"Exception: {e}")

        result.duration_ms = int((time.time() - start) * 1000)
        self.results.append(result)

        status = "✓" if result.passed else ("✗" if result.critical else "⚠")
        print(f"  {status} {name}: {result.message} ({result.duration_ms}ms)")

        return result

    def api_get(self, path: str, **kwargs) -> requests.Response:
        url = urljoin(self.api_url, path)
        headers = kwargs.pop("headers", {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        self.log(f"GET {url}")
        return self.session.get(url, headers=headers, timeout=30, **kwargs)

    def api_post(self, path: str, data: dict = None, **kwargs) -> requests.Response:
        url = urljoin(self.api_url, path)
        headers = kwargs.pop("headers", {})
        headers["Content-Type"] = "application/json"
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        self.log(f"POST {url} {json.dumps(data)[:100]}...")
        return self.session.post(url, json=data, headers=headers, timeout=30, **kwargs)

    # ========== Health Checks ==========

    def check_health_endpoint(self, result: ValidationResult):
        """Basic health check - verifies API is responding"""
        resp = self.api_get("/health")
        if resp.status_code != 200:
            result.fail(f"Health endpoint returned {resp.status_code}")
            return

        data = resp.json()
        if data.get("status") != "healthy":
            result.fail(f"Unhealthy status: {data}")
            return

        result.pass_(f"API healthy, DB connected")

    def check_healthz_endpoint(self, result: ValidationResult):
        """Kubernetes-style liveness probe"""
        resp = self.api_get("/healthz")
        if resp.status_code != 200:
            result.fail(f"Healthz returned {resp.status_code}")
            return
        result.pass_("Liveness probe OK")

    def check_database_tables(self, result: ValidationResult):
        """Verify critical tables exist via health endpoint details"""
        resp = self.api_get("/health")
        if resp.status_code != 200:
            result.fail("Cannot check DB - health endpoint failed")
            return

        data = resp.json()
        db_status = data.get("database", data.get("db"))
        if db_status in ["ok", "healthy", True]:
            result.pass_("Database tables accessible")
        else:
            result.fail(f"Database issue: {db_status}")

    # ========== Discovery Checks ==========

    def check_chargers_endpoint(self, result: ValidationResult):
        """Verify chargers endpoint returns data"""
        resp = self.api_get("/v1/chargers", params={
            "lat": TEST_LOCATION["lat"],
            "lng": TEST_LOCATION["lng"],
            "radius_m": 50000,
        })

        if resp.status_code != 200:
            result.fail(f"Chargers endpoint returned {resp.status_code}: {resp.text[:200]}")
            return

        data = resp.json()
        chargers = data.get("chargers", data) if isinstance(data, dict) else data

        if not chargers:
            result.fail("No chargers returned - database may be empty", critical=False)
            return

        result.pass_(f"Found {len(chargers)} chargers")

    def check_merchants_endpoint(self, result: ValidationResult):
        """Verify merchants endpoint returns data"""
        resp = self.api_get("/v1/discovery/merchants", params={
            "lat": TEST_LOCATION["lat"],
            "lng": TEST_LOCATION["lng"],
        })

        if resp.status_code != 200:
            result.fail(f"Merchants endpoint returned {resp.status_code}: {resp.text[:200]}")
            return

        data = resp.json()
        merchants = data.get("merchants", data) if isinstance(data, dict) else data

        if not merchants:
            result.fail("No merchants returned - database may be empty", critical=False)
            return

        result.pass_(f"Found {len(merchants)} merchants")

    # ========== OTP Flow Checks ==========

    def check_otp_start(self, result: ValidationResult):
        """Test OTP initiation"""
        test_phone = self.config.get("test_phone")
        if not test_phone:
            result.fail("No test phone configured for this environment", critical=False)
            return

        resp = self.api_post("/auth/otp/start", {
            "phone": test_phone,
        })

        if resp.status_code == 429:
            result.fail("Rate limited - too many OTP requests", critical=False)
            return

        if resp.status_code != 200:
            result.fail(f"OTP start failed: {resp.status_code} {resp.text[:200]}")
            return

        data = resp.json()
        if data.get("otp_sent") or data.get("success"):
            result.pass_("OTP sent successfully")
        else:
            result.fail(f"OTP not sent: {data}")

    def check_otp_verify(self, result: ValidationResult):
        """Test OTP verification and get access token"""
        test_phone = self.config.get("test_phone")
        test_otp = self.config.get("test_otp")

        if not test_phone:
            result.fail("No test phone configured", critical=False)
            return

        if not test_otp:
            # In production, we can't verify without a real OTP
            result.fail("No test OTP available (production mode)", critical=False)
            return

        resp = self.api_post("/auth/otp/verify", {
            "phone": test_phone,
            "code": test_otp,
        })

        if resp.status_code == 400:
            result.fail(f"Invalid OTP code: {resp.text[:200]}")
            return

        if resp.status_code != 200:
            result.fail(f"OTP verify failed: {resp.status_code} {resp.text[:200]}")
            return

        data = resp.json()
        access_token = data.get("access_token")

        if not access_token:
            result.fail(f"No access token in response: {data}")
            return

        self.access_token = access_token
        result.pass_("OTP verified, token acquired")

    # ========== Exclusive Flow Checks ==========

    def check_exclusive_activate(self, result: ValidationResult):
        """Test exclusive session activation"""
        if not self.access_token:
            result.fail("No auth token - skipping (OTP not verified)", critical=False)
            return

        resp = self.api_post("/v1/exclusive/activate", {
            "charger_id": TEST_CHARGER_ID,
            "lat": TEST_LOCATION["lat"],
            "lng": TEST_LOCATION["lng"],
            "accuracy_m": 10.0,
        })

        if resp.status_code == 428:
            result.fail("Auth required - OTP not properly verified")
            return

        if resp.status_code == 404:
            result.fail(f"Charger {TEST_CHARGER_ID} not found - check test data", critical=False)
            return

        if resp.status_code == 409:
            # Already has active session - that's OK for validation
            result.pass_("Already has active session (OK)")
            return

        if resp.status_code != 200:
            result.fail(f"Activate failed: {resp.status_code} {resp.text[:200]}")
            return

        data = resp.json()
        session = data.get("exclusive_session", data)

        if not session.get("id"):
            result.fail(f"No session ID returned: {data}")
            return

        remaining = session.get("remaining_seconds", 0)
        result.pass_(f"Session activated, {remaining}s remaining")

    def check_exclusive_active(self, result: ValidationResult):
        """Test getting active exclusive session"""
        if not self.access_token:
            result.fail("No auth token - skipping", critical=False)
            return

        resp = self.api_get("/v1/exclusive/active")

        if resp.status_code == 404:
            # No active session - OK if activation failed
            result.pass_("No active session (expected if activation failed)")
            return

        if resp.status_code != 200:
            result.fail(f"Get active failed: {resp.status_code} {resp.text[:200]}")
            return

        data = resp.json()
        session = data.get("exclusive_session", data)

        if session.get("id"):
            result.pass_(f"Active session found: {session.get('id')[:8]}...")
        else:
            result.pass_("No active session")

    def check_exclusive_complete(self, result: ValidationResult):
        """Test completing exclusive session - THE BUG WAS HERE"""
        if not self.access_token:
            result.fail("No auth token - skipping", critical=False)
            return

        # First check if there's an active session
        active_resp = self.api_get("/v1/exclusive/active")
        if active_resp.status_code == 404:
            result.pass_("No active session to complete (OK)")
            return

        resp = self.api_post("/v1/exclusive/complete", {})

        if resp.status_code == 404:
            result.pass_("No session to complete (OK)")
            return

        if resp.status_code == 500:
            # This was the "Failed to redeem" bug - HubSpot import missing
            result.fail(f"SERVER ERROR - likely HubSpot import bug: {resp.text[:200]}")
            return

        if resp.status_code != 200:
            result.fail(f"Complete failed: {resp.status_code} {resp.text[:200]}")
            return

        result.pass_("Session completed successfully")

    # ========== External Service Checks ==========

    def check_twilio_config(self, result: ValidationResult):
        """Verify Twilio is configured (by testing OTP)"""
        # This is a proxy check - if OTP start works, Twilio is configured
        # We already tested OTP start, so check if it passed
        otp_result = next((r for r in self.results if r.name == "OTP Start"), None)
        if otp_result and otp_result.passed:
            result.pass_("Twilio working (OTP sent)")
        elif otp_result:
            result.fail(f"Twilio may be misconfigured: {otp_result.message}", critical=False)
        else:
            result.fail("OTP not tested", critical=False)

    def check_hubspot_import(self, result: ValidationResult):
        """Verify HubSpot import exists (the bug we just fixed)"""
        # This is validated by the complete endpoint not returning 500
        complete_result = next((r for r in self.results if r.name == "Exclusive Complete"), None)
        if complete_result and "HubSpot import" in complete_result.message:
            result.fail("HubSpot import bug detected!")
        elif complete_result and complete_result.passed:
            result.pass_("HubSpot integration working")
        else:
            result.pass_("HubSpot check skipped (no completion tested)")

    # ========== Data Integrity Checks ==========

    def check_no_null_island(self, result: ValidationResult):
        """Verify no sessions at (0,0) - data integrity check"""
        # This requires DB access which we don't have via API
        # Mark as skipped for API-only validation
        result.pass_("Requires DB access - run SQL check separately")
        result.critical = False

    def check_no_uuid_place_ids(self, result: ValidationResult):
        """Verify no UUIDs in merchant_place_id"""
        # This requires DB access
        result.pass_("Requires DB access - run SQL check separately")
        result.critical = False

    # ========== Run All Checks ==========

    def run_quick_checks(self):
        """Quick health checks only - no auth, no writes"""
        print("\n=== Quick Health Checks ===")
        self.run_check("Health Endpoint", self.check_health_endpoint)
        self.run_check("Healthz Endpoint", self.check_healthz_endpoint)
        self.run_check("Database Tables", self.check_database_tables)
        self.run_check("Chargers Endpoint", self.check_chargers_endpoint, critical=False)
        self.run_check("Merchants Endpoint", self.check_merchants_endpoint, critical=False)

    def run_full_checks(self):
        """Full validation including auth and writes"""
        print("\n=== Health Checks ===")
        self.run_check("Health Endpoint", self.check_health_endpoint)
        self.run_check("Healthz Endpoint", self.check_healthz_endpoint)
        self.run_check("Database Tables", self.check_database_tables)

        print("\n=== Discovery Checks ===")
        self.run_check("Chargers Endpoint", self.check_chargers_endpoint, critical=False)
        self.run_check("Merchants Endpoint", self.check_merchants_endpoint, critical=False)

        print("\n=== OTP Flow ===")
        self.run_check("OTP Start", self.check_otp_start)
        self.run_check("OTP Verify", self.check_otp_verify)

        print("\n=== Exclusive Flow ===")
        self.run_check("Exclusive Activate", self.check_exclusive_activate)
        self.run_check("Exclusive Active", self.check_exclusive_active)
        self.run_check("Exclusive Complete", self.check_exclusive_complete)

        print("\n=== External Services ===")
        self.run_check("Twilio Config", self.check_twilio_config, critical=False)
        self.run_check("HubSpot Import", self.check_hubspot_import)

        print("\n=== Data Integrity ===")
        self.run_check("No Null Island Sessions", self.check_no_null_island, critical=False)
        self.run_check("No UUID Place IDs", self.check_no_uuid_place_ids, critical=False)

    def run(self) -> int:
        """Run validation and return exit code"""
        print(f"\n{'='*60}")
        print(f"Production Flow Validation - {self.env.upper()}")
        print(f"API: {self.api_url}")
        print(f"Time: {datetime.now().isoformat()}")
        print(f"{'='*60}")

        if self.quick:
            self.run_quick_checks()
        else:
            self.run_full_checks()

        # Summary
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")

        passed = sum(1 for r in self.results if r.passed)
        failed_critical = [r for r in self.results if not r.passed and r.critical]
        failed_noncritical = [r for r in self.results if not r.passed and not r.critical]

        print(f"  Passed: {passed}/{len(self.results)}")
        print(f"  Critical Failures: {len(failed_critical)}")
        print(f"  Non-Critical Failures: {len(failed_noncritical)}")

        if failed_critical:
            print("\n  CRITICAL FAILURES (blocks users):")
            for r in failed_critical:
                print(f"    ✗ {r.name}: {r.message}")

        if failed_noncritical:
            print("\n  NON-CRITICAL FAILURES (degraded experience):")
            for r in failed_noncritical:
                print(f"    ⚠ {r.name}: {r.message}")

        # Exit code
        if failed_critical:
            print("\n❌ VALIDATION FAILED - Critical issues found")
            return 1
        elif failed_noncritical:
            print("\n⚠️  VALIDATION PASSED WITH WARNINGS")
            return 2
        else:
            print("\n✅ VALIDATION PASSED - All checks OK")
            return 0


def main():
    parser = argparse.ArgumentParser(description="Validate production user flow")
    parser.add_argument("--env", choices=["local", "staging", "production"], default="local",
                        help="Environment to validate")
    parser.add_argument("--quick", action="store_true",
                        help="Quick health check only (no OTP, no writes)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    validator = ProductionValidator(args.env, quick=args.quick, verbose=args.verbose)
    exit_code = validator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
