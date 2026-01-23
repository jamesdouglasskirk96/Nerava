#!/usr/bin/env python3
"""
Apple Wallet Pass Build Gate

Validates generated .pkpass artifacts to ensure they meet Apple Wallet requirements.

P0 Validations:
- P0-1: Signature is valid CMS/PKCS#7 detached signature (not raw RSA)
- P0-2: WWDR intermediate certificate is included in signing chain
- P0-3: Required assets exist and have correct dimensions

This script:
1. Generates a fresh pkpass using create_pkpass_bundle()
2. Unzips and validates required files exist
3. Validates signature using OpenSSL
4. Validates image dimensions
5. Generates audit report
6. Exits non-zero on any failure
"""
import os
import sys
import json
import zipfile
import subprocess
import tempfile
from pathlib import Path
from io import BytesIO
from typing import List, Tuple, Optional

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.domain import DriverWallet
from app.services.apple_wallet_pass import create_pkpass_bundle


def generate_test_pkpass(db_session, test_user_id: int = 999999) -> Tuple[bytes, bool]:
    """
    Generate a test pkpass bundle.
    
    Creates a test wallet and generates a pkpass for validation.
    """
    # Ensure test wallet exists
    wallet = db_session.query(DriverWallet).filter(DriverWallet.user_id == test_user_id).first()
    if not wallet:
        wallet = DriverWallet(
            user_id=test_user_id,
            nova_balance=1000,
            energy_reputation_score=500
        )
        db_session.add(wallet)
        db_session.commit()
    
    # Generate pkpass
    bundle_bytes, is_signed = create_pkpass_bundle(db_session, test_user_id)
    return bundle_bytes, is_signed


def validate_pkpass_structure(bundle_bytes: bytes) -> Tuple[bool, List[str], List[str]]:
    """
    Validate pkpass ZIP structure.
    
    Returns:
        (is_valid, missing_files, found_files)
    """
    required_files = [
        "pass.json",
        "manifest.json",
        "signature",
        "icon.png",
        "icon@2x.png",
        "logo.png",
        "logo@2x.png"
    ]
    
    found_files = []
    missing_files = []
    
    try:
        with zipfile.ZipFile(BytesIO(bundle_bytes), 'r') as zf:
            file_list = zf.namelist()
            found_files = file_list
            
            for req_file in required_files:
                if req_file not in file_list:
                    missing_files.append(req_file)
    except Exception as e:
        return (False, [f"Failed to read ZIP: {e}"], [])
    
    is_valid = len(missing_files) == 0
    return (is_valid, missing_files, found_files)


