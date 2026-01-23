#!/usr/bin/env python3
"""
Nerava End-to-End Demo Verification Script

This script mimics all UI actions across the Driver App, Merchant Portal, and Admin Portal
to verify that backend endpoints are properly wired and functional.

Usage:
    python scripts/demo_verification.py --env local
    python scripts/demo_verification.py --env prod --skip-destructive

Environment Variables:
    API_BASE_URL: Base URL for the API (default: http://localhost:8000)
    ADMIN_EMAIL: Admin email for auth (default: admin@nerava.com)
    ADMIN_PASSWORD: Admin password (default: admin123)
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("ERROR: requests library required. Install with: pip install requests")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class TestResult:
    name: str
    endpoint: str
    method: str
    status: str  # PASS, FAIL, SKIP, WARN
    response_code: Optional[int] = None
    message: str = ""
    duration_ms: float = 0


class TestConfig:
    def __init__(self, env: str = "local"):
        self.env = env
        if env == "local":
            self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        elif env == "prod":
            self.base_url = "https://api.nerava.network"
        else:
            self.base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

        self.admin_email = os.getenv("ADMIN_EMAIL", "admin@nerava.com")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        self.test_phone = "+15551234567"
        self.test_charger_id = "ch_domain_tesla_001"
        self.test_merchant_id = "m_domain_starbucks"
        self.test_lat = 30.4025
        self.test_lng = -97.726


class APIClient:
    def __init__(self, config: TestConfig):
        self.config = config
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.driver_token: Optional[str] = None
        self.merchant_token: Optional[str] = None
        self.admin_token: Optional[str] = None

    def _url(self, path: str) -> str:
        return urljoin(self.config.base_url, path)

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        elif self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        token: Optional[str] = None,
        timeout: int = 30
    ) -> Tuple[int, Any, float]:
        """Make an API request and return (status_code, response_data, duration_ms)"""
        start = time.time()
        try:
            resp = self.session.request(
                method=method,
                url=self._url(path),
                json=data,
                params=params,
                headers=self._headers(token),
                timeout=timeout
            )
            duration = (time.time() - start) * 1000
            try:
                return resp.status_code, resp.json(), duration
            except:
                return resp.status_code, resp.text, duration
        except requests.exceptions.Timeout:
            return 0, "TIMEOUT", (time.time() - start) * 1000
        except requests.exceptions.ConnectionError as e:
            return 0, f"CONNECTION_ERROR: {e}", (time.time() - start) * 1000
        except Exception as e:
            return 0, f"ERROR: {e}", (time.time() - start) * 1000


# =============================================================================
# TEST SUITES
# =============================================================================

class TestSuite:
    def __init__(self, client: APIClient, skip_destructive: bool = False):
        self.client = client
        self.skip_destructive = skip_destructive
        self.results: List[TestResult] = []

    def add_result(self, result: TestResult):
        self.results.append(result)
        status_icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "WARN": "⚠️"}.get(result.status, "❓")
        print(f"  {status_icon} {result.name}: {result.status} ({result.duration_ms:.0f}ms)")
        if result.status == "FAIL":
            print(f"      {result.message}")


class HealthTests(TestSuite):
    """Test basic health and connectivity"""

    def run(self):
        print("\n" + "="*60)
        print("🏥 HEALTH & CONNECTIVITY TESTS")
        print("="*60)

        # Test 1: Basic health endpoint
        code, data, dur = self.client.request("GET", "/healthz")
        self.add_result(TestResult(
            name="Health Check (/healthz)",
            endpoint="/healthz",
            method="GET",
            status="PASS" if code == 200 and data.get("ok") else "FAIL",
            response_code=code,
            message=str(data) if code != 200 else "",
            duration_ms=dur
        ))

        # Test 2: Readiness probe
        code, data, dur = self.client.request("GET", "/v1/ops/readyz")
        self.add_result(TestResult(
            name="Readiness Probe (/v1/ops/readyz)",
            endpoint="/v1/ops/readyz",
            method="GET",
            status="PASS" if code == 200 else "FAIL",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # Test 3: Config endpoint
        code, data, dur = self.client.request("GET", "/v1/config")
        self.add_result(TestResult(
            name="Config Endpoint (/v1/config)",
            endpoint="/v1/config",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))


class DriverAppTests(TestSuite):
    """Test Driver App UI flows"""

    def run(self):
        print("\n" + "="*60)
        print("🚗 DRIVER APP TESTS")
        print("="*60)

        # === DISCOVERY FLOW ===
        print("\n📍 Discovery Flow:")

        # Test: Charger discovery
        code, data, dur = self.client.request(
            "GET", "/v1/chargers/discovery",
            params={"lat": self.client.config.test_lat, "lng": self.client.config.test_lng}
        )
        self.add_result(TestResult(
            name="Charger Discovery",
            endpoint="/v1/chargers/discovery",
            method="GET",
            status="PASS" if code == 200 else "FAIL",
            response_code=code,
            message=str(data)[:100] if code != 200 else f"Found {len(data) if isinstance(data, list) else 'N/A'} chargers",
            duration_ms=dur
        ))

        # Test: Merchants for charger (open endpoint)
        code, data, dur = self.client.request(
            "GET", "/v1/drivers/merchants/open",
            params={"charger_id": self.client.config.test_charger_id}
        )
        self.add_result(TestResult(
            name="Merchants for Charger",
            endpoint="/v1/drivers/merchants/open",
            method="GET",
            status="PASS" if code == 200 else "FAIL",
            response_code=code,
            message=str(data)[:100] if code != 200 else f"Found {len(data) if isinstance(data, list) else 'N/A'} merchants",
            duration_ms=dur
        ))

        # Test: Merchant details
        code, data, dur = self.client.request(
            "GET", f"/v1/merchants/{self.client.config.test_merchant_id}"
        )
        self.add_result(TestResult(
            name="Merchant Details",
            endpoint=f"/v1/merchants/{self.client.config.test_merchant_id}",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # === AUTHENTICATION FLOW ===
        print("\n🔐 Authentication Flow:")

        # Test: OTP Start
        code, data, dur = self.client.request(
            "POST", "/v1/auth/otp/start",
            data={"phone": self.client.config.test_phone}
        )
        otp_started = code == 200 or code == 429  # 429 = rate limited (still means endpoint works)
        self.add_result(TestResult(
            name="OTP Start",
            endpoint="/v1/auth/otp/start",
            method="POST",
            status="PASS" if otp_started else "FAIL",
            response_code=code,
            message="Rate limited" if code == 429 else (str(data)[:100] if code != 200 else ""),
            duration_ms=dur
        ))

        # Test: OTP Verify (will fail without real code, but tests endpoint exists)
        code, data, dur = self.client.request(
            "POST", "/v1/auth/otp/verify",
            data={"phone": self.client.config.test_phone, "code": "000000"}
        )
        # 401 = invalid code (endpoint exists), 400 = bad request
        self.add_result(TestResult(
            name="OTP Verify Endpoint",
            endpoint="/v1/auth/otp/verify",
            method="POST",
            status="PASS" if code in [200, 401, 400] else "FAIL",
            response_code=code,
            message="Endpoint exists (invalid code expected)" if code == 401 else str(data)[:100],
            duration_ms=dur
        ))

        # Test: Dev login (if available)
        code, data, dur = self.client.request(
            "POST", "/v1/auth/dev/login",
            data={"phone": self.client.config.test_phone}
        )
        if code == 200 and data.get("access_token"):
            self.client.driver_token = data["access_token"]
            self.add_result(TestResult(
                name="Dev Login",
                endpoint="/v1/auth/dev/login",
                method="POST",
                status="PASS",
                response_code=code,
                message="Got access token",
                duration_ms=dur
            ))
        else:
            self.add_result(TestResult(
                name="Dev Login",
                endpoint="/v1/auth/dev/login",
                method="POST",
                status="SKIP" if code == 403 else "WARN",
                response_code=code,
                message="Dev mode not enabled" if code == 403 else str(data)[:100],
                duration_ms=dur
            ))

        # === AUTHENTICATED DRIVER TESTS ===
        if self.client.driver_token:
            print("\n👤 Authenticated Driver Flow:")

            # Test: Get profile
            code, data, dur = self.client.request(
                "GET", "/v1/auth/me",
                token=self.client.driver_token
            )
            self.add_result(TestResult(
                name="Get User Profile",
                endpoint="/v1/auth/me",
                method="GET",
                status="PASS" if code == 200 else "FAIL",
                response_code=code,
                message=str(data)[:100] if code != 200 else "",
                duration_ms=dur
            ))

            # Test: Get wallet
            code, data, dur = self.client.request(
                "GET", "/v1/drivers/me/wallet",
                token=self.client.driver_token
            )
            self.add_result(TestResult(
                name="Get Driver Wallet",
                endpoint="/v1/drivers/me/wallet",
                method="GET",
                status="PASS" if code == 200 else "WARN",
                response_code=code,
                message=str(data)[:100] if code != 200 else "",
                duration_ms=dur
            ))

            # Test: Get user preferences
            code, data, dur = self.client.request(
                "GET", "/v1/user/preferences",
                token=self.client.driver_token
            )
            self.add_result(TestResult(
                name="Get User Preferences",
                endpoint="/v1/user/preferences",
                method="GET",
                status="PASS" if code == 200 else "WARN",
                response_code=code,
                message=str(data)[:100] if code != 200 else "",
                duration_ms=dur
            ))

            # Test: Update user preferences (Account page functionality)
            code, data, dur = self.client.request(
                "PUT", "/v1/user/preferences",
                token=self.client.driver_token,
                data={"food_tags": ["coffee", "mexican"], "preferred_networks": ["Tesla"]}
            )
            self.add_result(TestResult(
                name="Update User Preferences",
                endpoint="/v1/user/preferences",
                method="PUT",
                status="PASS" if code == 200 else "WARN",
                response_code=code,
                message=str(data)[:100] if code != 200 else "",
                duration_ms=dur
            ))

            # Test: Get favorites
            code, data, dur = self.client.request(
                "GET", "/v1/merchants/favorites",
                token=self.client.driver_token
            )
            self.add_result(TestResult(
                name="Get Favorites",
                endpoint="/v1/merchants/favorites",
                method="GET",
                status="PASS" if code == 200 else "WARN",
                response_code=code,
                message=str(data)[:100] if code != 200 else "",
                duration_ms=dur
            ))

            # Test: Activity feed
            code, data, dur = self.client.request(
                "GET", "/v1/activity",
                token=self.client.driver_token
            )
            self.add_result(TestResult(
                name="Get Activity Feed",
                endpoint="/v1/activity",
                method="GET",
                status="PASS" if code == 200 else "WARN",
                response_code=code,
                message=str(data)[:100] if code != 200 else "",
                duration_ms=dur
            ))

        # === EXCLUSIVE ACTIVATION FLOW ===
        print("\n⭐ Exclusive Activation Flow:")

        # Test: Activate exclusive endpoint exists
        code, data, dur = self.client.request(
            "POST", "/v1/exclusive/activate",
            data={
                "charger_id": self.client.config.test_charger_id,
                "merchant_id": self.client.config.test_merchant_id,
                "lat": self.client.config.test_lat,
                "lng": self.client.config.test_lng,
                "accuracy_m": 10
            },
            token=self.client.driver_token
        )
        # 401 = needs auth, 403 = not at charger, 428 = needs OTP - all valid responses
        self.add_result(TestResult(
            name="Exclusive Activate Endpoint",
            endpoint="/v1/exclusive/activate",
            method="POST",
            status="PASS" if code in [200, 201, 401, 403, 428] else "FAIL",
            response_code=code,
            message=str(data)[:100],
            duration_ms=dur
        ))

        # Test: Get active exclusive
        code, data, dur = self.client.request(
            "GET", "/v1/exclusive/active",
            token=self.client.driver_token
        )
        self.add_result(TestResult(
            name="Get Active Exclusive",
            endpoint="/v1/exclusive/active",
            method="GET",
            status="PASS" if code in [200, 401, 404] else "FAIL",
            response_code=code,
            message=str(data)[:100] if code not in [200, 404] else "",
            duration_ms=dur
        ))


class MerchantPortalTests(TestSuite):
    """Test Merchant Portal UI flows"""

    def run(self):
        print("\n" + "="*60)
        print("🏪 MERCHANT PORTAL TESTS")
        print("="*60)

        test_merchant_id = "m_asadas_grill"  # Known merchant

        # === MERCHANT DASHBOARD ===
        print("\n📊 Dashboard Flow:")

        # Test: Get merchant analytics
        code, data, dur = self.client.request(
            "GET", f"/v1/merchants/{test_merchant_id}/analytics",
            token=self.client.merchant_token
        )
        self.add_result(TestResult(
            name="Merchant Analytics",
            endpoint=f"/v1/merchants/{test_merchant_id}/analytics",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # Test: Get merchant visits
        code, data, dur = self.client.request(
            "GET", f"/v1/merchants/{test_merchant_id}/visits",
            params={"limit": 50},
            token=self.client.merchant_token
        )
        self.add_result(TestResult(
            name="Merchant Visits",
            endpoint=f"/v1/merchants/{test_merchant_id}/visits",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # === EXCLUSIVES MANAGEMENT ===
        print("\n⭐ Exclusives Management:")

        # Test: Get merchant exclusives
        code, data, dur = self.client.request(
            "GET", f"/v1/merchants/{test_merchant_id}/exclusives",
            token=self.client.merchant_token
        )
        self.add_result(TestResult(
            name="Get Merchant Exclusives",
            endpoint=f"/v1/merchants/{test_merchant_id}/exclusives",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # Test: Create exclusive endpoint exists
        code, data, dur = self.client.request(
            "POST", f"/v1/merchants/{test_merchant_id}/exclusives",
            token=self.client.merchant_token,
            data={
                "name": "Test Exclusive",
                "description": "Test description",
                "type": "free",
                "start_time": "09:00",
                "end_time": "17:00",
                "daily_cap": 10
            }
        )
        self.add_result(TestResult(
            name="Create Exclusive Endpoint",
            endpoint=f"/v1/merchants/{test_merchant_id}/exclusives",
            method="POST",
            status="PASS" if code in [200, 201, 401, 403, 422] else "FAIL",
            response_code=code,
            message=str(data)[:100],
            duration_ms=dur
        ))

        # === BILLING ===
        print("\n💳 Billing Flow:")

        # Test: Get billing summary
        code, data, dur = self.client.request(
            "GET", f"/v1/merchants/{test_merchant_id}/billing/summary",
            token=self.client.merchant_token
        )
        self.add_result(TestResult(
            name="Billing Summary",
            endpoint=f"/v1/merchants/{test_merchant_id}/billing/summary",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # Test: Get merchant balance
        code, data, dur = self.client.request(
            "GET", f"/v1/merchants/{test_merchant_id}/balance",
            token=self.client.merchant_token
        )
        self.add_result(TestResult(
            name="Merchant Balance",
            endpoint=f"/v1/merchants/{test_merchant_id}/balance",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # === BRAND IMAGE ===
        print("\n🖼️ Brand Management:")

        # Test: Update brand image
        code, data, dur = self.client.request(
            "PUT", f"/v1/merchants/{test_merchant_id}/brand-image",
            token=self.client.merchant_token,
            data={"brand_image_url": "https://example.com/logo.png"}
        )
        self.add_result(TestResult(
            name="Update Brand Image",
            endpoint=f"/v1/merchants/{test_merchant_id}/brand-image",
            method="PUT",
            status="PASS" if code in [200, 401, 403] else "WARN",
            response_code=code,
            message=str(data)[:100] if code not in [200] else "",
            duration_ms=dur
        ))


class AdminPortalTests(TestSuite):
    """Test Admin Portal UI flows"""

    def run(self):
        print("\n" + "="*60)
        print("👑 ADMIN PORTAL TESTS")
        print("="*60)

        # === ADMIN AUTHENTICATION ===
        print("\n🔐 Admin Authentication:")

        # Test: Admin login
        code, data, dur = self.client.request(
            "POST", "/v1/auth/admin/login",
            data={
                "email": self.client.config.admin_email,
                "password": self.client.config.admin_password
            }
        )
        if code == 200 and data.get("access_token"):
            self.client.admin_token = data["access_token"]
            self.add_result(TestResult(
                name="Admin Login",
                endpoint="/v1/auth/admin/login",
                method="POST",
                status="PASS",
                response_code=code,
                message="Got admin token",
                duration_ms=dur
            ))
        else:
            self.add_result(TestResult(
                name="Admin Login",
                endpoint="/v1/auth/admin/login",
                method="POST",
                status="WARN",
                response_code=code,
                message=str(data)[:100],
                duration_ms=dur
            ))

        # Use admin token if available, otherwise try without
        admin_token = self.client.admin_token

        # === ADMIN DASHBOARD ===
        print("\n📊 Dashboard:")

        # Test: Admin health
        code, data, dur = self.client.request(
            "GET", "/v1/admin/health",
            token=admin_token
        )
        self.add_result(TestResult(
            name="Admin Health",
            endpoint="/v1/admin/health",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # Test: Admin overview
        code, data, dur = self.client.request(
            "GET", "/v1/admin/overview",
            token=admin_token
        )
        self.add_result(TestResult(
            name="Admin Overview",
            endpoint="/v1/admin/overview",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # === MERCHANT MANAGEMENT ===
        print("\n🏪 Merchant Management:")

        # Test: List merchants
        code, data, dur = self.client.request(
            "GET", "/v1/admin/merchants",
            token=admin_token
        )
        self.add_result(TestResult(
            name="List Merchants",
            endpoint="/v1/admin/merchants",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # Test: Search merchants
        code, data, dur = self.client.request(
            "GET", "/v1/admin/merchants",
            params={"query": "starbucks"},
            token=admin_token
        )
        self.add_result(TestResult(
            name="Search Merchants",
            endpoint="/v1/admin/merchants?query=starbucks",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # === ACTIVE SESSIONS ===
        print("\n⚡ Session Monitoring:")

        # Test: Get active sessions
        code, data, dur = self.client.request(
            "GET", "/v1/admin/sessions/active",
            params={"limit": 100},
            token=admin_token
        )
        self.add_result(TestResult(
            name="Active Sessions",
            endpoint="/v1/admin/sessions/active",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else f"Found {data.get('total_active', 0)} active sessions" if isinstance(data, dict) else "",
            duration_ms=dur
        ))

        # === USER MANAGEMENT ===
        print("\n👥 User Management:")

        # Test: List users
        code, data, dur = self.client.request(
            "GET", "/v1/admin/users",
            token=admin_token
        )
        self.add_result(TestResult(
            name="List Users",
            endpoint="/v1/admin/users",
            method="GET",
            status="PASS" if code == 200 else "WARN",
            response_code=code,
            message=str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # === NOVA MANAGEMENT ===
        print("\n💎 Nova Management:")

        # Test: Nova grant endpoint exists (don't actually grant in prod)
        if self.skip_destructive:
            self.add_result(TestResult(
                name="Nova Grant",
                endpoint="/v1/admin/nova/grant",
                method="POST",
                status="SKIP",
                response_code=0,
                message="Skipped (destructive test)",
                duration_ms=0
            ))
        else:
            code, data, dur = self.client.request(
                "POST", "/v1/admin/nova/grant",
                token=admin_token,
                data={
                    "recipient_type": "driver",
                    "recipient_id": "test_user",
                    "amount": 0,  # Zero amount for testing
                    "reason": "API test - zero amount"
                }
            )
            self.add_result(TestResult(
                name="Nova Grant Endpoint",
                endpoint="/v1/admin/nova/grant",
                method="POST",
                status="PASS" if code in [200, 400, 401, 403, 422] else "FAIL",
                response_code=code,
                message=str(data)[:100],
                duration_ms=dur
            ))


class AccountPageTests(TestSuite):
    """Test Account Page functionality gaps"""

    def run(self):
        print("\n" + "="*60)
        print("👤 ACCOUNT PAGE TESTS (Gap Analysis)")
        print("="*60)

        if not self.client.driver_token:
            print("  ⏭️ Skipping - no driver token available")
            return

        # === PROFILE ===
        print("\n📝 Profile Endpoints:")

        # Test: Get profile
        code, data, dur = self.client.request(
            "GET", "/v1/auth/me",
            token=self.client.driver_token
        )
        self.add_result(TestResult(
            name="Get Profile",
            endpoint="/v1/auth/me",
            method="GET",
            status="PASS" if code == 200 else "FAIL",
            response_code=code,
            message=str(data)[:100] if code != 200 else "Profile data available",
            duration_ms=dur
        ))

        # Test: Update profile (missing endpoint)
        code, data, dur = self.client.request(
            "PUT", "/v1/auth/me",
            token=self.client.driver_token,
            data={"display_name": "Test User"}
        )
        self.add_result(TestResult(
            name="Update Profile",
            endpoint="/v1/auth/me",
            method="PUT",
            status="PASS" if code == 200 else "FAIL" if code == 404 else "WARN",
            response_code=code,
            message="MISSING ENDPOINT" if code == 404 else str(data)[:100],
            duration_ms=dur
        ))

        # === FAVORITES ===
        print("\n❤️ Favorites Endpoints:")

        # Test: Get favorites list
        code, data, dur = self.client.request(
            "GET", "/v1/merchants/favorites",
            token=self.client.driver_token
        )
        self.add_result(TestResult(
            name="Get Favorites List",
            endpoint="/v1/merchants/favorites",
            method="GET",
            status="PASS" if code == 200 else "FAIL" if code == 404 else "WARN",
            response_code=code,
            message="MISSING ENDPOINT" if code == 404 else str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # Test: Add favorite
        code, data, dur = self.client.request(
            "POST", f"/v1/merchants/{self.client.config.test_merchant_id}/favorite",
            token=self.client.driver_token
        )
        self.add_result(TestResult(
            name="Add Favorite",
            endpoint=f"/v1/merchants/{self.client.config.test_merchant_id}/favorite",
            method="POST",
            status="PASS" if code in [200, 201, 409] else "FAIL" if code == 404 else "WARN",
            response_code=code,
            message="MISSING ENDPOINT" if code == 404 else str(data)[:100],
            duration_ms=dur
        ))

        # Test: Remove favorite
        code, data, dur = self.client.request(
            "DELETE", f"/v1/merchants/{self.client.config.test_merchant_id}/favorite",
            token=self.client.driver_token
        )
        self.add_result(TestResult(
            name="Remove Favorite",
            endpoint=f"/v1/merchants/{self.client.config.test_merchant_id}/favorite",
            method="DELETE",
            status="PASS" if code in [200, 204, 404] else "FAIL",
            response_code=code,
            message="MISSING ENDPOINT" if code == 405 else str(data)[:100] if code not in [200, 204] else "",
            duration_ms=dur
        ))

        # === SETTINGS ===
        print("\n⚙️ Settings Endpoints:")

        # Test: Get notification preferences
        code, data, dur = self.client.request(
            "GET", "/v1/notifications/prefs",
            token=self.client.driver_token
        )
        self.add_result(TestResult(
            name="Get Notification Prefs",
            endpoint="/v1/notifications/prefs",
            method="GET",
            status="PASS" if code == 200 else "FAIL" if code == 404 else "WARN",
            response_code=code,
            message="MISSING ENDPOINT" if code == 404 else str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # Test: Update notification preferences
        code, data, dur = self.client.request(
            "PUT", "/v1/notifications/prefs",
            token=self.client.driver_token,
            data={"push_enabled": True, "email_enabled": True}
        )
        self.add_result(TestResult(
            name="Update Notification Prefs",
            endpoint="/v1/notifications/prefs",
            method="PUT",
            status="PASS" if code == 200 else "FAIL" if code == 404 else "WARN",
            response_code=code,
            message="MISSING ENDPOINT" if code == 404 else str(data)[:100] if code != 200 else "",
            duration_ms=dur
        ))

        # === ACCOUNT MANAGEMENT ===
        print("\n🔒 Account Management:")

        # Test: Export data endpoint
        code, data, dur = self.client.request(
            "POST", "/v1/account/export",
            token=self.client.driver_token
        )
        self.add_result(TestResult(
            name="Export Account Data",
            endpoint="/v1/account/export",
            method="POST",
            status="PASS" if code in [200, 202] else "WARN" if code == 501 else "FAIL" if code == 404 else "WARN",
            response_code=code,
            message="NOT IMPLEMENTED" if code == 501 else "MISSING ENDPOINT" if code == 404 else str(data)[:100],
            duration_ms=dur
        ))

        # Test: Delete account endpoint (don't actually delete)
        if self.skip_destructive:
            self.add_result(TestResult(
                name="Delete Account",
                endpoint="/v1/account",
                method="DELETE",
                status="SKIP",
                response_code=0,
                message="Skipped (destructive test)",
                duration_ms=0
            ))
        else:
            code, data, dur = self.client.request(
                "DELETE", "/v1/account",
                token=self.client.driver_token
            )
            self.add_result(TestResult(
                name="Delete Account Endpoint",
                endpoint="/v1/account",
                method="DELETE",
                status="PASS" if code in [200, 204, 401, 403] else "WARN" if code == 501 else "FAIL" if code == 404 else "WARN",
                response_code=code,
                message="NOT IMPLEMENTED" if code == 501 else "MISSING ENDPOINT" if code == 404 else str(data)[:100],
                duration_ms=dur
            ))


# =============================================================================
# MAIN
# =============================================================================

def print_summary(all_results: List[TestResult]):
    """Print test summary"""
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)

    total = len(all_results)
    passed = sum(1 for r in all_results if r.status == "PASS")
    failed = sum(1 for r in all_results if r.status == "FAIL")
    warned = sum(1 for r in all_results if r.status == "WARN")
    skipped = sum(1 for r in all_results if r.status == "SKIP")

    print(f"\n  Total Tests: {total}")
    print(f"  ✅ Passed:   {passed}")
    print(f"  ❌ Failed:   {failed}")
    print(f"  ⚠️  Warnings: {warned}")
    print(f"  ⏭️  Skipped:  {skipped}")

    pass_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n  Pass Rate: {pass_rate:.1f}%")

    if failed > 0:
        print("\n❌ FAILED TESTS:")
        for r in all_results:
            if r.status == "FAIL":
                print(f"   - {r.name}: {r.endpoint} -> {r.response_code}")
                if r.message:
                    print(f"     {r.message[:80]}")

    if warned > 0:
        print("\n⚠️  WARNINGS (May need attention):")
        for r in all_results:
            if r.status == "WARN":
                print(f"   - {r.name}: {r.endpoint} -> {r.response_code}")


def main():
    parser = argparse.ArgumentParser(description="Nerava E2E Demo Verification")
    parser.add_argument("--env", choices=["local", "prod"], default="local", help="Environment to test")
    parser.add_argument("--skip-destructive", action="store_true", help="Skip destructive tests")
    parser.add_argument("--suite", choices=["all", "health", "driver", "merchant", "admin", "account"],
                       default="all", help="Which test suite to run")
    args = parser.parse_args()

    print("="*60)
    print("🚀 NERAVA E2E DEMO VERIFICATION")
    print("="*60)
    print(f"Environment: {args.env}")
    print(f"Skip Destructive: {args.skip_destructive}")
    print(f"Test Suite: {args.suite}")

    config = TestConfig(env=args.env)
    client = APIClient(config)

    print(f"Base URL: {config.base_url}")

    all_results: List[TestResult] = []

    # Run test suites
    if args.suite in ["all", "health"]:
        health = HealthTests(client, args.skip_destructive)
        health.run()
        all_results.extend(health.results)

    if args.suite in ["all", "driver"]:
        driver = DriverAppTests(client, args.skip_destructive)
        driver.run()
        all_results.extend(driver.results)

    if args.suite in ["all", "account"]:
        account = AccountPageTests(client, args.skip_destructive)
        account.run()
        all_results.extend(account.results)

    if args.suite in ["all", "merchant"]:
        merchant = MerchantPortalTests(client, args.skip_destructive)
        merchant.run()
        all_results.extend(merchant.results)

    if args.suite in ["all", "admin"]:
        admin = AdminPortalTests(client, args.skip_destructive)
        admin.run()
        all_results.extend(admin.results)

    # Print summary
    print_summary(all_results)

    # Exit with appropriate code
    failed = sum(1 for r in all_results if r.status == "FAIL")
    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    main()
