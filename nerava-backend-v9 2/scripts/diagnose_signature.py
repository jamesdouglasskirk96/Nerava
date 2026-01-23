#!/usr/bin/env python3
"""
Diagnose Apple Wallet Pass Signature Issues

This script helps identify why a signature is being rejected.
"""
import sys
import json
import zipfile
import subprocess
import tempfile
import os
from pathlib import Path
from io import BytesIO

def analyze_pkpass(pkpass_path: str):
    """Analyze a pkpass file to diagnose signature issues."""
    print("🔍 Apple Wallet Pass Signature Diagnostic")
    print("=" * 60)
    print()
    
    # Read pkpass
    with open(pkpass_path, 'rb') as f:
        pkpass_bytes = f.read()
    
    print(f"📦 pkpass file: {pkpass_path}")
    print(f"   Size: {len(pkpass_bytes)} bytes")
    print()
    
    # Extract and analyze
    with zipfile.ZipFile(BytesIO(pkpass_bytes), 'r') as zf:
        files = zf.namelist()
        print(f"📋 Files in pkpass ({len(files)}):")
        for f in sorted(files):
            info = zf.getinfo(f)
            print(f"   {f} ({info.file_size} bytes)")
        print()
        
        # Check required files
        required = ["pass.json", "manifest.json", "signature"]
        missing = [f for f in required if f not in files]
        if missing:
            print(f"❌ Missing required files: {', '.join(missing)}")
            return
        else:
            print("✅ All required files present")
        print()
        
        # Analyze manifest.json
        print("📄 Analyzing manifest.json...")
        manifest_bytes = zf.read("manifest.json")
        manifest = json.loads(manifest_bytes.decode('utf-8'))
        print(f"   Entries: {len(manifest)}")
        print(f"   Content: {json.dumps(manifest, indent=2)}")
        print()
        
        # Verify manifest matches files
        print("🔍 Verifying manifest matches files...")
        manifest_files = set(manifest.keys())
        zip_files = set(files) - {"manifest.json", "signature"}
        
        if manifest_files != zip_files:
            print("❌ Manifest mismatch!")
            print(f"   In manifest but not in ZIP: {manifest_files - zip_files}")
            print(f"   In ZIP but not in manifest: {zip_files - manifest_files}")
        else:
            print("✅ Manifest matches ZIP contents")
        print()
        
        # Analyze signature
        print("🔐 Analyzing signature...")
        signature_bytes = zf.read("signature")
        print(f"   Signature size: {len(signature_bytes)} bytes")
        print(f"   First 20 bytes (hex): {signature_bytes[:20].hex()}")
        print()
        
        # Check signature format (should start with PKCS7/CMS markers)
        if signature_bytes.startswith(b'\x30\x82'):
            print("✅ Signature appears to be DER-encoded (starts with 0x30 0x82)")
        else:
            print("⚠️  Signature doesn't start with expected DER markers")
        print()
        
        # Try to parse with OpenSSL
        print("🔍 Parsing signature with OpenSSL...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.der') as tmp:
            tmp.write(signature_bytes)
            tmp_path = tmp.name
        
        try:
            # Try pkcs7 command
            result = subprocess.run(
                ["openssl", "pkcs7", "-inform", "DER", "-in", tmp_path, "-print_certs", "-text"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ OpenSSL pkcs7 parse successful")
                output = result.stdout
                
                # Count certificates
                cert_count = output.count("Certificate:")
                print(f"   Certificates found: {cert_count}")
                
                # Check for WWDR
                has_wwdr = (
                    "Apple Worldwide Developer Relations" in output or
                    "WWDR" in output or
                    "Apple Inc" in output
                )
                if has_wwdr:
                    print("✅ WWDR certificate found in signature")
                else:
                    print("⚠️  WWDR certificate not clearly identified")
                
                # Show certificate subjects
                print("\n   Certificate subjects:")
                lines = output.split('\n')
                in_cert = False
                for i, line in enumerate(lines):
                    if "Subject:" in line:
                        print(f"      {line.strip()}")
                        # Show next few lines for context
                        for j in range(i+1, min(i+5, len(lines))):
                            if lines[j].strip() and not lines[j].startswith(' '):
                                break
                            if lines[j].strip():
                                print(f"         {lines[j].strip()}")
            else:
                print(f"❌ OpenSSL pkcs7 failed: {result.stderr}")
                
                # Try CMS command as fallback
                print("\n   Trying CMS command...")
                result2 = subprocess.run(
                    ["openssl", "cms", "-inform", "DER", "-in", tmp_path, "-cmsout", "-print"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result2.returncode == 0:
                    print("✅ OpenSSL cms parse successful")
                    print(f"   Output: {result2.stdout[:500]}")
                else:
                    print(f"❌ OpenSSL cms also failed: {result2.stderr}")
        except FileNotFoundError:
            print("⚠️  OpenSSL not found - cannot parse signature")
        except Exception as e:
            print(f"❌ Error parsing signature: {e}")
        finally:
            os.unlink(tmp_path)
        
        print()
        
        # Check if signature is detached
        print("🔍 Checking if signature is detached...")
        # A detached signature should NOT contain the manifest.json content
        # We can't easily check this without parsing the ASN.1 structure
        # But we can check the size - detached signatures are typically smaller
        manifest_size = len(manifest_bytes)
        signature_size = len(signature_bytes)
        
        print(f"   Manifest.json size: {manifest_size} bytes")
        print(f"   Signature size: {signature_size} bytes")
        
        if signature_size < manifest_size:
            print("✅ Signature appears detached (smaller than manifest)")
        elif signature_size > manifest_size * 2:
            print("⚠️  Signature is larger than expected - might include data")
        else:
            print("ℹ️  Signature size is reasonable")
        
        print()
        print("=" * 60)
        print("📋 Summary:")
        print("   1. Check that WWDR certificate is included")
        print("   2. Verify signature is detached (manifest not embedded)")
        print("   3. Ensure manifest.json matches ZIP contents exactly")
        print("   4. Verify certificate chain is valid")
        print("   5. Check certificate expiration dates")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_signature.py <path-to.pkpass>")
        sys.exit(1)
    
    pkpass_path = sys.argv[1]
    if not os.path.exists(pkpass_path):
        print(f"❌ File not found: {pkpass_path}")
        sys.exit(1)
    
    analyze_pkpass(pkpass_path)

