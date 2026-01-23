#!/usr/bin/env python3
"""
Twilio Configuration Diagnostic Script

Checks Twilio configuration for OTP endpoint:
1. Validates environment variables are set
2. Tests Twilio credentials directly
3. Verifies Verify service exists and is active
4. Outputs diagnostic information

Usage:
    python scripts/check_twilio_config.py
    
    # Check AWS ECS task definition (requires AWS CLI)
    python scripts/check_twilio_config.py --check-aws
    
    # Test with specific phone number
    python scripts/check_twilio_config.py --test-phone +17133056318
"""
import sys
import os
import json
import subprocess
from typing import Optional, Dict, Any

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.config import settings


def check_env_vars() -> Dict[str, Any]:
    """Check if required environment variables are set"""
    print("=" * 60)
    print("Step 1: Checking Environment Variables")
    print("=" * 60)
    print()
    
    required_vars = {
        "OTP_PROVIDER": settings.OTP_PROVIDER,
        "TWILIO_ACCOUNT_SID": settings.TWILIO_ACCOUNT_SID,
        "TWILIO_AUTH_TOKEN": settings.TWILIO_AUTH_TOKEN,
        "TWILIO_VERIFY_SERVICE_SID": settings.TWILIO_VERIFY_SERVICE_SID,
        "ENV": settings.ENV,
    }
    
    optional_vars = {
        "TWILIO_TIMEOUT_SECONDS": settings.TWILIO_TIMEOUT_SECONDS,
        "OTP_FROM_NUMBER": settings.OTP_FROM_NUMBER,
    }
    
    results = {
        "required": {},
        "optional": {},
        "missing": [],
        "valid": True
    }
    
    # Check required vars
    for var_name, value in required_vars.items():
        if value:
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            results["required"][var_name] = masked_value
            print(f"✅ {var_name}: {masked_value}")
        else:
            results["required"][var_name] = None
            results["missing"].append(var_name)
            print(f"❌ {var_name}: MISSING")
            results["valid"] = False
    
    print()
    
    # Check optional vars
    for var_name, value in optional_vars.items():
        if value:
            if var_name == "TWILIO_TIMEOUT_SECONDS":
                print(f"ℹ️  {var_name}: {value}")
            else:
                masked_value = value[:8] + "..." if len(value) > 8 else "***"
                print(f"ℹ️  {var_name}: {masked_value}")
        else:
            print(f"⚠️  {var_name}: Not set (optional)")
    
    print()
    
    # Validate OTP_PROVIDER
    if settings.OTP_PROVIDER == "stub" and settings.ENV == "prod":
        print("❌ ERROR: OTP_PROVIDER=stub is not allowed in production")
        results["valid"] = False
    elif settings.OTP_PROVIDER not in ["twilio_verify", "twilio_sms", "stub"]:
        print(f"❌ ERROR: Invalid OTP_PROVIDER: {settings.OTP_PROVIDER}")
        results["valid"] = False
    
    # Validate provider-specific requirements
    if settings.OTP_PROVIDER == "twilio_verify":
        if not settings.TWILIO_VERIFY_SERVICE_SID:
            print("❌ ERROR: TWILIO_VERIFY_SERVICE_SID required for twilio_verify provider")
            results["valid"] = False
    elif settings.OTP_PROVIDER == "twilio_sms":
        if not settings.OTP_FROM_NUMBER:
            print("❌ ERROR: OTP_FROM_NUMBER required for twilio_sms provider")
            results["valid"] = False
    
    print()
    return results