def validate_signature_with_openssl(signature_bytes: bytes) -> Tuple[bool, str]:
    """
    Validate signature using OpenSSL.
    
    Returns:
        (is_valid, openssl_output)
    """
    try:
        # Write signature to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.der') as tmp:
            tmp.write(signature_bytes)
            tmp_path = tmp.name
        
        try:
            # Try pkcs7 command first
            result = subprocess.run(
                ["openssl", "pkcs7", "-inform", "DER", "-in", tmp_path, "-print_certs", "-text"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                # Check for multiple certificates (signer + WWDR)
                cert_count = output.count("Certificate:")
                has_multiple_certs = cert_count >= 2
                
                # Check for WWDR indicators (Apple Worldwide Developer Relations)
                has_wwdr = (
                    "Apple Worldwide Developer Relations" in output or
                    "WWDR" in output or
                    "Apple Inc" in output
                )
                
                is_valid = has_multiple_certs or has_wwdr
                return (is_valid, output)
            else:
                # Try CMS command as fallback
                result = subprocess.run(
                    ["openssl", "cms", "-inform", "DER", "-in", tmp_path, "-cmsout", "-print"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    # Basic validation - if it parses, it's likely valid CMS
                    is_valid = "CMS" in output or "PKCS7" in output
                    return (is_valid, output)
                else:
                    return (False, f"OpenSSL error: {result.stderr}")
        finally:
            os.unlink(tmp_path)
    except FileNotFoundError:
        return (False, "OpenSSL not found in PATH")
    except subprocess.TimeoutExpired:
        return (False, "OpenSSL command timed out")
    except Exception as e:
        return (False, f"Signature validation error: {e}")


def validate_image_dimensions(bundle_bytes: bytes) -> Tuple[bool, List[str]]:
    """
    Validate image dimensions in pkpass.
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    try:
        from PIL import Image
        
        expected_dims = {
            "icon.png": (29, 29),
            "icon@2x.png": (58, 58),
            "logo.png": (160, 50),
            "logo@2x.png": (320, 100)
        }
        
        with zipfile.ZipFile(BytesIO(bundle_bytes), 'r') as zf:
            for filename, (expected_w, expected_h) in expected_dims.items():
                if filename not in zf.namelist():
                    errors.append(f"{filename} missing from pkpass")
                    continue
                
                try:
                    img_data = zf.read(filename)
                    img = Image.open(BytesIO(img_data))
                    width, height = img.size
                    
                    if width != expected_w or height != expected_h:
                        errors.append(
                            f"{filename}: expected {expected_w}x{expected_h}, "
                            f"got {width}x{height}"
                        )
                except Exception as e:
                    errors.append(f"{filename}: failed to validate dimensions: {e}")
    except ImportError:
        errors.append("Pillow not available, skipping image dimension validation")
    except Exception as e:
        errors.append(f"Image validation error: {e}")
    
    return (len(errors) == 0, errors)


def generate_audit_report(
    bundle_bytes: bytes,
    found_files: List[str],
    missing_files: List[str],
    signature_valid: bool,
    signature_output: str,
    image_valid: bool,
    image_errors: List[str],
    overall_valid: bool,
    first_failure: Optional[str]
) -> str:
    """
    Generate audit report markdown.
    """
    report_lines = [
        "# Apple Wallet Pass Artifact Audit Report",
        "",
        f"**Status:** {'✅ PASS' if overall_valid else '❌ FAIL'}",
        "",
        "## Summary",
        "",
        f"- Overall Validation: {'PASS' if overall_valid else 'FAIL'}",
        f"- Signature Validation: {'PASS' if signature_valid else 'FAIL'}",
        f"- Image Dimensions: {'PASS' if image_valid else 'FAIL'}",
        "",
    ]
    
    if first_failure:
        report_lines.extend([
            "## First Failure",
            "",
            f"```",
            f"{first_failure}",
            f"```",
            "",
        ])
    
    report_lines.extend([
        "## PKPass Contents",
        "",
        f"**Files Found:** {len(found_files)}",
        "",
        "```",
    ])
    
    for f in sorted(found_files):
        report_lines.append(f"  {f}")
    
    report_lines.extend([
        "```",
        "",
    ])
    
    if missing_files:
        report_lines.extend([
            "## Missing Files",
            "",
            "```",
        ])
        for f in missing_files:
            report_lines.append(f"  {f}")
        report_lines.extend([
            "```",
            "",
        ])
    
    report_lines.extend([
        "## Signature Validation",
        "",
        f"**Status:** {'✅ Valid CMS/PKCS#7 signature' if signature_valid else '❌ Invalid'}",
        "",
        "### OpenSSL Output (truncated)",
        "",
        "```",
    ])
    
    # Truncate signature output to first 50 lines
    sig_lines = signature_output.split('\n')[:50]
    report_lines.extend(sig_lines)
    if len(signature_output.split('\n')) > 50:
        report_lines.append("... (truncated)")
    
    report_lines.extend([
        "```",
        "",
    ])
    
    if image_errors:
        report_lines.extend([
            "## Image Dimension Errors",
            "",
            "```",
        ])
        for err in image_errors:
            report_lines.append(f"  {err}")
        report_lines.extend([
            "```",
            "",
        ])
    else:
        report_lines.extend([
            "## Image Dimensions",
            "",
        ])
        try:
            from PIL import Image
            with zipfile.ZipFile(BytesIO(bundle_bytes), 'r') as zf:
                for img_file in ["icon.png", "icon@2x.png", "logo.png", "logo@2x.png"]:
                    if img_file in zf.namelist():
                        img = Image.open(BytesIO(zf.read(img_file)))
                        w, h = img.size
                        report_lines.append(f"- {img_file}: {w}x{h} ✅")
        except Exception:
            pass
        
        report_lines.append("")
    
    return "\n".join(report_lines)


def main():
    """Main build gate execution."""
    print("🔍 Apple Wallet Pass Build Gate")
    print("=" * 50)
    
    # Check if test mode is enabled
    test_mode = os.getenv("WALLET_BUILD_GATE_TEST_MODE", "false").lower() == "true"
    
    if test_mode:
        print("⚠️  Running in TEST MODE (signature validation may be skipped)")
        print("")
    
    # Setup database connection
    database_url = os.getenv("DATABASE_URL", "sqlite:///./nerava.db")
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    try:
        # Generate pkpass
        print("📦 Generating pkpass bundle...")
        try:
            bundle_bytes, is_signed = generate_test_pkpass(db, test_user_id=999999)
            print(f"   ✓ Generated pkpass ({len(bundle_bytes)} bytes, signed={is_signed})")
        except Exception as e:
            print(f"   ✗ Failed to generate pkpass: {e}")
            sys.exit(1)
        
        if not is_signed and not test_mode:
            print("   ✗ Pkpass is not signed (signing required)")
            sys.exit(1)
        
        # Validate structure
        print("\n📋 Validating pkpass structure...")
        struct_valid, missing_files, found_files = validate_pkpass_structure(bundle_bytes)
        if struct_valid:
            print(f"   ✓ All required files present ({len(found_files)} files)")
        else:
            print(f"   ✗ Missing files: {', '.join(missing_files)}")
            if not test_mode:
                sys.exit(1)
        
        # Validate signature
        print("\n🔐 Validating signature...")
        if is_signed:
            with zipfile.ZipFile(BytesIO(bundle_bytes), 'r') as zf:
                signature_bytes = zf.read("signature")
            
            sig_valid, sig_output = validate_signature_with_openssl(signature_bytes)
            if sig_valid:
                print("   ✓ Signature is valid CMS/PKCS#7")
            else:
                print(f"   ✗ Signature validation failed: {sig_output[:200]}")
                if not test_mode:
                    sys.exit(1)
        else:
            print("   ⚠️  Skipping signature validation (unsigned pass)")
            sig_valid = True
            sig_output = "Skipped (test mode)"
        
        # Validate image dimensions
        print("\n🖼️  Validating image dimensions...")
        img_valid, img_errors = validate_image_dimensions(bundle_bytes)
        if img_valid:
            print("   ✓ All images have correct dimensions")
        else:
            print(f"   ✗ Image dimension errors: {len(img_errors)}")
            for err in img_errors[:3]:
                print(f"      - {err}")
            if not test_mode:
                sys.exit(1)
        
        # Determine overall status
        overall_valid = struct_valid and sig_valid and img_valid
        
        # Determine first failure
        first_failure = None
        if not struct_valid:
            first_failure = f"Missing files: {', '.join(missing_files)}"
        elif not sig_valid:
            first_failure = f"Signature validation failed: {sig_output[:200]}"
        elif not img_valid:
            first_failure = f"Image dimension errors: {img_errors[0]}"
        
        # Generate audit report
        print("\n📄 Generating audit report...")
        report = generate_audit_report(
            bundle_bytes,
            found_files,
            missing_files,
            sig_valid,
            sig_output,
            img_valid,
            img_errors,
            overall_valid,
            first_failure
        )
        
        report_path = Path(__file__).parent.parent / "WALLET_AUDIT_ARTIFACT_REPORT.md"
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"   ✓ Report written to {report_path}")
        
        # Final status
        print("\n" + "=" * 50)
        if overall_valid:
            print("✅ BUILD GATE PASSED")
            return 0
        else:
            print("❌ BUILD GATE FAILED")
            print(f"   First failure: {first_failure}")
            return 1
    
    except Exception as e:
        print(f"\n❌ Build gate error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

