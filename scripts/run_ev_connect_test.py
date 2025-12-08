#!/usr/bin/env python3
"""
Test script for EV Connect flow
Authenticates via magic link, then calls /v1/ev/connect and opens Smartcar URL in browser
"""
import argparse
import sys
import re
import json
import webbrowser
from urllib.parse import urlparse, parse_qs
from typing import Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Install with: pip install httpx")
    sys.exit(1)

# Production backend URL
PROD_BACKEND = "https://web-production-526f6.up.railway.app"
CALLBACK_URL = f"{PROD_BACKEND}/oauth/smartcar/callback"


def extract_token_from_url(url: str) -> Optional[str]:
    """Extract token from magic link URL (format: .../#/auth/magic?token=...)"""
    # Handle hash-based routing
    if "#" in url:
        hash_part = url.split("#")[1]
        if "?" in hash_part:
            query_part = hash_part.split("?")[1]
            params = parse_qs(query_part)
            if "token" in params:
                return params["token"][0]
    # Also try regular query params
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "token" in params:
        return params["token"][0]
    return None


def request_magic_link(email: str) -> dict:
    """Request a magic link for the given email"""
    print(f"📧 Requesting magic link for: {email}")
    
    response = httpx.post(
        f"{PROD_BACKEND}/v1/auth/magic_link/request",
        json={"email": email},
        timeout=30.0
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to request magic link: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    
    data = response.json()
    print(f"✅ Magic link sent to {email}")
    print(f"   Check your email for the magic link URL")
    return data


def verify_magic_link_token(token: str) -> str:
    """Verify magic link token and get access token"""
    print("🔐 Verifying magic link token...")
    
    response = httpx.post(
        f"{PROD_BACKEND}/v1/auth/magic_link/verify",
        json={"token": token},
        timeout=30.0
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to verify token: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    
    data = response.json()
    access_token = data.get("access_token")
    
    if not access_token:
        print("❌ No access_token in response")
        print(f"   Response: {data}")
        sys.exit(1)
    
    print("✅ Token verified, access token obtained")
    return access_token


def get_ev_connect_url(access_token: str) -> str:
    """Get Smartcar Connect URL from /v1/ev/connect"""
    print("🚗 Requesting EV Connect URL...")
    
    response = httpx.get(
        f"{PROD_BACKEND}/v1/ev/connect",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30.0
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to get EV Connect URL: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)
    
    data = response.json()
    connect_url = data.get("url")
    
    if not connect_url:
        print("❌ No 'url' field in response")
        print(f"   Response: {data}")
        sys.exit(1)
    
    print("✅ EV Connect URL obtained")
    return connect_url


def open_browser(url: str):
    """Open URL in system browser"""
    print(f"🌐 Opening browser: {url}")
    webbrowser.open(url)


def main():
    parser = argparse.ArgumentParser(
        description="Test EV Connect flow: authenticate and open Smartcar Connect URL"
    )
    parser.add_argument(
        "--email",
        required=True,
        help="Email address to authenticate with"
    )
    args = parser.parse_args()
    
    email = args.email.strip().lower()
    
    print("=" * 60)
    print("EV Connect Test Script")
    print("=" * 60)
    print(f"Backend: {PROD_BACKEND}")
    print(f"Email: {email}")
    print()
    
    # Step 1: Request magic link
    request_magic_link(email)
    print()
    
    # Step 2: Get magic link URL from user
    print("📋 Paste the magic link URL you received in your email:")
    print("   (It should look like: https://.../#/auth/magic?token=...)")
    magic_link_url = input("> ").strip()
    
    if not magic_link_url:
        print("❌ No URL provided")
        sys.exit(1)
    
    # Step 3: Extract token from URL
    token = extract_token_from_url(magic_link_url)
    if not token:
        print("❌ Could not extract token from URL")
        print(f"   URL: {magic_link_url}")
        sys.exit(1)
    
    print(f"✅ Token extracted from URL")
    print()
    
    # Step 4: Verify token and get access token
    access_token = verify_magic_link_token(token)
    print()
    
    # Step 5: Get EV Connect URL
    connect_url = get_ev_connect_url(access_token)
    print()
    
    # Step 6: Open browser
    open_browser(connect_url)
    print()
    
    # Step 7: Print callback URL
    print("=" * 60)
    print("✅ Smartcar Connect URL opened in your browser.")
    print()
    print(f"📞 Callback URL is: {CALLBACK_URL}")
    print()
    print("After completing Smartcar OAuth, you will be redirected to:")
    print(f"   {CALLBACK_URL}")
    print("=" * 60)


if __name__ == "__main__":
    main()