def check_aws_ecs() -> Dict[str, Any]:
    """Check AWS ECS task definition for Twilio environment variables"""
    print("=" * 60)
    print("Step 2: Checking AWS ECS Task Definition")
    print("=" * 60)
    print()
    
    results = {
        "checked": False,
        "task_def": None,
        "env_vars": {},
        "error": None
    }
    
    try:
        # Try to get task definition
        cmd = [
            "aws", "ecs", "describe-task-definition",
            "--task-definition", "nerava-backend",
            "--query", "taskDefinition.containerDefinitions[0].environment",
            "--output", "json"
        ]
        
        print("Running: " + " ".join(cmd))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"⚠️  AWS CLI command failed: {result.stderr}")
            print("   (This is OK if AWS CLI is not configured or task definition doesn't exist)")
            results["error"] = result.stderr
            print()
            return results
        
        env_vars = json.loads(result.stdout)
        results["checked"] = True
        results["env_vars"] = {var["name"]: var.get("value", "") for var in env_vars}
        
        # Check Twilio vars
        twilio_vars = [
            "OTP_PROVIDER",
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_VERIFY_SERVICE_SID",
            "TWILIO_TIMEOUT_SECONDS",
            "OTP_FROM_NUMBER",
            "ENV"
        ]
        
        print("Twilio-related environment variables in ECS task definition:")
        for var_name in twilio_vars:
            value = results["env_vars"].get(var_name, "")
            if value:
                masked_value = value[:8] + "..." if len(value) > 8 else "***"
                print(f"  ✅ {var_name}: {masked_value}")
            else:
                print(f"  ❌ {var_name}: NOT SET")
        
        print()
        
    except FileNotFoundError:
        print("⚠️  AWS CLI not found. Install AWS CLI to check ECS task definition.")
        results["error"] = "AWS CLI not found"
        print()
    except subprocess.TimeoutExpired:
        print("⚠️  AWS CLI command timed out")
        results["error"] = "Timeout"
        print()
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse AWS CLI output: {e}")
        results["error"] = str(e)
        print()
    except Exception as e:
        print(f"⚠️  Error checking AWS ECS: {e}")
        results["error"] = str(e)
        print()
    
    return results


def test_twilio_credentials() -> Dict[str, Any]:
    """Test Twilio credentials directly"""
    print("=" * 60)
    print("Step 3: Testing Twilio Credentials")
    print("=" * 60)
    print()
    
    results = {
        "tested": False,
        "account_valid": False,
        "verify_service_valid": False,
        "error": None
    }
    
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print("⚠️  Skipping Twilio test - credentials not configured")
        print()
        return results
    
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioException
        
        print("Creating Twilio client...")
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        results["tested"] = True
        
        # Test account access
        print("Testing account access...")
        try:
            account = client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
            print(f"✅ Account valid: {account.friendly_name}")
            results["account_valid"] = True
        except TwilioException as e:
            print(f"❌ Account test failed: {e}")
            results["error"] = str(e)
            print()
            return results
        
        # Test Verify service
        if settings.TWILIO_VERIFY_SERVICE_SID:
            print(f"Testing Verify service: {settings.TWILIO_VERIFY_SERVICE_SID[:8]}...")
            try:
                service = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).fetch()
                print(f"✅ Verify service valid: {service.friendly_name}")
                print(f"   Status: {service.status}")
                results["verify_service_valid"] = True
            except TwilioException as e:
                print(f"❌ Verify service test failed: {e}")
                if "not found" in str(e).lower():
                    print("   → Service may have been deleted or SID is incorrect")
                results["error"] = str(e)
        else:
            print("⚠️  TWILIO_VERIFY_SERVICE_SID not set, skipping Verify service test")
        
        print()
        
    except ImportError:
        print("❌ ERROR: Twilio library not installed")
        print("   Install with: pip install twilio")
        results["error"] = "Twilio library not installed"
        print()
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        results["error"] = str(e)
        print()
    
    return results


def test_send_otp(phone: str) -> Dict[str, Any]:
    """Test sending OTP to a phone number"""
    print("=" * 60)
    print(f"Step 4: Testing OTP Send to {phone}")
    print("=" * 60)
    print()
    
    results = {
        "tested": False,
        "success": False,
        "verification_sid": None,
        "error": None
    }
    
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        print("⚠️  Skipping OTP send test - credentials not configured")
        print()
        return results
    
    if not settings.TWILIO_VERIFY_SERVICE_SID:
        print("⚠️  Skipping OTP send test - TWILIO_VERIFY_SERVICE_SID not configured")
        print()
        return results
    
    try:
        from twilio.rest import Client
        from twilio.base.exceptions import TwilioException
        
        print(f"Sending verification to {phone}...")
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        verification = client.verify.v2.services(settings.TWILIO_VERIFY_SERVICE_SID).verifications.create(
            to=phone,
            channel='sms'
        )
        
        print(f"✅ Verification sent successfully!")
        print(f"   Verification SID: {verification.sid}")
        print(f"   Status: {verification.status}")
        results["tested"] = True
        results["success"] = True
        results["verification_sid"] = verification.sid
        print()
        
    except TwilioException as e:
        print(f"❌ Failed to send verification: {e}")
        error_type = type(e).__name__
        print(f"   Error type: {error_type}")
        results["tested"] = True
        results["error"] = str(e)
        print()
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        results["error"] = str(e)
        print()
    
    return results


def main():
    """Run diagnostic checks"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Twilio configuration")
    parser.add_argument("--check-aws", action="store_true", help="Check AWS ECS task definition")
    parser.add_argument("--test-phone", type=str, help="Test sending OTP to phone number")
    args = parser.parse_args()
    
    print()
    print("Twilio Configuration Diagnostic")
    print("=" * 60)
    print()
    
    # Step 1: Check environment variables
    env_results = check_env_vars()
    
    # Step 2: Check AWS ECS (if requested)
    aws_results = None
    if args.check_aws:
        aws_results = check_aws_ecs()
    
    # Step 3: Test Twilio credentials
    if env_results["valid"]:
        twilio_results = test_twilio_credentials()
    else:
        print("⚠️  Skipping Twilio credential test - environment variables invalid")
        print()
        twilio_results = {"tested": False}
    
    # Step 4: Test OTP send (if phone provided)
    otp_results = None
    if args.test_phone:
        if env_results["valid"]:
            otp_results = test_send_otp(args.test_phone)
        else:
            print("⚠️  Skipping OTP send test - environment variables invalid")
            print()
    
    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    
    if env_results["valid"]:
        print("✅ Environment variables: Valid")
    else:
        print(f"❌ Environment variables: Invalid (missing: {', '.join(env_results['missing'])})")
    
    if twilio_results.get("tested"):
        if twilio_results.get("account_valid"):
            print("✅ Twilio account: Valid")
        else:
            print("❌ Twilio account: Invalid")
        
        if twilio_results.get("verify_service_valid"):
            print("✅ Twilio Verify service: Valid")
        elif settings.TWILIO_VERIFY_SERVICE_SID:
            print("❌ Twilio Verify service: Invalid or not found")
    
    if otp_results and otp_results.get("tested"):
        if otp_results.get("success"):
            print(f"✅ OTP send test: Success")
        else:
            print(f"❌ OTP send test: Failed")
    
    print()
    
    # Recommendations
    if not env_results["valid"]:
        print("RECOMMENDATIONS:")
        print("1. Set missing environment variables in AWS ECS task definition")
        print("2. Ensure OTP_PROVIDER is set to 'twilio_verify' or 'twilio_sms' (not 'stub' in prod)")
        print("3. Verify TWILIO_VERIFY_SERVICE_SID matches your Twilio Console Verify service")
        print()
    
    if twilio_results.get("tested") and not twilio_results.get("account_valid"):
        print("RECOMMENDATIONS:")
        print("1. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are correct")
        print("2. Verify Twilio account is active (not suspended)")
        print("3. Rotate credentials if needed in Twilio Console")
        print()
    
    if twilio_results.get("tested") and settings.TWILIO_VERIFY_SERVICE_SID and not twilio_results.get("verify_service_valid"):
        print("RECOMMENDATIONS:")
        print("1. Verify TWILIO_VERIFY_SERVICE_SID matches your Verify service SID")
        print("2. Check Verify service exists and is active in Twilio Console")
        print("3. Create new Verify service if needed and update environment variable")
        print()
    
    return 0 if env_results["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())

